"""Exhaustive verification suite for v1.303:
- Strict 内存保护(nil) crash guard in 22/97 VM: 猪肉/鸡肉 with 属性=nil / 附加=nil must drop cleanly without nil error!
- Ranged assassin mercenary blink:
  * Triggered by ANY adjacent enemy monster (even when locked target is far away!)
  * Destination is behind the CURRENTLY LOCKED ATTACK TARGET (target.地图格子) at ring distance 2~4,
    preferring walkable tiles not adjacent to any enemy, facing target!
  * Still launches spinning weapon projectile and defers both damage & 目标动画 to projectile arrival
  * Automatically re-wraps if 14/420 (merc_mode_v288) re-runs on save reload
- Assassin mercenary skill cooldown status in 12/18045 & 12/18047 verified exact 3s (KSHORT 3, 3)
- 「前尘忆梦」 100% untouched
"""
import hashlib
import json
import math
from pathlib import Path

from ljtool import Dump
from lua51_eval import LuaTable, syntax_check
from native_test_utils import trees
from patch_v139 import ad
from resource_tools import decode
from test_v300 import make_env
from test_v301 import V301VM, make_cast, make_enemy

W = Path(__file__).resolve().parent
BASE_SHA = '00c2acb1c566a1bf6776189156156f01c3ebc76515442c125fa685e85b604430'


