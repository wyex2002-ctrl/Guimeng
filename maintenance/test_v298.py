"""Static dataflow/JMP.A audit + real bytecode VM verification for v1.298."""
import hashlib
import json
import math
from pathlib import Path

from ljdis import OPS
from native_test_utils import trees
from resource_tools import decode, numbers
from test_v297 import LuaJIT20VM, analyze_proto

W = Path(__file__).resolve().parent
BASE_SHA = 'e5e4f5cf482ac1403112fd797a7f1366f2641672097d55c56157ffc72cec7233'
TALISMAN_CAP = 50_000_000


class ExtendedVM(LuaJIT20VM):
    """Extends LuaJIT20VM with ISFC, UCLO, RET, TSETV, UNM, FNEW(stub) for 12/302, 12/35, 12/259, 12/321."""

    def __init__(self, globals_env, child_handlers=None):
        super().__init__(globals_env)
        self.child_handlers = child_handlers or {}

    def run_slice(self, p, start_pc=0, stop_pc=None, init_regs=None, args=()):
        R = [None] * max(p.frame + 4, 32)
        for i, a in enumerate(args):
            R[i] = a
        if init_regs:
            for k, v in init_regs.items():
                R[k] = v
        pc = start_pc
        steps = 0
        while pc < p.nbc and (stop_pc is None or pc < stop_pc):
            steps += 1
            assert steps < 200000, f'Loop limit in proto {p.idx} at pc={pc}'
            w = p.bc[pc]
            op = OPS[w & 255]
            a = (w >> 8) & 255
            b = (w >> 24) & 255
            c = (w >> 16) & 255
            d = (w >> 16) & 65535

            if op == 'ISFC':
                if R[d] is None or R[d] is False:
                    R[a] = R[d]
                    pc += 1
                else:
                    pc += 2
            elif op == 'UCLO':
                pc = pc + 1 + d - 32768
            elif op == 'UNM':
                R[a] = -R[d]
                pc += 1
            elif op == 'TSETV':
                R[b][R[c]] = R[a]
                pc += 1
            elif op == 'FNEW':
                R[a] = self.child_handlers[d]
                pc += 1
            elif op == 'RET':
                return tuple(R[a + i] for i in range(d - 1))
            elif op in ('ISEQV', 'ISNEV'):
                cond = (R[a] == R[d]) if op == 'ISEQV' else (R[a] != R[d])
                pc += 1 if cond else 2
            elif op == 'TGETV':
                tbl = R[b]
                key = R[c]
                if isinstance(tbl, list):
                    R[a] = tbl[key - 1] if isinstance(key, int) and 1 <= key <= len(tbl) else None
                elif isinstance(tbl, dict):
                    R[a] = tbl.get(key)
                else:
                    R[a] = None
                pc += 1
            elif op == 'TGETS':
                tbl = R[b]
                key = self._kstr(p, c)
                R[a] = tbl.get(key) if isinstance(tbl, dict) else None
                pc += 1
            elif op == 'TSETS':
                R[b][self._kstr(p, c)] = R[a]
                pc += 1
            elif op == 'MOV':
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
            elif op == 'KNIL':
                for r in range(a, d + 1):
                    R[r] = None
                pc += 1
            elif op == 'TNEW':
                R[a] = {}
                pc += 1
            elif op == 'GGET':
                R[a] = self.G.get(self._kstr(p, d))
                pc += 1
            elif op == 'LEN':
                R[a] = len(R[d])
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
                pc += 1 if cond else 2
            elif op == 'JMP':
                pc = pc + 1 + d - 32768
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
        return R


