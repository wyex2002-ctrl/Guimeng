"""v1.339 patch for 「来世续缘」 only (「前尘忆梦」 untouched):
1. Restores the original Hero <-> Mercenary (刺客) equipment boundary
   (all 74 刺客 weapons/armors/helmets keep 职业要求='刺客'; Hero weapons/armors/helmets
   keep their original 装备通用 state so Merc cannot wear non-shared Hero gear),
   while keeping Hero's 3 classes (战士/法师/道士) completely unrestricted across
   all 560 Hero equipment items (already 职业要求='不限' in m12/4111, plus defensive
   normalization for any 战士/法师/道士 bag item).
2. Auto-heals any save items touched by v1.338 in S.包裹物品组 back to match
   clean S.游戏道具组 templates (restoring 刺客 职业要求 and removing added 装备通用=0).
3. Retains all v1.338 坐骑/勋章/印记 enchant slots, 坐骑 -> 勋章 -> 印记 priority,
   scroll tooltips, overwrite confirmation dialog, and all v1.336..v1.299 features.
"""
import hashlib
import json
import struct
import zlib

from ljtool import Dump, Proto, rc4
from patch_v139 import W, rebuild_proto
from patch_v201 import set_string
from resource_tools import decode

BASE_SHA = '022a19cc2e1cf0c25a927c85ede5ff805c0db2d8a6243a8b6f7dfb8807fc97d7'
MODULES = (12, 14, 30)


def patch_module14_init_781(m14, runtime_src):
    """Replace embedded runtime_v338.lua string constant in 14/781 with runtime_v339.lua."""
    p = Proto(m14.protos[781].raw, 781)
    marker = b'-- Guimeng v1.338 runtime helper'
    hits = []
    for slot, val in enumerate(p.kgc):
        if isinstance(val, bytes) and val.startswith(marker):
            hits.append(p.nkgc - 1 - slot)
    assert len(hits) == 1, f'Expected exactly 1 runtime_v338.lua constant in 14/781, found {hits}'
    set_string(p, hits[0], runtime_src.encode('gbk'))
    m14.protos[781] = Proto(rebuild_proto(p), 781)
    return hits[0]


def build():
    base = (W / 'game_v338.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v338.res SHA256 mismatch'

    runtime_src = (W / 'runtime_v339.lua').read_text(encoding='utf-8')
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
                updated = value.replace(b'v1.338', b'v1.339')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.338', b'1.339')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    version_updates += 1
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v339.res').write_bytes(data)

    report = {
        'version': 'v1.339',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'runtime_v339_lua_gbk_bytes': len(runtime_gbk),
        'runtime_gc_index_14_781': runtime_gc_idx,
        'version_string_updates': version_updates,
        'changes_v339': {
            'hero_merc_boundary_preserved': 'Restored Hero <-> Mercenary (刺客) equipment boundary; Hero 3 classes (战士/法师/道士) remain unrestricted across all Hero equipment (already 职业要求=不限 in m12/4111)',
            'v338_save_self_heal': 'Auto-heals any S.包裹物品组 items touched by v1.338 back to match clean S.游戏道具组 templates (restoring 刺客 职业要求 and clearing non-template 装备通用=0)',
            'mount_medal_seal_enchants_retained': 'Retains all v1.338 坐骑/勋章/印记 enchant rules, 坐骑 -> 勋章 -> 印记 duplicate priority, scroll tooltips, and overwrite confirmation dialog',
            'qianchi_isolated': '前尘忆梦 untouched',
        },
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v339.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v339.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], 'gc_idx=', runtime_gc_idx, 'ver_updates=', version_updates)


if __name__ == '__main__':
    build()
