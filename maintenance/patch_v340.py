"""v1.340 patch for 「来世续缘」 only (「前尘忆梦」 untouched):
Fixes delayed damage & hit-effect feedback on mercenary ranged projectile attacks:
1. Wraps __gm_merc_visual_step_v255 alongside __gm_merc_visual_prepare_v255 in runtime_v340.lua
   (with automatic re-wrap protection on pickup_frame so save/map reload never overwrites it).
2. Replaces exact-center-pixel arrival (dist <= speed*dt against 1-frame-stale target coords)
   with live target body-edge + weapon-edge impact detection (adaptive to target 模型大小/中心Y偏移
   and weapon icon size, capped at 45% of launch distance with ticks >= 2 so close 1-cell throws
   remain clearly visible), saving ~4..9 frames of post-contact lag on normal mobs & large bosses.
3. Flushes shot.raw() immediately on the exact arrival frame inside bullet.更新 (bypassing
   shot.skip and never waiting for shot.retired or merc hitstun 硬直), with a flushed_this_frame
   guard in public.刷新 to prevent double-dt while preserving original cast retirement & DPS.
4. Retains all v1.339..v1.299 features intact; 「前尘忆梦」 remains 100% untouched.
"""
import hashlib
import json
import struct
import zlib

from ljtool import Dump, Proto, rc4
from patch_v139 import W, rebuild_proto
from patch_v201 import set_string
from resource_tools import decode

BASE_SHA = '5ab8c1bef429e11d7e8be5556a7936576a87341b335a876fac1a2a6d6f2cdf44'
MODULES = (12, 14, 30)


def patch_module14_init_781(m14, runtime_src):
    """Replace embedded runtime_v339.lua string constant in 14/781 with runtime_v340.lua."""
    p = Proto(m14.protos[781].raw, 781)
    marker = b'-- Guimeng v1.339 runtime helper'
    hits = []
    for slot, val in enumerate(p.kgc):
        if isinstance(val, bytes) and val.startswith(marker):
            hits.append(p.nkgc - 1 - slot)
    assert len(hits) == 1, f'Expected exactly 1 runtime_v339.lua constant in 14/781, found {hits}'
    set_string(p, hits[0], runtime_src.encode('gbk'))
    m14.protos[781] = Proto(rebuild_proto(p), 781)
    return hits[0]


def build():
    base = (W / 'game_v339.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v339.res SHA256 mismatch'

    runtime_src = (W / 'runtime_v340.lua').read_text(encoding='utf-8')
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
                updated = value.replace(b'v1.339', b'v1.340')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.339', b'1.340')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    version_updates += 1
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v340.res').write_bytes(data)

    report = {
        'version': 'v1.340',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'runtime_v340_lua_gbk_bytes': len(runtime_gbk),
        'runtime_gc_index_14_781': runtime_gc_idx,
        'version_string_updates': version_updates,
        'changes_v340': {
            'merc_ranged_body_edge_impact': 'Triggers projectile impact when spinning weapon edge reaches live target body boundary (adaptive to 模型大小/中心Y偏移 & weapon icon size, capped on 1-cell throws) instead of exact center pixel',
            'merc_ranged_instant_arrival_flush': 'Flushes shot.raw() immediately on the exact arrival frame inside bullet.更新 (bypassing shot.skip and never waiting for shot.retired or merc hitstun 硬直) with flushed_this_frame double-dt guard',
            'merc_ranged_dps_and_blink_preserved': 'Preserves original shot.retire cast cadence/DPS, v1.303 blink-behind-locked-target, and auto-rewrap guard on pickup_frame',
            'qianchi_isolated': '前尘忆梦 untouched',
        },
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v340.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v340.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], 'gc_idx=', runtime_gc_idx, 'ver_updates=', version_updates)


if __name__ == '__main__':
    build()
