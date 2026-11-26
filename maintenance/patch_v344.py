"""v1.344 patch for 「来世续缘」 only (「前尘忆梦」 untouched):
Fixes the v1.343 LuaJIT 2.0 200-local-variable compile limit bug and hardens Gly独 hooking:
1. Fixes main-chunk active local overflow (>200 locals in v1.343 due to do..end sharing
   <main>'s local register slots in LuaJIT 2.0) by encapsulating the Dual-Layer GMWAL1
   fast-save & 3-second continuous auto-save subsystem inside an explicit-parameter IIFE
   with a dedicated register frame (keeping <main> active locals well below 200 and every
   function <= 195 active locals).
2. Hardens install_wal_hooks_v343() to hook both S.script_setting.Gly独 and _G.Gly独
   using rawset (bypassing Gly独's read-only __newindex metatable in m14/302) and accept
   tonumber(U.人物选择) slots cleanly.
3. Retains m14/256 WAL fast-load hooks (PC 1045 & PC 1111) and updates all version strings
   (modules 12/14/30, m12/76 game window title bar, and m12/22232 login UI) from 1.343
   to 1.344. 「前尘忆梦」 remains completely untouched.
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

BASE_SHA = 'e73cccc4a04d64685038ac92ece8e85d3dc075608899234a0e427ae4bbdff595'
MODULES = (12, 14, 30)


def patch_module14_init_781(m14, runtime_src):
    """Replace embedded runtime_v343.lua string constant in 14/781 with runtime_v344.lua."""
    p = Proto(m14.protos[781].raw, 781)
    marker = b'-- Guimeng v1.343 runtime helper'
    hits = []
    for slot, val in enumerate(p.kgc):
        if isinstance(val, bytes) and val.startswith(marker):
            hits.append(p.nkgc - 1 - slot)
    assert len(hits) == 1, f'Expected exactly 1 runtime_v343.lua constant in 14/781, found {hits}'
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
    base = (W / 'game_v343.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v343.res SHA256 mismatch'

    runtime_src = (W / 'runtime_v344.lua').read_text(encoding='utf-8')
    runtime_gbk = runtime_src.encode('gbk')
    for ch in runtime_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'

    outer, modules = decode(base, MODULES)

    verify_load_save_wal_14_256(modules[14])
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
                updated = value.replace(b'v1.343', b'v1.344')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.343', b'1.344')
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
    (W / 'game_v344.res').write_bytes(data)

    report = {
        'version': 'v1.344',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'runtime_v344_lua_gbk_bytes': len(runtime_gbk),
        'runtime_gc_index_14_781': runtime_gc_idx,
        'version_string_updates': version_updates,
        'window_title_updates_m12_76': window_title_updates,
        'changes_v344': {
            'fix_luajit20_200_local_overflow': 'Converts WAL subsystem from do..end (which pushed runtime_v343 <main> to 210 > 200 active locals and broke LuaJIT 2.0 loadstring compilation) into an explicit-parameter IIFE with its own register frame (<main> back to ~183 active locals)',
            'harden_gly_hooks_rawset_and_dual_host': 'Hooks both S.script_setting.Gly独 and _G.Gly独 via rawset (safe against read-only __newindex metatable in m14/302) and normalizes slot with tonumber(U.人物选择)',
            'retains_v343_wal_and_3s_autosave_and_v342_save_btn': 'Retains m14/256 WAL hooks (PC 1045 & PC 1111), GMWAL1 3ms/frame sliced fast-save, 3-second MMO silent auto-save, normal-exit vanilla flush, and N-key settings [Save] button for 来世续缘',
            'version_window_title_sync': 'Updates all version strings including OS game window title bar (m12/76) and login UI (m12/22232) to 1.344',
            'qianchi_isolated': '前尘忆梦 keeps original save/load/exit behavior completely untouched',
        },
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v344.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v344.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], 'gc_idx=', runtime_gc_idx,
          'ver_updates=', version_updates, 'win_title=', window_title_updates)


if __name__ == '__main__':
    build()
