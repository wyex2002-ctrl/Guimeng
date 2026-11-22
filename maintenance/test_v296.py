"""Full static dataflow, liveness, JMP.A, J->maxslot, and reverse-diff verifier for v1.296."""
import hashlib
import json

from bytecode_relocate import BRANCHES
from ljdis import OPS
from ljtool import Proto
from native_test_utils import trees
from patch_v139 import W
from patch_v201 import set_string
from patch_v296 import BASE_SHA
from resource_tools import decode

FILES = ('patch_v296.py', 'test_v296.py')
REPAIRED_PROTOS = {4, 29, 30, 44, 47, 52, 53, 70, 72, 73, 74}

WRITES_A = {
    'MOV', 'NOT', 'UNM', 'LEN', 'ADDVN', 'SUBVN', 'MULVN', 'DIVVN', 'MODVN',
    'ADDNV', 'SUBNV', 'MULNV', 'DIVNV', 'MODNV', 'ADDVV', 'SUBVV', 'MULVV', 'DIVVV', 'MODVV', 'POW', 'CAT',
    'KSTR', 'KCDATA', 'KSHORT', 'KNUM', 'KPRI', 'KNIL', 'UGET', 'FNEW', 'TNEW', 'TDUP',
    'GGET', 'TGETV', 'TGETS', 'TGETB', 'CALL', 'CALLM', 'ITERC', 'ITERN', 'VARG', 'ISNEXT',
}
COND_OPS = {
    'ISLT', 'ISGE', 'ISLE', 'ISGT', 'ISEQV', 'ISNEV',
    'ISEQS', 'ISNES', 'ISEQN', 'ISNEN', 'ISEQP', 'ISNEP',
    'ISTC', 'ISFC', 'IST', 'ISF',
}
TERM_OPS = {'RET', 'RET0', 'RET1', 'RETM', 'CALLT', 'CALLMT'}


def proto_succs(p, pc):
    w = p.bc[pc]
    op = OPS[w & 255]
    d = (w >> 16) & 65535
    if op in TERM_OPS:
        return []
    if op in COND_OPS:
        return [x for x in (pc + 1, pc + 2) if x < p.nbc]
    if op in ('JMP', 'UCLO', 'ISNEXT'):
        t = pc + 1 + d - 32768
        return [t] if 0 <= t < p.nbc else []
    if op in ('FORI', 'FORL', 'ITERL'):
        t = pc + 1 + d - 32768
        return [x for x in (pc + 1, t) if 0 <= x < p.nbc]
    return [pc + 1] if pc + 1 < p.nbc else []


def check_uninit_and_maxslot(p):
    """Verify ZERO uninitialized CALL slots under BOTH static uninit AND LuaJIT J->maxslot semantics."""
    full_mask = (1 << p.frame) - 1
    init_u = full_mask & ~((1 << p.params) - 1)
    may_u = [None] * p.nbc
    may_u[0] = init_u
    wl = [0]

    while wl:
        pc = wl.pop()
        u = may_u[pc]
        w = p.bc[pc]
        op = OPS[w & 255]
        a, b, d = (w >> 8) & 255, (w >> 24) & 255, (w >> 16) & 65535

        nu = u
        if op == 'JMP':
            # LuaJIT lj_record.c BC_JMP: if (ra < J->maxslot) J->maxslot = ra
            # Slots >= a are discarded by JMP.A in the trace recorder!
            nu |= full_mask & ~((1 << a) - 1)
        elif op == 'KNIL':
            for r in range(a, d + 1):
                nu &= ~(1 << r)
        elif op in ('FORI', 'FORL'):
            nu &= ~(1 << (a + 3))
        elif op in ('CALL', 'CALLM'):
            for r in range(a, a + (1 if b == 0 else max(0, b - 1))):
                nu &= ~(1 << r)
        elif op in ('ITERC', 'ITERN'):
            for r in range(a, a + max(0, b - 1)):
                nu &= ~(1 << r)
        elif op == 'VARG':
            if b > 1:
                for r in range(a, a + b - 1):
                    nu &= ~(1 << r)
        elif op in WRITES_A or op in ('ISTC', 'ISFC'):
            nu &= ~(1 << a)

        for s in proto_succs(p, pc):
            if may_u[s] is None:
                may_u[s] = nu
                wl.append(s)
            elif (may_u[s] | nu) != may_u[s]:
                may_u[s] |= nu
                wl.append(s)

    call_gaps = []
    for pc, w in enumerate(p.bc):
        if may_u[pc] is None:
            continue
        op = OPS[w & 255]
        a = (w >> 8) & 255
        if op in ('CALL', 'CALLM', 'CALLT', 'CALLMT'):
            bad = may_u[pc] & ((1 << a) - 1)
            if bad:
                call_gaps.append((pc, op, a, [r for r in range(a) if (bad >> r) & 1]))
    return call_gaps


