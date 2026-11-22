"""Exhaustive verification suite for v1.302:
Specifically enforces real Windows client environment split:
- Gly独, 文本加解密, 取两点间方向 live ONLY in S.script_setting (NOT in _G!)
- Raw actor in 22/97 has NO actor.附加; 附加.挖取 lives ONLY on S.script_setting.Gly独.事件对象(tonumber(actor.id))!
- Verifies 22/97 VM death drops for 鸡/牛 (empty 掉宝数据表), 赤龙魔王 (normal + 挖取), 0-multiplier, 镖车, 前尘忆梦
- Verifies ranged assassin merc blink + projectile + hit animation under real S.script_setting split
"""
import hashlib
import json
import math
from pathlib import Path

from ljtool import Dump
from lua51_eval import LuaTable, syntax_check
from native_test_utils import trees
from resource_tools import decode
from test_v300 import make_env, make_ground_obj, place_ground
from test_v301 import V301VM, make_cast, make_enemy

W = Path(__file__).resolve().parent
BASE_SHA = 'b7335dc65f4c32582fe8bfe1e78eaad162aea39fac2df0e954dca71fa76d4534'


def extract_runtime_v302(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.302 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v302.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_reverse_diff_and_syntax():
    base_bytes = (W / 'game_v301.res').read_bytes()
    out_bytes = (W / 'game_v302.res').read_bytes()
    assert hashlib.sha256(base_bytes).hexdigest() == BASE_SHA

    outer_b, mods_b = decode(base_bytes, (12, 14, 22, 30))
    outer_o, mods_o = decode(out_bytes, (12, 14, 22, 30))

    root_b, root_o = outer_b.protos[0], outer_o.protos[0]
    changed_slots = [i for i in range(root_b.nkgc) if root_b.gc(i) != root_o.gc(i)]
    assert changed_slots == [12, 14, 30], f'Expected only [12, 14, 30] changed, got {changed_slots}'
    for mid in (12, 14, 30):
        ro = mods_o[mid].rebuild()
        assert Dump(ro).rebuild() == ro
        trees(mods_o[mid])

    rt_src = extract_runtime_v302(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_corpse_drop_real_env_split(m22, rt_src):
    """Test 22/97 VM where raw actor has NO 附加 and Gly独/文本加解密 exist ONLY in S.script_setting."""
    p97 = m22.protos[97]

    def run_death(story, monster_name, drop_table, drop_mult, dig_items):
        env = make_env(story=story)
        ev, S = env['ev'], env['S']
        # STRICT REAL-CLIENT SPLIT: remove Gly独 and 文本加解密 from _G; put them ONLY in S.script_setting!
        ev.G.rawset('Gly独', None)
        ev.G.rawset('文本加解密', None)
        ss = S.rawget('script_setting')

        item_store = {}

        def mock_decrypt(raw, key):
            assert key == 'mir3zuobigou'
            return raw[4:] if raw.startswith('ENC:') else raw

        def mock_loadstring(plain):
            return item_store[plain]

        ss.rawset('文本加解密', mock_decrypt)
        ss_tbl = LuaTable()
        ss_tbl.rawset('loadstring', mock_loadstring)
        ss.rawset('table', ss_tbl)

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

        # Public event object (where 12/14572 writes 对象.附加.挖取!)
        pub_obj = LuaTable()
        pub_prop = LuaTable()
        pub_prop.rawset('名称', monster_name)
        pub_extra = LuaTable()
        pub_extra.rawset('挖取', dig_tbl)
        pub_obj.rawset('属性', pub_prop)
        pub_obj.rawset('附加', pub_extra)

        ss_gly = LuaTable()
        ss_gly.rawset('事件对象', lambda aid: pub_obj if aid == 9001 else None)
        ss.rawset('Gly独', ss_gly)

        ev.G.get('loadstring')(rt_src)(S)

        # Raw engine actor passed to 22/97: has id, 属性, 地图格子, 宠物配置 — NO 附加!!
        raw_actor_lua = LuaTable()
        raw_actor_lua.rawset('id', '9001')  # string or number -> tonumber() handles both!
        raw_prop_lua = LuaTable()
        raw_prop_lua.rawset('名称', monster_name)
        raw_actor_lua.rawset('属性', raw_prop_lua)
        assert raw_actor_lua.rawget('附加') is None

        dropped = []

        def copy_obj(o):
            if isinstance(o, dict):
                return dict(o)
            if isinstance(o, LuaTable):
                return {k: copy_obj(v) for k, v in o._data.items()}
            return o

        def sys_run(name, *args):
            if name == '数据保护':
                return args[0]
            if name == '掉落物前置处理':
                return (False, args[3], args[2])
            if name == '掉落物品':
                dropped.append({'item': args[1], 'count': args[2]})
                return None
            return None

        has_fn = ev.G.get('__gm_corpse_has_v301')
        drop_fn = ev.G.get('__gm_corpse_drop_v301')

        def vm_has(actor):
            return bool(has_fn(raw_actor_lua))

        def vm_drop(actor, drops):
            drops_lua = LuaTable()
            for i in range(1, len(drops) + 1):
                if i in drops:
                    drops_lua.rawset(i, drops[i])
            added = drop_fn(raw_actor_lua, drops_lua)
            n = drops_lua.length()
            for i in range(len(drops) + 1, n + 1):
                entry = drops_lua.rawget(i)
                drops[i] = {
                    '物品道具': copy_obj(entry.rawget('物品道具')),
                    '掉落数量': entry.rawget('掉落数量'),
                }
            return added

        dt_dict = {i: e for i, e in enumerate(drop_table, 1)}
        actor_vm = {
            'id': '9001',
            '宠物配置': {'掉落物品': True},
            '属性': {'名称': monster_name, '掉宝数据表': dt_dict, '掉宝倍数': drop_mult},
            '地图格子': {'x': 100, 'y': 100},
        }

        def get_item_info(name):
            return {'名称': name, '分类': '道具', '叠加': 0, '附加': {}, '属性': {}}

        vm_globals = {
            '引擎': {'置随机数种子': lambda *a: None, '取随机整数': lambda s, a, b: int(a)},
            'Gly独': {'取随机数': lambda a, b: a, '取道具信息_名称': get_item_info},
            'Ux雌': {'版本选择': story},
            'Q_地图': {'取格子信息': lambda x, y, k: 0},
            'Sys': {'run': sys_run, 'get': lambda k, n: get_item_info(n) if k == 'item' else None},
            'table': {'insert': lambda t, v: t.__setitem__(len(t) + 1, v), 'copy': copy_obj, 'sort': lambda *a: None},
            'math': {'floor': math.floor, 'ceil': math.ceil, 'abs': abs},
            'tonumber': lambda x: int(x),
            'lookupHelixNumber': lambda dx, dy: dx * dx + dy * dy,
            '__gm_corpse_has_v301': vm_has,
            '__gm_corpse_drop_v301': vm_drop,
        }
        vm = V301VM(vm_globals, child_handlers={36: lambda drops: None, 27: lambda a, b: a[1] < b[1]})
        vm.run_proto(p97, actor_vm)
        return dropped, pub_extra.rawget('挖取').length()

    # 1. 鸡 (empty drop table, 掉宝倍数=1) -> drops 鸡肉!
    d1, r1 = run_death('来世续缘', '鸡', [], 1, [{'名称': '鸡肉', '分类': '道具'}])
    assert [d['item']['名称'] for d in d1] == ['鸡肉'] and r1 == 0

    # 2. 牛 (empty drop table, 掉宝倍数=0) -> drops 牛肉!
    d2, r2 = run_death('来世续缘', '牛', [], 0, [{'名称': '牛肉', '分类': '道具'}])
    assert [d['item']['名称'] for d in d2] == ['牛肉'] and r2 == 0

    # 3. 赤龙魔王 (normal drop + 挖取) -> drops both and clears 挖取!
    normal_dt = [{'最小几率': 1, '道具标识': '金创药(大)', '掉落数量': 1}]
    d3, r3 = run_death('来世续缘', '赤龙魔王', normal_dt, 1, [{'名称': '四级蝉舞', '分类': '技能书', '强化书': 4}])
    names3 = [d['item']['名称'] for d in d3]
    assert '金创药(大)' in names3 and '四级蝉舞' in names3 and r3 == 0

    # 4. 镖车 excluded
    d4, r4 = run_death('来世续缘', '镖车', [], 0, [{'名称': '镖银', '分类': '道具'}])
    assert d4 == [] and r4 == 1

    # 5. 「前尘忆梦」 untouched
    d5, r5 = run_death('前尘忆梦', '鸡', [], 1, [{'名称': '鸡肉', '分类': '道具'}])
    assert d5 == [] and r5 == 1


def test_merc_ranged_real_env_split(rt_src):
    """Test merc_ranged_v301 when 取两点间方向 lives ONLY in S.script_setting (NOT _G)."""
    env = make_env(story='来世续缘')
    ev, S = env['ev'], env['S']
    ss = S.rawget('script_setting')

    def dir_fn(x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy < 0: return 1
        if dx > 0 and dy < 0: return 2
        if dx > 0 and dy == 0: return 3
        if dx > 0 and dy > 0: return 4
        if dx == 0 and dy > 0: return 5
        if dx < 0 and dy > 0: return 6
        if dx < 0 and dy == 0: return 7
        return 8

    # Put 取两点间方向 ONLY in S.script_setting (real client layout!)
    ss.rawset('取两点间方向', dir_fn)
    ev.G.rawset('取两点间方向', None)
    ev.G.rawset('dt', 0.05)

    qmap = LuaTable()
    qmap.rawset('取格子信息', lambda x, y, k: 0)
    ev.G.rawset('Q_地图', qmap)

    fireball = LuaTable()
    fireball.rawset('子弹速度', 600)
    sys_tbl = LuaTable()
    sys_tbl.rawset('get', lambda kind, key: fireball if kind == 'skill' and '火球术' in str(key) else None)
    sys_tbl.rawset('add', lambda kind, obj: None)
    ev.G.rawset('Sys', sys_tbl)

    spawned = []
    def proj_factory(x, y, tx, ty, speed, actor, target, mode, image, *rest):
        spawned.append((x, y, tx, ty))
        b = LuaTable()
        b.rawset('更新', lambda: None)
        b.rawset('已经消失', lambda: False)
        b.rawset('销毁', lambda: None)
        return b
    ev.G.rawset('__gm_merc_visual_factory_v255', proj_factory)

    w_attr = LuaTable({'绑定技能': '刺客普通攻击'})
    w_item = LuaTable({'名称': '飞镖(远程)', '分类': '装备', '子类': '武器', '地面图标': 'icon.img', '附加': w_attr})
    S.rawget('包裹物品组').rawset(397, LuaTable({'道具': w_item}))

    blinks = []
    m_grid = LuaTable({'x': 50, 'y': 50})
    m_px = LuaTable({'x': 50 * 48, 'y': 50 * 32})
    merc = LuaTable({
        'id': 501, '绑定技能': '刺客普通攻击', '方向': 3,
        '地图格子': m_grid, '地图坐标': m_px,
        '属性': LuaTable({'hp': 1000, '中心Y偏移': 20, '模型大小': 1}),
    })
    def do_blink(bx, by):
        blinks.append((bx, by))
        m_grid.rawset('x', bx); m_grid.rawset('y', by)
        m_px.rawset('x', bx * 48); m_px.rawset('y', by * 32)
    merc.rawset('瞬移', do_blink)
    env['U'].rawset('佣兵对象', merc)

    merc_src = (W / 'merc_mode_v288.lua').read_text(encoding='utf-8')
    ev.G.get('loadstring')(merc_src)()(S, ss)
    ev.G.get('loadstring')(rt_src)(S)

    far_target = make_enemy(1001, 55, 50, facing=7)
    adj_enemy = make_enemy(1002, 51, 50, facing=7)
    S.rawset('屏幕事件组', LuaTable({1: merc, 2: far_target, 3: adj_enemy}))

    state, public = make_cast(merc, far_target, '盛开', hit_delay=0.15, dmg_delays=(0.30,))
    ev.G.get('__gm_merc_visual_prepare_v255')(state, public)
    assert len(blinks) == 1, f'Expected blink using S.script_setting.取两点间方向, got {blinks}'
    assert state.rawget('命中动画延迟') == math.inf
    assert state.rawget('伤害进度').rawget(1) == math.inf
    ev.G.get('__gm_merc_visual_step_v255')(state)
    assert len(spawned) == 1 and spawned[0][0] == blinks[0][0] * 48


def main():
    mods_o, rt_src = test_reverse_diff_and_syntax()
    test_corpse_drop_real_env_split(mods_o[22], rt_src)
    test_merc_ranged_real_env_split(rt_src)

    out_sha = hashlib.sha256((W / 'game_v302.res').read_bytes()).hexdigest()
    tested_files = {
        fname: hashlib.sha256((W / fname).read_bytes()).hexdigest()
        for fname in ('game_v302.res', 'runtime_v302.lua', 'patch_v302.py', 'test_v302.py')
    }
    report = {
        'version': 'v1.302',
        'all_passed': True,
        'status': 'PASS',
        'sha256': out_sha,
        'tested_files': tested_files,
        'checks': [
            'Outer resource diff restricted strictly to modules [12, 14, 30] + rebuild + trees()',
            'Strict Lua 5.1 syntax parse + GBK 0x5C scan on embedded runtime_v302.lua',
            'Real client env split test (Gly独/文本加解密/table.loadstring ONLY in S.script_setting, raw actor has NO 附加): 鸡/牛/赤龙魔王/镖车/前尘忆梦 all verified via 22/97 VM',
            'Real client env split test (取两点间方向 ONLY in S.script_setting): ranged assassin merc blink + projectile + delayed damage & 目标动画 verified',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v302.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v302.json').write_text(text, encoding='utf-8')
    print('ALL v1.302 CHECKS PASSED!')


if __name__ == '__main__':
    main()