def run_collect(proto_302, group, merc, controls, merc_bag=()):
    """Execute real 12/302 bytecode with faithful offer & weakest closures."""
    groups = {
        '金创药_小': 1, '金创药_中': 1, '金创药_大': 1, '金创药_特': 1, '金创药_特大': 1, 'Q金创药_小': 1,
        '魔法药_小': 2, '魔法药_中': 2, '魔法药_大': 2, '魔法药_特': 2, '魔法药_特大': 2, 'Q魔法药_小': 2,
        '太阳水': 3, '强效太阳水': 3, '万年雪霜': 3,
    }

    def offer(target, slot, item, order):
        if not item or groups.get(item.get('名称')) != group or item.get('子类') != '消耗品':
            return None
        extra = item.get('附加')
        if not isinstance(extra, dict) or (item.get('数量') or 0) < 1:
            return None
        hp = extra.get('加血') or 0
        mp = extra.get('加蓝') or 0
        amount = hp + mp
        if amount <= 0:
            return None
        cand = {'slot': slot, 'item': item, 'order': order, 'hp': hp, 'mp': mp, 'amount': amount}
        # target is a Lua table represented as dict with 1-based integer keys
        target[len(target) + 1] = cand
        return cand

    def weakest(a, b):
        if a['amount'] == b['amount']:
            return a['order'] < b['order']
        return a['amount'] < b['amount']

    def tbl_sort(t, cmp_fn):
        items = [t[i] for i in range(1, len(t) + 1)]
        items.sort(key=lambda x: (x['amount'], x['order']))
        t.clear()
        for idx, it in enumerate(items, 1):
            t[idx] = it

    G = {
        'Ux雌': {'佣兵背包': list(merc_bag)},
        'Gly独': {'取控件对象': lambda name: controls.get(name)},
        'table': {'sort': tbl_sort},
    }
    vm = ExtendedVM(G, child_handlers={0: offer, 12: weakest})
    quick_t, bag_t = vm.run_slice(proto_302, args=(group, merc))
    quick = [quick_t[i] for i in range(1, len(quick_t) + 1)]
    bag = [bag_t[i] for i in range(1, len(bag_t) + 1)]
    return quick, bag


def make_potion(name, hp=0, mp=0, qty=10):
    return {
        '名称': name,
        '子类': '消耗品',
        '数量': qty,
        '附加': {'快捷物品': 0, '加血': hp, '加蓝': mp},
    }


