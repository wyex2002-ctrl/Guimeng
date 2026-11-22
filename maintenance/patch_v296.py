"""Eliminate uninitialized CALL register gaps and unsafe JMP.A=0 across Module 22 (v1.296)."""
import hashlib
import json
import struct
import zlib

from ljdis import OPS
from ljtool import Dump, Proto, rc4
from patch_v139 import W, ad, rebuild_proto
from patch_v201 import set_string
from patch_v289 import splice
from resource_tools import decode

BASE_SHA = '883e30c3439ac2b4ec088d8d27626ebf78f050584a5d0adcc7903baa3e9859f3'
MODULES = (12, 14, 22, 30)

# Helper encoders preserving exact opcode/fields while changing specific register operands.
def set_a(w, a): return (w & ~0x0000ff00) | ((a & 255) << 8)
def set_b(w, b): return (w & ~0xff000000) | ((b & 255) << 24)
def set_c(w, c): return (w & ~0x00ff0000) | ((c & 255) << 16)
def set_d(w, d): return (w & ~0xffff0000) | ((d & 65535) << 16)


def remap_regs(w, rmap):
    """Remap register operands of a single LuaJIT instruction word using rmap."""
    op = OPS[w & 255]
    a = (w >> 8) & 255
    b = (w >> 24) & 255
    c = (w >> 16) & 255
    d = (w >> 16) & 65535

    if op in ('GGET', 'KSTR', 'KSHORT', 'KPRI', 'UGET', 'CALL', 'JMP', 'RET1'):
        if a in rmap:
            w = set_a(w, rmap[a])
    elif op == 'MOV':
        if a in rmap:
            w = set_a(w, rmap[a])
        if d in rmap:
            w = set_d(w, rmap[d])
    elif op in ('TGETS', 'TSETS'):
        if a in rmap:
            w = set_a(w, rmap[a])
        if b in rmap:
            w = set_b(w, rmap[b])
    elif op in ('DIVVV', 'ADDVV', 'SUBVV', 'MULVV'):
        if a in rmap:
            w = set_a(w, rmap[a])
        if b in rmap:
            w = set_b(w, rmap[b])
        if c in rmap:
            w = set_c(w, rmap[c])
    elif op in ('ISF', 'IST'):
        if d in rmap:
            w = set_d(w, rmap[d])
    elif op in ('ISNES', 'ISEQS', 'ISNEN', 'ISEQN', 'ISEQP', 'ISNEP'):
        if a in rmap:
            w = set_a(w, rmap[a])
    elif op in ('ISNEV', 'ISEQV', 'ISGT', 'ISGE', 'ISLT', 'ISLE'):
        if a in rmap:
            w = set_a(w, rmap[a])
        if d in rmap:
            w = set_d(w, rmap[d])
    else:
        raise ValueError(f'Unhandled opcode in remap_regs: {op}')
    return w


def patch_range(q, start, end, rmap):
    changed = 0
    for pc in range(start, end + 1):
        nw = remap_regs(q.bc[pc], rmap)
        if nw != q.bc[pc]:
            q.bc[pc] = nw
            changed += 1
    return changed


