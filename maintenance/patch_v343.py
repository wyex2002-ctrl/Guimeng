"""v1.343 patch for 「来世续缘」 only (「前尘忆梦」 untouched):
Eliminates the 594-774ms save stutter and adds MMO-style continuous 3-second silent auto-save:
1. Dual-Layer WAL Fast-Save Architecture (「来世续缘」 only):
   - Intercepts Gly独.存档 for normal GameDate/*.dat saves (manual [Save] button, 100+ native
     auto-save triggers, and new 3s continuous auto-save) and routes them through a frame-sliced
     GMWAL1 tagged-stream serializer (<= 3ms budget/frame, zero sort_table, zero 400ms 核心.RC4,
     zero LuaJIT 65k loadstring constant limit, 100% binary/GBK-safe length-prefixed strings).
   - Captures mutable items/skills/hero/buffs/CDs atomically on frame 0 to prevent item duplication
     or loss, skips redundant disk commits while AFK (content MD5 unchanged), and commits atomically
     via .wal.tmp -> MoveFileExA(MOVEFILE_REPLACE_EXISTING) to GameDate/<save>.dat.wal without ever
     touching the underlying vanilla .dat file.
   - Binds each .wal to the exact 24-char MD5 of its underlying .dat (base_md5) plus a full payload
     MD5 checksum, so manually restoring an older backup .dat automatically supersedes any stale .wal.
2. MMO-Style Continuous 3-Second Silent Auto-Save:
   - Runs every 3,000ms in pickup_frame when 「来世续缘」 is in-game and N-key 游戏自动存档 is ON
     (镜头选择框.选中 ~= true), guarded by loading/alive/cursor-item/物品格子18/蝶恋花 checks.
   - Updates character-select INI summary only when name/level/gender/job actually changes.
3. Crash Recovery & 100% Vanilla Compatibility on Normal Exit:
   - Two minimal bytecode hooks in m14/256 (Gly独.读档): PC 1103 calls S.__gm_wal_try_load_v343
     to recover validated .wal directly into r4 (falling back seamlessly to vanilla 核心.RS if
     absent/corrupt/mismatched); PC 1045 accepts direct Lua table r4[8] without 加解密_f.
   - Wraps Gly独.结束游戏 to flush ONE synchronous vanilla m14/253 save to GameDate/<save>.dat
     and remove .wal on normal Quit Game, guaranteeing 100% vanilla save format compatibility.
4. Updates all version strings including the OS game window title bar (m12/76) and login UI (m12/22232)
   from 1.342 to 1.343.
"""
import hashlib
import json
import struct
import zlib

from ljdis import OPS
from ljtool import Dump, Proto, rc4
from patch_v139 import W, abc, ad, gcid, rebuild_proto
from patch_v201 import set_string
from patch_v289 import splice
from resource_tools import decode

BASE_SHA = '70c9710680769aa0c9ac911d0ce6f87eac4ca5e69b1ff6ab4c3be8a399c7340b'
MODULES = (12, 14, 30)


def patch_module14_init_781(m14, runtime_src):
    """Replace embedded runtime_v342.lua string constant in 14/781 with runtime_v343.lua."""
    p = Proto(m14.protos[781].raw, 781)
    marker = b'-- Guimeng v1.342 runtime helper'
    hits = []
    for slot, val in enumerate(p.kgc):
        if isinstance(val, bytes) and val.startswith(marker):
            hits.append(p.nkgc - 1 - slot)
    assert len(hits) == 1, f'Expected exactly 1 runtime_v342.lua constant in 14/781, found {hits}'
    set_string(p, hits[0], runtime_src.encode('gbk'))
    m14.protos[781] = Proto(rebuild_proto(p), 781)
    return hits[0]


