"""v1.346 patch for 「来世续缘」 only (「前尘忆梦」 untouched):
Suppresses all native in-game automatic save triggers in 「来世续缘」 now that the 3-second
silent WAL auto-save is active (keeping manual [Save], normal-exit vanilla flush, and new
character initial .dat creation intact):
1. Wraps Ux雌.窗口相关.存档读档 inside S.__gm_wal_boot_v346 in runtime_v346.lua (zero
   rawset, zero Gly独 mutation, <main> active locals remain 183 <= 200):
   - When 「来世续缘」 is in-game (底部窗口.可视 == true) and primary .dat exists, skips all
     native automatic 存档读档('存档', ...) calls (periodic timer m12/20, quest/escort/
     shop/forge triggers, and automatic C: backup saves) so they no longer cause redundant
     table snapshots, INI writes, or C: disk freezes.
   - Continues allowing through: manual [Save] (next_save_manual == true), normal Quit Game
     exit flush (force_vanilla == true), out-of-game/char-creation saves, missing initial
     .dat, all '读档' loads, and 100% of 「前尘忆梦」 saves.
2. Retains m14/253, m14/99, and m14/256 WAL bytecode hooks, N-key [Save] button, and
   GMWAL1 3-second continuous auto-save.
3. Updates all version strings (modules 12/14/30, m12/76 OS window title bar, and m12/22232
   login UI) from 1.345 to 1.346. 「前尘忆梦」 remains completely untouched.
"""
import hashlib
import json
import struct
import zlib

from ljdis import OPS
from ljtool import Dump, Proto, rc4
from patch_v139 import W, rebuild_proto
from patch_v201 import set_string
from resource_tools import decode

BASE_SHA = '319d761dd161aeb02cac0a4f9dbdd0da07a6c4dc5b8954e71069e819dad54ce6'
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


def patch_module14_init_781(m14, runtime_src):
    """Replace embedded runtime_v345.lua string constant in 14/781 with runtime_v346.lua."""
    p = Proto(m14.protos[781].raw, 781)
    marker = b'-- Guimeng v1.345 runtime helper'
    hits = []
    for slot, val in enumerate(p.kgc):
        if isinstance(val, bytes) and val.startswith(marker):
            hits.append(p.nkgc - 1 - slot)
    assert len(hits) == 1, f'Expected exactly 1 runtime_v345.lua constant in 14/781, found {hits}'
    set_string(p, hits[0], runtime_src.encode('gbk'))
    m14.protos[781] = Proto(rebuild_proto(p), 781)
    return hits[0]


def build():
    base = (W / 'game_v345.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v345.res SHA256 mismatch'

    runtime_src = (W / 'runtime_v346.lua').read_text(encoding='utf-8')
    assert 'rawset' not in runtime_src, 'runtime_v346.lua must not contain rawset'
    runtime_gbk = runtime_src.encode('gbk')
    for ch in runtime_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'

    outer, modules = decode(base, MODULES)

    verify_wal_bytecode_hooks(modules[14])
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
                updated = value.replace(b'v1.345', b'v1.346')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.345', b'1.346')
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
    (W / 'game_v346.res').write_bytes(data)

    report = {
        'version': 'v1.346',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'runtime_v346_lua_gbk_bytes': len(runtime_gbk),
        'runtime_gc_index_14_781': runtime_gc_idx,
        'version_string_updates': version_updates,
        'window_title_updates_m12_76': window_title_updates,
        'changes_v346': {
            'suppress_native_ingame_autosaves': 'Wraps Ux雌.窗口相关.存档读档 in 来世续缘 to suppress all native in-game automatic save triggers (periodic timer, quest/escort/shop/forge/item triggers, and automatic C: backup saves) once in-game with an existing .dat; replaced uniformly by the 3-second silent WAL auto-save',
            'preserved_save_paths': 'Manual [Save] button (next_save_manual=true), Quit Game normal exit flush (force_vanilla=true), new-character creation / missing .dat, all 读档 loads, and 100% of 前尘忆梦 saves remain completely allowed',
            'retains_v345_zero_mutation_wal': 'Retains m14/253, m14/99, and m14/256 zero-mutation WAL bytecode hooks and LuaJIT 2.0 <= 200 active locals',
            'version_window_title_sync': 'Updates all version strings including OS game window title bar (m12/76) and login UI (m12/22232) to 1.346',
            'qianchi_isolated': '前尘忆梦 keeps original auto-save, save, load, and exit behavior completely untouched',
        },
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v346.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v346.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], 'gc_idx=', runtime_gc_idx,
          'ver_updates=', version_updates, 'win_title=', window_title_updates)


if __name__ == '__main__':
    build()
