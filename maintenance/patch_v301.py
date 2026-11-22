"""Convert corpse-digging items to direct drops and upgrade ranged assassin mercenary skills (v1.301)."""
import hashlib
import json
import struct
import zlib

from ljdis import OPS
from ljtool import Dump, Proto, rc4
from patch_v139 import W, abc, ad, gcid, rebuild_proto
from patch_v201 import set_string
from patch_v289 import splice
from resource_tools import decode

BASE_SHA = 'dea530c0d8c61b622b28be864563dc32669f901870fa514af0a2e84b323bdbe7'
MODULES = (12, 14, 22, 30)


def patch_module14_init_781(m14, runtime_src):
    """Replace embedded runtime_v300.lua string constant in 14/781 with runtime_v301.lua."""
    p = Proto(m14.protos[781].raw, 781)
    marker = b'-- Guimeng v1.300 runtime helper'
    hits = []
    for slot, val in enumerate(p.kgc):
        if isinstance(val, bytes) and val.startswith(marker):
            hits.append(p.nkgc - 1 - slot)
    assert len(hits) == 1, f'Expected exactly 1 runtime_v300.lua constant in 14/781, found {hits}'
    set_string(p, hits[0], runtime_src.encode('gbk'))
    m14.protos[781] = Proto(rebuild_proto(p), 781)
    return hits[0]


def patch_corpse_drop_22_97(m22):
    """Hook 22/97 (monster death drop) to drop 附加.挖取 items directly in 「来世续缘」."""
    p = Proto(m22.protos[97].raw, 97)
    # Verify anchor instructions in 22/97
    assert OPS[p.bc[8] & 255] == 'ISEQN'
    assert OPS[p.bc[9] & 255] == 'JMP'
    assert OPS[p.bc[15] & 255] == 'UCLO'
    assert OPS[p.bc[116] & 255] == 'FNEW'
    assert OPS[p.bc[118] & 255] == 'CALL'
    assert OPS[p.bc[244] & 255] == 'RET0'

    k_has = gcid(p, b'__gm_corpse_has_v301')
    k_drop = gcid(p, b'__gm_corpse_drop_v301')

    # Splice 1 at pc 15 (early exit when #掉宝数据表 == 0 or 掉宝倍数 <= 0):
    # If __gm_corpse_has_v301(self) is true (来世续缘 + non-empty 附加.挖取 + not 镖车),
    # initialize R1={}, R2={}, R3=6, R4=0 and jump straight to pc 116 (skipping 掉宝数据表 loop).
    early_code = [
        ad('GGET', 1, k_has),        # 0: R1 = __gm_corpse_has_v301
        ad('ISF', 0, 1),             # 1: if not R1 -> early_exit (offset 12)
        0,                           # 2: JMP -> (15, 12), A=1
        ad('MOV', 2, 0),             # 3: R2 = self
        abc('CALL', 1, 2, 2),        # 4: R1 = __gm_corpse_has_v301(self)
        ad('ISF', 0, 1),             # 5: if not R1 -> early_exit (offset 12)
        0,                           # 6: JMP -> (15, 12), A=1
        ad('TNEW', 1, 0),            # 7: R1 = {}
        ad('TNEW', 2, 0),            # 8: R2 = {} (drops)
        ad('KSHORT', 3, 6),          # 9: R3 = 6 (drop radius)
        ad('KSHORT', 4, 0),          # 10: R4 = 0
        0,                           # 11: JMP -> 116, A=5
        0,                           # 12: JMP -> 244, A=0 (original early exit)
    ]

    # Splice 2 at pc 118 (right after 22/96(drops)):
    # Call __gm_corpse_drop_v301(self, drops) to append decrypted 附加.挖取 items and clear 附加.挖取.
    drop_code = [
        p.bc[118],                   # 0: original CALL 22/96(drops)
        ad('GGET', 5, k_drop),       # 1: R5 = __gm_corpse_drop_v301
        ad('ISF', 0, 5),             # 2: if not R5 -> 119
        0,                           # 3: JMP -> 119, A=5
        ad('MOV', 6, 0),             # 4: R6 = self
        ad('MOV', 7, 2),             # 5: R7 = drops
        abc('CALL', 5, 1, 3),        # 6: __gm_corpse_drop_v301(self, drops)
    ]

    patched = splice(
        p,
        {15: early_code, 118: drop_code},
        branches=(
            (15, 2, (15, 12), 1),
            (15, 6, (15, 12), 1),
            (15, 11, 116, 5),
            (15, 12, 244, 0),
            (118, 3, 119, 5),
        ),
    )
    m22.protos[97] = patched
    return len(patched.bc) - len(p.bc)


def build():
    base = (W / 'game_v300.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v300.res SHA256 mismatch'

    runtime_src = (W / 'runtime_v301.lua').read_text(encoding='utf-8')
    runtime_gbk = runtime_src.encode('gbk')
    for ch in runtime_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'

    outer, modules = decode(base, MODULES)

    runtime_gc_idx = patch_module14_init_781(modules[14], runtime_src)
    added_22_97 = patch_corpse_drop_22_97(modules[22])

    version_updates = 0
    for mid, dump in modules.items():
        for p in dump.protos:
            for slot, value in enumerate(p.kgc):
                if not isinstance(value, bytes):
                    continue
                if mid == 14 and p.idx == 781 and (p.nkgc - 1 - slot) == runtime_gc_idx:
                    continue
                updated = value.replace(b'v1.300', b'v1.301')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.300', b'1.301')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    version_updates += 1
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v301.res').write_bytes(data)

    report = {
        'version': 'v1.301',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'runtime_v301_lua_gbk_bytes': len(runtime_gbk),
        'runtime_gc_index_14_781': runtime_gc_idx,
        'added_instructions': {
            '22/97': added_22_97,
        },
        'version_string_updates': version_updates,
        'features': {
            'corpse_direct_drop': 'All 附加.挖取 corpse-digging items drop directly on monster death (incl. empty 掉宝数据表 monsters); 附加.挖取 cleared to prevent double-loot; 镖车 excluded.',
            'merc_ranged_any_enemy_blink': 'Ranged assassin mercenary skills (蝉舞/盛开/白莲/红莲/月桂) blink behind any adjacent enemy monster (Chebyshev dist <= 1), preferring tiles not adjacent to any enemy.',
            'merc_ranged_skill_projectile': 'Ranged assassin mercenary skills still launch the spinning weapon projectile and defer both damage and skill hit animation (目标动画) to projectile arrival.',
        },
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v301.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v301.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], 'gc_idx=', runtime_gc_idx, 'added_22_97=', added_22_97, 'ver_updates=', version_updates)


if __name__ == '__main__':
    build()
