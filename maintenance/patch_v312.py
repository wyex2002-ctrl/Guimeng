"""Append per-slot (武器/防具/首饰) stat descriptions to gem item tooltips without '+' signs, and remove '+' / '(+X)' from equipment socketed gem info while keeping equipment's own stat formatting unchanged (「来世续缘」 only, v1.312)."""
import hashlib
import json
import struct
import zlib

from ljtool import Dump, Proto, rc4
from patch_v139 import W, rebuild_proto
from patch_v201 import set_string
from resource_tools import decode

BASE_SHA = 'aeb6d266d97617fe974ed956983026e544c47e761b83dda883d04ae865faf17e'
MODULES = (12, 14, 30)


def patch_module14_init_781(m14, runtime_src):
    """Replace embedded runtime_v311.lua string constant in 14/781 with runtime_v312.lua."""
    p = Proto(m14.protos[781].raw, 781)
    marker = b'-- Guimeng v1.311 runtime helper'
    hits = []
    for slot, val in enumerate(p.kgc):
        if isinstance(val, bytes) and val.startswith(marker):
            hits.append(p.nkgc - 1 - slot)
    assert len(hits) == 1, f'Expected exactly 1 runtime_v311.lua constant in 14/781, found {hits}'
    set_string(p, hits[0], runtime_src.encode('gbk'))
    m14.protos[781] = Proto(rebuild_proto(p), 781)
    return hits[0]


def build():
    base = (W / 'game_v311.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v311.res SHA256 mismatch'

    runtime_src = (W / 'runtime_v312.lua').read_text(encoding='utf-8')
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
                updated = value.replace(b'v1.311', b'v1.312')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.311', b'1.312')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    version_updates += 1
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v312.res').write_bytes(data)

    report = {
        'version': 'v1.312',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'runtime_v312_lua_gbk_bytes': len(runtime_gbk),
        'runtime_gc_index_14_781': runtime_gc_idx,
        'version_string_updates': version_updates,
        'tooltip_v312_changes': {
            'gem_item_tooltip': 'appends 武器 / 防具 / 首饰 socket effects from Ux雌.暴食模块() without + signs (e.g. 武器: 破坏 12-0, 防具: 防御力 0-12, 首饰: 破坏 0-6)',
            'equip_socket_section': 'removes + and (+X) from 镶嵌信息 lines (e.g. 破坏:0-1, 防御力:0-2, 准确:5, 生命值:10, 魔法值:20)',
            'equip_base_stats': 'completely unchanged (keeps existing Mir3 layout & (+X) / + display)',
        },
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v312.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v312.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], 'gc_idx=', runtime_gc_idx, 'ver_updates=', version_updates)


if __name__ == '__main__':
    build()
