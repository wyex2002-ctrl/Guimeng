"""Static dataflow/liveness/JMP.A/J->maxslot + instruction-level bytecode VM verification for v1.297."""
import copy
import hashlib
import json
import math
import random
import re
from pathlib import Path

from ljdis import OPS
from ljtool import Dump
from native_test_utils import trees
from resource_tools import decode, numbers
from test_v296 import check_uninit_and_maxslot, compute_liveness

W = Path(__file__).resolve().parent
BASE_SHA = '345acf85e29af000d1a87a3eb3e51fcd300a7eb6516a42968e2095dd12dd913b'


def analyze_proto(p):
    call_gaps = check_uninit_and_maxslot(p)
    live_in, _ = compute_liveness(p)
    bad_jmp_a = []
    for pc, w in enumerate(p.bc):
        if OPS[w & 255] == 'JMP':
            a = (w >> 8) & 255
            target = pc + 1 + ((w >> 16) & 65535) - 32768
            if 0 <= target < p.nbc and live_in[target]:
                req = max(live_in[target]) + 1
                if a < req:
                    bad_jmp_a.append((pc, a, target, req))
    return {'call_gaps': call_gaps, 'bad_jmp_a': bad_jmp_a}


class LuaJIT20VM:
    """Faithful instruction-level executor for LuaJIT 2.0.4 bytecode protos (covering 22/96 & 12/14)."""

    def __init__(self, globals_env):
        self.G = globals_env

    def _knum(self, p, idx):
        vals, _ = numbers(p)
        return vals[idx]

    def _kstr(self, p, idx):
        v = p.gc(idx)
        if isinstance(v, bytes):
            return v.decode('gbk')
        return v

    def _pri(self, d):
        return (None, False, True)[d]

    def _tdup(self, p, d):
        spec = p.gc(d)
        assert isinstance(spec, tuple) and spec[0] == 'table'
        t = {}
        for i, v in enumerate(spec[1]):
            if v is not None:
                t[i] = v.decode('gbk') if isinstance(v, bytes) else (v[1] if isinstance(v, tuple) else v)
        for k, v in spec[2]:
            kk = k.decode('gbk') if isinstance(k, bytes) else (k[1] if isinstance(k, tuple) else k)
            vv = v.decode('gbk') if isinstance(v, bytes) else (v[1] if isinstance(v, tuple) else v)
            t[kk] = vv
        return t

    def run(self, p, *args):
        R = [None] * max(p.frame + 4, 32)
        for i, a in enumerate(args):
            R[i] = a
        pc = 0
        steps = 0
        while pc < p.nbc:
            steps += 1
            assert steps < 200000, f'Infinite loop in proto {p.idx} at pc={pc}'
            w = p.bc[pc]
            op = OPS[w & 255]
            a = (w >> 8) & 255
            b = (w >> 24) & 255
            c = (w >> 16) & 255
            d = (w >> 16) & 65535

            if op == 'MOV':
                R[a] = R[d]
                pc += 1
            elif op == 'KSTR':
                R[a] = self._kstr(p, d)
                pc += 1
            elif op == 'KSHORT':
                R[a] = d if d < 32768 else d - 65536
                pc += 1
            elif op == 'KNUM':
                R[a] = self._knum(p, d)
                pc += 1
            elif op == 'KPRI':
                R[a] = self._pri(d)
                pc += 1
            elif op == 'TNEW':
                R[a] = {}
                pc += 1
            elif op == 'TDUP':
                R[a] = self._tdup(p, d)
                pc += 1
            elif op == 'GGET':
                R[a] = self.G.get(self._kstr(p, d))
                pc += 1
            elif op == 'TGETS':
                tbl = R[b]
                key = self._kstr(p, c)
                if isinstance(tbl, str):
                    if key == 'find':
                        R[a] = lambda s, pat: (re.search(pat, s) is not None)
                    else:
                        raise KeyError(f'string method {key}')
                else:
                    R[a] = tbl.get(key)
                pc += 1
            elif op == 'TGETV':
                tbl = R[b]
                key = R[c]
                if isinstance(tbl, list):
                    R[a] = tbl[key - 1] if 1 <= key <= len(tbl) else None
                else:
                    R[a] = tbl.get(key)
                pc += 1
            elif op == 'TSETS':
                R[b][self._kstr(p, c)] = R[a]
                pc += 1
            elif op == 'LEN':
                R[a] = len(R[d])
                pc += 1
            elif op == 'ADDVV':
                R[a] = R[b] + R[c]
                pc += 1
            elif op == 'SUBVV':
                R[a] = R[b] - R[c]
                pc += 1
            elif op == 'MULVV':
                R[a] = R[b] * R[c]
                pc += 1
            elif op == 'DIVVV':
                R[a] = R[b] / R[c]
                pc += 1
            elif op == 'DIVVN':
                R[a] = R[b] / self._knum(p, c)
                pc += 1
            elif op == 'CAT':
                R[a] = ''.join(str(R[r]) for r in range(b, c + 1))
                pc += 1
            elif op in ('ISEQS', 'ISNES', 'ISEQP', 'ISNEP', 'ISLT', 'ISLE', 'ISGT', 'ISGE', 'ISNEN', 'ISEQN', 'IST', 'ISF'):
                if op == 'ISEQS':
                    cond = (R[a] == self._kstr(p, d))
                elif op == 'ISNES':
                    cond = (R[a] != self._kstr(p, d))
                elif op == 'ISEQP':
                    cond = (R[a] is self._pri(d))
                elif op == 'ISNEP':
                    cond = (R[a] is not self._pri(d))
                elif op == 'ISNEN':
                    cond = (R[a] != self._knum(p, d))
                elif op == 'ISEQN':
                    cond = (R[a] == self._knum(p, d))
                elif op == 'ISLT':
                    cond = (R[a] < R[d])
                elif op == 'ISLE':
                    cond = (R[a] <= R[d])
                elif op == 'ISGT':
                    cond = (R[a] > R[d])
                elif op == 'ISGE':
                    cond = (R[a] >= R[d])
                elif op == 'IST':
                    cond = bool(R[d] is not None and R[d] is not False)
                elif op == 'ISF':
                    cond = not bool(R[d] is not None and R[d] is not False)
                if cond:
                    pc += 1  # execute following JMP
                else:
                    pc += 2  # skip following JMP
            elif op == 'JMP':
                pc = pc + 1 + d - 32768
            elif op == 'LOOP':
                pc += 1
            elif op == 'FORI':
                step = R[a + 2]
                if (step > 0 and R[a] <= R[a + 1]) or (step < 0 and R[a] >= R[a + 1]):
                    R[a + 3] = R[a]
                    pc += 1
                else:
                    pc = pc + 1 + d - 32768
            elif op == 'FORL':
                step = R[a + 2]
                R[a] = R[a] + step
                if (step > 0 and R[a] <= R[a + 1]) or (step < 0 and R[a] >= R[a + 1]):
                    R[a + 3] = R[a]
                    pc = pc + 1 + d - 32768
                else:
                    pc += 1
            elif op == 'CALL':
                fn = R[a]
                call_args = [R[a + 1 + i] for i in range(c - 1)]
                res = fn(*call_args)
                nret = b - 1
                if nret == 1:
                    R[a] = res
                elif nret > 1:
                    for i in range(nret):
                        R[a + i] = res[i] if isinstance(res, tuple) and i < len(res) else None
                pc += 1
            elif op == 'RET0':
                return None
            elif op == 'RET1':
                return R[a]
            else:
                raise NotImplementedError(f'Opcode {op} at pc={pc}')
        return None


