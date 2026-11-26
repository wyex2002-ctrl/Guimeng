"""v1.345 patch for 「来世续缘」 only (「前尘忆梦」 untouched):
Fixes the v1.344 live Windows crash on load completion where mutating Gly独 via rawset
triggered native integrity exit (C:\\cccyyy\\main:68 -> 公共方法_.lua:216 -> os.exit()):
1. Removes ALL rawset calls and ALL table writes to Gly独 from runtime_v345.lua.
2. Replaces Lua-level Gly独 wrapping with clean LuaJIT bytecode hooks on S (uv[0]):
   - m14/253 (Gly独.存档): PC 0 calls S.__gm_wal_try_save_v345(path, hero_data, key) and
     returns early via RET0 if handled by WAL fast-save; falls through to vanilla m14/253
     otherwise and calls S.__gm_wal_after_vanilla_save_v345(path) right after 核心.写到文件
     to refresh base_md5 and clear any superseded .wal.
   - m14/99 (Gly独.结束游戏): PC 9 calls S.__gm_wal_on_exit_v345(flag) before __gm_diag_exit_v164
     and Ae冻集.逻辑结束 / os.exit() to flush one synchronous vanilla .dat save and remove .wal.
3. Retains m14/256 WAL fast-load hooks (PC 1045 & PC 1111), GMWAL1 frame-sliced fast-save,
   3-second continuous auto-save, N-key [Save] button, and LuaJIT 2.0 <= 200 active locals.
4. Updates all version strings (modules 12/14/30, m12/76 OS window title bar, and m12/22232
   login UI) from 1.344 to 1.345. 「前尘忆梦」 remains completely untouched.
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

BASE_SHA = '61c6a22b90694b45f777a444893e812dde6fa1e6a9e636b4698400e5b5761f98'
MODULES = (12, 14, 30)


def patch_save_wal_14_253(m14):
    """Hook m14/253 (Gly独.存档) via S.__gm_wal_try_save_v345 & S.__gm_wal_after_vanilla_save_v345."""
    p = Proto(m14.protos[253].raw, 253)
    assert p.params == 3 and p.frame == 43
    assert OPS[p.bc[0] & 255] == 'ISNEP'
    assert OPS[p.bc[560] & 255] == 'GGET' and p.gc((p.bc[560] >> 16) & 65535) == '核心'.encode('gbk')
    assert OPS[p.bc[561] & 255] == 'TGETS' and p.gc((p.bc[561] >> 16) & 255) == '写到文件'.encode('gbk')
    assert OPS[p.bc[564] & 255] == 'UCLO'
    assert OPS[p.bc[565] & 255] == 'CALLT'
    assert OPS[p.bc[566] & 255] == 'RET0'

    k_try = gcid(p, '__gm_wal_try_save_v345')
    k_after = gcid(p, '__gm_wal_after_vanilla_save_v345')
    assert max(k_try, k_after) < 256, (k_try, k_after)

    # Pre-hook at PC 0: R0=path, R1=hero_data, R2=key; R3..R6 scratch (frame=43)
    pre_hook = [
        ad('UGET', 3, 0),                 # 0: R3 = S
        abc('TGETS', 3, 3, k_try),        # 1: R3 = S.__gm_wal_try_save_v345
        ad('ISF', 0, 3),                  # 2: if falsy -> orig PC 0
        0,                                # 3: JMP A=3 -> (0, 11)
        ad('MOV', 4, 0),                  # 4: arg1 = path
        ad('MOV', 5, 1),                  # 5: arg2 = hero_data
        ad('MOV', 6, 2),                  # 6: arg3 = key
        abc('CALL', 3, 2, 4),             # 7: R3 = fn(path, hero_data, key)
        ad('ISF', 0, 3),                  # 8: if falsy -> orig PC 0
        0,                                # 9: JMP A=3 -> (0, 11)
        ad('RET0', 0, 1),                 # 10: WAL fast-save accepted -> return
        p.bc[0],                          # 11: orig ISNEP 1 0
    ]

    # Post-hook replacing PC 564..565: close upvalues, call 核心.写到文件(R0, R36), then notify WAL
    post_hook = [
        ad('UCLO', 0, 32768),             # 0: UCLO 0 => next ins (PC+1)
        abc('CALL', 38, 2, 3),            # 1: R38 = 核心.写到文件(R0, R36)
        ad('UGET', 39, 0),                # 2: R39 = S
        abc('TGETS', 39, 39, k_after),    # 3: R39 = S.__gm_wal_after_vanilla_save_v345
        ad('ISF', 0, 39),                 # 4: if falsy -> RET1 38
        0,                                # 5: JMP A=39 -> (564, 8)
        ad('MOV', 40, 0),                 # 6: arg1 = path
        abc('CALL', 39, 1, 2),            # 7: fn(path)
        ad('RET1', 38, 2),                # 8: return R38
    ]

    patched = splice(
        p,
        {0: pre_hook, 564: post_hook, 565: []},
        (
            (0, 3, (0, 11), 3),
            (0, 9, (0, 11), 3),
            (564, 5, (564, 8), 39),
        ),
    )
    m14.protos[253] = patched
    return k_try, k_after


def patch_exit_wal_14_99(m14):
    """Hook m14/99 (Gly独.结束游戏) at PC 9 via S.__gm_wal_on_exit_v345."""
    p = Proto(m14.protos[99].raw, 99)
    assert p.params == 1 and p.frame == 5
    assert OPS[p.bc[0] & 255] == 'JMP' and (0 + 1 + (p.bc[0] >> 16) - 32768) == 9
    assert OPS[p.bc[9] & 255] == 'UGET'
    assert OPS[p.bc[10] & 255] == 'TGETS' and p.gc((p.bc[10] >> 16) & 255) == b'__gm_diag_exit_v164'

    k_exit = gcid(p, '__gm_wal_on_exit_v345')
    assert k_exit < 256, k_exit

    # Hook at PC 9: R0=flag; R3..R4 scratch (frame=5)
    exit_hook = [
        ad('UGET', 3, 0),                 # 0: R3 = S
        abc('TGETS', 3, 3, k_exit),       # 1: R3 = S.__gm_wal_on_exit_v345
        ad('ISF', 0, 3),                  # 2: if falsy -> orig PC 9
        0,                                # 3: JMP A=3 -> (9, 6)
        ad('MOV', 4, 0),                  # 4: arg1 = flag
        abc('CALL', 3, 1, 2),             # 5: fn(flag)
        p.bc[9],                          # 6: orig UGET 3 0 (__gm_diag_exit_v164)
    ]

    patched = splice(
        p,
        {9: exit_hook},
        (
            (9, 3, (9, 6), 3),
        ),
    )
    m14.protos[99] = patched
    return k_exit


def patch_module14_init_781(m14, runtime_src):
    """Replace embedded runtime_v344.lua string constant in 14/781 with runtime_v345.lua."""
    p = Proto(m14.protos[781].raw, 781)
    marker = b'-- Guimeng v1.344 runtime helper'
    hits = []
    for slot, val in enumerate(p.kgc):
        if isinstance(val, bytes) and val.startswith(marker):
            hits.append(p.nkgc - 1 - slot)
    assert len(hits) == 1, f'Expected exactly 1 runtime_v344.lua constant in 14/781, found {hits}'
    set_string(p, hits[0], runtime_src.encode('gbk'))
    m14.protos[781] = Proto(rebuild_proto(p), 781)
    return hits[0]


def verify_load_save_wal_14_256(m14):
    """Verify m14/256 (Gly独.读档) retains both v1.343 WAL hooks intact."""
    p = m14.protos[256]
    assert OPS[p.bc[1044] & 255] == 'TGETB'
    assert OPS[p.bc[1045] & 255] == 'GGET' and p.gc((p.bc[1045] >> 16) & 65535) == b'type'
    assert OPS[p.bc[1051] & 255] == 'JMP' and (1051 + 1 + (p.bc[1051] >> 16) - 32768) == 1074
    assert OPS[p.bc[1111] & 255] == 'TGETS' and p.gc((p.bc[1111] >> 16) & 255) == b'__gm_wal_try_load_v343'
    assert OPS[p.bc[1121] & 255] == 'JMP' and (1121 + 1 + (p.bc[1121] >> 16) - 32768) == 1124
    assert OPS[p.bc[1123] & 255] == 'JMP' and (1123 + 1 + (p.bc[1123] >> 16) - 32768) == 144


def build():
    base = (W / 'game_v344.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v344.res SHA256 mismatch'

    runtime_src = (W / 'runtime_v345.lua').read_text(encoding='utf-8')
    assert 'rawset' not in runtime_src, 'runtime_v345.lua must not contain rawset'
    runtime_gbk = runtime_src.encode('gbk')
    for ch in runtime_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'

    outer, modules = decode(base, MODULES)

    verify_load_save_wal_14_256(modules[14])
    k_try, k_after = patch_save_wal_14_253(modules[14])
    k_exit = patch_exit_wal_14_99(modules[14])
    runtime_gc_idx = patch_module14_init_781(modules[14], runtime_src)

    version_updates = 0
    window_title_updates = 0
    for mid, dump in modules.items():
        for p in dump.protos:
            for slot, value in enumerate(p.kgc):
                if not isinstance(value, bytes):
                    continue
                if mid == 14 and p.idx == 781 and (p.nkgc - 1 - slot) == runtime_gc_idx:
                    continue
                updated = value.replace(b'v1.344', b'v1.345')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.344', b'1.345')
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
    (W / 'game_v345.res').write_bytes(data)

    report = {
        'version': 'v1.345',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'runtime_v345_lua_gbk_bytes': len(runtime_gbk),
        'runtime_gc_index_14_781': runtime_gc_idx,
        'm14_253_const_try': k_try,
        'm14_253_const_after': k_after,
        'm14_99_const_exit': k_exit,
        'version_string_updates': version_updates,
        'window_title_updates_m12_76': window_title_updates,
        'changes_v345': {
            'fix_v344_rawset_crash': 'Removes ALL rawset calls and ALL table writes to Gly独 (which triggered native C:\\cccyyy\\main:68 -> os.exit() in v1.344 right after loading a save)',
            'bytecode_hooks_m14_253_and_m14_99': 'Hooks m14/253 (Gly独.存档) via S.__gm_wal_try_save_v345 (PC 0) & S.__gm_wal_after_vanilla_save_v345 (post 核心.写到文件) and m14/99 (Gly独.结束游戏) via S.__gm_wal_on_exit_v345 (PC 9) using pure S upvalue fields with zero Gly独 mutation',
            'retains_wal_3s_autosave_and_save_btn': 'Retains m14/256 WAL fast-load hooks, GMWAL1 3ms/frame sliced fast-save, 3-second continuous auto-save, N-key [Save] button, and LuaJIT 2.0 <= 200 active locals',
            'version_window_title_sync': 'Updates all version strings including OS game window title bar (m12/76) and login UI (m12/22232) to 1.345',
            'qianchi_isolated': '前尘忆梦 keeps original save/load/exit behavior completely untouched',
        },
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v345.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v345.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], 'gc_idx=', runtime_gc_idx,
          'ver_updates=', version_updates, 'win_title=', window_title_updates)


if __name__ == '__main__':
    build()
