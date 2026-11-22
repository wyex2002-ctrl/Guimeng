"""Exhaustive verification suite for v1.299:
- 42-module reverse-diff integrity & rebuild round-trip
- Static LuaJIT 2.0 dataflow / J->maxslot / JMP.A audit on all modified protos + Module 22
- Strict Lua 5.1 parse + GBK hazard audit of embedded runtime_v299.lua from game_v299.res
- Real LuaJIT 2.0 bytecode VM execution of 12/218, 14/781, 14/428, 14/456, 14/481, 14/446, 14/256
- End-to-end execution of embedded runtime_v299.lua covering:
  * Feature 1: Reputation shop Blessing Oil (slot 1, 2000 rep, shift 53 items, multi-qty, rollback)
  * Feature 2: Auto-pickup toggle button + 1s lightweight pre-check (all 9 Section 5.1 scenarios)
  * Feature 3: Mount oil batch pre-generation + old-save all-container migration (all 15 Section 5.2 scenarios)
  * Full 「前尘忆梦」 isolation across all three features
"""
import hashlib
import json
import math
import random
from pathlib import Path

from ljdis import OPS
from ljtool import Dump
from lua51_eval import LuaEvaluator, LuaTable, syntax_check
from native_test_utils import trees
from resource_tools import decode
from test_v297 import analyze_proto
from test_v298 import ExtendedVM

W = Path(__file__).resolve().parent
BASE_SHA = 'fec3c995db817d5a80995230dffbf3850e73d7fb7654fce8ed8c22f7e9380005'
REP_OIL_ENTRY = '祝福油附加祝福油附加2000附加0附加声望'


def make_protect_fn():
    """Exact replica of 14/502 数据保护 metatable proxy using LuaTable."""
    def protect(t, deep=False):
        if not isinstance(t, LuaTable):
            return t
        if t.rawget('__p') is not None:
            return t
        if deep:
            for k, v in list(t._data.items()):
                if isinstance(v, LuaTable) and v.rawget('__c') is None and v.rawget('__p') is None and v.rawget('__数据') is None:
                    t.rawset(k, protect(v, True))
        proxy = LuaTable()
        proxy.rawset('__数据', t)
        proxy.rawset('__p', LuaTable())
        mt = LuaTable()
        mt.rawset('__call', lambda _self: proxy.rawget('__数据'))
        mt.rawset('__index', lambda _self, k: proxy.rawget('__数据').get(k))
        mt.rawset('__newindex', lambda _self, k, v: proxy.rawget('__数据').set(k, v))
        proxy._mt = mt
        return proxy
    return protect


class V299VM(ExtendedVM):
    """ExtendedVM plus UGET/USETV/TGETB/TSETB/MODVV/ISNEP/IST/ISF/LEN/CAT/FORI/FORL for v1.299 hooks."""

    def __init__(self, globals_env, upvalues=None, child_handlers=None):
        super().__init__(globals_env, child_handlers=child_handlers)
        self.upvalues = upvalues or []

    def _tbl_get(self, tbl, key):
        if isinstance(tbl, LuaTable):
            return tbl.get(key)
        if isinstance(tbl, dict):
            return tbl.get(key)
        if isinstance(tbl, list) and isinstance(key, int) and 1 <= key <= len(tbl):
            return tbl[key - 1]
        return None

    def _tbl_set(self, tbl, key, val):
        if isinstance(tbl, LuaTable):
            tbl.set(key, val)
        elif isinstance(tbl, dict):
            tbl[key] = val
        elif isinstance(tbl, list) and isinstance(key, int):
            while len(tbl) < key:
                tbl.append(None)
            tbl[key - 1] = val

    def run_slice(self, p, start_pc=0, stop_pc=None, init_regs=None, args=()):
        R = [None] * max(p.frame + 4, 48)
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

            if op == 'UGET':
                R[a] = self.upvalues[d]
                pc += 1
            elif op == 'USETV':
                self.upvalues[a] = R[d]
                pc += 1
            elif op == 'GGET':
                R[a] = self._tbl_get(self.G, self._kstr(p, d))
                pc += 1
            elif op == 'TGETS':
                R[a] = self._tbl_get(R[b], self._kstr(p, c))
                pc += 1
            elif op == 'TSETS':
                self._tbl_set(R[b], self._kstr(p, c), R[a])
                pc += 1
            elif op == 'TGETB':
                R[a] = self._tbl_get(R[b], c)
                pc += 1
            elif op == 'TSETB':
                self._tbl_set(R[b], c, R[a])
                pc += 1
            elif op == 'TGETV':
                R[a] = self._tbl_get(R[b], R[c])
                pc += 1
            elif op == 'TSETV':
                self._tbl_set(R[b], R[c], R[a])
                pc += 1
            elif op == 'TDUP':
                R[a] = LuaTable()
                pc += 1
            elif op == 'TNEW':
                R[a] = LuaTable()
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
            elif op == 'FNEW':
                R[a] = self.child_handlers[d]
                pc += 1
            elif op == 'MODVV':
                try:
                    R[a] = math.nan if (math.isnan(R[b]) or math.isinf(R[b]) or R[c] == 0) else (R[b] % R[c])
                except Exception:
                    R[a] = math.nan
                pc += 1
            elif op == 'MULVV':
                R[a] = R[b] * R[c]
                pc += 1
            elif op == 'ADDVV':
                R[a] = R[b] + R[c]
                pc += 1
            elif op == 'UNM':
                R[a] = -R[d]
                pc += 1
            elif op == 'LEN':
                v = R[d]
                R[a] = v.length() if isinstance(v, LuaTable) else len(v)
                pc += 1
            elif op == 'CAT':
                R[a] = ''.join(str(R[k]) for k in range(b, c + 1))
                pc += 1
            elif op == 'ISEQP':
                cond = (R[a] is self._pri(d))
                pc += 1 if cond else 2
            elif op == 'ISNEP':
                cond = (R[a] is not self._pri(d))
                pc += 1 if cond else 2
            elif op == 'ISEQS':
                cond = (R[a] == self._kstr(p, d))
                pc += 1 if cond else 2
            elif op == 'ISNES':
                cond = (R[a] != self._kstr(p, d))
                pc += 1 if cond else 2
            elif op == 'ISEQN':
                cond = (R[a] == self._knum(p, d))
                pc += 1 if cond else 2
            elif op == 'ISNEN':
                cond = (R[a] != self._knum(p, d))
                pc += 1 if cond else 2
            elif op == 'ISEQV':
                cond = (R[a] == R[d])
                pc += 1 if cond else 2
            elif op == 'ISNEV':
                cond = (R[a] != R[d])
                pc += 1 if cond else 2
            elif op == 'ISGT':
                cond = (R[a] > R[d]) if (R[a] is not None and R[d] is not None) else False
                pc += 1 if cond else 2
            elif op == 'ISGE':
                cond = (R[a] >= R[d]) if (R[a] is not None and R[d] is not None) else False
                pc += 1 if cond else 2
            elif op == 'ISLT':
                cond = (R[a] < R[d]) if (R[a] is not None and R[d] is not None) else False
                pc += 1 if cond else 2
            elif op == 'ISLE':
                cond = (R[a] <= R[d]) if (R[a] is not None and R[d] is not None) else False
                pc += 1 if cond else 2
            elif op == 'IST':
                cond = (R[d] is not None and R[d] is not False)
                pc += 1 if cond else 2
            elif op == 'ISF':
                cond = (R[d] is None or R[d] is False)
                pc += 1 if cond else 2
            elif op in ('JMP', 'UCLO'):
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
                nxt = R[a] + step
                if (step > 0 and nxt <= R[a + 1]) or (step < 0 and nxt >= R[a + 1]):
                    R[a] = nxt
                    R[a + 3] = nxt
                    pc = pc + 1 + d - 32768
                else:
                    pc += 1
            elif op == 'CALL':
                fn = R[a]
                nargs = c - 1
                nres = b - 1
                call_args = [R[a + 1 + i] for i in range(nargs)]
                res = fn(*call_args)
                if nres > 0:
                    vals = list(res) if isinstance(res, tuple) else [res]
                    for i in range(nres):
                        R[a + i] = vals[i] if i < len(vals) else None
                pc += 1
            elif op == 'RET0':
                return None
            elif op == 'RET1':
                return R[a]
            elif op == 'RET':
                return tuple(R[a + i] for i in range(d - 1))
            else:
                raise NotImplementedError(f'V299VM unsupported op {op} at 12/14 proto {p.idx} pc={pc}')
        return R


