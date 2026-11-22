"""Fix corpse-digging direct-drop equipment 极品 stats (merge flattened wr.全图窗口 stats into out.属性) and restrict Mercenary 「（远程）」 weapon tag so Hero/general weapons (e.g. 精灵骸骨) do not show 「（远程）」 outside Mercenary slots (「来世续缘」 only, v1.332)."""
import hashlib
import json
import struct
import zlib

from ljtool import Dump, Proto, rc4
from patch_v139 import W, rebuild_proto
from patch_v201 import set_string
from resource_tools import decode

BASE_SHA = 'b9d05b41d64f2dbfd657c4c2a466f3bcb90b8af63a009aeded60b9a2dea385d2'
MODULES = (12, 14, 30)


def patch_module14_init_781(m14, runtime_src):
    """Replace embedded runtime_v331.lua string constant in 14/781 with runtime_v332.lua."""
    p = Proto(m14.protos[781].raw, 781)
    marker = b'-- Guimeng v1.331 runtime helper'
    hits = []
    for slot, val in enumerate(p.kgc):
        if isinstance(val, bytes) and val.startswith(marker):
            hits.append(p.nkgc - 1 - slot)
    assert len(hits) == 1, f'Expected exactly 1 runtime_v331.lua constant in 14/781, found {hits}'
    set_string(p, hits[0], runtime_src.encode('gbk'))
    m14.protos[781] = Proto(rebuild_proto(p), 781)
    return hits[0]


def build():
    base = (W / 'game_v331.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v331.res SHA256 mismatch'

    runtime_src = (W / 'runtime_v332.lua').read_text(encoding='utf-8')
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
                updated = value.replace(b'v1.331', b'v1.332')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.331', b'1.332')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    version_updates += 1
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v332.res').write_bytes(data)

    report = {
        'version': 'v1.332',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'runtime_v332_lua_gbk_bytes': len(runtime_gbk),
        'runtime_gc_index_14_781': runtime_gc_idx,
        'version_string_updates': version_updates,
        'fixes_v332': {
            'corpse_drop_jipin_stats': (
                'build_live_drop_item merges flattened rolled stats from wr.全图窗口 into out.属性[k] '
                '(matching m14/86 & m14/447); corpse_drop_v301 accepts callable tables / S.游戏道具组 fallback '
                'and calls wr.全图窗口(item_name, mlv, nil, nil, mon_extra)'
            ),
            'merc_ranged_weapon_tag': (
                'install_merc_name_v332 wraps __gm_merc_name_v253 (G_ROOT & S.script_setting): '
                'only pure assassin ranged weapons (职业要求==刺客 & 绑定技能==刺客普通攻击, 15 weapons) always show （远程）; '
                'non-刺客 general weapons (7 装备通用=0 weapons incl. 精灵骸骨/拍拍手/...) only show （远程） in Merc slots (333..410), '
                'stripping stale （远程） outside Merc slots and refreshing existing save tooltips once on load'
            ),
        },
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v332.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v332.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], 'gc_idx=', runtime_gc_idx, 'ver_updates=', version_updates)


if __name__ == '__main__':
    build()
