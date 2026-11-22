"""Fix quickbar auto-potion fallback (all potion groups) & raise 聚灵符咒(灵) cap to 50,000,000 (v1.298)."""
import hashlib
import json
import struct
import zlib

from ljdis import OPS
from ljtool import Dump, Proto, rc4
from patch_v139 import W, abc, ad, gcid, jump, rebuild_proto
from patch_v201 import set_string
from patch_v289 import splice
from resource_tools import change_numbers, decode, numbers

BASE_SHA = 'e5e4f5cf482ac1403112fd797a7f1366f2641672097d55c56157ffc72cec7233'
MODULES = (12, 14, 30)
TALISMAN_CAP = 50_000_000


def fix_quickbar_autopotion(m12):
    """In 12/302 (potions collect), fall back to quickbar slot id (PC 84) when main bag has no duplicate stock."""
    p = Proto(m12.protos[302].raw, 302)
    assert OPS[p.bc[74] & 255] == 'TGETV' and ((p.bc[74] >> 8) & 255) == 12
    assert OPS[p.bc[75] & 255] == 'ISF' and ((p.bc[75] >> 16) & 65535) == 12
    assert OPS[p.bc[76] & 255] == 'JMP' and (76 + 1 + (p.bc[76] >> 16) - 32768) == 90
    assert OPS[p.bc[84] & 255] == 'MOV' and ((p.bc[84] >> 8) & 255) == 12
    assert OPS[p.bc[89] & 255] == 'CALL' and ((p.bc[89] >> 8) & 255) == 12

    # When byName[item.名称] is nil (no duplicate potion in main bag 31..126),
    # jump to PC 84 (offer(quick, id, item, id)) instead of PC 90 (skip quickbar slot).
    # At PC 84, R0..R11 are live and R12..R16 are immediately written.
    p.bc[76] = jump(76, 84, 12)
    m12.protos[302] = Proto(rebuild_proto(p), 302)


def patch_talisman_template_12_4111(m12):
    """Give 聚灵符咒_灵 its own 附加 string constant with 最大储存ぅ50000000ぃ (leave 聚灵符咒_中 at 2000000)."""
    p = Proto(m12.protos[4111].raw, 4111)
    pc = 111116
    assert OPS[p.bc[pc] & 255] == 'KSTR' and ((p.bc[pc] >> 8) & 255) == 4
    old_k = (p.bc[pc] >> 16) & 65535
    old_s = p.gc(old_k).decode('gbk')
    assert old_s == '商店ぅ杂货店ぃ最小次数ぅ10ぃ最大次数ぅ10ぃ最小储存ぅ0ぃ最大储存ぅ2000000ぃ聚灵符咒ぅ2ぃ辞职ぅ56ぃ', old_s
    # Verify PC 111176 is indeed 聚灵符咒_灵 right below this block
    assert OPS[p.bc[111176] & 255] == 'KSTR' and p.gc((p.bc[111176] >> 16) & 65535) == '聚灵符咒_灵'.encode('gbk')

    new_s = old_s.replace('最大储存ぅ2000000ぃ', f'最大储存ぅ{TALISMAN_CAP}ぃ')
    new_k = gcid(p, new_s)
    p.bc[pc] = ad('KSTR', 4, new_k)
    m12.protos[4111] = Proto(rebuild_proto(p), 4111)
    return old_k, new_k


def patch_talisman_guard_helper(m12, pid):
    """In 12/35 & 12/259, auto-upgrade existing saved 聚灵符咒_灵's 最大储存 to 50,000,000 before use/claim."""
    p = Proto(m12.protos[pid].raw, pid)
    assert OPS[p.bc[94] & 255] == 'ISNES' and p.gc((p.bc[94] >> 16) & 65535) == '聚灵符咒_灵'.encode('gbk')
    assert OPS[p.bc[146] & 255] == 'TGETS' and p.gc((p.bc[146] >> 16) & 255) == '最大储存'.encode('gbk')
    assert OPS[p.bc[155] & 255] == 'MOV' and ((p.bc[155] >> 8) & 255) == 7 and ((p.bc[155] >> 16) & 65535) == 6
    max_k = gcid(p, '最大储存')
    assert max_k == 20, max_k

    # Append 50,000,000 as a numeric constant
    p = change_numbers(p, {}, append=(TALISMAN_CAP,))
    k50m = len(numbers(p)[0]) - 1
    assert numbers(p)[0][k50m] == TALISMAN_CAP

    # At PC 155 (R6 = validated extra table of 聚灵符咒_灵 with 最大储存 > 0):
    #   if R6.最大储存 < 50000000 then R6.最大储存 = 50000000 end
    #   MOV R7, R6
    injected = [
        abc('TGETS', 7, 6, max_k),
        ad('KNUM', 8, k50m),
        ad('ISGE', 7, 8),
        0,  # JMP A=7 -> orig PC 155 (index 5 inside injected)
        abc('TSETS', 8, 6, max_k),
        p.bc[155],
    ]
    patched = splice(p, {155: injected}, ((155, 3, (155, 5), 7),))
    m12.protos[pid] = patched
    return len(patched.bc) - p.nbc