def compute_liveness(p):
    live_in = [set() for _ in range(p.nbc)]
    live_out = [set() for _ in range(p.nbc)]

    def use_def(pc):
        w = p.bc[pc]
        op = OPS[w & 255]
        a, b, c, d = (w >> 8) & 255, (w >> 24) & 255, (w >> 16) & 255, (w >> 16) & 65535
        u, df = set(), set()
        if op in ('MOV', 'NOT', 'UNM', 'LEN'):
            u.add(d); df.add(a)
        elif op in ('ADDVN', 'SUBVN', 'MULVN', 'DIVVN', 'MODVN', 'ADDNV', 'SUBNV', 'MULNV', 'DIVNV', 'MODNV'):
            u.add(b); df.add(a)
        elif op in ('ADDVV', 'SUBVV', 'MULVV', 'DIVVV', 'MODVV', 'POW'):
            u.add(b); u.add(c); df.add(a)
        elif op == 'CAT':
            for r in range(b, c + 1):
                u.add(r)
            df.add(a)
        elif op in ('KSTR', 'KCDATA', 'KSHORT', 'KNUM', 'KPRI', 'UGET', 'GGET', 'TNEW', 'TDUP', 'FNEW'):
            df.add(a)
        elif op == 'KNIL':
            for r in range(a, d + 1):
                df.add(r)
        elif op == 'USETV':
            u.add(d)
        elif op == 'GSET':
            u.add(a)
        elif op == 'TGETV':
            u.add(b); u.add(c); df.add(a)
        elif op in ('TGETS', 'TGETB'):
            u.add(b); df.add(a)
        elif op == 'TSETV':
            u.add(a); u.add(b); u.add(c)
        elif op in ('TSETS', 'TSETB'):
            u.add(a); u.add(b)
        elif op == 'TSETM':
            u.add(a - 1)
            for r in range(a, p.frame):
                u.add(r)
        elif op in ('ISLT', 'ISGE', 'ISLE', 'ISGT', 'ISEQV', 'ISNEV'):
            u.add(a); u.add(d)
        elif op in ('ISEQS', 'ISNES', 'ISEQN', 'ISNEN', 'ISEQP', 'ISNEP'):
            u.add(a)
        elif op in ('IST', 'ISF'):
            u.add(d)
        elif op in ('ISTC', 'ISFC'):
            u.add(d); df.add(a)
        elif op == 'CALL':
            for r in range(a, a + c):
                u.add(r)
            if b == 0:
                for r in range(a, p.frame):
                    df.add(r)
            else:
                for r in range(a, a + max(0, b - 1)):
                    df.add(r)
        elif op == 'CALLM':
            for r in range(a, p.frame):
                u.add(r)
            if b == 0:
                for r in range(a, p.frame):
                    df.add(r)
            else:
                for r in range(a, a + max(0, b - 1)):
                    df.add(r)
        elif op == 'CALLT':
            for r in range(a, a + d):
                u.add(r)
        elif op == 'CALLMT':
            for r in range(a, p.frame):
                u.add(r)
        elif op in ('ITERC', 'ITERN'):
            for r in range(a - 3, a):
                u.add(r)
            for r in range(a, a + max(0, b - 1)):
                df.add(r)
        elif op == 'VARG':
            if b == 0:
                for r in range(a, p.frame):
                    df.add(r)
            else:
                for r in range(a, a + max(0, b - 1)):
                    df.add(r)
        elif op == 'RET':
            for r in range(a, a + d - 1):
                u.add(r)
        elif op == 'RET1':
            u.add(a)
        elif op == 'RETM':
            for r in range(a, p.frame):
                u.add(r)
        elif op in ('FORI', 'FORL'):
            u.add(a); u.add(a + 1); u.add(a + 2); df.add(a + 3)
        elif op == 'ITERL':
            u.add(a); df.add(a - 1)
        elif op == 'ISNEXT':
            u.add(a - 3); u.add(a - 2); u.add(a - 1)
        return u, df

    changed = True
    while changed:
        changed = False
        for pc in range(p.nbc - 1, -1, -1):
            out = set()
            for s in proto_succs(p, pc):
                out |= live_in[s]
            u, df = use_def(pc)
            inn = u | (out - df)
            if out != live_out[pc] or inn != live_in[pc]:
                live_out[pc] = out
                live_in[pc] = inn
                changed = True
    return live_in, live_out


