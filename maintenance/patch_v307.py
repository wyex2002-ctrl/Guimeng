"""Upgrade remote 【仓库】 button (normal -> guild -> close with subtle tint) and add ordinary-mob materials to Mode 2 auto-pickup+sell in 「来世续缘」 (v1.307)."""
import hashlib
import json
import struct
import zlib

from ljtool import Dump, Proto, rc4
from patch_v139 import W, rebuild_proto
from patch_v201 import set_string
from resource_tools import decode

BASE_SHA = '0575204f1f4017a6e647b77cdc600cae5aebb9e5dcf2afef7780abcb034e0497'
MODULES = (12, 14, 30)


def patch_module14_init_781(m14, runtime_src):
    """Replace embedded runtime_v306.lua string constant in 14/781 with runtime_v307.lua."""
    p = Proto(m14.protos[781].raw, 781)
    marker = b'-- Guimeng v1.306 runtime helper'
    hits = []
    for slot, val in enumerate(p.kgc):
        if isinstance(val, bytes) and val.startswith(marker):
            hits.append(p.nkgc - 1 - slot)
    assert len(hits) == 1, f'Expected exactly 1 runtime_v306.lua constant in 14/781, found {hits}'
    set_string(p, hits[0], runtime_src.encode('gbk'))
    m14.protos[781] = Proto(rebuild_proto(p), 781)
    return hits[0]


def build():
    base = (W / 'game_v306.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v306.res SHA256 mismatch'

    runtime_src = (W / 'runtime_v307.lua').read_text(encoding='utf-8')
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
                updated = value.replace(b'v1.306', b'v1.307')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.306', b'1.307')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    version_updates += 1
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v307.res').write_bytes(data)

    report = {
        'version': 'v1.307',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'runtime_v307_lua_gbk_bytes': len(runtime_gbk),
        'runtime_gc_index_14_781': runtime_gc_idx,
        'version_string_updates': version_updates,
        'features': {
            'remote_warehouse_button': {
                'click_cycle_guild_active': 'closed -> 普通仓库 (warm amber tint) -> 关闭普通仓库+打开行会仓库 (cool teal tint) -> 关闭行会仓库 (default grey)',
                'click_cycle_guild_inactive': 'closed -> 普通仓库 (warm amber tint) -> 关闭普通仓库 (default grey)',
                'guild_activation_check': 'type(Ux雌.啾啾啵啵().行会) == "table"',
                'external_close_reset': 'Restores default grey tint immediately when window 可视 becomes false',
            },
            'mode2_autopickup_sell_materials': {
                'count': 36,
                'matches_bulk_sell_v305': True,
                'excluded': ['商会物资', '沃玛号角', '精灵骸骨', '火影晶体', '震天魔印', '飞龙剑碎片', 'all 30 *_印记', '禁止出售', '任务关联', '剧情关联'],
            },
        },
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v307.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v307.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], 'gc_idx=', runtime_gc_idx, 'ver_updates=', version_updates)


if __name__ == '__main__':
    build()
