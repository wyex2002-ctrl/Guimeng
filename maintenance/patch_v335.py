"""Optimize long-press ranged auto-cast UX in 「来世续缘」 only (v1.335):
1. Clicking while hovering friendly units (Mercenary/Summons, 所属阵营=='友方') no longer cancels auto-cast.
2. Opening functional windows (背包/仓库/商店/交易/设置/存档/读档/对话/菜单 or input focus) no longer cancels auto-cast.
3. Non-hotbar keys (Tab/Shift/Ctrl/R/Space/B/F/C/M/etc.) no longer cancel auto-cast; ONLY ESC (VK_ESCAPE=27) cancels.
「前尘忆梦」 delegates 100% untouched to original m26/88.
"""
import hashlib
import json
import struct
import zlib

from ljtool import Dump, Proto, rc4
from patch_v139 import W, rebuild_proto
from patch_v201 import set_string
from resource_tools import decode

BASE_SHA = '3dd0865f4db9395dc1a42fb57c49fe74a5f2204779394a6cf4ed0f8bc8c716be'
MODULES = (12, 14, 30)


def patch_module14_init_781(m14, runtime_src):
    """Replace embedded runtime_v334.lua string constant in 14/781 with runtime_v335.lua."""
    p = Proto(m14.protos[781].raw, 781)
    marker = b'-- Guimeng v1.334 runtime helper'
    hits = []
    for slot, val in enumerate(p.kgc):
        if isinstance(val, bytes) and val.startswith(marker):
            hits.append(p.nkgc - 1 - slot)
    assert len(hits) == 1, f'Expected exactly 1 runtime_v334.lua constant in 14/781, found {hits}'
    set_string(p, hits[0], runtime_src.encode('gbk'))
    m14.protos[781] = Proto(rebuild_proto(p), 781)
    return hits[0]


def build():
    base = (W / 'game_v334.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v334.res SHA256 mismatch'

    runtime_src = (W / 'runtime_v335.lua').read_text(encoding='utf-8')
    runtime_gbk = runtime_src.encode('gbk')
    for ch in runtime_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'

    outer, modules = decode(base, MODULES)

    runtime_gc_idx = patch_module14_init_781(modules[14], runtime_src)

    version_updates = 0
    for mid, dump in modules.items():
        for p in dump.protos:
            for slot, value in enumerate(p.kgc):
                if not isinstance(value, bytes):
                    continue
                if mid == 14 and p.idx == 781 and (p.nkgc - 1 - slot) == runtime_gc_idx:
                    continue
                updated = value.replace(b'v1.334', b'v1.335')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.334', b'1.335')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    version_updates += 1
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v335.res').write_bytes(data)

    report = {
        'version': 'v1.335',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'runtime_v335_lua_gbk_bytes': len(runtime_gbk),
        'runtime_gc_index_14_781': runtime_gc_idx,
        'version_string_updates': version_updates,
        'changes_v335': {
            'friendly_click_no_cancel': 'mouse click while hovering 所属阵营==友方 (Mercenary/Summons) no longer cancels auto-cast',
            'windows_no_cancel': 'opening 背包/仓库/商店/交易/设置/存档/读档/对话/菜单 windows or input focus no longer cancels auto-cast',
            'non_hotbar_keys_only_esc_cancels': 'Tab/Shift/Ctrl/R/Space/B/F/C/M/etc. no longer cancel auto-cast; only ESC (27) cancels',
            'qianchi_isolated': '前尘忆梦 delegates directly to original m26/88',
        },
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v335.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v335.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], 'gc_idx=', runtime_gc_idx, 'ver_updates=', version_updates)


if __name__ == '__main__':
    build()
