"""v1.347 patch:
1. 火影地牢密室 — 冥影魔王 (ID 1377, m12/18558 #1497):
   Sets 刷新间隔=0 -> 刷新间隔=45 so m22 natively respawns 冥影魔王 45 seconds after death.
2. 赤龙城 — 赤龙女王 (ID 1477) <-> 赤龙魔王 (ID 1478) 45-second loop:
   - Patches all 247 copies of the 随着剧烈的震动,赤龙魔王会在 timer proto in m12 so killing
     赤龙女王 spawns 赤龙魔王 after 45 seconds across all difficulties (PC 9: 300->45,
     PC 17: 450->45, PC 26: 150->45).
   - Adds S.__gm_boss_cycle_boot_v347 IIFE in runtime_v347.lua wrapping 类_事件.死亡 so
     killing 赤龙魔王 in 赤龙城 (「来世续缘」) schedules a 45-second countdown toast and
     respawns 赤龙女王 (ID 1477) via Ux雌.窗口相关.经验倍率(50, 24, nil, nil, 1477, '指定'),
     repeating the Queen -> 45s -> Demon -> 45s -> Queen loop continuously while in 赤龙城.
3. Retains all v1.346..v1.299 features and zero-mutation WAL bytecode hooks (m14/253, 99, 256),
   plus <main> active locals <= 200 and zero rawset.
4. Updates all version strings (modules 12/14/30, m12/76 OS window title bar, and m12/22232
   login UI) from 1.346 to 1.347.
"""
import hashlib
import json
import struct
import zlib

from ljdis import OPS
from ljtool import Dump, Proto, rc4
from patch_v139 import W, ad, rebuild_proto
from patch_v201 import pack_config, set_string, unpack_config
from resource_tools import decode

BASE_SHA = '16e5b454ae9f58764924d07e9eef10ba48d17579db87130dfd211b8e1c86be09'
MODULES = (12, 14, 30)


def verify_wal_bytecode_hooks(m14):
    """Verify m14/253, m14/99, and m14/256 retain v1.345 zero-mutation WAL bytecode hooks intact."""
    p253 = m14.protos[253]
    assert OPS[p253.bc[1] & 255] == 'TGETS' and p253.gc((p253.bc[1] >> 16) & 255) == b'__gm_wal_try_save_v345'
    assert OPS[p253.bc[-7] & 255] == 'TGETS' and p253.gc((p253.bc[-7] >> 16) & 255) == b'__gm_wal_after_vanilla_save_v345'

    p99 = m14.protos[99]
    assert OPS[p99.bc[10] & 255] == 'TGETS' and p99.gc((p99.bc[10] >> 16) & 255) == b'__gm_wal_on_exit_v345'

    p256 = m14.protos[256]
    assert OPS[p256.bc[1045] & 255] == 'GGET' and p256.gc((p256.bc[1045] >> 16) & 65535) == b'type'
    assert OPS[p256.bc[1111] & 255] == 'TGETS' and p256.gc((p256.bc[1111] >> 16) & 255) == b'__gm_wal_try_load_v343'


def patch_mingying_respawn_12_18558(m12):
    """Set 冥影魔王 (ID 1377) 刷新间隔=45 in m12/18558 #1497."""
    p = Proto(m12.protos[18558].raw, 18558)
    logical = 1497
    raw_val = p.gc(logical)
    assert isinstance(raw_val, bytes) and raw_val.endswith(b'*')
    body = unpack_config(raw_val)
    text = body.decode('gbk')
    assert '绑定属性=冥影魔王\r\n' in text and '事件标识=1377\r\n' in text
    old_line = '刷新间隔=0\r\n'.encode('gbk')
    new_line = '刷新间隔=45\r\n'.encode('gbk')
    assert body.count(old_line) == 1
    set_string(p, logical, pack_config(body.replace(old_line, new_line, 1)))
    m12.protos[18558] = Proto(rebuild_proto(p), 18558)
    return logical


