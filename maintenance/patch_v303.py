"""Fix nil item.属性 crash on corpse-dig drops, blink behind locked target on any adjacent enemy, and set assassin merc skill cooldown to 3s (v1.303)."""
import hashlib
import json
import struct
import zlib

from ljtool import Dump, Proto, rc4
from patch_v139 import W, ad, rebuild_proto
from patch_v201 import set_string
from resource_tools import decode

BASE_SHA = '00c2acb1c566a1bf6776189156156f01c3ebc76515442c125fa685e85b604430'
MODULES = (12, 14, 30)


def patch_module14_init_781(m14, runtime_src):
    """Replace embedded runtime_v302.lua string constant in 14/781 with runtime_v303.lua."""
    p = Proto(m14.protos[781].raw, 781)
    marker = b'-- Guimeng v1.302 runtime helper'
    hits = []
    for slot, val in enumerate(p.kgc):
        if isinstance(val, bytes) and val.startswith(marker):
            hits.append(p.nkgc - 1 - slot)
    assert len(hits) == 1, f'Expected exactly 1 runtime_v302.lua constant in 14/781, found {hits}'
    set_string(p, hits[0], runtime_src.encode('gbk'))
    m14.protos[781] = Proto(rebuild_proto(p), 781)
    return hits[0]


def patch_assassin_merc_skill_cd(m12):
    """Set assassin mercenary post-skill cooldown status duration from 15~20s to 3s in 12/18045 and 12/18047."""
    # 12/18045: attack-time skill cast (蝉舞/月桂/红莲/白莲/盛开)
    p45 = Proto(m12.protos[18045].raw, 18045)
    assert p45.bc[117] == ad('KSHORT', 17, 15), f'12/18045 pc 117 mismatch: {p45.bc[117]:#x}'
    assert p45.bc[118] == ad('KSHORT', 18, 20), f'12/18045 pc 118 mismatch: {p45.bc[118]:#x}'
    p45.bc[117] = ad('KSHORT', 17, 3)
    p45.bc[118] = ad('KSHORT', 18, 3)
    m12.protos[18045] = Proto(rebuild_proto(p45), 18045)

    # 12/18047: reactive 蝉舞 cast
    p47 = Proto(m12.protos[18047].raw, 18047)
    assert p47.bc[103] == ad('KSHORT', 12, 15), f'12/18047 pc 103 mismatch: {p47.bc[103]:#x}'
    assert p47.bc[104] == ad('KSHORT', 13, 20), f'12/18047 pc 104 mismatch: {p47.bc[104]:#x}'
    p47.bc[103] = ad('KSHORT', 12, 3)
    p47.bc[104] = ad('KSHORT', 13, 3)
    m12.protos[18047] = Proto(rebuild_proto(p47), 18047)


def build():
    base = (W / 'game_v302.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v302.res SHA256 mismatch'

    runtime_src = (W / 'runtime_v303.lua').read_text(encoding='utf-8')
    runtime_gbk = runtime_src.encode('gbk')
    for ch in runtime_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'

    outer, modules = decode(base, MODULES)

    runtime_gc_idx = patch_module14_init_781(modules[14], runtime_src)
    patch_assassin_merc_skill_cd(modules[12])

    version_updates = 0
    for mid, dump in modules.items():
        for p in dump.protos:
            for slot, value in enumerate(p.kgc):
                if not isinstance(value, bytes):
                    continue
                if mid == 14 and p.idx == 781 and (p.nkgc - 1 - slot) == runtime_gc_idx:
                    continue
                updated = value.replace(b'v1.302', b'v1.303')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.302', b'1.303')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    version_updates += 1
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v303.res').write_bytes(data)

    report = {
        'version': 'v1.303',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'runtime_v303_lua_gbk_bytes': len(runtime_gbk),
        'runtime_gc_index_14_781': runtime_gc_idx,
        'added_instructions': {},
        'version_string_updates': version_updates,
        'fixes': {
            'corpse_drop_nil_attr_crash': 'Ensure decrypted corpse-dig items always have table 附加 & 属性 (plus missing scalar template fields from Sys.get) so 22/97 数据保护 never receives nil (fixes pig/chicken crash).',
            'merc_ranged_blink_behind_locked_target': 'When ANY alive enemy is adjacent (dist <= 1), ranged assassin merc skills blink to a suitable walkable tile behind the currently locked attack target (target.地图格子), preferring tiles not adjacent to any enemy.',
            'merc_ranged_rewrap_guard': 'Compare __gm_merc_visual_prepare_v255 ~= wrapped_prepare_v303 on pickup_frame so game_start (14/421 -> 14/420) reloads can never overwrite the wrapper.',
            'assassin_merc_skill_cooldown_3s': 'Changed 12/18045 (pc 117..118) & 12/18047 (pc 103..104) post-skill status duration from 15..20s to 3s.',
        },
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v303.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v303.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], 'gc_idx=', runtime_gc_idx, 'ver_updates=', version_updates)


if __name__ == '__main__':
    build()