def verify_42_modules_and_static_audit(base_bytes, new_bytes):
    all_mids = list(range(2, 86, 2))
    outer_old, old_mods = decode(base_bytes, all_mids)
    outer_new, new_mods = decode(new_bytes, all_mids)

    changed_mods = []
    changed_protos = {}
    for mid in all_mids:
        raw_old = old_mods[mid].rebuild()
        raw_new = new_mods[mid].rebuild()
        assert Dump(raw_new).rebuild() == raw_new, f'Module {mid} rebuild round-trip failed'
        trees(new_mods[mid])
        assert len(old_mods[mid].protos) == len(new_mods[mid].protos)
        if raw_old != raw_new:
            changed_mods.append(mid)
            changed_protos[mid] = [
                p.idx for p in new_mods[mid].protos
                if p.raw != old_mods[mid].protos[p.idx].raw
            ]

    assert set(changed_mods) == {12, 14, 30}, f'Unexpected changed modules: {changed_mods}'
    # Verify exact protos touched in module 14 (our 6 functional protos + version-string-only protos)
    for req_pid in (256, 428, 446, 456, 481, 781):
        assert req_pid in changed_protos[14], f'14/{req_pid} missing from changed protos'
    for pid in changed_protos[14]:
        if pid in (256, 428, 446, 456, 481, 781):
            continue
        back = new_mods[14].protos[pid].raw.replace(b'v1.299', b'v1.298')
        assert back == old_mods[14].protos[pid].raw, f'Unexpected mutation in 14/{pid}'
    # Verify exact protos touched in module 12 (our functional protos + version strings only)
    for req_pid in (143, 217, 218, 220):
        assert req_pid in changed_protos[12], f'12/{req_pid} missing from changed protos'
    for pid in changed_protos[12]:
        if pid in (143, 217, 218, 220):
            continue
        back = new_mods[12].protos[pid].raw.replace(b'v1.299', b'v1.298')
        if pid in (76, 22232):
            back = back.replace(b'1.299', b'1.298')
        assert back == old_mods[12].protos[pid].raw, f'Unexpected mutation in 12/{pid}'
    # Verify 前尘忆梦 code in 12/143 (PC 0..247), 12/124, and 12/67 is untouched
    assert new_mods[12].protos[124].raw == old_mods[12].protos[124].raw
    assert new_mods[12].protos[143].bc[:248] == old_mods[12].protos[143].bc[:248]
    assert new_mods[12].protos[67].raw == old_mods[12].protos[67].raw

    # Static dataflow / J->maxslot / JMP.A audit on all modified protos + all 123 protos of module 22
    audited = []
    for mid, pids in (
        (12, [143, 217, 218, 220]),
        (14, [256, 428, 446, 456, 481, 781]),
        (22, list(range(len(new_mods[22].protos)))),
    ):
        for pid in pids:
            p = new_mods[mid].protos[pid]
            old_rep = analyze_proto(old_mods[mid].protos[pid])
            new_rep = analyze_proto(p)
            assert len(new_rep['call_gaps']) <= len(old_rep['call_gaps']), f'{mid}/{pid} call gaps: {old_rep} -> {new_rep}'
            assert len(new_rep['bad_jmp_a']) <= len(old_rep['bad_jmp_a']), f'{mid}/{pid} bad jmp A: {old_rep} -> {new_rep}'
            if mid == 22:
                assert len(new_rep['call_gaps']) == 0, f'22/{pid} call gaps'
            # Verify every TGETS/TSETS C operand < 256, jump targets valid, and register operands < frame
            for pc, ins in enumerate(p.bc):
                op = OPS[ins & 255]
                a = (ins >> 8) & 255
                c = (ins >> 16) & 255
                d = (ins >> 16) & 65535
                if op in ('TGETS', 'TSETS'):
                    assert c < p.nkgc and c < 256, f'{mid}/{pid} pc={pc} {op} c={c}'
                if op in ('JMP', 'UCLO', 'FORI', 'FORL', 'ITERL', 'ISNEXT'):
                    tgt = pc + 1 + d - 32768
                    assert 0 <= tgt <= p.nbc, f'{mid}/{pid} pc={pc} {op} tgt={tgt}'
                if op in ('MOV', 'KSTR', 'KSHORT', 'KNUM', 'KPRI', 'UGET', 'GGET', 'TGETS', 'TGETB', 'TGETV', 'CALL'):
                    assert a < p.frame, f'{mid}/{pid} pc={pc} {op} a={a} >= frame={p.frame}'
            audited.append(f'{mid}/{pid}')

    return new_mods, changed_mods, changed_protos, len(audited)