def patch_talisman_tooltip_12_321(m12):
    """In 12/321 (item tooltip), auto-upgrade existing saved 聚灵符咒_灵's 最大储存 to 50,000,000 on display."""
    p = Proto(m12.protos[321].raw, 321)
    assert OPS[p.bc[2156] & 255] == 'TGETS' and p.gc((p.bc[2156] >> 16) & 255) == '附加'.encode('gbk')
    assert OPS[p.bc[2157] & 255] == 'KSTR' and p.gc((p.bc[2157] >> 16) & 65535) == '最大储存'.encode('gbk')
    assert OPS[p.bc[2159] & 255] == 'ISEQP' and ((p.bc[2159] >> 8) & 255) == 6
    assert OPS[p.bc[2161] & 255] == 'MOV' and ((p.bc[2161] >> 8) & 255) == 6 and ((p.bc[2161] >> 16) & 65535) == 3

    name_k = gcid(p, '名称')
    extra_k = gcid(p, '附加')
    max_k = gcid(p, '最大储存')
    ling_k = gcid(p, '聚灵符咒_灵')
    assert (name_k, extra_k, max_k, ling_k) == (5, 6, 256, 292), (name_k, extra_k, max_k, ling_k)

    p = change_numbers(p, {}, append=(TALISMAN_CAP,))
    k50m = len(numbers(p)[0]) - 1
    assert numbers(p)[0][k50m] == TALISMAN_CAP

    # At PC 2161 (R6 = R0.附加['最大储存'] ~= nil):
    #   if R0.名称 == '聚灵符咒_灵' and R6 < 50000000 then
    #       R0.附加['最大储存'] = 50000000
    #   end
    #   MOV R6, R3
    injected = [
        abc('TGETS', 7, 0, name_k),
        ad('ISNES', 7, ling_k),
        0,  # JMP A=6 -> orig PC 2161 (index 9)
        ad('KNUM', 7, k50m),
        ad('ISGE', 6, 7),
        0,  # JMP A=6 -> orig PC 2161 (index 9)
        abc('TGETS', 8, 0, extra_k),
        ad('KSTR', 9, max_k),
        abc('TSETV', 7, 8, 9),
        p.bc[2161],
    ]
    patched = splice(p, {2161: injected}, (
        (2161, 2, (2161, 9), 6),
        (2161, 5, (2161, 9), 6),
    ))
    m12.protos[321] = patched
    return len(patched.bc) - p.nbc


def build():
    base = (W / 'game_v297.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v297.res SHA256 mismatch'

    outer, modules = decode(base, MODULES)
    fix_quickbar_autopotion(modules[12])
    old_k, new_k = patch_talisman_template_12_4111(modules[12])
    add_35 = patch_talisman_guard_helper(modules[12], 35)
    add_259 = patch_talisman_guard_helper(modules[12], 259)
    add_321 = patch_talisman_tooltip_12_321(modules[12])

    version_updates = 0
    for mid, dump in modules.items():
        for p in dump.protos:
            for slot, value in enumerate(p.kgc):
                if not isinstance(value, bytes):
                    continue
                updated = value.replace(b'v1.297', b'v1.298')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.297', b'1.298')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    version_updates += 1
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v298.res').write_bytes(data)
    report = {
        'version': 'v1.298',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'quickbar_autopotion_fix': {'proto': '12/302', 'pc': 76, 'old_target': 90, 'new_target': 84},
        'talisman_cap': TALISMAN_CAP,
        'talisman_template_kstr': {'old_shared_k': old_k, 'new_ling_k': new_k},
        'added_instructions': {'12/35': add_35, '12/259': add_259, '12/321': add_321},
        'version_string_updates': version_updates,
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v298.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v298.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], report['added_instructions'])


if __name__ == '__main__':
    build()
