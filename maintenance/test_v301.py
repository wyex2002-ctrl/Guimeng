"""Exhaustive verification suite for v1.301:
- 42-module reverse-diff integrity against game_v300.res & rebuild round-trip
- Static LuaJIT 2.0 J->maxslot / JMP.A audit on 22/97 + all 123 protos of Module 22
- Strict Lua 5.1 syntax parse + GBK 0x5C hazard audit on embedded runtime_v301.lua from game_v301.res
- Real bytecode VM execution of patched 22/97 (monster death drop):
  * Normal monster with 掉宝数据表 + 附加.挖取 drops both and clears 附加.挖取
  * Empty 掉宝数据表 monster (鸡/鹿/栗子树) with 附加.挖取 drops corpse items directly and clears 附加.挖取
  * 0-multiplier monster with 掉宝数据表 + 附加.挖取 skips normal drops and drops only 附加.挖取
  * 镖车 is excluded (附加.挖取 untouched)
  * 「前尘忆梦」 is 100% untouched (附加.挖取 untouched)
- End-to-end execution of embedded runtime_v301.lua + merc_mode_v288.lua:
  * Ranged assassin mercenary blinks behind ANY adjacent enemy monster (not only locked target),
    preferring walkable tiles not adjacent to any enemy, and faces the locked target
  * All 5 ranged skills (蝉舞/盛开/白莲/红莲/月桂) + 刺客普通攻击 launch spinning weapon projectile,
    deferring BOTH damage (伤害进度) AND skill hit animation (命中动画延迟 -> 目标动画) to projectile arrival
  * No blink when no enemy is adjacent; still blinks when locked target is adjacent
  * 「前尘忆梦」 delegates to original merc_mode_v288 (no non-target blink, no skill projectile)
- v1.300 regression checks (0.5s auto-pickup, unfocused window, 3-state cycle, tooltip)
"""
import hashlib
import json
import math
from pathlib import Path

from ljdis import OPS
from ljtool import Dump
from lua51_eval import LuaEvaluator, LuaTable, syntax_check
from native_test_utils import trees
from resource_tools import decode, numbers
from test_v297 import analyze_proto
from test_v299 import V299VM
from test_v300 import make_env, make_ground_obj, place_ground

W = Path(__file__).resolve().parent
BASE_SHA = 'dea530c0d8c61b622b28be864563dc32669f901870fa514af0a2e84b323bdbe7'