def patch_load_save_wal_14_256(m14):
    """Add WAL fast-load hook (PC 1103) and direct table r4[8] hook (PC 1045) to m14/256 (Gly独.读档)."""
    p = Proto(m14.protos[256].raw, 256)
    # Verify exact anchor instructions before splicing
    assert OPS[p.bc[1044] & 255] == 'TGETB' and ((p.bc[1044] >> 8) & 255) == 22
    assert OPS[p.bc[1045] & 255] == 'ISEQP' and ((p.bc[1045] >> 8) & 255) == 22
    assert OPS[p.bc[1046] & 255] == 'JMP'
    assert (1046 + 1 + (p.bc[1046] >> 16) - 32768) == 1062
    assert OPS[p.bc[1067] & 255] == 'GGET' and p.gc((p.bc[1067] >> 16) & 65535) == '引擎'.encode('gbk')
    assert OPS[p.bc[1102] & 255] == 'CALL' and ((p.bc[1102] >> 8) & 255) == 32
    assert OPS[p.bc[1103] & 255] == 'GGET' and p.gc((p.bc[1103] >> 16) & 65535) == '核心'.encode('gbk')
    assert OPS[p.bc[1104] & 255] == 'JMP'
    assert (1104 + 1 + (p.bc[1104] >> 16) - 32768) == 144
    assert OPS[p.bc[1105] & 255] == 'UGET' and ((p.bc[1105] >> 8) & 255) == 32

    k_type = gcid(p, 'type')
    k_table = gcid(p, 'table')
    k_wal_load = gcid(p, '__gm_wal_try_load_v343')
    assert max(k_type, k_table, k_wal_load) < 256, (k_type, k_table, k_wal_load)

    # Hook 2 at PC 1045: if type(r4[8]) == 'table', assign directly to r21 and skip 加解密_f + table.loadstring
    inj_1045 = [
        ad('GGET', 23, k_type),         # 0: R23 = type
        ad('MOV', 24, 22),              # 1: R24 = R22 (r4[8])
        abc('CALL', 23, 2, 2),          # 2: R23 = type(r4[8])
        ad('ISNES', 23, k_table),       # 3: if type ~= 'table' -> orig PC 1045
        0,                              # 4: JMP A=23 -> (1045, 7)
        ad('MOV', 21, 22),              # 5: R21 = r4[8]
        0,                              # 6: JMP A=22 -> (1067, 0)
        p.bc[1045],                     # 7: orig ISEQP 22 0 (paired with PC 1046 JMP -> 1062)
    ]

    # Hook 1 at PC 1103: try WAL decode via S.__gm_wal_try_load_v343(path, base_md5, is_raw)
    # R0=path, R2=is_raw, R4=save_table, R5=base_md5; R32..R35 scratch (frame=37)
    inj_1103 = [
        ad('UGET', 32, 0),              # 0: R32 = S
        abc('TGETS', 32, 32, k_wal_load),  # 1: R32 = S.__gm_wal_try_load_v343
        ad('ISF', 0, 32),               # 2: if falsy -> orig PC 1103
        0,                              # 3: JMP A=32 -> (1103, 12)
        ad('MOV', 33, 0),               # 4: arg1 = path
        ad('MOV', 34, 5),               # 5: arg2 = base_md5
        ad('MOV', 35, 2),               # 6: arg3 = is_raw
        abc('CALL', 32, 2, 4),          # 7: R32 = fn(path, base_md5, is_raw)
        ad('ISF', 0, 32),               # 8: if nil/false -> orig PC 1103
        0,                              # 9: JMP A=32 -> (1103, 12)
        ad('MOV', 4, 32),               # 10: R4 = wal_r4
        0,                              # 11: JMP A=32 -> (1105, 0) (load.decoded -> PC 195)
        p.bc[1103],                     # 12: orig GGET 9 '核心'
    ]

    patched = splice(
        p,
        {1045: inj_1045, 1103: inj_1103},
        (
            (1045, 4, (1045, 7), 23),
            (1045, 6, (1067, 0), 22),
            (1103, 3, (1103, 12), 32),
            (1103, 9, (1103, 12), 32),
            (1103, 11, (1105, 0), 32),
        ),
    )
    m14.protos[256] = patched
    return len(patched.bc) - p.nbc, k_wal_load


def build():
    base = (W / 'game_v342.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v342.res SHA256 mismatch'

    runtime_src = (W / 'runtime_v343.lua').read_text(encoding='utf-8')
    runtime_gbk = runtime_src.encode('gbk')
    for ch in runtime_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'

    outer, modules = decode(base, MODULES)

    runtime_gc_idx = patch_module14_init_781(modules[14], runtime_src)
    wal_bc_delta, wal_k_idx = patch_load_save_wal_14_256(modules[14])

    version_updates = 0
    window_title_updates = 0
    for mid, dump in modules.items():
        for p in dump.protos:
            for slot, value in enumerate(p.kgc):
                if not isinstance(value, bytes):
                    continue
                if mid == 14 and p.idx == 781 and (p.nkgc - 1 - slot) == runtime_gc_idx:
                    continue
                updated = value.replace(b'v1.342', b'v1.343')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.342', b'1.343')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    version_updates += 1
                    if mid == 12 and p.idx == 76:
                        window_title_updates += 1
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    assert window_title_updates >= 2, f'Expected >=2 window title version updates in m12/76, got {window_title_updates}'

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v343.res').write_bytes(data)

    report = {
        'version': 'v1.343',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'runtime_v343_lua_gbk_bytes': len(runtime_gbk),
        'runtime_gc_index_14_781': runtime_gc_idx,
        'wal_14_256_bc_delta': wal_bc_delta,
        'wal_14_256_k_idx': wal_k_idx,
        'version_string_updates': version_updates,
        'window_title_updates_m12_76': window_title_updates,
        'changes_v343': {
            'dual_layer_wal_save': 'Routes 来世续缘 in-game saves (manual [Save], native auto-save triggers, and 3s continuous auto-save) through a frame-sliced GMWAL1 tagged-stream serializer (<=3ms/frame budget, zero sort_table/核心.RC4 stall) with atomic .wal.tmp -> .wal replace and MD5 + base_md5 binding',
            'mmo_3s_continuous_autosave': 'Adds 3-second silent continuous auto-save in pickup_frame (respecting N-key 游戏自动存档 toggle 镜头选择框.选中 ~= true and loading/alive/cursor/物品格子18/蝶恋花 guards), skipping redundant disk writes while AFK when content MD5 is unchanged',
            'crash_recovery_and_vanilla_exit_flush': 'm14/256 recovers validated .wal directly on load (with seamless fallback to vanilla .dat if missing/corrupt/mismatched); Gly独.结束游戏 flushes one synchronous vanilla m14/253 save to .dat and removes .wal on normal exit for 100% vanilla compatibility',
            'version_window_title_sync': 'Updates all version strings including OS game window title bar (m12/76) and login UI (m12/22232) to 1.343',
            'qianchi_isolated': '前尘忆梦 keeps original save/load/exit behavior completely untouched',
        },
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v343.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v343.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], 'gc_idx=', runtime_gc_idx,
          'wal_bc_delta=', wal_bc_delta, 'ver_updates=', version_updates, 'win_title=', window_title_updates)


if __name__ == '__main__':
    build()
