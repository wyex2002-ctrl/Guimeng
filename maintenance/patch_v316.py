"""Tighten element spacing (攻击元素:冰(寒冰)+50) and use lowercase ASCII 'x' (强元素:冰(寒冰)x50) across equipment/set tooltips, and format non-element stats on sets & gems with '+' prefix (e.g. 破坏:+0-6, 准确:+35) in 「来世续缘」 only (v1.316)."""
import hashlib
import json
import struct
import zlib

from ljtool import Dump, Proto, rc4
from patch_v139 import W, rebuild_proto
from patch_v201 import set_string
from resource_tools import decode

BASE_SHA = 'c23312e78435bb92de8b1ed964844ec16297de899e5a8a9a2a2e3212556f4485'
MODULES = (12, 14, 30)


def patch_module14_init_781(m14, runtime_src):
    """Replace embedded runtime_v315.lua string constant in 14/781 with runtime_v316.lua."""
    p = Proto(m14.protos[781].raw, 781)
    marker = b'-- Guimeng v1.315 runtime helper'
    hits = []
    for slot, val in enumerate(p.kgc):
        if isinstance(val, bytes) and val.startswith(marker):
            hits.append(p.nkgc - 1 - slot)
    assert len(hits) == 1, f'Expected exactly 1 runtime_v315.lua constant in 14/781, found {hits}'
    set_string(p, hits[0], runtime_src.encode('gbk'))
    m14.protos[781] = Proto(rebuild_proto(p), 781)
    return hits[0]


def build():
    base = (W / 'game_v315.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v315.res SHA256 mismatch'

    runtime_src = (W / 'runtime_v316.lua').read_text(encoding='utf-8')
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
                updated = value.replace(b'v1.315', b'v1.316')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.315', b'1.316')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    version_updates += 1
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v316.res').write_bytes(data)

    report = {
        'version': 'v1.316',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'runtime_v316_lua_gbk_bytes': len(runtime_gbk),
        'runtime_gc_index_14_781': runtime_gc_idx,
        'version_string_updates': version_updates,
        'tooltip_v316_changes': {
            'compact_elements': '攻击元素:<el>(<desc>)+<N> and 强元素:<el>(<desc>)x<N> (ASCII lowercase x, no extra spaces) across equipment, set blueprints, and equipment 套装信息',
            'set_and_gem_non_element_stats': 'formatted with + prefix (e.g. 破坏:+0-6, 破坏:+12-0, 伤害:+0-15, 防御:+0-12, 魔防:+1-0, 准确:+35, 魔法值:-200)',
        },
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v316.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v316.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], 'gc_idx=', runtime_gc_idx, 'ver_updates=', version_updates)


if __name__ == '__main__':
    build()