def patch_chilong_queen_timer_12(m12):
    """Set 赤龙女王 -> 赤龙魔王 wake countdown to 45s across all 247 timer protos in m12."""
    kw = '随着剧烈的震动'.encode('gbk')
    patched_ids = []
    for p_old in m12.protos:
        if any(isinstance(v, bytes) and kw in v for v in p_old.kgc):
            p = Proto(p_old.raw, p_old.idx)
            assert p.bc[9] == ad('KSHORT', 1, 300), f'm12/{p.idx} PC 9 mismatch'
            assert p.bc[17] == ad('KSHORT', 1, 450), f'm12/{p.idx} PC 17 mismatch'
            assert p.bc[26] == ad('KSHORT', 1, 150), f'm12/{p.idx} PC 26 mismatch'
            ins45 = ad('KSHORT', 1, 45)
            p.bc[9] = ins45
            p.bc[17] = ins45
            p.bc[26] = ins45
            m12.protos[p.idx] = Proto(rebuild_proto(p), p.idx)
            patched_ids.append(p.idx)
    assert len(patched_ids) == 247, f'Expected 247 赤龙魔王 timer protos, got {len(patched_ids)}'
    return patched_ids


def patch_module14_init_781(m14, runtime_src):
    """Replace embedded runtime_v346.lua string constant in 14/781 with runtime_v347.lua."""
    p = Proto(m14.protos[781].raw, 781)
    marker = b'-- Guimeng v1.346 runtime helper'
    hits = []
    for slot, val in enumerate(p.kgc):
        if isinstance(val, bytes) and val.startswith(marker):
            hits.append(p.nkgc - 1 - slot)
    assert len(hits) == 1, f'Expected exactly 1 runtime_v346.lua constant in 14/781, found {hits}'
    set_string(p, hits[0], runtime_src.encode('gbk'))
    m14.protos[781] = Proto(rebuild_proto(p), 781)
    return hits[0]


def build():
    base = (W / 'game_v346.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v346.res SHA256 mismatch'

    runtime_src = (W / 'runtime_v347.lua').read_text(encoding='utf-8')
    assert 'rawset' not in runtime_src, 'runtime_v347.lua must not contain rawset'
    runtime_gbk = runtime_src.encode('gbk')
    for ch in runtime_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'

    outer, modules = decode(base, MODULES)

    verify_wal_bytecode_hooks(modules[14])
    mingying_gc_idx = patch_mingying_respawn_12_18558(modules[12])
    chilong_timer_protos = patch_chilong_queen_timer_12(modules[12])
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
                updated = value.replace(b'v1.346', b'v1.347')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.346', b'1.347')
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
    (W / 'game_v347.res').write_bytes(data)

    report = {
        'version': 'v1.347',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': 'm12 boss timers/configs + 来世续缘 runtime boss loop',
        'runtime_v347_lua_gbk_bytes': len(runtime_gbk),
        'runtime_gc_index_14_781': runtime_gc_idx,
        'mingying_config_12_18558_idx': mingying_gc_idx,
        'chilong_timer_protos_count': len(chilong_timer_protos),
        'version_string_updates': version_updates,
        'window_title_updates_m12_76': window_title_updates,
        'changes_v347': {
            'mingying_45s_respawn': 'Updates m12/18558 #1497 (冥影魔王, ID 1377) 刷新间隔=0 -> 45 so m22 natively respawns 冥影魔王 45s after death in 火影地牢密室',
            'chilong_queen_to_demon_45s': 'Patches all 247 copies of 随着剧烈的震动 timer proto in m12 (PC 9/17/26: 300/450/150 -> 45) so killing 赤龙女王 spawns 赤龙魔王 after 45s across all difficulties',
            'chilong_demon_to_queen_45s_loop': 'Adds S.__gm_boss_cycle_boot_v347 IIFE in runtime_v347.lua wrapping 类_事件.死亡 so killing 赤龙魔王 in 赤龙城 (来世续缘) schedules a 45s countdown toast and spawns 赤龙女王 (ID 1477) via 经验倍率(50,24,nil,nil,1477,"指定"), looping indefinitely',
            'retains_v346_wal_and_suppression': 'Retains v1.346 native autosave suppression, v1.345 zero-mutation WAL hooks, N-key [Save], and LuaJIT 2.0 <= 200 active locals',
            'version_window_title_sync': 'Updates all version strings including OS game window title bar (m12/76) and login UI (m12/22232) to 1.347',
        },
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v347.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v347.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], 'gc_idx=', runtime_gc_idx,
          'timers=', len(chilong_timer_protos), 'ver_updates=', version_updates, 'win_title=', window_title_updates)


if __name__ == '__main__':
    build()