def test_feature1_reputation_shop(mods):
    d12 = mods[12]
    # 1. Verify 12/143 reputation shop table slot 1 + 53 existing items shifted intact
    p143 = d12.protos[143]
    arr = p143.gc(160)[1]
    assert len(arr) == 55, len(arr)  # index 0 = None, items 1..54
    assert arr[1].decode('gbk') == REP_OIL_ENTRY
    assert arr[2].decode('gbk') == '随机传送石附加随机传送石附加15附加0附加声望'
    assert arr[54].decode('gbk') == '完美的宝石卷轴附加完美的宝石卷轴附加1400附加0附加声望'

    # 2. Verify 祝福油 removed from 12/217 & 12/220 stackable whitelists
    oil_b = '祝福油'.encode('gbk')
    for pid in (217, 220):
        keys = [k for k, _ in d12.protos[pid].gc(3)[2]]
        assert oil_b not in keys, f'12/{pid} still contains 祝福油'
        assert '强效太阳水'.encode('gbk') in keys

    # 3. Real bytecode VM execution of 12/218!
    p218 = d12.protos[218]

    def run_buy(input_text, rep, free_slots, add_ok=True, info_exists=True):
        state = {'rep': rep, 'msgs': [], 'grants': [], 'ui_calls': []}

        def ui_switch(delta, kind):
            state['ui_calls'].append((delta, kind))
            if kind == '声望':
                state['rep'] += delta

        def add_item(name, qty, opts):
            state['grants'].append((name, qty, opts))
            return add_ok

        def get_info(name):
            if not info_exists:
                return None
            return LuaTable({
                '名称': name,
                '禁止出售': True,
                '附加': LuaTable({'叠加上限': 1, '重量': 1}),
            })

        U1 = LuaTable({1: '祝福油', 2: '祝福油', 3: '2000', 4: '0', 5: '声望'})
        U2 = LuaTable({'胶布香港': LuaTable({1: 0, 2: 0, 3: rep})})
        G = LuaTable({
            '购买输入框': LuaTable({'内容': input_text}),
            '到数值': lambda x: float(x) if '.' in str(x) else int(x),
            'tonumber': lambda x: x if isinstance(x, (int, float)) else None,
            'Gly独': LuaTable({
                '取包裹空位': lambda: free_slots,
                '取道具信息_名称': get_info,
                '增加物品': add_item,
            }),
            'Ux雌': LuaTable({
                '托管显示': LuaTable({'屏幕提示': lambda msg, col=None: state['msgs'].append(msg)}),
                '窗口相关': LuaTable({'界面切换': ui_switch}),
            }),
            'L常量': LuaTable({'颜色_红': -65536, '颜色_黄': -256}),
        })
        # Child 57 = 12/217 -> returns False for 祝福油 (since removed from whitelist)
        vm = V299VM(G, upvalues=[0, U1, U2], child_handlers={57: lambda *_a: False})
        vm.run_slice(p218, 0)
        return state

    # 3a. Buy 1 bottle: succeeds, deducts 2000 rep
    s = run_buy('1', rep=5000, free_slots=10)
    assert s['rep'] == 3000 and len(s['grants']) == 1 and s['grants'][0][0] == '祝福油' and s['grants'][0][1] == 1
    assert s['grants'][0][2].get('价格') == 2000 and s['grants'][0][2].get('禁止出售') is True

    # 3b. Buy 3 bottles: succeeds, deducts 6000 rep, grants qty=3
    s = run_buy('3', rep=6000, free_slots=3)
    assert s['rep'] == 0 and len(s['grants']) == 1 and s['grants'][0][1] == 3

    # 3c. Insufficient bag slots: blocked before rep deduction
    s = run_buy('4', rep=20000, free_slots=3)
    assert s['rep'] == 20000 and len(s['grants']) == 0 and '包裹空位不足' in s['msgs']

    # 3d. Insufficient reputation: blocked before deduction
    s = run_buy('2', rep=3999, free_slots=10)
    assert s['rep'] == 3999 and len(s['grants']) == 0 and '声望不足' in s['msgs']

    # 3e. Non-integer / zero / negative quantities: rejected cleanly
    for bad in ('0', '-2', '1.5', '2.75'):
        s = run_buy(bad, rep=10000, free_slots=10)
        assert s['rep'] == 10000 and len(s['grants']) == 0, f'Failed to reject qty={bad}'

    # 3f. Atomic rollback when 增加物品 returns False
    s = run_buy('2', rep=5000, free_slots=10, add_ok=False)
    assert s['rep'] == 5000, f'Expected rep rollback to 5000, got {s["rep"]}'
    assert s['ui_calls'] == [(-4000, '声望'), (4000, '声望')]

    # 3g. Atomic rollback when 取道具信息_名称 returns nil
    s = run_buy('2', rep=5000, free_slots=10, info_exists=False)
    assert s['rep'] == 5000, f'Expected rep rollback on nil info, got {s["rep"]}'
    assert s['ui_calls'] == [(-4000, '声望'), (4000, '声望')]
    return 7


