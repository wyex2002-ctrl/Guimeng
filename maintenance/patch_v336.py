"""v1.336 patch for 「来世续缘」 only (「前尘忆梦」 untouched):
1. Ground drop label color for the 36 ordinary mob/gathering materials
   (ORDINARY_MOB_MATERIALS) changed from bright green (0xFF80FF00) to white
   (-1 / #FFFFFF) via 地图物品类.初始化 wrapper in runtime_v336.lua, while
   restoring item.颜色值 immediately after label creation (bag/tooltip/auto-sell
   unchanged) and setting __gm_ground_label_color_v287 = -1 for partial-pickup
   stack shrink consistency. Boss/rare/quest/enchant/gem materials, ores, and
   equipment keep original colors.
2. Hardened corpse-digging direct-drop 极品 generation (corpse_drop_v301 +
   build_live_drop_item): coerce numeric mlv (tonumber(mlv) or 15), strengthen
   unproxy() with __call fallback, and track diagnostic roll counters in
   S.__gm_corpse_jipin_stats_v336.
"""
import hashlib
import json
import struct
import zlib

from ljtool import Dump, Proto, rc4
from patch_v139 import W, rebuild_proto
from patch_v201 import set_string
from resource_tools import decode

BASE_SHA = '43fa1cf89756e180773336659e00822a677b5d728c6dc3d9ade9243f78fe4504'
MODULES = (12, 14, 30)


def patch_module14_init_781(m14, runtime_src):
    """Replace embedded runtime_v335.lua string constant in 14/781 with runtime_v336.lua."""
    p = Proto(m14.protos[781].raw, 781)
    marker = b'-- Guimeng v1.335 runtime helper'
    hits = []
    for slot, val in enumerate(p.kgc):
        if isinstance(val, bytes) and val.startswith(marker):
            hits.append(p.nkgc - 1 - slot)
    assert len(hits) == 1, f'Expected exactly 1 runtime_v335.lua constant in 14/781, found {hits}'
    set_string(p, hits[0], runtime_src.encode('gbk'))
    m14.protos[781] = Proto(rebuild_proto(p), 781)
    return hits[0]


def build():
    base = (W / 'game_v335.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v335.res SHA256 mismatch'

    runtime_src = (W / 'runtime_v336.lua').read_text(encoding='utf-8')
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
                updated = value.replace(b'v1.335', b'v1.336')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.335', b'1.336')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    version_updates += 1
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v336.res').write_bytes(data)

    report = {
        'version': 'v1.336',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'runtime_v336_lua_gbk_bytes': len(runtime_gbk),
        'runtime_gc_index_14_781': runtime_gc_idx,
        'version_string_updates': version_updates,
        'changes_v336': {
            'ordinary_materials_ground_white': '36 ORDINARY_MOB_MATERIALS ground drop names rendered in white (-1 / #FFFFFF) via 地图物品类.初始化 wrapper; item.颜色值 restored immediately after label creation; partial pickup preserves white via __gm_ground_label_color_v287',
            'corpse_drop_jipin_hardened': 'corpse_drop_v301 coerces tonumber(mlv) or 15, strengthens unproxy() with __call fallback, and records roll counters in S.__gm_corpse_jipin_stats_v336',
            'qianchi_isolated': '前尘忆梦 untouched (ordinary materials keep green ground name; corpse digging untouched)',
        },
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v336.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v336.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], 'gc_idx=', runtime_gc_idx, 'ver_updates=', version_updates)


if __name__ == '__main__':
    build()