def make_env(version_name, bonus, rng):
    templates = {
        '金币_极小': {'名称': '金币_极小', '显示名': '金币', '附加': {'小金币': 5, '大金币': 20}},
        '金币_小':   {'名称': '金币_小',   '显示名': '金币', '附加': {'小金币': 20, '大金币': 200}},
        '金币_中':   {'名称': '金币_中',   '显示名': '金币', '附加': {'小金币': 200, '大金币': 800}},
        '金币_大':   {'名称': '金币_大',   '显示名': '金币', '附加': {'小金币': 800, '大金币': 1500}},
        '金币_极大': {'名称': '金币_极大', '显示名': '金币', '附加': {'小金币': 1500, '大金币': 2000}},
    }

    def lua_type(v):
        if v is None:
            return 'nil'
        if isinstance(v, bool):
            return 'boolean'
        if isinstance(v, (int, float)):
            return 'number'
        if isinstance(v, str):
            return 'string'
        if isinstance(v, (dict, list)):
            return 'table'
        if callable(v):
            return 'function'
        return 'userdata'

    def lua_tonumber(v):
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return v
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                try:
                    return float(v)
                except ValueError:
                    return None
        return None

    def tbl_remove(lst, idx):
        return lst.pop(idx - 1)

    def tbl_insert(lst, val):
        lst.append(val)

    def tbl_copy(obj):
        return copy.deepcopy(obj)

    def sys_get(kind, name):
        if kind == 'item':
            return templates.get(name)
        return None

    def rand_int(self_obj, lo, hi):
        return rng.randint(int(lo), int(hi))

    ux = {'版本选择': version_name, '主角金币掉落': bonus}
    engine = {'取随机整数': rand_int}
    gly = {'取随机数': lambda lo, hi: rng.randint(int(lo), int(hi))}

    G = {
        'type': lua_type,
        'tonumber': lua_tonumber,
        'math': {'ceil': math.ceil, 'floor': math.floor},
        'table': {'remove': tbl_remove, 'insert': tbl_insert, 'copy': tbl_copy},
        'Sys': {'get': sys_get},
        'Ae冻': ux,
        'Ux雌': ux,
        '引擎': engine,
        'Gly独': gly,
        '物品格子18': {'道具': None},
        '是否为调试版': lambda: True,
        '掉落选择框': {'选中': True},
    }
    return G, templates