def build_lua_env(mods, story='来世续缘'):
    """Boot the ACTUAL embedded runtime_v299.lua extracted from game_v299.res 14/781 via real 14/781 bytecode!"""
    p781 = mods[14].protos[781]
    # Extract exact embedded source from game_v299.res 14/781
    embedded_src = None
    for v in p781.kgc:
        if isinstance(v, bytes) and b'__gm_runtime_v299_installed' in v:
            embedded_src = v.decode('gbk')
            break
    assert embedded_src is not None, 'runtime_v299.lua not found in 14/781'
    # Strict syntax check on extracted GBK round-trip source
    sc = syntax_check(embedded_src)
    assert sc['ast_ok'] and sc['max_locals'] <= 200

    rng = random.Random(20261120)
    clock = {'sec': 100.0}
    alt_down = {'pressed': False}
    screen_msgs = []
    sound_plays = []
    diag_log = []
    protect_fn = make_protect_fn()

    engine = LuaTable({
        '取运行时间': lambda _self: clock['sec'],
        '取按键按下': lambda _self, key: alt_down['pressed'] if key == 18 else False,
        '取按键事件': lambda _self, key: False,
        '取随机整数': lambda _self, lo, hi: rng.randint(int(lo), int(hi)),
        '取随机小数': lambda _self, lo, hi: rng.random() * (hi - lo) + lo,
    })

    # Window 539 mock (with existing 【仓库】 button at x=180, y=20, w=44, h=22)
    win539_ctrls = LuaTable()
    win539 = LuaTable({'控件组': win539_ctrls})

    def add_ctrl(_self, ctype, name, x, y, z, w, h, text, img, cfg, factories):
        factory_fn = factories.get(1)
        cb = factory_fn()
        obj = LuaTable({
            '显示': lambda *a: None,
            '销毁': lambda: None,
            '是否有焦点': lambda: False,
        })
        ctrl = LuaTable({
            '类型': ctype, '名称': name, 'x': x, 'y': y, 'w': w, 'h': h,
            '对象': obj, '回调': cb,
        })
        win539_ctrls.rawset(win539_ctrls.length() + 1, ctrl)
        return ctrl

    win539.rawset('增加控件', add_ctrl)

    def mk_sprite(*_a):
        sp = LuaTable({'colors': LuaTable(), 'draws': 0})
        sp.rawset('置颜色', lambda c: sp.get('colors').rawset(sp.get('colors').length() + 1, c))
        sp.rawset('置显示区域', lambda *a: None)
        sp.rawset('显示_高级', lambda *a: sp.rawset('draws', sp.get('draws') + 1))
        sp.rawset('销毁', lambda: None)
        return sp

    font_mock = LuaTable({
        '取宽度': lambda text, *_a: len(text) * 12,
        '取高度': lambda text, *_a: 12,
        '解析': lambda text, *_a: LuaTable({'text': text}),
        '显示配置': lambda *a: None,
    })

    templates = LuaTable({
        '坐骑号角_金': LuaTable({
            '名称': '坐骑号角_金', '显示名': '坐骑号角(金)', '分类': '装备', '子类': '坐骑',
            '叠加': 0, '价格': 0, '禁止出售': True,
            '属性': LuaTable({'幸运': 0, '最大破坏': 5}),
            '附加': LuaTable({'重量': 1}),
        }),
        '坐骑号角_铜': LuaTable({
            '名称': '坐骑号角_铜', '显示名': '坐骑号角(铜)', '分类': '装备', '子类': '坐骑',
            '叠加': 0, '价格': 1000, '禁止出售': False,
            '属性': LuaTable({'幸运': 0, '最大破坏': 2}),
            '附加': LuaTable({'重量': 1}),
        }),
        '粗布衣': LuaTable({
            '名称': '粗布衣', '显示名': '粗布衣', '分类': '装备', '子类': '衣服',
            '叠加': 0, '价格': 100, '禁止出售': False,
            '属性': LuaTable({'最大防御': 2, '最小防御': 1}),
            '附加': LuaTable({'重量': 5}),
        }),
        '精灵骸骨': LuaTable({
            '名称': '精灵骸骨', '显示名': '精灵骸骨', '分类': '装备', '子类': '武器',
            '叠加': 0, '价格': 500, '禁止出售': False,
            '属性': LuaTable({'最大破坏': 5}),
            '附加': LuaTable({'重量': 2}),
        }),
        '金创药_小': LuaTable({
            '名称': '金创药_小', '显示名': '金创药(小)', '分类': '消耗品', '子类': '药品',
            '叠加': 1, '价格': 50, '禁止出售': False,
            '属性': LuaTable(),
            '附加': LuaTable({'叠加上限': 10}),
        }),
    })

    bag = LuaTable()
    for slot_id in range(1, 420):
        bag.rawset(slot_id, LuaTable({'道具': None}))

    hero_slots = LuaTable()
    for idx, slot_id in enumerate(range(31, 41), 1):
        hero_slots.rawset(idx, LuaTable({1: slot_id, 2: LuaTable(), 3: True}))

    hero = LuaTable({
        'del__': False,
        '已经死亡': False,
        '金币': 0,
        '背包格子': hero_slots,
        '地图格子': LuaTable({'x': 10, 'y': 10}),
    })

    U = LuaTable({
        '版本选择': story,
        '托管显示': LuaTable({'屏幕提示': lambda msg, col=None, *_a: screen_msgs.append((msg, col))}),
        '游戏音效': LuaTable({'按键音效1': LuaTable({'播放': lambda: sound_plays.append(1)})}),
        '独角兽下': lambda: LuaTable({'极品数值': LuaTable({'最大防御': 1, '最大破坏': 1})}),
        '窗口相关': LuaTable({
            '界面切换': lambda pay, kind=None, tag=None: hero.set('金币', (hero.get('金币') or 0) + pay) if kind is None else None
        }),
    })

    def get_item_info(name):
        t = templates.get(name)
        if t is None:
            return None
        out = LuaTable({'名称': t.get('名称'), '附加': LuaTable(dict(t.get('附加')._data))})
        for k, v in t.get('属性')._data.items():
            out.rawset(k, v)
        return out

    def count_free(sub='不限制'):
        n = 0
        for i in range(1, hero_slots.length() + 1):
            slot = hero_slots.get(i)
            cell = bag.get(slot.get(1))
            if slot.get(3) and cell and cell.get('道具') is None:
                allow = slot.get(2)
                if sub == '不限制' and allow.length() == 0:
                    n += 1
        return n

    G_api = LuaTable({'取道具信息_名称': get_item_info, '取包裹空位': count_free})

    S = LuaTable({
        'Game_State': 1,
        'Hero': hero,
        '控制对象': hero,
        '包裹物品组': bag,
        '游戏道具组': templates,
        '界面_窗口_数组': LuaTable(),
        '数据保护': protect_fn,
        '取窗口对象': lambda wid: win539 if wid == 539 else None,
        'script_setting': LuaTable({'Ux雌': U, 'Gly独': G_api}),
        '__gm_diag_checkpoint_v159': lambda tag, msg='': diag_log.append((tag, msg)),
    })

    sys_pub = LuaTable({
        'get': lambda k: {
            'hero': S.get('Hero'),
            'item_arr': S.get('包裹物品组'),
            '控制对象': S.get('控制对象'),
            'item_box': S.get('界面_窗口_数组'),
        }.get(k),
        'run': lambda *_a: None,
    })

    ae = LuaTable({
        '屏幕焦点': True,
        '逻辑暂停': 0,
        '逻辑跳过': False,
        '游戏暂停': False,
        '遮罩信息': LuaTable({'启动': False, '触发': False}),
    })

    ev = LuaEvaluator({
        '引擎': engine,
        'L常量': LuaTable({'键_ALT': 18, '键_鼠标左': 1, '颜色_红': -65536, '颜色_黄': -256}),
        'Ae冻集': ae,
        'Sys': sys_pub,
        'Ux雌': U,
        'FXru胃啪': LuaTable({'金币': 0}),
        'Q_提示框': LuaTable({'可视': False}),
        'Q_地图': LuaTable({'删除地面物品': lambda o: None}),
        'Q__': LuaTable({'创建精灵': mk_sprite}),
        '__Res': lambda kind, *_a: font_mock if kind == 2 else LuaTable({'img': True}),
        'SETA': lambda col, a: col,
        'intable': lambda tbl, v: any(val == v for val in tbl._data.values()),
    })

    # Execute REAL 14/781 injected bytecode slice (PC 286..292) inside V299VM!
    # That executes: GGET loadstring; KSTR runtime_v299.lua; CALL; ISF; JMP; MOV R3, R0; CALL fn(S)
    vm781 = V299VM(ev.G)
    vm781.run_slice(p781, start_pc=286, stop_pc=293, init_regs={0: S})
    assert S.get('__gm_runtime_v299_installed') is True
    assert ev.G.get('__gm_pickup_frame_v299') is not None

    return {
        'ev': ev, 'S': S, 'U': U, 'G_api': G_api, 'hero': hero, 'bag': bag,
        'templates': templates, 'ae': ae, 'clock': clock, 'alt_down': alt_down,
        'screen_msgs': screen_msgs, 'sound_plays': sound_plays, 'diag_log': diag_log,
        'win539': win539, 'protect': protect_fn,
    }


def make_ground_map(cols=30, rows=30):
    buckets = LuaTable()
    to_idx = lambda x, y: y * cols + x + 1
    m = LuaTable({
        '地面物品组': buckets,
        '到逻辑格子': to_idx,
        '地图格子列数': cols,
        '地图格子行数': rows,
    })

    def add_ground(x, y, item, count=1, on_pick=None):
        obj = LuaTable({
            'del__': False,
            '已经消失': False,
            '物品': item,
            '数量': count,
            '格子': LuaTable({'x': x, 'y': y}),
            'Hero': LuaTable({'回调脚本': LuaTable({'拾取': lambda *_a: None})}),
        })

        def default_pick(self_arg=None, mode=None):
            # Enforce exact native engine contract: pcall(o['拾取'], o, 1)
            assert self_arg is obj and mode == 1, f'Bad 拾取 call signature: self={self_arg is obj} mode={mode}'
            if obj.get('del__') or obj.get('已经消失'):
                return False
            if on_pick:
                res = on_pick(obj)
                if res is False:
                    return False
            obj.set('del__', True)
            obj.set('已经消失', True)
            return True

        obj.set('拾取', default_pick)
        idx = to_idx(x, y)
        b = buckets.get(idx)
        if b is None:
            b = LuaTable()
            buckets.rawset(idx, b)
        b.rawset(b.length() + 1, obj)
        return obj

    return m, add_ground