def test():
    old_bytes = (W / 'game_v297.res').read_bytes()
    new_bytes = (W / 'game_v298.res').read_bytes()
    assert hashlib.sha256(old_bytes).hexdigest() == BASE_SHA
    build = json.loads((W / 'build_v298.json').read_text(encoding='utf-8'))
    sha = hashlib.sha256(new_bytes).hexdigest()
    assert build['sha256'] == sha and build['bytes'] == len(new_bytes)

    all_mids = list(range(2, 86, 2))
    _, old = decode(old_bytes, all_mids)
    _, new = decode(new_bytes, all_mids)

    # 1. Full 42-module reverse-diff integrity
    changed_protos = {}
    for mid in all_mids:
        assert new[mid].rebuild() == new[mid].raw, mid
        trees(new[mid])
        assert len(old[mid].protos) == len(new[mid].protos), mid
        for i, (op, np) in enumerate(zip(old[mid].protos, new[mid].protos)):
            if op.raw == np.raw:
                continue
            changed_protos.setdefault(mid, []).append(i)
            if mid == 12 and i in (35, 259, 302, 321, 4111):
                continue
            back = np.raw.replace(b'v1.298', b'v1.297')
            if mid == 12 and i in (76, 22232):
                back = back.replace(b'1.298', b'1.297')
            assert back == op.raw, f'Unexpected mutation in {mid}/{i}'

    assert sorted(changed_protos[12]) == [35, 76, 259, 302, 321, 4111, 22232], changed_protos[12]

    # 2. Static dataflow / J->maxslot / JMP.A audit on modified protos + all of Module 22
    for pid in (35, 259, 302, 321):
        old_info = analyze_proto(old[12].protos[pid])
        new_info = analyze_proto(new[12].protos[pid])
        assert len(new_info['call_gaps']) <= len(old_info['call_gaps']), (pid, old_info, new_info)
        assert len(new_info['bad_jmp_a']) <= len(old_info['bad_jmp_a']), (pid, old_info, new_info)

    m22_gaps = sum(len(analyze_proto(p)['call_gaps']) for p in new[22].protos)
    assert m22_gaps == 0, m22_gaps

    # 3. Quickbar auto-potion verification (reproduce v1.297 bug -> verify v1.298 fix for ALL 3 potion groups)
    p302_old = old[12].protos[302]
    p302_new = new[12].protos[302]

    # 3a. Exact user scenario: 魔法药_小 in quickslot 1 (21) and 魔法药_大 in quickslot 2 (22), empty main bag
    controls_blue = {
        '物品格子21': {'道具': make_potion('魔法药_小', mp=40, qty=50)},
        '物品格子22': {'道具': make_potion('魔法药_大', mp=180, qty=50)},
    }
    q_old, b_old = run_collect(p302_old, 2, None, controls_blue)
    assert q_old == [] and b_old == [], 'Expected v1.297 to reproduce empty quickbar bug'

    q_new, b_new = run_collect(p302_new, 2, None, controls_blue)
    assert [(c['slot'], c['item']['名称']) for c in q_new] == [(21, '魔法药_小'), (22, '魔法药_大')], q_new
    assert b_new == []

    # 3b. Red potions in quickbar only (larger in slot 1, smaller in slot 2 -> weakest-first picks slot 2!)
    controls_red = {
        '物品格子21': {'道具': make_potion('金创药_大', hp=110, qty=20)},
        '物品格子22': {'道具': make_potion('金创药_小', hp=30, qty=20)},
    }
    assert run_collect(p302_old, 1, None, controls_red)[0] == []
    q_red, _ = run_collect(p302_new, 1, None, controls_red)
    assert [(c['slot'], c['item']['名称']) for c in q_red] == [(22, '金创药_小'), (21, '金创药_大')], q_red

    # 3c. Compound potions in quickbar only (万年雪霜 in slot 5, 太阳水 in slot 6 -> weakest-first picks 太阳水!)
    controls_comp = {
        '物品格子25': {'道具': make_potion('万年雪霜', hp=170, mp=250, qty=10)},
        '物品格子26': {'道具': make_potion('太阳水', hp=70, mp=110, qty=10)},
    }
    assert run_collect(p302_old, 3, None, controls_comp)[0] == []
    q_comp, _ = run_collect(p302_new, 3, None, controls_comp)
    assert [(c['slot'], c['item']['名称']) for c in q_comp] == [(26, '太阳水'), (25, '万年雪霜')], q_comp

    # 3d. All 15 potion names individually in quickslot 21
    all_15 = [
        ('金创药_小', 1, 30, 0), ('金创药_中', 1, 70, 0), ('金创药_大', 1, 110, 0),
        ('金创药_特', 1, 170, 0), ('金创药_特大', 1, 200, 0), ('Q金创药_小', 1, 30, 0),
        ('魔法药_小', 2, 0, 40), ('魔法药_中', 2, 0, 110), ('魔法药_大', 2, 0, 180),
        ('魔法药_特', 2, 0, 250), ('魔法药_特大', 2, 0, 300), ('Q魔法药_小', 2, 0, 40),
        ('太阳水', 3, 70, 110), ('强效太阳水', 3, 110, 180), ('万年雪霜', 3, 170, 250),
    ]
    for pname, grp, hp, mp in all_15:
        q, _ = run_collect(p302_new, grp, None, {'物品格子21': {'道具': make_potion(pname, hp=hp, mp=mp)}})
        assert len(q) == 1 and q[0]['slot'] == 21 and q[0]['item']['名称'] == pname, (pname, q)

    # 3e. Bag stock priority preserved when BOTH quickbar AND main bag have same potion
    controls_both = {
        '物品格子21': {'道具': make_potion('魔法药_小', mp=40, qty=5)},
        '物品格子22': {'道具': make_potion('魔法药_大', mp=180, qty=5)},
        '物品格子35': {'道具': make_potion('魔法药_小', mp=40, qty=99)},
    }
    q_both, b_both = run_collect(p302_new, 2, None, controls_both)
    # Slot 21 resolves to bag stock slot 35; slot 22 falls back directly to quickslot 22!
    assert [(c['slot'], c['item']['名称']) for c in q_both] == [(35, '魔法药_小'), (22, '魔法药_大')], q_both
    assert [(c['slot'], c['item']['名称']) for c in b_both] == [(35, '魔法药_小')], b_both

    # 3f. Mercenary bag collection unaffected
    merc_slots = [{'道具': make_potion('魔法药_大', mp=180)}, {'道具': make_potion('魔法药_小', mp=40)}]
    qm, bm = run_collect(p302_new, 2, {'HP': 100}, {}, merc_bag=merc_slots)
    assert qm == [] and [(c['slot'], c['item']['名称']) for c in bm] == [(2, '魔法药_小'), (1, '魔法药_大')], bm

    # 4. 聚灵符咒(灵) 50,000,000 cap verification
    # 4a. Template in 12/4111
    p4111 = new[12].protos[4111]
    assert p4111.gc(9748).decode('gbk') == '商店ぅ杂货店ぃ最小次数ぅ10ぃ最大次数ぅ10ぃ最小储存ぅ0ぃ最大储存ぅ2000000ぃ聚灵符咒ぅ2ぃ辞职ぅ56ぃ'
    ling_k = (p4111.bc[111116] >> 16) & 65535
    assert ling_k != 9748
    assert p4111.gc(ling_k).decode('gbk') == '商店ぅ杂货店ぃ最小次数ぅ10ぃ最大次数ぅ10ぃ最小储存ぅ0ぃ最大储存ぅ50000000ぃ聚灵符咒ぅ2ぃ辞职ぅ56ぃ'

    # 4b. Existing saved 聚灵符咒_灵 auto-upgraded in 12/35 and 12/259
    def lua_type(v):
        if v is None: return 'nil'
        if isinstance(v, bool): return 'boolean'
        if isinstance(v, (int, float)): return 'number'
        if isinstance(v, str): return 'string'
        if isinstance(v, dict): return 'table'
        return 'function'

    for pid in (35, 259):
        p = new[12].protos[pid]
        assert numbers(p)[0][-1] == TALISMAN_CAP
        extra_hero = {'最小储存': 1500000, '最大储存': 2000000}
        extra_merc = {'最小储存': 800000, '最大储存': 2000000}
        cell_hero = {'道具': {'名称': '聚灵符咒_灵', '附加': extra_hero}}
        cell_merc = {'道具': {'名称': '聚灵符咒_灵', '附加': extra_merc}}
        G_tal = {
            'type': lua_type,
            'math': {'huge': math.inf},
            'FXru胃啪': {'HP': 500},
            '物品格子12': cell_hero,
            '物品格子408': cell_merc,
            'Ux雌': {'佣兵对象': {'HP': 300}, '啾啾啵啵': lambda: {'佣兵': {'__gm_talisman_summoned_v206': True}}},
        }
        res_h = ExtendedVM(G_tal).run_slice(p, args=(12,))
        assert res_h[0] is extra_hero and extra_hero['最大储存'] == TALISMAN_CAP and extra_hero['最小储存'] == 1500000, res_h

        res_m = ExtendedVM(G_tal).run_slice(p, args=(408,))
        assert res_m[0] is extra_merc and extra_merc['最大储存'] == TALISMAN_CAP and extra_merc['最小储存'] == 800000, res_m

        # Already >= 50,000,000 stays untouched
        extra_big = {'最小储存': 30000000, '最大储存': 50000000}
        cell_hero['道具']['附加'] = extra_big
        res2 = ExtendedVM(G_tal).run_slice(p, args=(12,))
        assert res2[0] is extra_big and extra_big['最大储存'] == TALISMAN_CAP

    # 4c. Tooltip 12/321 PC 2156..2184 auto-upgrades 聚灵符咒_灵 and leaves 聚灵符咒_中 untouched
    p321 = new[12].protos[321]
    assert numbers(p321)[0][-1] == TALISMAN_CAP
    G_tip = {'格式化数值': lambda v: str(int(v))}

    ling_item = {'名称': '聚灵符咒_灵', '附加': {'最小储存': 123456, '最大储存': 2000000}}
    R_ling = ExtendedVM(G_tip).run_slice(p321, start_pc=2156, stop_pc=2184, init_regs={0: ling_item, 3: 'desc'})
    assert ling_item['附加']['最大储存'] == TALISMAN_CAP
    assert R_ling[3] == 'desc\n#md#W储值:123456/50000000', R_ling[3]

    mid_item = {'名称': '聚灵符咒_中', '附加': {'最小储存': 123456, '最大储存': 2000000}}
    R_mid = ExtendedVM(G_tip).run_slice(p321, start_pc=2156, stop_pc=2184, init_regs={0: mid_item, 3: 'desc'})
    assert mid_item['附加']['最大储存'] == 2000000
    assert R_mid[3] == 'desc\n#md#W储值:123456/2000000', R_mid[3]

    report = {
        'version': 'v1.298',
        'sha256': sha,
        'all_passed': True,
        'changed_protos': {str(k): v for k, v in sorted(changed_protos.items())},
        'module22_total_call_gaps': m22_gaps,
        'quickbar_autopotion_all_15_passed': True,
        'quickbar_v297_bug_reproduced': True,
        'quickbar_bag_priority_preserved': True,
        'talisman_cap': TALISMAN_CAP,
        'talisman_template_and_save_upgrade_passed': True,
        'talisman_mid_untouched': True,
        'tested_files': {
            'game_v298.res': sha,
            'patch_v298.py': hashlib.sha256((W / 'patch_v298.py').read_bytes()).hexdigest(),
            'test_v298.py': hashlib.sha256((W / 'test_v298.py').read_bytes()).hexdigest(),
            'potions_v298.lua': hashlib.sha256((W / 'potions_v298.lua').read_bytes()).hexdigest(),
        },
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v298.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v298.json').write_text(text, encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    test()