def verify(base, updated):
    outer_old, before = decode(base, range(2, 86, 2))
    outer_new, after = decode(updated, range(2, 86, 2))
    assert outer_new.protos[0].bc == outer_old.protos[0].bc and updated[-10:] == base[-10:]

    for mid, dump in after.items():
        assert dump.rebuild() == dump.raw
        assert len(dump.protos) == len(before[mid].protos)
        trees(dump)
        if mid not in (12, 14, 22, 30):
            assert dump.raw == before[mid].raw, mid
            continue
        if mid in (12, 14, 30):
            for p in before[mid].protos:
                now = dump.protos[p.idx]
                restored = Proto(now.raw, now.idx)
                for slot, value in enumerate(restored.kgc):
                    if not isinstance(value, bytes):
                        continue
                    previous = value.replace(b'v1.296', b'v1.295')
                    if mid == 12 and p.idx in (76, 22232):
                        previous = previous.replace(b'1.296', b'1.295')
                    if previous != value:
                        set_string(restored, restored.nkgc - 1 - slot, previous)
                assert restored.rebuild() == p.raw, (mid, p.idx)
        else:
            # Module 22 checks
            for p in before[22].protos:
                now = dump.protos[p.idx]
                if p.idx not in REPAIRED_PROTOS:
                    assert now.raw == p.raw, (22, p.idx)
                else:
                    # Structure, header, params, frame, constants, upvalues must be identical
                    expected_nbc = p.nbc + (1 if p.idx == 73 else 0)
                    assert (now.flags, now.params, now.frame, now.nuv, now.nkgc, now.nkn, now.nbc) == (
                        p.flags, p.params, p.frame, p.nuv, p.nkgc, p.nkn, expected_nbc), (22, p.idx)
                    assert now.uv == p.uv and now.kgc == p.kgc, (22, p.idx)
                    if p.idx != 73:
                        assert now.raw[now.kend:] == p.raw[p.kend:], (22, p.idx)
                        for pc, (w0, w1) in enumerate(zip(p.bc, now.bc)):
                            assert (w0 & 255) == (w1 & 255), (22, p.idx, pc)
                            if OPS[w0 & 255] in BRANCHES:
                                assert (w0 >> 16) == (w1 >> 16), (22, p.idx, pc)
                    else:
                        assert OPS[now.bc[132] & 255] == 'KNIL' and ((now.bc[132] >> 8) & 255) == 3 and (now.bc[132] >> 16) == 5
                        assert OPS[now.bc[133] & 255] == 'JMP' and ((now.bc[133] >> 8) & 255) == 6
                        assert 133 + 1 + (now.bc[133] >> 16) - 32768 == 162

        for p in dump.protos:
            for pc, word in enumerate(p.bc):
                if OPS[word & 255] in BRANCHES:
                    assert 0 <= pc + 1 + (word >> 16) - 32768 < p.nbc, (mid, p.idx, pc)

    # Strict Module 22 invariants: ZERO uninit CALL gaps (even with JMP.A maxslot shrink!)
    m22 = after[22]
    m22_gaps = {}
    m22_bad_jmp_a = {}
    for p in m22.protos:
        gaps = check_uninit_and_maxslot(p)
        if gaps:
            m22_gaps[p.idx] = gaps
        if p.idx in REPAIRED_PROTOS:
            li, _ = compute_liveness(p)
            bad_j = []
            for pc, w in enumerate(p.bc):
                if OPS[w & 255] == 'JMP':
                    a = (w >> 8) & 255
                    t = pc + 1 + ((w >> 16) & 65535) - 32768
                    if 0 <= t < p.nbc and li[t]:
                        # Note: ignore unreachable / dead pseudo-live regs only if needed; check strict bound
                        need = max(li[t]) + 1
                        if a < need:
                            bad_j.append((pc, a, t, sorted(li[t])))
            if bad_j:
                m22_bad_jmp_a[p.idx] = bad_j

    assert not m22_gaps, f'Remaining Module 22 uninit/maxslot CALL gaps: {m22_gaps}'
    assert not m22_bad_jmp_a, f'Unsafe JMP.A below live_in[target]: {m22_bad_jmp_a}'
    # Also confirm v1.295 DID have those gaps before our fix!
    before_gaps = {p.idx: len(check_uninit_and_maxslot(p)) for p in before[22].protos if check_uninit_and_maxslot(p)}
    assert before_gaps, 'Expected v1.295 to reproduce Module 22 CALL gaps'

    return {
        'before_module22_gap_protos': before_gaps,
        'after_module22_gap_protos': m22_gaps,
        'repaired_protos_jmp_a_notes': m22_bad_jmp_a,
    }


def main():
    base = (W / 'game_v295.res').read_bytes()
    updated = (W / 'game_v296.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    checks = verify(base, updated)
    tested_files = {name: hashlib.sha256((W / name).read_bytes()).hexdigest() for name in FILES}
    report = {
        'version': 'v1.296',
        'base_sha256': BASE_SHA,
        'sha256': hashlib.sha256(updated).hexdigest(),
        'bytes': len(updated),
        'tested_files': tested_files,
        'checks': checks,
        'all_passed': True,
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v296.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v296.json').write_text(report_text, encoding='utf-8')
    print('ALL PASSED:', report['sha256'])
    print('Before gaps:', checks['before_module22_gap_protos'])
    print('After gaps :', checks['after_module22_gap_protos'])
    print('JMP.A notes:', checks['repaired_protos_jmp_a_notes'])


if __name__ == '__main__':
    main()