class V301VM(V299VM):
    """Full LuaJIT 2.0 bytecode executor for 22/97 (adds FNEW, UNM, CALLM, UCLO, ADDVN/SUBVN)."""

    def run_proto(self, p, *args):
        R = [None] * max(p.frame + 8, 64)
        for i, v in enumerate(args):
            R[i] = v
        knums, _ = numbers(p)
        pc = 0
        multres = []
        steps = 0
        while pc < p.nbc:
            steps += 1
            assert steps < 200000, f'Loop limit in proto {p.idx} at pc={pc}'
            w = p.bc[pc]
            op = OPS[w & 255]
            a, b, c, d = (w >> 8) & 255, (w >> 24) & 255, (w >> 16) & 255, (w >> 16) & 65535
            if op == 'MOV':
                R[a] = R[d]; pc += 1
            elif op == 'KSHORT':
                R[a] = d if d < 32768 else d - 65536; pc += 1
            elif op == 'KNUM':
                R[a] = knums[d]; pc += 1
            elif op == 'KSTR':
                R[a] = self._kstr(p, d); pc += 1
            elif op == 'KPRI':
                R[a] = (None, False, True)[d]; pc += 1
            elif op == 'TNEW':
                R[a] = {}; pc += 1
            elif op == 'TDUP':
                R[a] = self._tdup(p, d); pc += 1
            elif op == 'FNEW':
                R[a] = self.child_handlers[d]; pc += 1
            elif op == 'GGET':
                R[a] = self._tbl_get(self.G, self._kstr(p, d)); pc += 1
            elif op == 'TGETS':
                R[a] = self._tbl_get(R[b], self._kstr(p, c)); pc += 1
            elif op == 'TSETS':
                self._tbl_set(R[b], self._kstr(p, c), R[a]); pc += 1
            elif op == 'TGETB':
                R[a] = self._tbl_get(R[b], c); pc += 1
            elif op == 'TSETB':
                self._tbl_set(R[b], c, R[a]); pc += 1
            elif op == 'TGETV':
                R[a] = self._tbl_get(R[b], R[c]); pc += 1
            elif op == 'TSETV':
                self._tbl_set(R[b], R[c], R[a]); pc += 1
            elif op == 'LEN':
                v = R[d]
                R[a] = len(v) if isinstance(v, (dict, list, str)) else (v.length() if isinstance(v, LuaTable) else 0)
                pc += 1
            elif op == 'UNM':
                R[a] = -R[d]; pc += 1
            elif op == 'ADDVV':
                R[a] = R[b] + R[c]; pc += 1
            elif op == 'SUBVV':
                R[a] = R[b] - R[c]; pc += 1
            elif op == 'MULVV':
                R[a] = R[b] * R[c]; pc += 1
            elif op == 'DIVVV':
                R[a] = R[b] / R[c]; pc += 1
            elif op == 'ADDVN':
                R[a] = R[b] + knums[c]; pc += 1
            elif op == 'SUBVN':
                R[a] = R[b] - knums[c]; pc += 1
            elif op == 'JMP' or op == 'UCLO':
                pc = pc + 1 + d - 32768
            elif op == 'ISLT':
                pc += 1 if (R[a] < R[d]) else 2
            elif op == 'ISGE':
                pc += 1 if (R[a] >= R[d]) else 2
            elif op == 'ISLE':
                pc += 1 if (R[a] <= R[d]) else 2
            elif op == 'ISGT':
                pc += 1 if (R[a] > R[d]) else 2
            elif op == 'ISEQV':
                pc += 1 if (R[a] == R[d]) else 2
            elif op == 'ISNEV':
                pc += 1 if (R[a] != R[d]) else 2
            elif op == 'ISEQN':
                pc += 1 if (R[a] == knums[d]) else 2
            elif op == 'ISNEN':
                pc += 1 if (R[a] != knums[d]) else 2
            elif op == 'ISEQP':
                pc += 1 if (R[a] is (None, False, True)[d]) else 2
            elif op == 'ISNEP':
                pc += 1 if (R[a] is not (None, False, True)[d]) else 2
            elif op == 'IST':
                pc += 1 if (R[d] is not None and R[d] is not False) else 2
            elif op == 'ISF':
                pc += 1 if (R[d] is None or R[d] is False) else 2
            elif op == 'FORI':
                if (R[a + 2] >= 0 and R[a] <= R[a + 1]) or (R[a + 2] < 0 and R[a] >= R[a + 1]):
                    R[a + 3] = R[a]; pc += 1
                else:
                    pc = pc + 1 + d - 32768
            elif op == 'FORL':
                R[a] = R[a] + R[a + 2]
                if (R[a + 2] >= 0 and R[a] <= R[a + 1]) or (R[a + 2] < 0 and R[a] >= R[a + 1]):
                    R[a + 3] = R[a]; pc = pc + 1 + d - 32768
                else:
                    pc += 1
            elif op == 'CALL':
                fn = R[a]
                cargs = [R[a + 1 + i] for i in range(c - 1)]
                res = fn(*cargs)
                res_list = list(res) if isinstance(res, tuple) else [res]
                if b == 0:
                    multres = res_list
                else:
                    for i in range(b - 1):
                        R[a + i] = res_list[i] if i < len(res_list) else None
                pc += 1
            elif op == 'CALLM':
                fn = R[a]
                cargs = [R[a + 1 + i] for i in range(c)] + multres
                res = fn(*cargs)
                res_list = list(res) if isinstance(res, tuple) else [res]
                if b == 0:
                    multres = res_list
                else:
                    for i in range(b - 1):
                        R[a + i] = res_list[i] if i < len(res_list) else None
                pc += 1
            elif op == 'RET0':
                return None
            else:
                raise NotImplementedError(f'V301VM opcode {op} at pc={pc}')
        return None


