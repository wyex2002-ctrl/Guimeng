"""Change allowed enchant slots to 武器/衣服/头盔 (replacing 鞋子 with 头盔 across rules, drag guard, tooltips & red eligibility note) (「来世续缘」 only, v1.328)."""
import hashlib
import json
import struct
import zlib

from ljtool import Dump, Proto, rc4
from patch_v139 import W, rebuild_proto
from patch_v201 import set_string
from resource_tools import decode

BASE_SHA = '27701fc919fc4b21a8a4f63e42256aed793706dc66cc471c2d8544d408ba08fb'
MODULES = (12, 14, 30)


def patch_module14_init_781(m14, runtime_src):
    """Replace embedded runtime_v327.lua string constant in 14/781 with runtime_v328.lua."""
    p = Proto(m14.protos[781].raw, 781)
    marker = b'-- Guimeng v1.327 runtime helper'
    hits = []
    for slot, val in enumerate(p.kgc):
        if isinstance(val, bytes) and val.startswith(marker):
            hits.append(p.nkgc - 1 - slot)
    assert len(hits) == 1, f'Expected exactly 1 runtime_v327.lua constant in 14/781, found {hits}'
    set_string(p, hits[0], runtime_src.encode('gbk'))
    m14.protos[781] = Proto(rebuild_proto(p), 781)
    return hits[0]


def build():
    base = (W / 'game_v327.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v327.res SHA256 mismatch'

    runtime_src = (W / 'runtime_v328.lua').read_text(encoding='utf-8')
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
                updated = value.replace(b'v1.327', b'v1.328')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.327', b'1.328')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    version_updates += 1
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v328.res').write_bytes(data)

    report = {
        'version': 'v1.328',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'runtime_v328_lua_gbk_bytes': len(runtime_gbk),
        'runtime_gc_index_14_781': runtime_gc_idx,
        'version_string_updates': version_updates,
        'enchant_slot_updates_v328': {
            'allowed_slots': ['武器', '衣服', '头盔'],
            'scroll_hint': '#Y拖到武器/衣服/头盔使用#W',
            'drag_block_prompt': '附魔卷只能用于武器、衣服或头盔',
            'ineligible_note': '#R附魔仅在武器/衣服/头盔生效#W',
        },
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v328.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v328.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], 'gc_idx=', runtime_gc_idx, 'ver_updates=', version_updates)


if __name__ == '__main__':
    build()
