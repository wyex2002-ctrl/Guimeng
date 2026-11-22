"""v1.337 patch for 「来世续缘」 only (「前尘忆梦」 untouched):
1. All enchant scroll tooltips append '#Y同名附魔不重复叠加#W' right below
   '#Y拖到武器/衣服/头盔使用#W'.
2. Equipped duplicate-enchant priority strictly follows 武器 -> 衣服 -> 头盔
   (independently for Hero 1..13 and Merc 397..409): lower-priority duplicate
   slots render as inactive (grey outlined scroll name + grey #H stat lines)
   with red '#R同名附魔不重复叠加#W' at the bottom, and immediately refresh
   when equipping, unequipping, enchanting, or finishing save load.
3. Dragging an enchant scroll onto an already-enchanted 武器/衣服/头盔
   releases Q_鼠标 and opens a confirmation dialog:
   '该装备已有【<名字>】的附魔。\n确认是否覆盖？'
   Confirming safely verifies persistent S.包裹物品组 items, overwrites the
   enchant, consumes the scroll, recalculates sets, and refreshes tooltips;
   canceling leaves both equipment and scroll untouched.
"""
import hashlib
import json
import struct
import zlib

from ljtool import Dump, Proto, rc4
from patch_v139 import W, rebuild_proto
from patch_v201 import set_string
from resource_tools import decode

BASE_SHA = 'c8034e8e15459d8dd28a2c9ce3308d2ecacd166f588e12554bbcc51b7b9da715'
MODULES = (12, 14, 30)


def patch_module14_init_781(m14, runtime_src):
    """Replace embedded runtime_v336.lua string constant in 14/781 with runtime_v337.lua."""
    p = Proto(m14.protos[781].raw, 781)
    marker = b'-- Guimeng v1.336 runtime helper'
    hits = []
    for slot, val in enumerate(p.kgc):
        if isinstance(val, bytes) and val.startswith(marker):
            hits.append(p.nkgc - 1 - slot)
    assert len(hits) == 1, f'Expected exactly 1 runtime_v336.lua constant in 14/781, found {hits}'
    set_string(p, hits[0], runtime_src.encode('gbk'))
    m14.protos[781] = Proto(rebuild_proto(p), 781)
    return hits[0]


def build():
    base = (W / 'game_v336.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v336.res SHA256 mismatch'

    runtime_src = (W / 'runtime_v337.lua').read_text(encoding='utf-8')
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
                updated = value.replace(b'v1.336', b'v1.337')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.336', b'1.337')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    version_updates += 1
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v337.res').write_bytes(data)

    report = {
        'version': 'v1.337',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'runtime_v337_lua_gbk_bytes': len(runtime_gbk),
        'runtime_gc_index_14_781': runtime_gc_idx,
        'version_string_updates': version_updates,
        'changes_v337': {
            'scroll_tooltip_non_stack_note': 'All enchant scroll tooltips append #Y同名附魔不重复叠加#W below #Y拖到武器/衣服/头盔使用#W',
            'duplicate_enchant_priority_display': 'Equipped duplicate enchants follow strict 武器 -> 衣服 -> 头盔 order (Hero & Merc independent); lower-priority duplicate slots render inactive (grey outlined scroll name + #H stats) with #R同名附魔不重复叠加#W at bottom and auto-refresh on equip/unequip/enchant/load',
            'enchant_overwrite_confirm_dialog': 'Dragging an enchant scroll onto an already-enchanted 武器/衣服/头盔 releases Q_鼠标 and opens Gly独.询问 confirmation: 该装备已有【<名字>】的附魔。\\n确认是否覆盖？',
            'qianchi_isolated': '前尘忆梦 untouched',
        },
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v337.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v337.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], 'gc_idx=', runtime_gc_idx, 'ver_updates=', version_updates)


if __name__ == '__main__':
    build()