def test():
    old_bytes = (W / 'game_v296.res').read_bytes()
    new_bytes = (W / 'game_v297.res').read_bytes()
    assert hashlib.sha256(old_bytes).hexdigest() == BASE_SHA
    build = json.loads((W / 'build_v297.json').read_text(encoding='utf-8'))
    sha = hashlib.sha256(new_bytes).hexdigest()
    assert build['sha256'] == sha and build['bytes'] == len(new_bytes)

    all_mids = list(range(2, 86, 2))
    _, old = decode(old_bytes, all_mids)
    _, new = decode(new_bytes, all_mids)

    # 1. Exact reverse-diff integrity across all 42 modules
    changed_protos = {}
    for mid in all_mids:
        assert new[mid].rebuild() == new[mid].raw, mid
        trees(new[mid])
        assert len(old[mid].protos) == len(new[mid].protos), mid
        for i, (op, np) in enumerate(zip(old[mid].protos, new[mid].protos)):
            if op.raw == np.raw:
                continue
            changed_protos.setdefault(mid, []).append(i)
            if (mid, i) in ((12, 14), (22, 96)):
                continue
            # All other changed protos must ONLY be version string bumps 1.296 -> 1.297
            back = np.raw.replace(b'v1.297', b'v1.296')
            if mid == 12 and i in (76, 22232):
                back = back.replace(b'1.297', b'1.296')
            assert back == op.raw, f'Unexpected mutation in {mid}/{i}'

    assert 14 in changed_protos.get(12, []), '12/14 not updated'
    assert changed_protos.get(22) == [96], f'Unexpected module 22 changes: {changed_protos.get(22)}'

    # 2. Strict static dataflow / liveness / J->maxslot / JMP.A audit
    #    on 22/96, 12/14, and ALL 123 protos of Module 22
    m22_gaps = 0
    m22_bad_jmp = []
    for p in new[22].protos:
        info = analyze_proto(p)
        m22_gaps += len(info['call_gaps'])
        for b in info['bad_jmp_a']:
            m22_bad_jmp.append((p.idx, b))
    assert m22_gaps == 0, f'Module 22 CALL gaps found: {m22_gaps}'
    assert not m22_bad_jmp, f'Module 22 bad JMP.A found: {m22_bad_jmp}'

    p22_96 = new[22].protos[96]
    p12_14 = new[12].protos[14]
    info_96 = analyze_proto(p22_96)
    info_14 = analyze_proto(p12_14)
    assert info_96['call_gaps'] == [] and info_96['bad_jmp_a'] == [], info_96
    assert info_14['call_gaps'] == [] and info_14['bad_jmp_a'] == [], info_14

    # 3. Functional bytecode VM execution tests
    # 3a. Exact boundary totals via pre-rolled gold entries in 「来世续缘」
    boundary_cases = [
        (1,     [1],                        ['金币_极小']),
        (37,    [37],                       ['金币_极小']),
        (60,    [60],                       ['金币_极小']),
        (61,    [61],                       ['金币_小']),
        (600,   [600],                      ['金币_小']),
        (601,   [601],                      ['金币_中']),
        (2400,  [2400],                     ['金币_中']),
        (2401,  [2401],                     ['金币_大']),
        (4500,  [4500],                     ['金币_大']),
        (4501,  [4501],                     ['金币_极大']),
        (4999,  [4999],                     ['金币_极大']),
        (5000,  [5000],                     ['金币_极大']),
        (5001,  [5000, 1],                  ['金币_极大', '金币_极小']),
        (7600,  [5000, 2600],               ['金币_极大', '金币_大']),
        (10000, [5000, 5000],               ['金币_极大', '金币_极大']),
        (10001, [5000, 5000, 1],            ['金币_极大', '金币_极大', '金币_极小']),
        (26100, [5000, 5000, 5000, 5000, 5000, 1100],
                ['金币_极大', '金币_极大', '金币_极大', '金币_极大', '金币_极大', '金币_中']),
    ]
    for total_val, expected_piles, expected_tiers in boundary_cases:
        G, tpls = make_env('来世续缘', 0, random.Random(42))
        vm = LuaJIT20VM(G)
        item = copy.deepcopy(tpls['金币_中'])
        item['附加']['金币'] = total_val
        drops = [{'物品道具': item, '掉落数量': 1}]
        vm.run(p22_96, drops)
        got_piles = [e['物品道具']['附加']['金币'] for e in drops]
        got_tiers = [e['物品道具']['名称'] for e in drops]
        assert got_piles == expected_piles, (total_val, got_piles, expected_piles)
        assert got_tiers == expected_tiers, (total_val, got_tiers, expected_tiers)
        # Verify 12/14 preserves exact pre-calculated pile value and returns exact display name
        for e in drops:
            res = vm.run(p12_14, 10, 10, e['物品道具']['名称'], 999, e['物品道具']['附加'])
            assert res == {'显示名': f"金币({e['物品道具']['附加']['金币']})"}, res
        # Verify shared templates were NEVER mutated
        for tn, tv in tpls.items():
            assert '金币' not in tv['附加'], f'Shared template {tn} mutated!'

    # 3b. 200 randomized monster kills across all 18 real monster gold patterns + bonus variations
    patterns = [
        [('金币_极小', 1)],
        [('金币_极小', 1), ('金币_极小', 1)],
        [('金币_小', 1)],
        [('金币_极小', 1), ('金币_极小', 1), ('金币_小', 1)],
        [('金币_小', 1), ('金币_小', 1)],
        [('金币_极小', 1), ('金币_中', 1), ('金币_中', 1)],
        [('金币_中', 1), ('金币_中', 1)],
        [('金币_中', 1), ('金币_大', 1)],
        [('金币_极小', 1), ('金币_中', 1), ('金币_大', 1)],
        [('金币_小', 1), ('金币_中', 1), ('金币_大', 1)],
        [('金币_中', 1)] * 5,
        [('金币_中', 1), ('金币_中', 1), ('金币_中', 1), ('金币_大', 1)],
        [('金币_中', 1)] * 3 + [('金币_大', 1)] * 2,
        [('金币_大', 1)] * 4,
        [('金币_大', 1)] * 5,
        [('金币_大', 1)] * 6,
        [('金币_大', 1)] * 3 + [('金币_极大', 1)] * 3,
        [('金币_中', 3)],  # count > 1 edge case
    ]
    bonus_choices = [None, 0, 15, 50, 100, 200]
    trials = 200
    for trial in range(trials):
        pat = patterns[trial % len(patterns)]
        bonus = bonus_choices[trial % len(bonus_choices)]
        seed = 10000 + trial

        # Reference calculation using exact 12/14 formula (in reverse scan order)
        ref_rng = random.Random(seed)
        bval = 0 if bonus is None else bonus
        expected_total = 0
        # 22/96 scans drops backwards from #drops down to 1
        for tier_name, cnt in reversed(pat):
            lo, hi = {
                '金币_极小': (5, 20), '金币_小': (20, 200), '金币_中': (200, 800),
                '金币_大': (800, 1500), '金币_极大': (1500, 2000),
            }[tier_name]
            for _ in range(cnt):
                g = ref_rng.randint(lo, hi)
                g = (g + math.ceil((bval / 150) * g)) * 3
                expected_total += g

        G, tpls = make_env('来世续缘', bonus, random.Random(seed))
        vm = LuaJIT20VM(G)
        drops = [
            {'物品道具': {'名称': '裁决之杖', '附加': {'重量': 80}}, '掉落数量': 1},
            {'物品道具': {'名称': '回城卷', '附加': {}}, '掉落数量': 1},
            {'物品道具': {'名称': '金创药_大', '附加': {}}, '掉落数量': 1},
            {'物品道具': {'名称': 'Q魔法药_特', '附加': {}}, '掉落数量': 1},
        ]
        for tier_name, cnt in pat:
            drops.append({'物品道具': tpls[tier_name], '掉落数量': cnt})

        vm.run(p22_96, drops)

        # Equipment kept; scroll & potions removed; gold consolidated
        non_gold = [e for e in drops if not e['物品道具']['名称'].startswith('金币_')]
        gold_entries = [e for e in drops if e['物品道具']['名称'].startswith('金币_')]
        assert [e['物品道具']['名称'] for e in non_gold] == ['裁决之杖'], non_gold

        piles = [e['物品道具']['附加']['金币'] for e in gold_entries]
        assert sum(piles) == expected_total, (trial, sum(piles), expected_total)
        assert len(piles) == math.ceil(expected_total / 5000), (trial, piles, expected_total)
        assert all(p == 5000 for p in piles[:-1]), piles
        assert 1 <= piles[-1] <= 5000, piles

        # Run each consolidated gold pile through 12/14
        for e in gold_entries:
            ex = copy.deepcopy(e['物品道具']['附加'])
            res = vm.run(p12_14, 5, 5, e['物品道具']['名称'], 777, ex)
            assert res == {'显示名': f"金币({e['物品道具']['附加']['金币']})"}, res
            assert ex['金币'] == e['物品道具']['附加']['金币']

        # Shared templates untouched
        for tn, tv in tpls.items():
            assert '金币' not in tv['附加']

    # 3c. 「前尘忆梦」 isolation test: gold drops MUST remain completely untouched
    G_old, tpls_old = make_env('前尘忆梦', 50, random.Random(7))
    vm_old = LuaJIT20VM(G_old)
    drops_old = [
        {'物品道具': {'名称': '回城卷', '附加': {}}, '掉落数量': 1},
        {'物品道具': tpls_old['金币_小'], '掉落数量': 1},
        {'物品道具': tpls_old['金币_中'], '掉落数量': 1},
        {'物品道具': tpls_old['金币_大'], '掉落数量': 1},
    ]
    vm_old.run(p22_96, drops_old)
    assert [e['物品道具']['名称'] for e in drops_old] == ['金币_小', '金币_中', '金币_大'], drops_old
    assert all('金币' not in e['物品道具']['附加'] for e in drops_old)

    # 3d. Non-monster direct 12/14 gold drop (R4.金币 == nil) still rolls normally with bonus/150 * 3
    G_dir, tpls_dir = make_env('来世续缘', 20, random.Random(123))
    vm_dir = LuaJIT20VM(G_dir)
    ex_dir = copy.deepcopy(tpls_dir['金币_中']['附加'])
    res_dir = vm_dir.run(p12_14, 1, 1, '金币_中', 100, ex_dir)
    ref_g = random.Random(123).randint(200, 800)
    ref_g = (ref_g + math.ceil((20 / 150) * ref_g)) * 3
    assert ex_dir['金币'] == ref_g and res_dir == {'显示名': f'金币({ref_g})'}, (ex_dir, res_dir, ref_g)

    # 3e. Cross-check 22/96 single-pile roll bit-for-bit against original 12/14 formula (knum[2]=150)
    for b in (0, 20, 75, 150):
        G1, t1 = make_env('来世续缘', b, random.Random(555))
        G2, t2 = make_env('来世续缘', b, random.Random(555))
        d1 = [{'物品道具': t1['金币_中'], '掉落数量': 1}]
        LuaJIT20VM(G1).run(p22_96, d1)
        ex2 = copy.deepcopy(t2['金币_中']['附加'])
        LuaJIT20VM(G2).run(p12_14, 1, 1, '金币_中', 100, ex2)
        assert sum(e['物品道具']['附加']['金币'] for e in d1) == ex2['金币'], (b, d1, ex2)

    report = {
        'version': 'v1.297',
        'sha256': sha,
        'all_passed': True,
        'changed_protos': {str(k): v for k, v in sorted(changed_protos.items())},
        'module22_total_call_gaps': m22_gaps,
        'module22_bad_jmp_a_count': len(m22_bad_jmp),
        'boundary_cases_passed': len(boundary_cases),
        'randomized_monster_trials_passed': trials,
        'qiancheng_isolation_passed': True,
        'direct_12_14_fallback_passed': True,
        'tested_files': {
            'game_v297.res': sha,
            'patch_v297.py': hashlib.sha256((W / 'patch_v297.py').read_bytes()).hexdigest(),
            'test_v297.py': hashlib.sha256((W / 'test_v297.py').read_bytes()).hexdigest(),
            'monster_drop_filter_v297.lua': hashlib.sha256((W / 'monster_drop_filter_v297.lua').read_bytes()).hexdigest(),
        },
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v297.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v297.json').write_text(text, encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    test()