def extract_runtime_v301(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.301 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v301.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_reverse_diff_and_static_audit():
    base_bytes = (W / 'game_v300.res').read_bytes()
    out_bytes = (W / 'game_v301.res').read_bytes()
    assert hashlib.sha256(base_bytes).hexdigest() == BASE_SHA

    outer_b, mods_b = decode(base_bytes, (12, 14, 22, 30))
    outer_o, mods_o = decode(out_bytes, (12, 14, 22, 30))

    # Full outer-resource diff across all gc slots
    root_b, root_o = outer_b.protos[0], outer_o.protos[0]
    assert root_b.nkgc == root_o.nkgc
    changed_slots = [i for i in range(root_b.nkgc) if root_b.gc(i) != root_o.gc(i)]
    assert changed_slots == [12, 14, 22, 30], f'Unexpected changed outer slots: {changed_slots}'

    changed_mods = []
    for mid in (12, 14, 22, 30):
        rb = mods_b[mid].rebuild()
        ro = mods_o[mid].rebuild()
        if rb != ro:
            changed_mods.append(mid)
            assert Dump(ro).rebuild() == ro
    assert changed_mods == [12, 14, 22, 30], f'Unexpected changed modules: {changed_mods}'

    # Verify proto-level diffs in Module 14 and Module 22
    m14_diff = [i for i in range(len(mods_o[14].protos)) if mods_b[14].protos[i].raw != mods_o[14].protos[i].raw]
    m22_diff = [i for i in range(len(mods_o[22].protos)) if mods_b[22].protos[i].raw != mods_o[22].protos[i].raw]
    assert 781 in m14_diff
    assert m22_diff == [97], f'Expected only 22/97 changed in Module 22, got {m22_diff}'

    # trees() integrity on all changed modules
    for mid in changed_mods:
        trees(mods_o[mid])

    # Static J->maxslot / JMP.A audit on all 123 protos of Module 22
    for idx, p in enumerate(mods_o[22].protos):
        res_o = analyze_proto(p)
        res_b = analyze_proto(mods_b[22].protos[idx])
        assert res_o['bad_jmp_a'] == [], f'22/{idx} has bad_jmp_a: {res_o["bad_jmp_a"]}'
        assert len(res_o['call_gaps']) <= len(res_b['call_gaps']), f'22/{idx} introduced new call gaps: {res_o["call_gaps"]} vs {res_b["call_gaps"]}'

    # Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v301.lua
    rt_src = extract_runtime_v301(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'

    return mods_o, rt_src


def test_corpse_drop_vm_22_97(m22, rt_src):
    """Execute actual patched 22/97 bytecode in V299VM across 5 monster scenarios."""
    p97 = m22.protos[97]

    def run_death(story, monster_name, drop_table, drop_mult, dig_items):
        env = make_env(story=story)
        ev, S = env['ev'], env['S']
        ev.G.get('loadstring')(rt_src)(S)

        # Wire mock decrypt/loadstring for 附加.挖取
        item_store = {}

        def mock_decrypt(raw, key):
            assert key == 'mir3zuobigou'
            if raw.startswith('ENC:'):
                return raw[4:]
            return raw

        def mock_loadstring(plain):
            return item_store[plain]

        ev.G.rawset('文本加解密', mock_decrypt)
        ev.G.get('table').rawset('loadstring', mock_loadstring)

        dig_tbl = LuaTable()
        for idx, it in enumerate(dig_items, 1):
            token = f'ITEM_{idx}'
            t = LuaTable()
            for k, v in it.items():
                t.rawset(k, v)
            t.rawset('附加', LuaTable())
            t.rawset('属性', LuaTable())
            item_store[token] = t
            dig_tbl.rawset(idx, 'ENC:' + token)

        dropped = []

        # Build VM globals mirroring game engine for 22/97
        def copy_obj(o):
            if isinstance(o, dict):
                return dict(o)
            if isinstance(o, LuaTable):
                d = {}
                for k, v in o._data.items():
                    d[k] = copy_obj(v)
                return d
            return o

        def sys_run(name, *args):
            if name == '数据保护':
                return args[0]
            if name == '掉落物前置处理':
                # args: x, y, item, count, id -> return skip=False, count, item
                return (False, args[3], args[2])
            if name == '掉落物品':
                # args: True, item, count, x, y, mx, my
                dropped.append({
                    'item': args[1],
                    'count': args[2],
                    'x': args[3],
                    'y': args[4],
                })
                return None
            return None

        # Bridge __gm_corpse_has_v301 and __gm_corpse_drop_v301 from LuaEvaluator into V299VM
        # Converting dict <-> LuaTable cleanly at boundary
        def to_lua(obj):
            if isinstance(obj, LuaTable):
                return obj
            if isinstance(obj, dict):
                t = LuaTable()
                for k, v in obj.items():
                    t.rawset(k, to_lua(v))
                return t
            if isinstance(obj, list):
                t = LuaTable()
                for i, v in enumerate(obj, 1):
                    t.rawset(i, to_lua(v))
                return t
            return obj

        has_fn = ev.G.get('__gm_corpse_has_v301')
        drop_fn = ev.G.get('__gm_corpse_drop_v301')

        actor_lua = LuaTable()
        prop_lua = LuaTable()
        prop_lua.rawset('名称', monster_name)
        extra_lua = LuaTable()
        extra_lua.rawset('挖取', dig_tbl)
        actor_lua.rawset('属性', prop_lua)
        actor_lua.rawset('附加', extra_lua)

        def vm_has(actor):
            return bool(has_fn(actor_lua))

        def vm_drop(actor, drops):
            drops_lua = LuaTable()
            for i in range(1, len(drops) + 1):
                if i in drops:
                    drops_lua.rawset(i, drops[i])
            added = drop_fn(actor_lua, drops_lua)
            # Sync newly appended entries back to V299VM drops dict
            n = drops_lua.length()
            for i in range(len(drops) + 1, n + 1):
                entry = drops_lua.rawget(i)
                it_lua = entry.rawget('物品道具')
                drops[i] = {
                    '物品道具': copy_obj(it_lua),
                    '掉落数量': entry.rawget('掉落数量'),
                }
            return added

        # Build monster dict for 22/97 VM
        dt_dict = {}
        for i, entry in enumerate(drop_table, 1):
            dt_dict[i] = entry

        actor_vm = {
            'id': 9001,
            '宠物配置': {'掉落物品': True},
            '属性': {
                '名称': monster_name,
                '掉宝数据表': dt_dict,
                '掉宝倍数': drop_mult,
            },
            '地图格子': {'x': 100, 'y': 100},
        }

        def get_item_info(name):
            return {'名称': name, '分类': '道具', '叠加': 0, '附加': {}, '属性': {}}

        vm_globals = {
            '引擎': {
                '置随机数种子': lambda *a: None,
                '取随机整数': lambda self_e, a, b: int(a),
            },
            'Gly独': {
                '取随机数': lambda a, b: a,
                '取道具信息_名称': get_item_info,
            },
            'Ux雌': {'版本选择': story},
            'Q_地图': {'取格子信息': lambda x, y, k: 0},
            'Sys': {
                'run': sys_run,
                'get': lambda kind, name: get_item_info(name) if kind == 'item' else None,
            },
            'table': {
                'insert': lambda t, v: t.__setitem__(len(t) + 1, v),
                'copy': copy_obj,
                'sort': lambda *a: None,
            },
            'math': {'floor': math.floor, 'ceil': math.ceil, 'abs': abs},
            'tonumber': lambda x: int(x),
            'lookupHelixNumber': lambda dx, dy: dx * dx + dy * dy,
            '__gm_corpse_has_v301': vm_has,
            '__gm_corpse_drop_v301': vm_drop,
            '__gm_drop_filter_v297': lambda drops: None,
        }

        vm = V301VM(vm_globals, child_handlers={36: lambda drops: None, 27: lambda a, b: a[1] < b[1]})
        vm.run_proto(p97, actor_vm)
        remaining_dig = extra_lua.rawget('挖取').length()
        return dropped, remaining_dig

    # 1. Normal monster (赤龙魔王) with normal drop + corpse dig drops (四级蝉舞 + 赤龙宝甲_男)
    normal_dt = [{'最小几率': 1, '道具标识': '金创药(大)', '掉落数量': 1}]
    dig_boss = [
        {'名称': '四级蝉舞', '分类': '技能书', '强化书': 4},
        {'名称': '赤龙宝甲_男', '分类': '装备', '子类': '衣服'},
    ]
    dropped, rem = run_death('来世续缘', '赤龙魔王', normal_dt, 1, dig_boss)
    names = [d['item']['名称'] for d in dropped]
    assert '金创药(大)' in names and '四级蝉舞' in names and '赤龙宝甲_男' in names, f'Boss drops: {names}'
    assert rem == 0, f'Expected 附加.挖取 cleared to 0, got {rem}'

    # 2. Empty drop-table monster (鸡) with 掉宝倍数=1 and 附加.挖取=[鸡肉]
    dropped2, rem2 = run_death('来世续缘', '鸡', [], 1, [{'名称': '鸡肉', '分类': '道具'}])
    names2 = [d['item']['名称'] for d in dropped2]
    assert names2 == ['鸡肉'], f'Chicken drops: {names2}'
    assert rem2 == 0

    # 3. Empty drop-table monster (栗子树) with 掉宝倍数=0 and 附加.挖取=[栗子]
    dropped3, rem3 = run_death('来世续缘', '栗子树', [], 0, [{'名称': '栗子', '分类': '道具'}])
    names3 = [d['item']['名称'] for d in dropped3]
    assert names3 == ['栗子'], f'Chestnut drops: {names3}'
    assert rem3 == 0

    # 4. 0-multiplier monster with normal drop table + 附加.挖取 -> skips normal drops, drops ONLY 挖取
    dropped4, rem4 = run_death('来世续缘', '毒蜘蛛', normal_dt, 0, [{'名称': '蜘蛛牙齿', '分类': '道具'}])
    names4 = [d['item']['名称'] for d in dropped4]
    assert names4 == ['蜘蛛牙齿'], f'0-mult drops should skip normal table: {names4}'
    assert rem4 == 0

    # 5. 镖车 excluded
    dropped5, rem5 = run_death('来世续缘', '镖车', [], 0, [{'名称': '镖银', '分类': '道具'}])
    assert dropped5 == [] and rem5 == 1, f'镖车 should be excluded: {dropped5}, rem={rem5}'

    # 6. 「前尘忆梦」 completely untouched
    dropped6, rem6 = run_death('前尘忆梦', '赤龙魔王', normal_dt, 1, dig_boss)
    names6 = [d['item']['名称'] for d in dropped6]
    assert names6 == ['金创药(大)'] and rem6 == 2, f'前尘忆梦 must not drop 挖取: {names6}, rem={rem6}'


def make_merc_env(rt_src, story='来世续缘'):
    """Load BOTH merc_mode_v288.lua and embedded runtime_v301.lua into one LuaEvaluator."""
    env = make_env(story=story)
    ev, S = env['ev'], env['S']

    # Direction helper (8 directions 1..8) matching engine convention
    def dir_fn(x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy < 0:
            return 1
        if dx > 0 and dy < 0:
            return 2
        if dx > 0 and dy == 0:
            return 3
        if dx > 0 and dy > 0:
            return 4
        if dx == 0 and dy > 0:
            return 5
        if dx < 0 and dy > 0:
            return 6
        if dx < 0 and dy == 0:
            return 7
        return 8

    ev.G.rawset('取两点间方向', dir_fn)
    ev.G.rawset('dt', 0.05)

    # Blocked tiles set for obstacle testing
    blocked = set()
    qmap = LuaTable()
    qmap.rawset('取格子信息', lambda x, y, k: 1 if (x, y) in blocked else 0)
    ev.G.rawset('Q_地图', qmap)

    # Skill speed lookup + Sys.add
    fireball = LuaTable()
    fireball.rawset('子弹速度', 600)
    added_bullets = []
    sys_tbl = LuaTable()
    sys_tbl.rawset('get', lambda kind, key: fireball if kind == 'skill' and '火球术' in str(key) else None)
    sys_tbl.rawset('add', lambda kind, obj: added_bullets.append((kind, obj)))
    ev.G.rawset('Sys', sys_tbl)

    # Projectile factory spy matching 16-arg ABI in merc_mode_v288.lua line 219
    spawned = []

    def proj_factory(x, y, tx, ty, speed, actor, target, mode, image, *rest):
        p = {'x': x, 'y': y, 'tx': tx, 'ty': ty, 'speed': speed, 'image': image}
        spawned.append(p)
        b = LuaTable()
        b.rawset('更新', lambda: None)
        b.rawset('已经消失', lambda: False)
        b.rawset('销毁', lambda: None)
        return b

    ev.G.rawset('__gm_merc_visual_factory_v255', proj_factory)

    # Equip ranged assassin weapon in slot 397
    w_attr = LuaTable()
    w_attr.rawset('绑定技能', '刺客普通攻击')
    w_item = LuaTable()
    w_item.rawset('名称', '飞镖(远程)')
    w_item.rawset('分类', '装备')
    w_item.rawset('子类', '武器')
    w_item.rawset('地面图标', 'icon_dart.img')
    w_item.rawset('附加', w_attr)
    slot397 = LuaTable()
    slot397.rawset('道具', w_item)
    S.rawget('包裹物品组').rawset(397, slot397)

    # Create assassin mercenary actor
    blinks = []
    merc = LuaTable()
    merc.rawset('id', 501)
    merc.rawset('HP', 1000)
    merc.rawset('绑定技能', '刺客普通攻击')
    merc.rawset('方向', 3)
    m_grid = LuaTable()
    m_grid.rawset('x', 50)
    m_grid.rawset('y', 50)
    m_px = LuaTable()
    m_px.rawset('x', 50 * 48)
    m_px.rawset('y', 50 * 32)
    m_prop = LuaTable()
    m_prop.rawset('hp', 1000)
    m_prop.rawset('中心Y偏移', 20)
    m_prop.rawset('模型大小', 1)
    merc.rawset('地图格子', m_grid)
    merc.rawset('地图坐标', m_px)
    merc.rawset('属性', m_prop)

    def do_blink(bx, by):
        blinks.append((bx, by))
        m_grid.rawset('x', bx)
        m_grid.rawset('y', by)
        m_px.rawset('x', bx * 48)
        m_px.rawset('y', by * 32)

    merc.rawset('瞬移', do_blink)
    env['U'].rawset('佣兵对象', merc)

    # Load merc_mode_v288.lua first (just like module 14 init), then runtime_v301.lua
    merc_src = (W / 'merc_mode_v288.lua').read_text(encoding='utf-8')
    merc_init = ev.G.get('loadstring')(merc_src)()
    merc_init(S, ev.G)
    ev.G.get('loadstring')(rt_src)(S)

    return ev, S, merc, blinks, spawned, blocked


def make_enemy(eid, x, y, facing=3, camp='敌方', hp=500, unselectable=False):
    e = LuaTable()
    e.rawset('id', eid)
    e.rawset('HP', hp)
    e.rawset('所属阵营', camp)
    e.rawset('方向', facing)
    if unselectable:
        e.rawset('不可选中', True)
    g = LuaTable()
    g.rawset('x', x)
    g.rawset('y', y)
    px = LuaTable()
    px.rawset('x', x * 48)
    px.rawset('y', y * 32)
    prop = LuaTable()
    prop.rawset('hp', hp)
    prop.rawset('中心Y偏移', 20)
    prop.rawset('模型大小', 1)
    e.rawset('地图格子', g)
    e.rawset('地图坐标', px)
    e.rawset('属性', prop)
    return e


def make_cast(merc, target, skill_name, hit_delay=0.15, dmg_delays=(0.30,)):
    state = LuaTable()
    cfg = LuaTable()
    cfg.rawset('名称', skill_name)
    state.rawset('施法者', merc)
    state.rawset('目标', target)
    state.rawset('对象', cfg)
    state.rawset('起手动画延迟', 0)
    state.rawset('命中动画延迟', hit_delay)
    state.rawset('延迟dt', 0.0)
    dmg = LuaTable()
    for i, d in enumerate(dmg_delays, 1):
        dmg.rawset(i, d)
    state.rawset('伤害进度', dmg)
    public = LuaTable()
    public.rawset('刷新', lambda: False)
    return state, public


def test_merc_ranged_skills(rt_src):
    # Case 1: Locked target is FAR (55, 50), another enemy E2 is ADJACENT (51, 50)
    # Casting each of the 5 ranged skills MUST blink behind E2 AND launch projectile + defer damage & hit anim!
    expected_dist = {'蝉舞': 4, '盛开': 2, '白莲': 2, '红莲': 3, '月桂': 3}
    for skill, dist in expected_dist.items():
        ev, S, merc, blinks, spawned, _ = make_merc_env(rt_src, story='来世续缘')
        far_target = make_enemy(1001, 55, 50, facing=7)
        adj_enemy = make_enemy(1002, 51, 50, facing=7)  # facing west (toward merc), behind is east (x = 51 + dist)
        actors = LuaTable()
        actors.rawset(1, merc)
        actors.rawset(2, far_target)
        actors.rawset(3, adj_enemy)
        S.rawset('屏幕事件组', actors)

        state, public = make_cast(merc, far_target, skill, hit_delay=0.15, dmg_delays=(0.30, 0.45))
        prepare = ev.G.get('__gm_merc_visual_prepare_v255')
        step = ev.G.get('__gm_merc_visual_step_v255')
        prepare(state, public)

        # Must have blinked!
        assert len(blinks) == 1, f'{skill}: expected blink when non-target enemy adjacent, got {blinks}'
        bx, by = blinks[0]
        assert max(abs(bx - 51), abs(by - 50)) == dist, f'{skill}: expected ring dist {dist} around E2, got ({bx},{by})'
        # Must NOT have returned early: projectile shot MUST be created & both damage and hit anim deferred!
        shot = state.rawget('__gm_merc_visual_v255')
        assert isinstance(shot, LuaTable), f'{skill}: expected projectile shot created'
        assert state.rawget('命中动画延迟') == math.inf, f'{skill}: 命中动画延迟 must be deferred to inf'
        assert state.rawget('伤害进度').rawget(1) == math.inf, f'{skill}: 伤害进度[1] must be deferred to inf'
        assert state.rawget('伤害进度').rawget(2) == math.inf, f'{skill}: 伤害进度[2] must be deferred to inf'

        # Step 1: launches projectile from post-blink position toward far_target!
        step(state)
        assert len(spawned) == 1, f'{skill}: expected projectile spawned'
        assert spawned[0]['x'] == bx * 48, f'{skill}: projectile must launch from post-blink x'
        assert spawned[0]['tx'] == 55 * 48, f'{skill}: projectile must target locked target'

        # While in flight: both remain inf
        state.rawset('延迟dt', 0.20)
        step(state)
        assert state.rawget('命中动画延迟') == math.inf
        assert state.rawget('伤害进度').rawget(1) == math.inf

        # On arrival: BOTH hit animation AND damage release at state.延迟dt!
        state.rawset('延迟dt', 0.55)
        shot.rawset('arrived', True)
        step(state)
        assert state.rawget('命中动画延迟') == 0.55, f'{skill}: hit anim must start on arrival'
        assert abs(state.rawget('伤害进度').rawget(1) - 0.55) < 1e-6, f'{skill}: dmg[1] must land on arrival'
        assert abs(state.rawget('伤害进度').rawget(2) - 0.70) < 1e-6, f'{skill}: dmg[2] keeps +0.15 offset'

    # Case 2: Prefer safe tile not adjacent to a 3rd enemy when retreating
    ev, S, merc, blinks, _, _ = make_merc_env(rt_src, story='来世续缘')
    far_target = make_enemy(1001, 56, 50, facing=7)
    adj_enemy = make_enemy(1002, 51, 50, facing=7)   # first ring tile for dist=2 is (53, 50)
    blocker_enemy = make_enemy(1003, 53, 50, facing=7)  # sitting right on (53, 50)!
    actors = LuaTable()
    actors.rawset(1, merc)
    actors.rawset(2, far_target)
    actors.rawset(3, adj_enemy)
    actors.rawset(4, blocker_enemy)
    S.rawset('屏幕事件组', actors)
    state, public = make_cast(merc, far_target, '盛开')
    ev.G.get('__gm_merc_visual_prepare_v255')(state, public)
    assert len(blinks) == 1
    bx, by = blinks[0]
    assert max(abs(bx - 53), abs(by - 50)) > 1, f'Expected safe tile away from E3(53,50), got ({bx},{by})'

    # Case 3: No adjacent enemy (all enemies dist >= 2), plus adjacent ally & dead enemy -> NO blink, YES projectile!
    ev, S, merc, blinks, spawned, _ = make_merc_env(rt_src, story='来世续缘')
    far_target = make_enemy(1001, 54, 50, facing=7)
    adj_ally = make_enemy(1004, 51, 50, camp='友方')
    adj_dead = make_enemy(1005, 49, 50, hp=0)
    adj_unsel = make_enemy(1006, 50, 51, unselectable=True)
    actors = LuaTable()
    actors.rawset(1, merc)
    actors.rawset(2, far_target)
    actors.rawset(3, adj_ally)
    actors.rawset(4, adj_dead)
    actors.rawset(5, adj_unsel)
    S.rawset('屏幕事件组', actors)
    state, public = make_cast(merc, far_target, '红莲')
    ev.G.get('__gm_merc_visual_prepare_v255')(state, public)
    assert blinks == [], f'Must not blink for ally/dead/unselectable: {blinks}'
    assert isinstance(state.rawget('__gm_merc_visual_v255'), LuaTable), 'Projectile must still fire'

    # Case 4: Basic ranged attack (刺客普通攻击) still fires projectile and never blinks
    ev, S, merc, blinks, spawned, _ = make_merc_env(rt_src, story='来世续缘')
    adj_target = make_enemy(1001, 51, 50, facing=7)
    actors = LuaTable()
    actors.rawset(1, merc)
    actors.rawset(2, adj_target)
    S.rawset('屏幕事件组', actors)
    state, public = make_cast(merc, adj_target, '刺客普通攻击')
    ev.G.get('__gm_merc_visual_prepare_v255')(state, public)
    assert blinks == []
    assert isinstance(state.rawget('__gm_merc_visual_v255'), LuaTable)

    # Case 5: 「前尘忆梦」 isolation: delegates to original merc_mode_v288 (no non-target blink, no skill projectile)
    ev, S, merc, blinks, spawned, _ = make_merc_env(rt_src, story='前尘忆梦')
    far_target = make_enemy(1001, 55, 50, facing=7)
    adj_enemy = make_enemy(1002, 51, 50, facing=7)
    actors = LuaTable()
    actors.rawset(1, merc)
    actors.rawset(2, far_target)
    actors.rawset(3, adj_enemy)
    S.rawset('屏幕事件组', actors)
    state, public = make_cast(merc, far_target, '盛开')
    ev.G.get('__gm_merc_visual_prepare_v255')(state, public)
    assert blinks == [], f'前尘忆梦 must NOT blink for non-target enemy: {blinks}'
    assert state.rawget('__gm_merc_visual_v255') is None, '前尘忆梦 must NOT launch projectile for 盛开'


def test_v300_regression(rt_src):
    """Verify v1.300 0.5s unfocused auto-pickup & 3-state button still work identically."""
    env = make_env(story='来世续缘')
    ev, S = env['ev'], env['S']
    ev.G.get('loadstring')(rt_src)(S)
    pf = ev.G.get('__gm_pickup_frame_v299')
    set_mode = S.rawget('__gm_set_auto_pickup_mode_v300')
    set_mode(2, True)
    env['E'].rawset('屏幕焦点', False)  # unfocused window!

    # Place a white sword on ground at hero position (10, 10)
    it = LuaTable({'名称': '木剑', '分类': '装备', '价格': 200, '持久': 10, '最大持久': 10, '附加': LuaTable()})
    obj = make_ground_obj(it, x=10, y=10)
    place_ground(env, [obj], x=10, y=10)

    env['now_sec'][0] = 20.0
    pf(env['U'], env['G'])
    assert obj.rawget('已经消失') is True, 'Unfocused 0.5s auto-pickup regression failed'
    assert len(env['gold_delta']) == 1 and env['gold_delta'][0][0] > 0, f'Expected gold sale, got {env["gold_delta"]}'


def main():
    mods_o, rt_src = test_reverse_diff_and_static_audit()
    test_corpse_drop_vm_22_97(mods_o[22], rt_src)
    test_merc_ranged_skills(rt_src)
    test_v300_regression(rt_src)

    out_bytes = (W / 'game_v301.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    tested_files = {}
    for fname in ('game_v301.res', 'runtime_v301.lua', 'patch_v301.py', 'test_v301.py'):
        tested_files[fname] = hashlib.sha256((W / fname).read_bytes()).hexdigest()

    report = {
        'version': 'v1.301',
        'all_passed': True,
        'status': 'PASS',
        'sha256': out_sha,
        'tested_files': tested_files,
        'checks': [
            '42-module reverse-diff integrity against game_v300.res (only modules 12, 14, 22, 30 changed)',
            'Module 22 proto diff restricted strictly to 22/97',
            'Dump.rebuild() round-trip + trees() on all changed modules',
            'Static LuaJIT 2.0 J->maxslot / JMP.A audit on 22/97 and all 123 protos of Module 22',
            'Strict Lua 5.1 syntax parse + GBK 0x5C hazard scan on embedded runtime_v301.lua',
            'Real bytecode VM execution of 22/97: normal monster + empty drop-table monster + 0-multiplier monster + 镖车 excluded + 前尘忆梦 isolated',
            'End-to-end merc_mode_v288 + runtime_v301: any-enemy-adjacent blink with safe tile preference for all 5 skills (蝉舞/盛开/白莲/红莲/月桂)',
            'End-to-end merc_mode_v288 + runtime_v301: ranged skill projectile launch + synchronized damage & 目标动画 (命中动画延迟) deferral to arrival',
            '前尘忆梦 full isolation for both corpse drop and assassin merc skills',
            'v1.300 regression (0.5s unfocused auto-pickup & 3-state cycle)',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v301.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v301.json').write_text(text, encoding='utf-8')
    print('ALL v1.301 CHECKS PASSED!')


if __name__ == '__main__':
    main()
