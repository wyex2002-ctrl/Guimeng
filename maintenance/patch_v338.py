"""v1.338 patch for 「来世续缘」 only (「前尘忆梦」 untouched):
1. Allowed enchant slots changed from 武器/衣服/头盔 to 坐骑/勋章/印记
   (internal 子类: 坐骑, 勋章, 饰品), with strict priority order
   坐骑 -> 勋章 -> 印记 (Hero 1..13 and Merc 397..409 independent):
   - Enchant scroll tooltips: '#Y拖到坐骑/勋章/印记使用#W' + '#Y同名附魔不重复叠加#W'.
   - Dragging onto any other slot (武器/衣服/头盔/鞋子/项链/手镯/戒指) blocked with
     '附魔卷只能用于坐骑、勋章或印记'.
   - Old-save enchants on non-allowed slots render grey + '#R附魔仅在坐骑/勋章/印记生效#W'.
   - Duplicate equipped enchants on lower-priority allowed slots render grey +
     '#R同名附魔不重复叠加#W' at bottom, with live refresh on equip/unequip/enchant/load.
   - Overwrite confirmation dialog applies to already-enchanted 坐骑/勋章/印记.
2. Remove class requirements on ALL equipment (「来世续缘」 only):
   - Sets 职业要求 = '不限' on all 分类=='装备' templates in S.游戏道具组 (and migrates
     S.包裹物品组 items in existing saves), and adds 附加.装备通用 = 0 on all 武器/衣服/头盔
     so Hero can equip all 刺客 gear and Merc can equip all Hero gear (gender & slot limits kept).
   - Preserves original job identity in no_job_state_v338.orig_job / added_shared so
     merc ranged tags (v1.332), 7 shared weapon notes (v1.333), and white auto-sell (SKIP_EXTRA)
     stay accurate; cleanly restores all templates when switching to 「前尘忆梦」.
"""
import hashlib
import json
import struct
import zlib

from ljtool import Dump, Proto, rc4
from patch_v139 import W, rebuild_proto
from patch_v201 import set_string
from resource_tools import decode

BASE_SHA = 'e90fd5c684eef9b19163d256c34e2c92edec6afe082a8671fd889aaab91bbf73'
MODULES = (12, 14, 30)


def patch_module14_init_781(m14, runtime_src):
    """Replace embedded runtime_v337.lua string constant in 14/781 with runtime_v338.lua."""
    p = Proto(m14.protos[781].raw, 781)
    marker = b'-- Guimeng v1.337 runtime helper'
    hits = []
    for slot, val in enumerate(p.kgc):
        if isinstance(val, bytes) and val.startswith(marker):
            hits.append(p.nkgc - 1 - slot)
    assert len(hits) == 1, f'Expected exactly 1 runtime_v337.lua constant in 14/781, found {hits}'
    set_string(p, hits[0], runtime_src.encode('gbk'))
    m14.protos[781] = Proto(rebuild_proto(p), 781)
    return hits[0]


def build():
    base = (W / 'game_v337.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v337.res SHA256 mismatch'

    runtime_src = (W / 'runtime_v338.lua').read_text(encoding='utf-8')
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
                updated = value.replace(b'v1.337', b'v1.338')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.337', b'1.338')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    version_updates += 1
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v338.res').write_bytes(data)

    report = {
        'version': 'v1.338',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'runtime_v338_lua_gbk_bytes': len(runtime_gbk),
        'runtime_gc_index_14_781': runtime_gc_idx,
        'version_string_updates': version_updates,
        'changes_v338': {
            'enchant_slots_mount_medal_seal': 'Allowed enchant slots changed to 坐骑 / 勋章 / 印记 (子类 坐骑/勋章/饰品) in strict priority order 坐骑 -> 勋章 -> 印记; all scroll/tooltip/drag/overwrite prompts updated accordingly',
            'all_equip_no_job_req': 'All equipment (分类==装备) sets 职业要求=不限 and all 武器/衣服/头盔 set 附加.装备通用=0 in 来世续缘 (both S.游戏道具组 templates and existing S.包裹物品组 items), preserving gender/slot limits and restoring originals in 前尘忆梦',
            'qianchi_isolated': '前尘忆梦 untouched',
        },
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v338.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v338.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], 'gc_idx=', runtime_gc_idx, 'ver_updates=', version_updates)


if __name__ == '__main__':
    build()