def repair_module_22(m22):
    stats = {}

    # 1. 22/4: PC 1102..1107 (__gm_merc_range_v253) R20..R23 -> R12..R15
    p = Proto(m22.protos[4].raw, 4)
    assert OPS[p.bc[1102] & 255] == 'GGET' and p.gc(p.bc[1102] >> 16) == b'__gm_merc_range_v253'
    assert OPS[p.bc[1106] & 255] == 'CALL' and ((p.bc[1106] >> 8) & 255) == 20
    c = patch_range(p, 1102, 1107, {20: 12, 21: 13, 22: 14, 23: 15})
    m22.protos[4] = Proto(rebuild_proto(p), 4)
    stats['22/4'] = c

    # 2. 22/29: Fix JMP A=0 in hand-patched healthbar block (PC 634..668)
    #    and shift PC 649..665 from R5..R7 -> R4..R6 so R4 is initialized before CALL at PC 652/658.
    p = Proto(m22.protos[29].raw, 29)
    c = 0
    for pc, new_a in ((634, 4), (654, 4), (660, 4), (663, 4), (666, 2), (668, 5)):
        assert OPS[p.bc[pc] & 255] == 'JMP' and ((p.bc[pc] >> 8) & 255) == 0, (29, pc)
        p.bc[pc] = set_a(p.bc[pc], new_a)
        c += 1
    c += patch_range(p, 649, 665, {5: 4, 6: 5, 7: 6})
    m22.protos[29] = Proto(rebuild_proto(p), 29)
    stats['22/29'] = c

    # 3. 22/30: Fix JMP A=0 (PC 432, 619..755) and tighten high CALL slots R27..R31 -> contiguous
    p = Proto(m22.protos[30].raw, 30)
    c = 0
    jmp_16 = (432, 619, 621, 627, 633, 639, 642, 650, 653, 656, 662, 671,
              699, 705, 707, 709, 715, 721, 723, 729, 731, 734, 736, 739)
    jmp_17 = (755,)
    jmp_19 = (680, 689, 698)
    for pc in jmp_16:
        assert OPS[p.bc[pc] & 255] == 'JMP' and ((p.bc[pc] >> 8) & 255) == 0, (30, pc)
        p.bc[pc] = set_a(p.bc[pc], 16)
        c += 1
    for pc in jmp_17:
        assert OPS[p.bc[pc] & 255] == 'JMP' and ((p.bc[pc] >> 8) & 255) == 0, (30, pc)
        p.bc[pc] = set_a(p.bc[pc], 17)
        c += 1
    for pc in jmp_19:
        assert OPS[p.bc[pc] & 255] == 'JMP' and ((p.bc[pc] >> 8) & 255) == 0, (30, pc)
        p.bc[pc] = set_a(p.bc[pc], 19)
        c += 1
    c += patch_range(p, 623, 626, {27: 17, 28: 18})
    c += patch_range(p, 629, 632, {27: 17, 28: 18})
    c += patch_range(p, 635, 638, {27: 17, 28: 18})
    c += patch_range(p, 640, 641, {23: 17})
    c += patch_range(p, 646, 649, {27: 18, 28: 19})
    c += patch_range(p, 658, 661, {27: 19, 28: 20})
    c += patch_range(p, 663, 697, {27: 19, 28: 20, 29: 21, 30: 22, 31: 23})
    c += patch_range(p, 701, 704, {27: 20, 28: 21})
    c += patch_range(p, 711, 714, {27: 21, 28: 22})
    c += patch_range(p, 717, 720, {27: 22, 28: 23})
    c += patch_range(p, 725, 728, {27: 23, 28: 24})
    c += patch_range(p, 744, 753, {27: 24, 28: 25, 29: 26})
    m22.protos[30] = Proto(rebuild_proto(p), 30)
    stats['22/30'] = c

    # 4. 22/44: PC 354..363 and PC 559..568 (__gm_hit_factor_v260) R52..R54 -> R28..R30
    p = Proto(m22.protos[44].raw, 44)
    assert OPS[p.bc[354] & 255] == 'GGET' and p.gc(p.bc[354] >> 16) == b'__gm_hit_factor_v260'
    assert OPS[p.bc[559] & 255] == 'GGET' and p.gc(p.bc[559] >> 16) == b'__gm_hit_factor_v260'
    c = 0
    c += patch_range(p, 354, 363, {52: 28, 53: 29, 54: 30})
    c += patch_range(p, 559, 563, {52: 28, 53: 29, 54: 30})
    assert OPS[p.bc[566] & 255] == 'JMP' and ((p.bc[566] >> 8) & 255) == 52
    assert OPS[p.bc[568] & 255] == 'JMP' and ((p.bc[568] >> 8) & 255) == 52
    p.bc[566] = set_a(p.bc[566], 27)
    p.bc[568] = set_a(p.bc[568], 26)
    c += 2
    m22.protos[44] = Proto(rebuild_proto(p), 44)
    stats['22/44'] = c

    # 5. 22/47: PC 0..7 (__gm_guard_ignore_v224) R13..R15 -> R5..R7
    p = Proto(m22.protos[47].raw, 47)
    assert OPS[p.bc[1] & 255] == 'TGETS' and p.gc((p.bc[1] >> 16) & 255) == b'__gm_guard_ignore_v224'
    assert OPS[p.bc[3] & 255] == 'CALL' and ((p.bc[3] >> 8) & 255) == 13
    c = patch_range(p, 0, 7, {13: 5, 14: 6, 15: 7})
    m22.protos[47] = Proto(rebuild_proto(p), 47)
    stats['22/47'] = c

    # 6. 22/52: PC 29..31 (__gm_merc_visual_step_v255) R36..R37 -> R0..R1
    p = Proto(m22.protos[52].raw, 52)
    assert OPS[p.bc[29] & 255] == 'GGET' and p.gc(p.bc[29] >> 16) == b'__gm_merc_visual_step_v255'
    assert OPS[p.bc[31] & 255] == 'CALL' and ((p.bc[31] >> 8) & 255) == 36
    c = patch_range(p, 29, 31, {36: 0, 37: 1})
    m22.protos[52] = Proto(rebuild_proto(p), 52)
    stats['22/52'] = c

    # 7. 22/53: PC 399..402 (__gm_merc_visual_prepare_v255) R35..R37 -> R24..R26
    p = Proto(m22.protos[53].raw, 53)
    assert OPS[p.bc[399] & 255] == 'GGET' and p.gc(p.bc[399] >> 16) == b'__gm_merc_visual_prepare_v255'
    assert OPS[p.bc[402] & 255] == 'CALL' and ((p.bc[402] >> 8) & 255) == 35
    c = patch_range(p, 399, 402, {35: 24, 36: 25, 37: 26})
    m22.protos[53] = Proto(rebuild_proto(p), 53)
    stats['22/53'] = c

    # 8. 22/70: PC 87..92 (__gm_guard_ignore_v224) R15..R17 -> R14..R16
    p = Proto(m22.protos[70].raw, 70)
    assert OPS[p.bc[88] & 255] == 'TGETS' and p.gc((p.bc[88] >> 16) & 255) == b'__gm_guard_ignore_v224'
    assert OPS[p.bc[90] & 255] == 'CALL' and ((p.bc[90] >> 8) & 255) == 15
    c = patch_range(p, 87, 92, {15: 14, 16: 15, 17: 16})
    m22.protos[70] = Proto(rebuild_proto(p), 70)
    stats['22/70'] = c

    # 9. 22/72: PC 0..10 (__gm_guard_ignore_v224 & 停止) R7..R9 -> R1..R3
    #    and PC 112..117, 130..135, 141..146 (__gm_merc_range_v253) R11..R14 -> R3..R6
    p = Proto(m22.protos[72].raw, 72)
    assert OPS[p.bc[1] & 255] == 'TGETS' and p.gc((p.bc[1] >> 16) & 255) == b'__gm_guard_ignore_v224'
    assert OPS[p.bc[3] & 255] == 'CALL' and ((p.bc[3] >> 8) & 255) == 7
    c = 0
    c += patch_range(p, 0, 10, {7: 1, 8: 2, 9: 3})
    for s, e in ((112, 117), (130, 135), (141, 146)):
        assert OPS[p.bc[s] & 255] == 'GGET' and p.gc(p.bc[s] >> 16) == b'__gm_merc_range_v253'
        c += patch_range(p, s, e, {11: 3, 12: 4, 13: 5, 14: 6})
    m22.protos[72] = Proto(rebuild_proto(p), 72)
    stats['22/72'] = c

    # 10. 22/73: PC 0..10 (__gm_guard_ignore_v224 & 停止) R14..R16 -> R1..R3
    #     PC 88..93, 106..111, 117..122 (__gm_merc_range_v253) R18..R21 -> R3..R6
    #     PC 95, 113 JMP A=2 -> JMP A=3 (preserve R2 across merge to PC 124)
    #     PC 124..132 (__gm_merc_ranged_v253) R22..R23 -> R3..R4, JMP A=23 -> JMP A=3
    p = Proto(m22.protos[73].raw, 73)
    assert OPS[p.bc[1] & 255] == 'TGETS' and p.gc((p.bc[1] >> 16) & 255) == b'__gm_guard_ignore_v224'
    assert OPS[p.bc[3] & 255] == 'CALL' and ((p.bc[3] >> 8) & 255) == 14
    c = 0
    c += patch_range(p, 0, 10, {14: 1, 15: 2, 16: 3})
    for s, e in ((88, 93), (106, 111), (117, 122)):
        assert OPS[p.bc[s] & 255] == 'GGET' and p.gc(p.bc[s] >> 16) == b'__gm_merc_range_v253'
        c += patch_range(p, s, e, {18: 3, 19: 4, 20: 5, 21: 6})
    for pc in (95, 113):
        assert OPS[p.bc[pc] & 255] == 'JMP' and ((p.bc[pc] >> 8) & 255) == 2
        p.bc[pc] = set_a(p.bc[pc], 3)
        c += 1
    assert OPS[p.bc[124] & 255] == 'GGET' and p.gc(p.bc[124] >> 16) == b'__gm_merc_ranged_v253'
    c += patch_range(p, 124, 127, {22: 3, 23: 4})
    assert OPS[p.bc[128] & 255] == 'JMP' and ((p.bc[128] >> 8) & 255) == 23
    p.bc[128] = set_a(p.bc[128], 3)
    c += 1
    c += patch_range(p, 129, 130, {22: 3})
    assert OPS[p.bc[131] & 255] == 'JMP' and ((p.bc[131] >> 8) & 255) == 23
    p.bc[131] = set_a(p.bc[131], 3)
    c += 1
    assert OPS[p.bc[132] & 255] == 'JMP' and ((p.bc[132] >> 8) & 255) == 23
    # Before skipping FindPath (PC 133..160) to PC 161 (which calls at R6), explicitly
    # initialize R3..R5 with KNIL and preserve R0..R5 via JMP A=6.
    p = Proto(rebuild_proto(p), 73)
    p = splice(p, {132: [ad('KNIL', 3, 5), 0]}, ((132, 1, 161, 6),))
    c += 2
    m22.protos[73] = p
    stats['22/73'] = c

    # 11. 22/74: PC 71..76 and PC 86..91 (__gm_merc_range_v253) R8..R11 -> R3..R6
    p = Proto(m22.protos[74].raw, 74)
    c = 0
    for s, e in ((71, 76), (86, 91)):
        assert OPS[p.bc[s] & 255] == 'GGET' and p.gc(p.bc[s] >> 16) == b'__gm_merc_range_v253'
        c += patch_range(p, s, e, {8: 3, 9: 4, 10: 5, 11: 6})
    m22.protos[74] = Proto(rebuild_proto(p), 74)
    stats['22/74'] = c

    return stats


def build():
    base = (W / 'game_v295.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v295.res SHA256 mismatch'

    outer, modules = decode(base, MODULES)
    repaired_stats = repair_module_22(modules[22])

    version_updates = 0
    for mid, dump in modules.items():
        if mid in (12, 14, 30):
            for p in dump.protos:
                for slot, value in enumerate(p.kgc):
                    if not isinstance(value, bytes):
                        continue
                    updated = value.replace(b'v1.295', b'v1.296')
                    if mid == 12 and p.idx in (76, 22232):
                        updated = updated.replace(b'1.295', b'1.296')
                    if updated != value:
                        set_string(p, p.nkgc - 1 - slot, updated)
                        version_updates += 1
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v296.res').write_bytes(data)
    report = {
        'version': 'v1.296',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'repaired_module22_instructions': repaired_stats,
        'total_repaired_instructions': sum(repaired_stats.values()),
        'version_string_updates': version_updates,
        'jit_globally_disabled': False,
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v296.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v296.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], report['repaired_module22_instructions'])


if __name__ == '__main__':
    build()