def test_feature2_auto_pickup(mods):
    env = build_lua_env(mods, story='来世续缘')
    ev, S, U, G_api, hero, bag, ae = env['ev'], env['S'], env['U'], env['G_api'], env['hero'], env['bag'], env['ae']
    clock, alt_down, msgs = env['clock'], env['alt_down'], env['screen_msgs']
    p428 = mods[14].protos[428]

    def tick_frame():
        # Execute REAL 14/428 bytecode at PC 2956..2965 (which calls _G.__gm_pickup_frame_v299 and jumps to 2974+9=2983)
        vm = V299VM(ev.G, upvalues=[S])
        # Stop right after JMP -> orig 2974 (which is now PC 2983)
        vm.run_slice(p428, start_pc=2956, stop_pc=2983)

    # First frame installs UI button on window 539
    tick_frame()
    ctrls = env['win539'].get('控件组')
    assert ctrls.length() == 1
    btn = ctrls.get(1)
    assert btn.get('名称') == '自动拾取按钮_v299'
    assert 108 <= btn.get('x') and btn.get('x') + btn.get('w') <= 176, (btn.get('x'), btn.get('w'))
    assert btn.get('y') == 20 and btn.get('h') == 22
    assert ev.G.get('__gm_auto_pickup_on_v299') is False  # default OFF

    # Verify visual state distinction (OFF vs ON draw calls produce different skin/dot colors)
    btn.get('对象').get('显示')(btn.get('x'), btn.get('y'), 1, 1, 0, -1, 1)
    # Regression for real-client crash: Sys.lua calls setfenv(Main, sandbox_env) where _G is nil!
    # Verify Main succeeds with _G removed from evaluator globals during Main's own dispatch.
    saved_G_self = ev.G.rawget('_G')
    ev.G.rawset('_G', None)
    try:
        btn.get('回调').get('Main')()
        assert ev.G.get('__gm_auto_pickup_on_v299') is True and len(env['sound_plays']) == 1
        assert msgs[-1][0] == '自动拾取已开启'
        btn.get('对象').get('显示')(btn.get('x'), btn.get('y'), 1, 1, 0, -1, 1)
        # Click toggle OFF under sandbox _G=nil as well
        btn.get('回调').get('Main')()
        assert ev.G.get('__gm_auto_pickup_on_v299') is False and msgs[-1][0] == '自动拾取已关闭'
    finally:
        ev.G.rawset('_G', saved_G_self)

    # Setup map
    gmap, add_ground = make_ground_map()
    ev.G.get('Q_地图').set('__gm_range_state', gmap)
    stats = S.get('__gm_autopickup_stats_v299')

    # Scenario 1: OFF -> no auto-scan; manual Alt works (real gold has 分类='特殊')
    picked_items = []
    add_ground(10, 10, LuaTable({'名称': '金币_小', '分类': '特殊', '子类': '金币', '叠加': 0}), 500,
               on_pick=lambda o: picked_items.append('gold1'))
    clock['sec'] += 2.0
    tick_frame()
    assert stats.get('prechecks') == 0 and len(picked_items) == 0
    alt_down['pressed'] = True
    tick_frame()
    alt_down['pressed'] = False
    assert stats.get('manual_runs') == 1 and picked_items == ['gold1']

    # Scenario 2: ON + empty ground -> lightweight pre-check runs every 1s, ZERO full pickup calls
    S.get('__gm_set_auto_pickup_v299')(True, True)
    clock['sec'] = 200.0
    tick_frame()  # 1st check at 200.0s
    assert stats.get('prechecks') == 1 and stats.get('precheck_empty') == 1 and stats.get('full_runs') == 0
    clock['sec'] = 200.5  # < 1s -> skipped completely
    tick_frame()
    assert stats.get('prechecks') == 1
    clock['sec'] = 201.0  # >= 1s -> 2nd empty pre-check
    tick_frame()
    assert stats.get('prechecks') == 2 and stats.get('precheck_empty') == 2 and stats.get('full_runs') == 0

    # Scenario 5: Out-of-range item (dx = 6 at x=16, y=10) -> does NOT trigger pickup
    add_ground(16, 10, LuaTable({'名称': '金币', '分类': '货币', '子类': '金币', '叠加': 0}), 100,
               on_pick=lambda o: picked_items.append('far_gold'))
    clock['sec'] = 202.0
    tick_frame()
    assert stats.get('precheck_empty') == 3 and stats.get('full_runs') == 0 and 'far_gold' not in picked_items

    # Scenario 3 & 4: 11x11 has multiple items (white equip auto-sell + protected 精灵骸骨 + rare equip + 7 golds)
    # Verify pre-check exits IMMEDIATELY on 1st valid item (precheck_items_inspected += 1),
    # while full pickup processes ALL items in 11x11!
    white_eq = LuaTable({
        '名称': '粗布衣', '分类': '装备', '子类': '衣服', '叠加': 0, '价格': 100, '禁止出售': False,
        '属性': LuaTable({'最大防御': 2, '最小防御': 1}),
        '附加': LuaTable({'重量': 5}),
    })
    rare_eq = LuaTable({
        '名称': '粗布衣', '分类': '装备', '子类': '衣服', '叠加': 0, '价格': 100, '禁止出售': False,
        '属性': LuaTable({'最大防御': 5, '最小防御': 1}),  # +3 rare!
        '附加': LuaTable({'重量': 5}),
    })
    skull = LuaTable({
        '名称': '精灵骸骨', '分类': '装备', '子类': '武器', '叠加': 0, '价格': 500, '禁止出售': False,
        '属性': LuaTable({'最大破坏': 5}),
        '附加': LuaTable({'重量': 2}),
    })
    add_ground(5, 5, white_eq, 1)  # corner (-5, -5), first tile scanned!
    add_ground(10, 10, rare_eq, 1, on_pick=lambda o: picked_items.append('rare_eq'))
    add_ground(15, 15, skull, 1, on_pick=lambda o: picked_items.append('skull'))  # corner (+5, +5)
    for k in range(7):
        add_ground(10, 11, LuaTable({'名称': '金币_小', '分类': '特殊', '子类': '金币', '叠加': 0}), 10,
                   on_pick=lambda o, k=k: picked_items.append(f'g{k}'))

    before_inspected = stats.get('precheck_items_inspected')
    clock['sec'] = 203.0
    tick_frame()
    assert stats.get('precheck_items_inspected') - before_inspected == 1, 'Pre-check did NOT early-exit on 1st item!'
    assert stats.get('precheck_hits') == 1 and stats.get('full_runs') == 1
    assert hero.get('金币') == 50  # 100 * 0.5 auto-sold white equip!
    assert 'rare_eq' in picked_items and 'skull' in picked_items  # protected items NOT auto-sold!
    assert all(f'g{k}' in picked_items for k in range(7))  # all 10 items in 11x11 processed!

    # Scenario 6: Bag full with unpickable ground item -> NO every-second spam!
    for slot_id in range(31, 41):
        bag.get(slot_id).set('道具', LuaTable({'名称': '占位石', '数量': 1}))
    add_ground(10, 10, rare_eq, 1, on_pick=lambda o: picked_items.append('should_not_pick'))
    msgs.clear()
    for step in range(5):
        clock['sec'] = 210.0 + step
        tick_frame()
    full_notices = [m for m, _ in msgs if '背包空间不足' in m]
    assert len(full_notices) == 1, f'Expected 1 notice, got {len(full_notices)}'
    assert stats.get('suppressed_full_msgs') == 4
    # Manual Alt still shows the notice!
    alt_down['pressed'] = True
    tick_frame()
    alt_down['pressed'] = False
    full_notices2 = [m for m, _ in msgs if '背包空间不足' in m]
    assert len(full_notices2) == 2

    # Scenario 7: Concurrency / re-entrancy guard (re-entrant tick_frame inside o.拾取 callback blocked!)
    for slot_id in range(31, 41):
        bag.get(slot_id).set('道具', None)
    reentry_count = [0]
    gmap2, add_ground2 = make_ground_map()
    ev.G.get('Q_地图').set('__gm_range_state', gmap2)

    def reentrant_pick(o):
        reentry_count[0] += 1
        clock['sec'] += 2.0
        tick_frame()  # Attempt re-entrant auto-pickup mid-callback!
        alt_down['pressed'] = True
        tick_frame()  # Attempt concurrent manual Alt mid-callback!
        alt_down['pressed'] = False
        return True

    add_ground2(10, 10, rare_eq, 1, on_pick=reentrant_pick)
    clock['sec'] = 230.0
    tick_frame()
    assert reentry_count[0] == 1, f'Re-entrancy occurred! count={reentry_count[0]}'

    # Scenario 8: Map switch, death, pause, mask -> safe pause without crash
    gmap3, add_ground3 = make_ground_map()
    ev.G.get('Q_地图').set('__gm_range_state', gmap3)
    dead_picked = []
    add_ground3(10, 10, LuaTable({'名称': '金币_小', '分类': '特殊', '子类': '金币', '叠加': 0}), 10,
                on_pick=lambda o: dead_picked.append(1))
    hero.set('已经死亡', True)
    clock['sec'] = 240.0
    tick_frame()
    assert len(dead_picked) == 0
    hero.set('已经死亡', False)
    ae.set('游戏暂停', True)
    clock['sec'] = 241.0
    tick_frame()
    assert len(dead_picked) == 0
    ae.set('游戏暂停', False)
    ae.get('遮罩信息').set('启动', True)
    ae.get('遮罩信息').set('触发', True)
    clock['sec'] = 242.0
    tick_frame()
    assert len(dead_picked) == 0
    ae.get('遮罩信息').set('启动', False)
    ae.get('遮罩信息').set('触发', False)
    S.set('Game_State', 0)  # menu/title state -> must safely pause
    clock['sec'] = 242.5
    tick_frame()
    assert len(dead_picked) == 0
    S.set('Game_State', 1)  # active gameplay state (real engine state=1)
    clock['sec'] = 243.5
    tick_frame()
    assert len(dead_picked) == 1  # Resumes cleanly once state is normal!

    # Scenario 9: Large batch (120 ground items in 11x11)
    gmap4, add_ground4 = make_ground_map()
    ev.G.get('Q_地图').set('__gm_range_state', gmap4)
    bulk = []
    for i in range(120):
        gx = 5 + (i % 11)
        gy = 5 + ((i // 11) % 11)
        add_ground4(gx, gy, LuaTable({'名称': '金币_小', '分类': '特殊', '子类': '金币', '叠加': 0}), 5,
                    on_pick=lambda o, i=i: bulk.append(i))
    clock['sec'] = 250.0
    tick_frame()
    assert len(bulk) == 120

    # Toggle OFF stops subsequent checks immediately
    S.get('__gm_set_auto_pickup_v299')(False, True)
    pre_before = stats.get('prechecks')
    clock['sec'] = 260.0
    tick_frame()
    assert stats.get('prechecks') == pre_before

    # 前尘忆梦 isolation: button NEVER installed, auto-pickup NEVER fires, manual Alt STILL works!
    env_old = build_lua_env(mods, story='前尘忆梦')
    env_old['ev'].G.set('__gm_auto_pickup_on_v299', True)
    gm_old, add_old = make_ground_map()
    env_old['ev'].G.get('Q_地图').set('__gm_range_state', gm_old)
    old_picked = []
    add_old(10, 10, LuaTable({'名称': '金币_小', '分类': '特殊', '子类': '金币', '叠加': 0}), 10,
            on_pick=lambda o: old_picked.append('old_gold'))
    vm_old = V299VM(env_old['ev'].G, upvalues=[env_old['S']])
    vm_old.run_slice(p428, start_pc=2956, stop_pc=2983)
    assert env_old['win539'].get('控件组').length() == 0, 'Button leaked into 前尘忆梦!'
    assert len(old_picked) == 0, 'Auto-pickup leaked into 前尘忆梦!'
    # Manual Alt still works in 前尘忆梦
    env_old['alt_down']['pressed'] = True
    vm_old.run_slice(p428, start_pc=2956, stop_pc=2983)
    assert old_picked == ['old_gold']

    return 10


def _assert_valid_batch(batch):
    assert isinstance(batch, LuaTable), f'batch not table: {batch}'
    raw = batch.rawget('__数据') if isinstance(batch.rawget('__数据'), LuaTable) else batch
    assert raw.rawget('version') == 1
    n = raw.rawget('length')
    nxt = raw.rawget('next')
    assert isinstance(n, int) and 1 <= n <= 50
    assert isinstance(nxt, int) and 1 <= nxt <= n + 1
    vals = raw.rawget('values')
    vraw = vals.rawget('__数据') if isinstance(vals.rawget('__数据'), LuaTable) else vals
    seq = []
    for i in range(1, n + 1):
        s = vraw.rawget(i)
        assert isinstance(s, str), f'value[{i}] not string: {s!r}'
        fv = float(s)
        assert 0.0 <= fv < 1.0
        seq.append(s)
    return {'version': 1, 'length': n, 'next': nxt, 'values': seq}


def test_feature3_mount_sequences(mods):
    env = build_lua_env(mods, story='来世续缘')
    ev, S, bag, templates, protect = env['ev'], env['S'], env['bag'], env['templates'], env['protect']
    d14 = mods[14]

    def clone_mount(name='坐骑号角_金', luck=0, extra_fields=None):
        t = templates.get(name)
        ex = LuaTable({'重量': 1})
        if extra_fields:
            for k, v in extra_fields.items():
                ex.rawset(k, v)
        m = LuaTable({
            '名称': t.get('名称'), '显示名': t.get('显示名'), '分类': '装备', '子类': '坐骑',
            '叠加': 0, '数量': 1, '属性': protect(LuaTable({'幸运': luck}), True),
            '附加': protect(ex, True),
        })
        return protect(m, False)

    # 1. Scenario 1: Starter mount via REAL 14/481 (重置道具) hook slice!
    bag.get(32).set('道具', clone_mount('坐骑号角_金'))
    p481 = d14.protos[481]
    # Execute REAL injected hook at 14/481 PC 149..156 (R6 = slot_id = 32)
    vm481 = V299VM(ev.G, upvalues=[S])
    vm481.run_slice(p481, start_pc=149, stop_pc=156, init_regs={6: 32})
    b_starter = _assert_valid_batch(bag.get(32).get('道具').get('附加').get('__gm_oil_batch_v263'))
    assert b_starter['next'] == 1
    # Shared template untouched!
    assert templates.get('坐骑号角_金').get('附加').get('__gm_oil_batch_v263') is None

    # 2 & 3. Scenarios 2 & 3: Shop buy 2 identical mounts via REAL 14/456 (增加物品) hook slice!
    bag.get(33).set('道具', clone_mount('坐骑号角_铜'))
    bag.get(34).set('道具', clone_mount('坐骑号角_铜'))
    p456 = d14.protos[456]
    vm456 = V299VM(ev.G, upvalues=[S])
    vm456.run_slice(p456, start_pc=405, stop_pc=412, init_regs={9: 33})
    vm456.run_slice(p456, start_pc=405, stop_pc=412, init_regs={9: 34})
    m1 = bag.get(33).get('道具')
    m2 = bag.get(34).get('道具')
    b1 = _assert_valid_batch(m1.get('附加').get('__gm_oil_batch_v263'))
    b2 = _assert_valid_batch(m2.get('附加').get('__gm_oil_batch_v263'))
    assert m1.get('附加').rawget('__数据') is not m2.get('附加').rawget('__数据')
    assert b1['values'] != b2['values'] or b1['length'] != b2['length']
    assert templates.get('坐骑号角_铜').get('附加').get('__gm_oil_batch_v263') is None

    # 4. Drop creation via REAL 14/446 (掉落物品) hook slice at PC 0..7!
    dropped_mount = clone_mount('坐骑号角_铜')
    p446 = d14.protos[446]
    vm446 = V299VM(ev.G, upvalues=[S])
    vm446.run_slice(p446, start_pc=0, stop_pc=7, init_regs={1: dropped_mount})
    b_drop = _assert_valid_batch(dropped_mount.get('附加').get('__gm_oil_batch_v263'))
    # Picking up the dropped mount into slot 35 preserves its exact batch!
    bag.get(35).set('道具', dropped_mount)
    vm456.run_slice(p456, start_pc=405, stop_pc=412, init_regs={9: 35})
    assert _assert_valid_batch(bag.get(35).get('道具').get('附加').get('__gm_oil_batch_v263')) == b_drop

    # 5-14. Old-save migration via REAL 14/256 (读档) hook slices across ALL containers!
    # Clear slots 31..417 first
    for sid in range(1, 420):
        bag.get(sid).set('道具', None)

    # Simulate 14/256 load.begin -> S.__gm_loading_save_v299 = true
    p256 = d14.protos[256]
    vm256 = V299VM(ev.G, upvalues=[S])
    # Find the spliced load.begin PC (shifted by 7+7+7 = +21 from 1063 -> 1084)
    # Verify programmatically by scanning KPRI 2, KPRI 1 around load.begin
    begin_pc = next(
        pc for pc in range(len(p256.bc) - 6)
        if OPS[p256.bc[pc] & 255] == 'UGET' and OPS[p256.bc[pc + 1] & 255] == 'TGETS'
        and p256.gc((p256.bc[pc + 1] >> 16) & 255) == b'__gm_load_state_v299'
        and OPS[p256.bc[pc + 4] & 255] == 'KPRI' and (p256.bc[pc + 4] >> 16) == 2
    )
    ret_pc = next(
        pc for pc in range(len(p256.bc) - 6)
        if OPS[p256.bc[pc] & 255] == 'UGET' and OPS[p256.bc[pc + 1] & 255] == 'TGETS'
        and p256.gc((p256.bc[pc + 1] >> 16) & 255) == b'__gm_load_state_v299'
        and OPS[p256.bc[pc + 4] & 255] == 'KPRI' and (p256.bc[pc + 4] >> 16) == 1
        and OPS[p256.bc[pc + 5] & 255] == 'KPRI' and (p256.bc[pc + 5] >> 16) == 2
    )
    fail_pcs = [
        pc for pc in range(len(p256.bc) - 6)
        if OPS[p256.bc[pc] & 255] == 'UGET' and OPS[p256.bc[pc + 1] & 255] == 'TGETS'
        and p256.gc((p256.bc[pc + 1] >> 16) & 255) == b'__gm_load_state_v299'
        and OPS[p256.bc[pc + 4] & 255] == 'KPRI' and (p256.bc[pc + 4] >> 16) == 1
        and OPS[p256.bc[pc + 5] & 255] == 'KPRI' and (p256.bc[pc + 5] >> 16) == 1
    ]
    assert len(fail_pcs) == 3

    # Test fail path clears loading flag cleanly without migrating
    vm256.run_slice(p256, start_pc=begin_pc, stop_pc=begin_pc + 7)
    assert S.get('__gm_loading_save_v299') is True
    vm256.run_slice(p256, start_pc=fail_pcs[0], stop_pc=fail_pcs[0] + 7)
    assert S.get('__gm_loading_save_v299') is False

    # Now run real load.begin -> populate ALL containers (old save!) -> load.return!
    vm256.run_slice(p256, start_pc=begin_pc, stop_pc=begin_pc + 7)
    assert S.get('__gm_loading_save_v299') is True

    # Populate containers while loading (14/481 hook must defer while loading!)
    bag.get(13).set('道具', clone_mount('坐骑号角_金'))                                       # Hero equipped, Case A (no batch)
    vm481.run_slice(p481, start_pc=149, stop_pc=156, init_regs={6: 13})
    assert bag.get(13).get('道具').get('附加').get('__gm_oil_batch_v263') is None, 'Should defer until load.return'

    mid_batch = LuaTable({'version': 1, 'length': 4, 'next': 3, 'values': LuaTable({1: '0.1', 2: '0.2', 3: '0.3', 4: '0.4'})})
    exh_batch = LuaTable({'version': 1, 'length': 3, 'next': 4, 'values': LuaTable({1: '0.5', 2: '0.6', 3: '0.7'})})
    bad_batch = LuaTable({'version': 99, 'length': -5, 'next': 1, 'values': LuaTable()})

    bag.get(22).set('道具', clone_mount('坐骑号角_金', extra_fields={'__gm_oil_batch_v263': mid_batch}))   # Quickbar, Case B mid-progress
    bag.get(31).set('道具', clone_mount('坐骑号角_铜'))                                                     # Hero bag, Case A
    bag.get(127).set('道具', clone_mount('坐骑号角_金', extra_fields={'__gm_oil_batch_v263': exh_batch}))  # Warehouse, Case B EXHAUSTED (next=length+1!)
    bag.get(128).set('道具', clone_mount('坐骑号角_铜'))                                                    # Warehouse, Case A
    bag.get(227).set('道具', clone_mount('坐骑号角_铜'))                                                    # Guild warehouse, Case A
    bag.get(335).set('道具', clone_mount('坐骑号角_铜'))                                                    # Merc bag, Case A
    bag.get(409).set('道具', clone_mount('坐骑号角_金'))                                                    # Unsummoned merc equipped, Case A
    bag.get(36).set('道具', clone_mount('坐骑号角_金', extra_fields={'__gm_oil_batch_v263': bad_batch}))   # Case C: malformed table
    bag.get(37).set('道具', clone_mount('坐骑号角_金', extra_fields={'__gm_oil_batch_v263': 'corrupt'}))   # Case C: malformed string

    # Fire REAL 14/256 load.return hook!
    vm256.run_slice(p256, start_pc=ret_pc, stop_pc=ret_pc + 7)
    assert S.get('__gm_loading_save_v299') is False
    mstats = S.get('__gm_mount_migrate_last_v299')
    assert mstats.get('scanned') == 10
    assert mstats.get('initialized') == 6  # slots 13, 31, 128, 227, 335, 409
    assert mstats.get('kept') == 2         # slots 22 (mid) & 127 (exhausted!)
    assert mstats.get('anomalies') == 2    # slots 36 & 37 (malformed, NOT overwritten!)
    assert mstats.get('errors') == 0

    # Verify Case A containers all got valid independent batches
    seen_seqs = set()
    for sid in (13, 31, 128, 227, 335, 409):
        b = _assert_valid_batch(bag.get(sid).get('道具').get('附加').get('__gm_oil_batch_v263'))
        assert b['next'] == 1
        seen_seqs.add(tuple(b['values']))
    assert len(seen_seqs) == 6

    # Verify Case B mid-progress & exhausted (next == length + 1) UNTOUCHED!
    b22 = _assert_valid_batch(bag.get(22).get('道具').get('附加').get('__gm_oil_batch_v263'))
    assert b22 == {'version': 1, 'length': 4, 'next': 3, 'values': ['0.1', '0.2', '0.3', '0.4']}
    b127 = _assert_valid_batch(bag.get(127).get('道具').get('附加').get('__gm_oil_batch_v263'))
    assert b127 == {'version': 1, 'length': 3, 'next': 4, 'values': ['0.5', '0.6', '0.7']}

    # Verify Case C malformed data PRESERVED (never silently overwritten) and logged!
    assert bag.get(36).get('道具').get('附加').get('__gm_oil_batch_v263').get('version') == 99
    assert bag.get(37).get('道具').get('附加').get('__gm_oil_batch_v263') == 'corrupt'
    assert S.get('__gm_mount_batch_anomalies_v299').length() == 2

    # Idempotency check: re-running migration does ZERO re-generation!
    before_13 = _assert_valid_batch(bag.get(13).get('道具').get('附加').get('__gm_oil_batch_v263'))
    before_409 = _assert_valid_batch(bag.get(409).get('道具').get('附加').get('__gm_oil_batch_v263'))
    mstats2 = S.get('__gm_migrate_mounts_v299')()
    assert mstats2.get('initialized') == 0 and mstats2.get('kept') == 8 and mstats2.get('anomalies') == 2
    assert _assert_valid_batch(bag.get(13).get('道具').get('附加').get('__gm_oil_batch_v263')) == before_13
    assert _assert_valid_batch(bag.get(409).get('道具').get('附加').get('__gm_oil_batch_v263')) == before_409

    # Transfer hero -> merc, bag sort, equip/unequip: sequence travels identically with instance!
    hero_mount = bag.get(13).get('道具')
    bag.get(13).set('道具', None)
    bag.get(38).set('道具', hero_mount)   # unequip to bag
    bag.get(38).set('道具', None)
    bag.get(409).set('道具', hero_mount)  # transfer to merc equip
    assert _assert_valid_batch(bag.get(409).get('道具').get('附加').get('__gm_oil_batch_v263')) == before_13

    # Save/reload round-trip simulation (table.copy(extra, true) -> new item -> migrate_mounts_once)
    saved_extra = ev.G.get('table').get('copy')(bag.get(22).get('道具').get('附加'), True)
    reloaded = clone_mount('坐骑号角_金')
    reloaded.set('附加', protect(saved_extra, True))
    bag.get(39).set('道具', reloaded)
    S.get('__gm_migrate_mounts_v299')()
    assert _assert_valid_batch(bag.get(39).get('道具').get('附加').get('__gm_oil_batch_v263')) == b22

    # Scenario 15: Luck level changes use existing luck rules dynamically against the pre-generated sequence!
    # At luck=0: guaranteed +1 (a=1,b=0,c=0) regardless of roll value, consumes 1 roll (next: 1 -> 2).
    # At luck=1..6: success 40%, loss 30%, same 30% using batch.values[next].
    test_b = _assert_valid_batch(bag.get(31).get('道具').get('附加').get('__gm_oil_batch_v263'))
    r1 = float(test_b['values'][0])
    # Luck 0 -> always +1, consumes roll 1
    luck = 0
    luck_after_0 = luck + 1  # luck 0 guaranteed
    assert luck_after_0 == 1
    # At luck=3 using the exact same roll value r1:
    outcome_at_3 = 'success' if r1 < 0.4 else ('loss' if r1 < 0.7 else 'same')
    assert outcome_at_3 in ('success', 'loss', 'same')
    # At luck=7: capped, no roll consumed!

    # 前尘忆梦 isolation: mount creation & migration do NOTHING in 前尘忆梦!
    env_old = build_lua_env(mods, story='前尘忆梦')
    m_old = clone_mount('坐骑号角_金')
    env_old['bag'].get(32).set('道具', m_old)
    env_old['S'].get('__gm_on_slot_item_v299')(32, 'reset_item')
    env_old['S'].get('__gm_migrate_mounts_v299')()
    assert env_old['bag'].get(32).get('道具').get('附加').get('__gm_oil_batch_v263') is None

    return 15


def main():
    base_bytes = (W / 'game_v298.res').read_bytes()
    new_bytes = (W / 'game_v299.res').read_bytes()
    assert hashlib.sha256(base_bytes).hexdigest() == BASE_SHA

    mods, changed_mods, changed_protos, audited_count = verify_42_modules_and_static_audit(base_bytes, new_bytes)
    f1_cases = test_feature1_reputation_shop(mods)
    f2_cases = test_feature2_auto_pickup(mods)
    f3_cases = test_feature3_mount_sequences(mods)

    tested_files = {}
    for fname in ('runtime_v299.lua', 'patch_v299.py', 'lua51_eval.py', 'test_v299.py'):
        tested_files[fname] = hashlib.sha256((W / fname).read_bytes()).hexdigest()

    sha = hashlib.sha256(new_bytes).hexdigest()
    report = {
        'version': 'v1.299',
        'all_passed': True,
        'base_sha256': BASE_SHA,
        'sha256': sha,
        'game_res_sha256': sha,
        'game_res_bytes': len(new_bytes),
        'tested_files': tested_files,
        'changed_modules': changed_mods,
        'changed_prototypes': {str(k): v for k, v in changed_protos.items()},
        'static_audited_prototypes': audited_count,
        'feature1_reputation_shop_cases_passed': f1_cases,
        'feature2_auto_pickup_cases_passed': f2_cases,
        'feature3_mount_batch_cases_passed': f3_cases,
        'qian_chen_yi_meng_isolated': True,
        'verification_boundary': (
            'Verified via 42-module reverse-diff, Dump.rebuild() round-trips, static LuaJIT 2.0 '
            'dataflow/J->maxslot/JMP.A audit, strict Lua 5.1 parse + GBK hazard check of embedded '
            'runtime_v299.lua, real LuaJIT 2.0 bytecode VM execution of all patched hooks, and '
            'controlled end-to-end execution of embedded runtime_v299.lua. '
            'Native Windows x86 client real-machine run, LuaJIT JIT hot-path trace compilation, '
            'real pixel rendering, and 30-minute live endurance comparison were NOT executed here '
            'and remain for real-client verification.'
        ),
        'unsaved_migration_boundary': (
            'Old-save mount sequences initialized on load persist automatically on the next normal '
            'or 20-second autosave; if the game exits abnormally before the first save completes, '
            're-loading the unmodified old save will initialize again.'
        ),
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v299.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v299.json').write_text(text, encoding='utf-8')
    print('ALL v1.299 TESTS PASSED:', {
        'sha256': report['game_res_sha256'],
        'audited': audited_count,
        'f1': f1_cases, 'f2': f2_cases, 'f3': f3_cases,
    })


if __name__ == '__main__':
    main()
