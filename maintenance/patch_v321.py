"""Fix v1.320 S.shelp callback registration on wrapped qs_item_box.Main (restoring right-click gem UI, equip/unequip set recalc, and blueprint drag), always trigger 绑定属性更新 on set recalc, and optimize O(1) bag lookup (「来世续缘」 only, v1.321)."""
import hashlib
import json
import struct
import zlib

from ljtool import Dump, Proto, rc4
from patch_v139 import W, rebuild_proto
from patch_v201 import set_string
from resource_tools import decode

BASE_SHA = 'e3042bd87e64f38014a1d23cea1b54a78cbb5ad01b3070fd0ae8064c0d66233d'
MODULES = (12, 14, 30)


def patch_module14_init_781(m14, runtime_src):
    """Replace embedded runtime_v320.lua string constant in 14/781 with runtime_v321.lua."""
    p = Proto(m14.protos[781].raw, 781)
    marker = b'-- Guimeng v1.320 runtime helper'
    hits = []
    for slot, val in enumerate(p.kgc):
        if isinstance(val, bytes) and val.startswith(marker):
            hits.append(p.nkgc - 1 - slot)
    assert len(hits) == 1, f'Expected exactly 1 runtime_v320.lua constant in 14/781, found {hits}'
    set_string(p, hits[0], runtime_src.encode('gbk'))
    m14.protos[781] = Proto(rebuild_proto(p), 781)
    return hits[0]


def build():
    base = (W / 'game_v320.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v320.res SHA256 mismatch'

    runtime_src = (W / 'runtime_v321.lua').read_text(encoding='utf-8')
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
                updated = value.replace(b'v1.320', b'v1.321')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.320', b'1.321')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    version_updates += 1
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v321.res').write_bytes(data)

    report = {
        'version': 'v1.321',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'runtime_v321_lua_gbk_bytes': len(runtime_gbk),
        'runtime_gc_index_14_781': runtime_gc_idx,
        'version_string_updates': version_updates,
        'fixes_v321': [
            'register_wrapped_qs_item_box_main_in_S_shelp_so_S_fun_never_drops_ev1_ev2_ev3_ev4',
            'always_call_hidden_更新道具属性_even_on_empty_stats_so_绑定属性更新_refreshes_hero_and_merc',
            'direct_O1_S_包裹物品组_lookup_in_recalc_single_set_and_zero_alloc_pickup_frame_guard',
            'track_req_fn_identity_and_refresh_元素图标_and_佣兵窗口_on_equipped_blueprint_drag',
        ],
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v321.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v321.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], 'gc_idx=', runtime_gc_idx, 'ver_updates=', version_updates)


if __name__ == '__main__':
    build()