def extract_runtime_v303(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.303 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v303.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_syntax_and_cd():
    base_bytes = (W / 'game_v302.res').read_bytes()
    out_bytes = (W / 'game_v303.res').read_bytes()
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

    # Verify exact 3-second cooldown in 12/18045 and 12/18047
    p45 = mods_o[12].protos[18045]
    p47 = mods_o[12].protos[18047]
    assert p45.bc[117] == ad('KSHORT', 17, 3) and p45.bc[118] == ad('KSHORT', 18, 3)
    assert p47.bc[103] == ad('KSHORT', 12, 3) and p47.bc[104] == ad('KSHORT', 13, 3)

    rt_src = extract_runtime_v303(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_corpse_drop_strict_protect(m22, rt_src):
    """Enforce real 14/502 数据保护 behavior: passing nil MUST raise 内存保护() 参数为nil!"""
    p97 = m22.protos[97]

    def run_death(story, monster_name, dig_items):
        env = make_env(story=story)
        ev, S = env['ev'], env['S']
        ev.G.rawset('Gly独', None)
        ev.G.rawset('文本加解密', None)
        ss = S.rawget('script_setting')

        item_store = {}
        ss.rawset('文本加解密', lambda raw, key: raw[4:] if raw.startswith('ENC:') else raw)
        ss_tbl = LuaTable()
        ss_tbl.rawset('loadstring', lambda plain: item_store[plain])
        ss.rawset('table', ss_tbl)

        # Mock Sys.get('item', name) returning template with scalar fields
        def mock_sys_get(kind, name):
            if kind == 'item':
                return LuaTable({'名称': name, '分类': '道具', '地面图标': f'{name}.img', '叠加': 0})
            return None
        ev.G.rawset('Sys', LuaTable({'get': mock_sys_get}))

        dig_tbl = LuaTable()
        for idx, it in enumerate(dig_items, 1):
            token = f'ITEM_{idx}'
            # Intentionally omit 属性 and/or 附加 to reproduce real pig/chicken meat items!
            t = LuaTable(it)
            item_store[token] = t
            dig_tbl.rawset(idx, 'ENC:' + token)

        pub_obj = LuaTable({
            '属性': LuaTable({'名称': monster_name}),
            '附加': LuaTable({'挖取': dig_tbl}),
        })
        ss.rawset('Gly独', LuaTable({'事件对象': lambda aid: pub_obj if aid == 9001 else None}))

        ev.G.get('loadstring')(rt_src)(S)

        raw_actor_lua = LuaTable({'id': 9001, '属性': LuaTable({'名称': monster_name})})
        dropped = []

        def copy_obj(o):
            if isinstance(o, dict):
                return {k: copy_obj(v) for k, v in o.items()}
            if isinstance(o, LuaTable):
                return {k: copy_obj(v) for k, v in o._data.items()}
            return o

        def sys_run(name, *args):
            if name == '数据保护':
                # STRICT REAL ENGINE ASSERTION (14/502 pc 0..7):
                if args[0] is None:
                    raise RuntimeError('内存保护() 参数为nil,请检查！')
                return args[0]
            if name == '掉落物前置处理':
                return (False, args[3], args[2])
            if name == '掉落物品':
                dropped.append({'item': args[1], 'count': args[2]})
                return None
            return None

        has_fn = ev.G.get('__gm_corpse_has_v301')
        drop_fn = ev.G.get('__gm_corpse_drop_v301')

        def vm_drop(actor, drops):
            drops_lua = LuaTable()
            for i in range(1, len(drops) + 1):
                if i in drops:
                    drops_lua.rawset(i, drops[i])
            added = drop_fn(raw_actor_lua, drops_lua)
            for i in range(len(drops) + 1, drops_lua.length() + 1):
                entry = drops_lua.rawget(i)
                drops[i] = {
                    '物品道具': copy_obj(entry.rawget('物品道具')),
                    '掉落数量': entry.rawget('掉落数量'),
                }
            return added

        actor_vm = {
            'id': 9001,
            '宠物配置': {'掉落物品': True},
            '属性': {'名称': monster_name, '掉宝数据表': {}, '掉宝倍数': 1},
            '地图格子': {'x': 100, 'y': 100},
        }
        vm_globals = {
            '引擎': {'置随机数种子': lambda *a: None, '取随机整数': lambda s, a, b: int(a)},
            'Gly独': {'取随机数': lambda a, b: a},
            'Ux雌': {'版本选择': story},
            'Q_地图': {'取格子信息': lambda x, y, k: 0},
            'Sys': {'run': sys_run},
            'table': {'insert': lambda t, v: t.__setitem__(len(t) + 1, v), 'copy': copy_obj, 'sort': lambda *a: None},
            'math': {'floor': math.floor, 'ceil': math.ceil, 'abs': abs},
            'tonumber': lambda x: int(x),
            'lookupHelixNumber': lambda dx, dy: dx * dx + dy * dy,
            '__gm_corpse_has_v301': lambda a: bool(has_fn(raw_actor_lua)),
            '__gm_corpse_drop_v301': vm_drop,
        }
        vm = V301VM(vm_globals, child_handlers={36: lambda drops: None, 27: lambda a, b: a[1] < b[1]})
        vm.run_proto(p97, actor_vm)
        return dropped, pub_obj.rawget('附加').rawget('挖取').length()

    # Pig meat with 属性=nil (exact crash trigger in v1.302!)
    d_pig, rem = run_death('来世续缘', '猪', [{'名称': '猪肉', '分类': '道具', '价格': 120, '附加': LuaTable({'品质': 7})}])
    assert len(d_pig) == 1 and d_pig[0]['item']['名称'] == '猪肉'
    assert d_pig[0]['item']['附加']['品质'] == 7
    assert d_pig[0]['item']['地面图标'] == '猪肉.img'
    assert isinstance(d_pig[0]['item']['属性'], dict)
    assert rem == 0

    # Chicken meat with BOTH 属性=nil and 附加=nil
    d_chk, rem2 = run_death('来世续缘', '鸡', [{'名称': '鸡肉', '分类': '道具', '价格': 80}])
    assert len(d_chk) == 1 and d_chk[0]['item']['名称'] == '鸡肉'
    assert isinstance(d_chk[0]['item']['附加'], dict) and isinstance(d_chk[0]['item']['属性'], dict)
    assert rem2 == 0

    # 「前尘忆梦」 untouched
    d_old, rem3 = run_death('前尘忆梦', '猪', [{'名称': '猪肉', '分类': '道具'}])
    assert d_old == [] and rem3 == 1


def test_merc_blink_behind_locked_target_and_rewrap(rt_src):
    """Verify:
    1. When non-target monster E2 is adjacent to merc (50,50), casting any of the 5 skills
       blinks behind LOCKED TARGET (55,50) at ring distance (2/2/3/3/4) around (55,50)!
    2. Re-running merc_mode_v288 (simulating save reload / 14/421) is automatically re-wrapped on pickup_frame!
    """
    expected_dist = {'蝉舞': 4, '盛开': 2, '白莲': 2, '红莲': 3, '月桂': 3}
    merc_src = (W / 'merc_mode_v288.lua').read_text(encoding='utf-8')

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

    for skill, dist in expected_dist.items():
        env = make_env(story='来世续缘')
        ev, S = env['ev'], env['S']
        ss = S.rawget('script_setting')
        ss.rawset('取两点间方向', dir_fn)
        ev.G.rawset('取两点间方向', None)
        ev.G.rawset('dt', 0.05)
        ev.G.rawset('Q_地图', LuaTable({'取格子信息': lambda x, y, k: 0}))

        fireball = LuaTable({'子弹速度': 600})
        ev.G.rawset('Sys', LuaTable({
            'get': lambda kind, key: fireball if kind == 'skill' and '火球术' in str(key) else None,
            'add': lambda kind, obj: None,
        }))
        spawned = []
        def proj_factory(x, y, tx, ty, speed, actor, target, mode, image, *rest):
            spawned.append((x, y, tx, ty))
            return LuaTable({'更新': lambda: None, '已经消失': lambda: False, '销毁': lambda: None})
        ev.G.rawset('__gm_merc_visual_factory_v255', proj_factory)

        w_item = LuaTable({'名称': '飞镖(远程)', '分类': '装备', '子类': '武器', '地面图标': 'icon.img',
                           '附加': LuaTable({'绑定技能': '刺客普通攻击'})})
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

        # Simulate real startup order: runtime_v303 runs FIRST (14/781), THEN merc_mode_v288 runs (14/421),
        # THEN pickup_frame runs (14/428), THEN merc_mode_v288 runs AGAIN (reload!), THEN pickup_frame runs!
        ev.G.get('loadstring')(rt_src)(S)
        ev.G.get('loadstring')(merc_src)()(S, ss)
        ev.G.get('__gm_pickup_frame_v299')(env['U'], env['G'])
        # Simulate save reload overwriting __gm_merc_visual_prepare_v255:
        ev.G.get('loadstring')(merc_src)()(S, ss)
        ev.G.get('__gm_pickup_frame_v299')(env['U'], env['G'])

        # Locked target at (55, 50) facing west (7 -> behind is east: x = 55 + dist, y = 50)
        # Adjacent OTHER monster E2 at (49, 50) (1 tile west of merc at (50, 50))!
        locked_target = make_enemy(1001, 55, 50, facing=7)
        adj_other = make_enemy(1002, 49, 50, facing=3)
        S.rawset('屏幕事件组', LuaTable({1: merc, 2: locked_target, 3: adj_other}))

        state, public = make_cast(merc, locked_target, skill, hit_delay=0.15, dmg_delays=(0.30,))
        ev.G.get('__gm_merc_visual_prepare_v255')(state, public)

        # MUST blink behind LOCKED TARGET (55, 50) at exact ring distance `dist`!
        assert len(blinks) == 1, f'{skill}: expected blink when other monster adjacent, got {blinks}'
        bx, by = blinks[0]
        assert (bx, by) == (55 + dist, 50), f'{skill}: expected behind locked target ({55+dist},50), got ({bx},{by})'
        assert merc.rawget('方向') == 7, f'{skill}: expected merc facing west toward locked target'

        # MUST launch projectile from post-blink pos & defer BOTH damage and hit anim!
        assert state.rawget('命中动画延迟') == math.inf
        assert state.rawget('伤害进度').rawget(1) == math.inf
        ev.G.get('__gm_merc_visual_step_v255')(state)
        assert len(spawned) == 1 and spawned[0][0] == bx * 48 and spawned[0][2] == 55 * 48


def main():
    mods_o, rt_src = test_diff_syntax_and_cd()
    test_corpse_drop_strict_protect(mods_o[22], rt_src)
    test_merc_blink_behind_locked_target_and_rewrap(rt_src)

    out_sha = hashlib.sha256((W / 'game_v303.res').read_bytes()).hexdigest()
    tested_files = {
        fname: hashlib.sha256((W / fname).read_bytes()).hexdigest()
        for fname in ('game_v303.res', 'runtime_v303.lua', 'patch_v303.py', 'test_v303.py')
    }
    report = {
        'version': 'v1.303',
        'all_passed': True,
        'status': 'PASS',
        'sha256': out_sha,
        'tested_files': tested_files,
        'checks': [
            'Outer resource diff restricted strictly to modules [12, 14, 30] + rebuild + trees()',
            '12/18045 (pc 117..118) & 12/18047 (pc 103..104) verified exact 3s assassin skill cooldown',
            'Strict Lua 5.1 syntax parse + GBK 0x5C scan on embedded runtime_v303.lua',
            'Strict 14/502 内存保护(nil) crash guard in 22/97 VM: 猪肉 (属性=nil) & 鸡肉 (附加=nil, 属性=nil) drop cleanly; 前尘忆梦 isolated',
            'Real init/reload order (14/781 -> 14/420 -> pickup_frame -> 14/420 reload -> pickup_frame) verified auto-rewrap',
            'Ranged assassin merc: any adjacent enemy triggers blink behind LOCKED TARGET (target.地图格子) at ring distance 2~4 + projectile + synchronized damage & 目标动画',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v303.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v303.json').write_text(text, encoding='utf-8')
    print('ALL v1.303 CHECKS PASSED!')


if __name__ == '__main__':
    main()
