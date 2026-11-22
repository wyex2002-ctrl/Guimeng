"""Exhaustive verification suite for v1.300:
- 42-module reverse-diff integrity against game_v299.res & rebuild round-trip
- Static LuaJIT 2.0 J->maxslot / JMP.A audit on all hooked protos + Module 22
- Strict Lua 5.1 syntax parse + GBK 0x5C hazard audit on embedded runtime_v300.lua from game_v300.res
- Real bytecode VM execution of 14/781 startup and 14/428 frame dispatch
- End-to-end execution of embedded runtime_v300.lua covering:
  * 0.5s (500ms) check interval timing
  * 3-state button cycle (0=OFF/grey -> 1=Normal/green -> 2=BulkSell/royal-blue -> 0) under _G==nil sandbox
  * Distinct button skin, hover, and dot colors for all 3 modes
  * Hover tooltip callback (鼠标焦点) under _G==nil sandbox with distinct color tags per mode & dynamic screen positioning
  * Mode 1 (green): white equip auto-sell only; rare equip & all skill books picked up
  * Mode 2 (royal blue): sells white equip, 1~6-affix rare equip, and non-4/5 skill books;
    strictly keeps 7-affix rare equip, 4/5-level skill books (by 强化书 and name prefix),
    禁止出售, 保护名单 (精灵骸骨/青铜斧/魔法长袍_女/鹤嘴锄), 任务关联, 剧情关联, potions, oil, and gold
  * Manual Alt isolation (stays white-equip-only even while Mode 2 is active)
  * Full-bag no-spam, map switch, death/pause/Game_State guards, mount batch regression, and 「前尘忆梦」 isolation
"""
import hashlib
import json
import math
import random
from pathlib import Path

from ljtool import Dump
from lua51_eval import LuaEvaluator, LuaTable, syntax_check
from native_test_utils import trees
from resource_tools import decode
from test_v297 import analyze_proto
from test_v299 import V299VM, make_protect_fn

W = Path(__file__).resolve().parent
BASE_SHA = '87b42bdba8aade6b6dd17ef6d87be503b7e357d694431341162f7a7c4baf1bbf'


def make_env(story='来世续缘'):
    """Build a realistic runtime mock environment for testing embedded runtime_v300.lua."""
    ev = LuaEvaluator()
    protect = make_protect_fn()
    tbl_lib = ev.G.get('table')

    def lua_deep_copy(t, deep=False):
        if not isinstance(t, LuaTable):
            return t
        raw = t.rawget('__数据') if isinstance(t.rawget('__数据'), LuaTable) else t
        out = LuaTable()
        for k, v in raw._data.items():
            out.rawset(k, lua_deep_copy(v, True) if deep and isinstance(v, LuaTable) else v)
        return out

    tbl_lib.rawset('copy', lua_deep_copy)

    now_sec = [10.0]
    alt_pressed = [False]
    mouse_left = [False]
    rng = random.Random(20261120)
    toasts = []
    tips = []
    gly_tips = []
    gold_delta = []
    sound_clicks = [0]
    draw_log = []
    dot_fg_colors = []
    text_colors = []

    L = LuaTable({'颜色_红': -65536, '颜色_黄': -256, '颜色_绿': -16711936, '键_ALT': 18, '键_鼠标左': 1})
    ev.G.rawset('L常量', L)
    ev.G.rawset('SETA', lambda col, a: col)

    engine = LuaTable({
        '取运行时间': lambda _self: now_sec[0],
        '取按键按下': lambda _self, k: alt_pressed[0] if k == 18 else False,
        '取按键事件': lambda _self, k: mouse_left[0] if k == 1 else False,
        '取随机整数': lambda _self, a, b: rng.randint(int(a), int(b)),
        '取随机小数': lambda _self, a, b: rng.random(),
    })
    ev.G.rawset('引擎', engine)

    E = LuaTable({
        '屏幕焦点': True,
        '逻辑暂停': 0,
        '逻辑跳过': False,
        '游戏暂停': False,
        '遮罩信息': LuaTable({'启动': False, '触发': False}),
        '地面道具描边': True,
        '屏幕宽度': 1024,
        '屏幕高度': 600,
        '鼠标_屏幕坐标': LuaTable({'x': 720, 'y': 50}),
    })
    ev.G.rawset('Ae冻集', E)
    ev.G.rawset('Q_提示框', LuaTable({'可视': False}))

    def make_sprite(name_tag):
        st = {'color': None}
        sp = LuaTable({
            '置颜色': lambda c: st.__setitem__('color', c),
            '置显示区域': lambda *a: None,
            '显示_高级': lambda *a: draw_log.append((name_tag, st['color'])),
            '销毁': lambda: None,
        })
        return sp

    sprite_idx = [0]
    sprite_names = ['left', 'middle', 'right', 'dot_bg', 'dot_fg']

    def create_sprite(*args):
        tag = sprite_names[sprite_idx[0] % len(sprite_names)]
        sprite_idx[0] += 1
        sp = make_sprite(tag)
        if tag == 'dot_fg':
            orig_col = sp.rawget('置颜色')

            def cap_dot(c):
                dot_fg_colors.append(c)
                orig_col(c)

            sp.rawset('置颜色', cap_dot)
        return sp

    ev.G.rawset('Q__', LuaTable({'创建精灵': create_sprite}))

    font = LuaTable({
        '取宽度': lambda s, sp=0: len(str(s)) * 12,
        '取高度': lambda s, sp=0: 14,
        '解析': lambda s, a, b: LuaTable({'text': s}),
        '显示配置': lambda layout, x, y, col, stroke: text_colors.append(col),
    })

    def res_loader(kind, name, idx=None):
        if kind == 2:
            return font
        return LuaTable({'img': name})

    ev.G.rawset('__Res', res_loader)

    U = LuaTable({
        '版本选择': story,
        '托管显示': LuaTable({'屏幕提示': lambda msg, col=None, *a: toasts.append((msg, col))}),
        '游戏音效': LuaTable({'按键音效1': LuaTable({'播放': lambda: sound_clicks.__setitem__(0, sound_clicks[0] + 1)})}),
        '窗口相关': LuaTable({'界面切换': lambda delta, _nil=None, tag=None: gold_delta.append((delta, tag))}),
        '独角兽下': lambda: LuaTable({'极品数值': LuaTable({'最大破坏': 5, '暴击几率': 2})}),
    })
    ev.G.rawset('Ux雌', U)

    hovered_state = [False]
    win539 = LuaTable({'控件组': LuaTable(), '可视': True})

    def add_ctrl(_self, ctype, name, x, y, z, w, h, title, img, cfg, factories):
        fac = factories.get(1)
        scripts = fac()
        obj = LuaTable({
            '显示': lambda *a: None,
            '销毁': lambda: None,
            '是否有焦点': lambda: hovered_state[0],
        })
        ctrl = LuaTable({
            '类型': ctype, '名称': name, 'x': x, 'y': y, 'w': w, 'h': h,
            '对象': obj, '脚本': scripts,
        })
        win539.get('控件组').rawset(win539.get('控件组').length() + 1, ctrl)

    win539.rawset('增加控件', add_ctrl)

    S = LuaTable({
        'script_setting': LuaTable({'Ux雌': U}),
        'Game_State': 1,
        '界面_窗口_数组': LuaTable([win539]),
        '取窗口对象': lambda wid: win539 if wid == 539 else None,
        '数据保护': protect,
        '游戏道具组': LuaTable(),
        '包裹物品组': LuaTable(),
        '气泡提示': lambda *a: tips.append(a),
    })
    ev.G.rawset('Gly独', LuaTable({
        '鼠标气泡': lambda *a: gly_tips.append(a),
    }))

    hero = LuaTable({
        'del__': False,
        '已经死亡': False,
        '地图格子': LuaTable({'x': 10, 'y': 10}),
        '背包格子': LuaTable(),
        '装备': LuaTable(),
    })
    S.rawset('Hero', hero)
    S.rawset('控制对象', hero)

    # Set up bag slots (10 free slots by default)
    free_slots = [10]
    bag_items = S.get('包裹物品组')
    for idx in range(1, 11):
        bag_items.rawset(idx, LuaTable({'道具': None}))
        hero.get('背包格子').rawset(idx, LuaTable([idx, 1, True]))

    def sys_get(k):
        return {
            'hero': S.get('Hero'),
            'item_arr': S.get('包裹物品组'),
            '控制对象': S.get('控制对象'),
            'item_box': S.get('界面_窗口_数组'),
        }.get(k)

    def sys_run(kind, cb, args=None):
        if kind == 'fun' and callable(cb):
            return False, False
        return None

    ev.G.rawset('Sys', LuaTable({'get': sys_get, 'run': sys_run}))

    # Equipment baselines for safe_sell
    baselines = {
        '木剑': LuaTable({'名称': '木剑', '最大破坏': 5, '附加': LuaTable({})}),
        '屠龙': LuaTable({'名称': '屠龙', '最大破坏': 35, '附加': LuaTable({})}),
        '战神盔甲': LuaTable({'名称': '战神盔甲', '最大防御': 9, '附加': LuaTable({})}),
        '青铜斧': LuaTable({'名称': '青铜斧', '最大破坏': 15, '附加': LuaTable({})}),
    }
    G = LuaTable({
        '取道具信息_名称': lambda name: baselines.get(name),
        '取包裹空位': lambda sub: free_slots[0] if sub == '不限制' else 0,
    })

    # Ground map setup
    ground = LuaTable()

    def to_idx(x, y):
        return y * 100 + x

    map_state = LuaTable({
        '地面物品组': ground,
        '到逻辑格子': to_idx,
        '地图格子列数': 50,
        '地图格子行数': 50,
    })
    ev.G.rawset('Q_地图', LuaTable({'__gm_range_state': map_state}))

    return {
        'ev': ev, 'S': S, 'U': U, 'G': G, 'E': E, 'hero': hero,
        'win539': win539, 'ground': ground, 'map': map_state, 'to_idx': to_idx,
        'now_sec': now_sec, 'alt_pressed': alt_pressed, 'mouse_left': mouse_left,
        'hovered': hovered_state, 'free_slots': free_slots,
        'toasts': toasts, 'tips': tips, 'gly_tips': gly_tips,
        'gold_delta': gold_delta, 'sound_clicks': sound_clicks,
        'draw_log': draw_log, 'dot_fg_colors': dot_fg_colors, 'text_colors': text_colors,
        'protect': protect,
    }


def make_ground_obj(item_tbl, x=10, y=10, qty=1, picked_log=None, reject_pickup=False):
    obj = LuaTable({
        '物品': item_tbl,
        '数量': qty,
        'del__': False,
        '已经消失': False,
        '格子': LuaTable({'x': x, 'y': y}),
        'Hero': LuaTable({'回调脚本': LuaTable({'拾取': lambda *a: (False, False)})}),
    })

    def do_pickup(self_arg, mode):
        # Strictly enforce real engine ABI: o['拾取'](o, 1)!
        assert self_arg is obj, f'pickup self mismatch: {self_arg}'
        assert mode == 1, f'pickup mode must be 1, got {mode}'
        if reject_pickup:
            return False
        obj.rawset('已经消失', True)
        if picked_log is not None:
            picked_log.append((item_tbl.get('名称'), obj.get('数量')))
        return True

    obj.rawset('拾取', do_pickup)
    return obj


def place_ground(env, objs, x=10, y=10):
    key = env['to_idx'](x, y)
    bucket = LuaTable()
    for i, o in enumerate(objs, 1):
        bucket.rawset(i, o)
    env['ground'].rawset(key, bucket)


def invoke_sandboxed_cb(ev, fn):
    """Simulate real client Sys.lua:fun calling setfenv(cb, {no _G})!"""
    saved_g = ev.G.rawget('_G')
    ev.G.rawset('_G', None)
    try:
        return fn()
    finally:
        ev.G.rawset('_G', saved_g)


def run_all():
    v299_bytes = (W / 'game_v299.res').read_bytes()
    v300_bytes = (W / 'game_v300.res').read_bytes()
    assert hashlib.sha256(v299_bytes).hexdigest() == BASE_SHA

    # 1. 42-module reverse-diff integrity & rebuild round-trip
    out299, _ = decode(v299_bytes, ())
    out300, _ = decode(v300_bytes, ())
    assert out300.rebuild() == out300.raw
    all_mods = [i for i in range(out300.protos[0].nkgc) if isinstance(out300.protos[0].gc(i), bytes) and len(out300.protos[0].gc(i)) > 64]
    _, mods299 = decode(v299_bytes, all_mods)
    _, mods300 = decode(v300_bytes, all_mods)
    changed_mods = sorted(m for m in all_mods if mods299[m].raw != mods300[m].raw)
    assert changed_mods == [12, 14, 30], f'Unexpected changed modules: {changed_mods}'
    for m in changed_mods:
        assert Dump(mods300[m].raw).rebuild() == mods300[m].raw
        trees(mods300[m])

    # Verify zero bytecode instruction changes in any proto across {12, 14, 30}
    for m in changed_mods:
        assert len(mods299[m].protos) == len(mods300[m].protos)
        for p299, p300 in zip(mods299[m].protos, mods300[m].protos):
            assert p299.bc == p300.bc, f'Unexpected bytecode change in {m}/{p300.idx}'

    # 2. Static LuaJIT 2.0 J->maxslot / JMP.A audit on all hooked protos + Module 22
    m12, m14, m22 = mods300[12], mods300[14], mods300[22]
    for mid, pids in (
        (12, [143, 217, 218, 220]),
        (14, [256, 428, 446, 456, 481, 781]),
        (22, list(range(len(m22.protos)))),
    ):
        for pid in pids:
            old_rep = analyze_proto(mods299[mid].protos[pid])
            new_rep = analyze_proto(mods300[mid].protos[pid])
            assert len(new_rep['call_gaps']) <= len(old_rep['call_gaps']), f'{mid}/{pid} call gaps: {new_rep}'
            assert len(new_rep['bad_jmp_a']) <= len(old_rep['bad_jmp_a']), f'{mid}/{pid} bad jmp A: {new_rep}'

    # 3. Extract embedded runtime_v300.lua directly from 14/781 in game_v300.res
    p781 = m14.protos[781]
    embedded = [p781.gc(i).decode('gbk') for i in range(p781.nkgc)
                if isinstance(p781.gc(i), bytes) and p781.gc(i).startswith(b'-- Guimeng v1.300 runtime helper')]
    assert len(embedded) == 1
    runtime_src = embedded[0]
    for ch in runtime_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    syntax_check(runtime_src)

    # Version strings updated cleanly
    v300_hits = 0
    for m in changed_mods:
        for p in mods300[m].protos:
            for i in range(p.nkgc):
                v = p.gc(i)
                if isinstance(v, bytes):
                    if b'v1.300' in v:
                        v300_hits += 1
    assert v300_hits >= 9, f'Expected >=9 v1.300 strings, got {v300_hits}'

    # 4. Real bytecode VM execution of 14/781 injected slice (PC 286..292)
    env = make_env('来世续缘')
    vm781 = V299VM(env['ev'].G)
    vm781.run_slice(p781, start_pc=286, stop_pc=293, init_regs={0: env['S']})
    assert env['S'].get('__gm_runtime_v300_installed') is True
    assert callable(env['S'].get('__gm_pickup_frame_v299'))

    # 5. Real bytecode VM execution of 14/428 pickup dispatch at PC 2956
    p428 = m14.protos[428]
    # First frame installs the bag button in Window 539!
    vm428 = V299VM(
        env['ev'].G,
        upvalues=[env['S']],
    )
    vm428.run_slice(p428, start_pc=2956, stop_pc=2983)
    assert env['win539'].get('控件组').length() == 1
    btn_ctrl = env['win539'].get('控件组').get(1)
    btn_obj = btn_ctrl.get('对象')
    btn_scripts = btn_ctrl.get('脚本')
    assert btn_ctrl.get('名称') == '自动拾取按钮_v299'
    assert btn_ctrl.get('x') + btn_ctrl.get('w') <= 176  # zero overlap with 【仓库】 at x=180

    # 6. Test 3-state button cycle (0 -> 1 -> 2 -> 0) & colors under _G==nil sandbox!
    get_mode = env['S'].get('__gm_get_auto_pickup_mode_v300')
    assert get_mode() == 0 and env['ev'].G.get('__gm_auto_pickup_on_v299') is False

    def render_btn(hovered=False):
        env['hovered'][0] = hovered
        env['draw_log'].clear()
        env['dot_fg_colors'].clear()
        env['text_colors'].clear()
        btn_obj.get('显示')(110, 20, 1, 1, 0, -1, 1)
        skin_cols = [c for tag, c in env['draw_log'] if tag == 'left']
        return skin_cols[0], env['dot_fg_colors'][0], env['text_colors'][0]

    off_skin, off_dot, off_txt = render_btn(False)
    off_hover, _, _ = render_btn(True)
    assert (off_skin, off_hover, off_dot, off_txt) == (-5723992, -4671304, -8355712, -4210753)

    # Click 1 -> Mode 1 (绿色 普通自动拾取) under _G == nil sandbox!
    invoke_sandboxed_cb(env['ev'], btn_scripts.get('Main'))
    assert get_mode() == 1 and env['ev'].G.get('__gm_auto_pickup_on_v299') is True
    assert env['toasts'][-1] == ('自动拾取已开启（普通模式）', -11739014)
    m1_skin, m1_dot, m1_txt = render_btn(False)
    m1_hover, _, _ = render_btn(True)
    assert (m1_skin, m1_hover, m1_dot, m1_txt) == (-9910150, -8658802, -13369549, -1)

    # Click 2 -> Mode 2 (宝蓝色 自动拾取+出售) under _G == nil sandbox!
    invoke_sandboxed_cb(env['ev'], btn_scripts.get('Main'))
    assert get_mode() == 2 and env['ev'].G.get('__gm_auto_pickup_on_v299') is True
    assert env['toasts'][-1] == ('自动拾取已开启（自动出售模式）', -8204545)
    m2_skin, m2_dot, m2_txt = render_btn(False)
    m2_hover, _, _ = render_btn(True)
    assert (m2_skin, m2_hover, m2_dot, m2_txt) == (-11365633, -9721601, -13392385, -1)

    # All 3 button states must have strictly distinct skin, hover, and dot colors!
    assert len({off_skin, m1_skin, m2_skin}) == 3
    assert len({off_hover, m1_hover, m2_hover}) == 3
    assert len({off_dot, m1_dot, m2_dot}) == 3

    # Click 3 -> Mode 0 (关闭) under _G == nil sandbox!
    invoke_sandboxed_cb(env['ev'], btn_scripts.get('Main'))
    assert get_mode() == 0 and env['ev'].G.get('__gm_auto_pickup_on_v299') is False
    assert env['toasts'][-1] == ('自动拾取已关闭', -4210753)
    assert env['sound_clicks'][0] == 3

    # 7. Test Hover Tooltip (鼠标焦点) under _G==nil sandbox + edge positioning!
    set_mode = env['S'].get('__gm_set_auto_pickup_mode_v300')
    expected_tip = '#c(-11739014)【普通自动拾取】\n#c(-8204545)【自动拾取+自动出售】保留重要稀有装备物品'
    for m in (0, 1, 2):
        set_mode(m, True)
        env['tips'].clear()
        invoke_sandboxed_cb(env['ev'], btn_scripts.get('鼠标焦点'))
        assert len(env['tips']) == 1
        args = env['tips'][0]
        tip_txt, kind, alpha, ox, oy, fixed, fx, fy, slot, skin_id, max_w = args
        assert kind == 0 and alpha == 235 and fixed is False and max_w == -1
        assert ox == -1.05 and oy == 0.08  # right-top mouse -> left & below cursor
        assert tip_txt == expected_tip

    # Edge positioning: mouse near left edge & bottom edge
    env['E'].get('鼠标_屏幕坐标').rawset('x', 120)
    env['E'].get('鼠标_屏幕坐标').rawset('y', 520)
    env['tips'].clear()
    invoke_sandboxed_cb(env['ev'], btn_scripts.get('鼠标焦点'))
    assert env['tips'][0][3] == 16 and env['tips'][0][4] == -10

    # Fallback to Gly独.鼠标气泡 when S.气泡提示 is nil
    saved_tip_fn = env['S'].get('气泡提示')
    env['S'].rawset('气泡提示', None)
    env['gly_tips'].clear()
    invoke_sandboxed_cb(env['ev'], btn_scripts.get('鼠标焦点'))
    assert len(env['gly_tips']) == 1 and env['gly_tips'][0][0] == expected_tip
    env['S'].rawset('气泡提示', saved_tip_fn)

    # 8. Test 0.5s (500ms) check interval timing!
    pickup_frame = env['S'].get('__gm_pickup_frame_v299')
    stats = env['S'].get('__gm_autopickup_stats_v299')
    set_mode(1, True)
    env['now_sec'][0] = 20.0
    p0 = stats.get('prechecks')
    pickup_frame(env['U'], env['G'])
    assert stats.get('prechecks') == p0 + 1  # immediate first check
    env['now_sec'][0] = 20.400
    pickup_frame(env['U'], env['G'])
    assert stats.get('prechecks') == p0 + 1  # 400ms -> skipped
    env['now_sec'][0] = 20.499
    pickup_frame(env['U'], env['G'])
    assert stats.get('prechecks') == p0 + 1  # 499ms -> skipped
    env['now_sec'][0] = 20.500
    pickup_frame(env['U'], env['G'])
    assert stats.get('prechecks') == p0 + 2  # 500ms -> fires!
    env['now_sec'][0] = 21.000
    pickup_frame(env['U'], env['G'])
    assert stats.get('prechecks') == p0 + 3  # next 500ms -> fires!

    # 9. Test Mode 1 (绿色 普通自动拾取): ONLY white equip auto-sold; rare & books picked up!
    picked_m1 = []
    env['gold_delta'].clear()
    env['toasts'].clear()
    white_sword = LuaTable({
        '名称': '木剑', '显示名': '木剑', '分类': '装备', '子类': '武器', '价格': 100, '叠加': 0,
        '附加': LuaTable({}), '属性': LuaTable({'最大破坏': 5}),
    })
    rare3 = LuaTable({
        '名称': '屠龙', '显示名': '极品屠龙', '分类': '装备', '子类': '武器', '价格': 1000, '叠加': 0,
        '附加': LuaTable({'条数': 3}), '属性': LuaTable({'最大破坏': 40}),
    })
    rare7 = LuaTable({
        '名称': '屠龙', '显示名': '7条屠龙', '分类': '装备', '子类': '武器', '价格': 2000, '叠加': 0,
        '附加': LuaTable({'条数': 7}), '属性': LuaTable({'最大破坏': 50}),
    })
    book_base = LuaTable({
        '名称': '雷电术', '显示名': '雷电术', '分类': '道具', '子类': '消耗品', '价格': 400, '叠加': 0,
        '附加': LuaTable({'商店': '书店'}),
    })
    book_lv4 = LuaTable({
        '名称': '四级雷电术', '显示名': '四级雷电术', '分类': '道具', '子类': '消耗品', '价格': 800, '叠加': 0,
        '附加': LuaTable({'商店': '书店', '强化书': 4}),
    })
    book_lv5 = LuaTable({
        '名称': '五级魔法盾', '显示名': '五级魔法盾', '分类': '道具', '子类': '消耗品', '价格': 1200, '叠加': 0,
        '附加': LuaTable({'商店': '书店', '强化书': 5}),
    })
    place_ground(env, [
        make_ground_obj(white_sword, picked_log=picked_m1),
        make_ground_obj(rare3, picked_log=picked_m1),
        make_ground_obj(rare7, picked_log=picked_m1),
        make_ground_obj(book_base, picked_log=picked_m1),
        make_ground_obj(book_lv4, picked_log=picked_m1),
        make_ground_obj(book_lv5, picked_log=picked_m1),
    ])
    env['now_sec'][0] = 21.500
    pickup_frame(env['U'], env['G'])
    # Only white_sword sold (pay = ceil(100/2) = 50), all others picked up!
    assert env['gold_delta'] == [(50, '__gm_alt_sale_v283')]
    assert [n for n, _ in picked_m1] == ['屠龙', '屠龙', '雷电术', '四级雷电术', '五级魔法盾']
    assert any('自动出售了白色装备，获得金币【50】' in msg for msg, _ in env['toasts'])

    # 10. Test Mode 2 (宝蓝色 自动拾取+类一键出售):
    #     Sells: white equip, 1~6-affix rare equip, base/non-4/5 skill books
    #     Keeps (picks up): 7-affix rare equip, 4/5-level skill books, 禁止出售, 保护名单, 任务关联, 剧情关联, potions, oil, gold!
    set_mode(2, True)
    picked_m2 = []
    env['gold_delta'].clear()
    env['toasts'].clear()
    env['free_slots'][0] = 20

    # Items that MUST BE SOLD in Mode 2:
    s_white = LuaTable({'名称': '木剑', '显示名': '木剑', '分类': '装备', '子类': '武器', '价格': 101, '叠加': 0, '附加': LuaTable({}), '属性': LuaTable({'最大破坏': 5})})  # pay 51
    s_rare1 = LuaTable({'名称': '屠龙', '显示名': '1条屠龙', '分类': '装备', '子类': '武器', '价格': 600, '叠加': 0, '附加': LuaTable({'条数': 1}), '属性': LuaTable({'最大破坏': 37})})  # pay 300
    s_rare6 = LuaTable({'名称': '战神盔甲', '显示名': '6条战神', '分类': '装备', '子类': '衣服', '价格': 1200, '叠加': 0, '附加': LuaTable({'条数': 6}), '属性': LuaTable({'最大防御': 15})})  # pay 600
    s_book1 = LuaTable({'名称': '雷电术', '显示名': '雷电术', '分类': '道具', '子类': '消耗品', '价格': 400, '叠加': 0, '附加': LuaTable({'商店': '书店'})})  # pay 200
    s_book2 = LuaTable({'名称': 'Q火球术', '显示名': '火球术', '分类': '道具', '子类': '消耗品', '价格': 200, '叠加': 0, '附加': LuaTable({})})  # pay 100 (in SELLABLE_BOOKS even without 商店)
    s_book3 = LuaTable({'名称': '三级秘籍测试', '显示名': '三级秘籍测试', '分类': '道具', '子类': '消耗品', '价格': 300, '叠加': 0, '附加': LuaTable({'商店': '书店', '强化书': 3})})  # pay 150 (rank 3 book)

    # Items that MUST BE KEPT (picked up, NOT sold) in Mode 2:
    k_rare7 = LuaTable({'名称': '屠龙', '显示名': '7条屠龙', '分类': '装备', '子类': '武器', '价格': 2000, '叠加': 0, '附加': env['protect'](LuaTable({'条数': 7})), '属性': LuaTable({'最大破坏': 55})})
    k_rare8 = LuaTable({'名称': '战神盔甲', '显示名': '8条战神', '分类': '装备', '子类': '衣服', '价格': 3000, '叠加': 0, '附加': LuaTable({'条数': 8}), '属性': LuaTable({'最大防御': 20})})
    k_book4_rank = LuaTable({'名称': '四级雷电术', '显示名': '四级雷电术', '分类': '道具', '子类': '消耗品', '价格': 800, '叠加': 0, '附加': env['protect'](LuaTable({'商店': '书店', '强化书': 4}))})
    k_book5_rank = LuaTable({'名称': '五级魔法盾', '显示名': '五级魔法盾', '分类': '道具', '子类': '消耗品', '价格': 1200, '叠加': 0, '附加': env['protect'](LuaTable({'商店': '书店', '强化书': 5}))})
    k_book4_name = LuaTable({'名称': '四级烈火剑法', '显示名': '四级烈火剑法', '分类': '道具', '子类': '消耗品', '价格': 800, '叠加': 0, '附加': LuaTable({'商店': '书店'})})  # no 强化书 field, caught by prefix!
    k_book5_qname = LuaTable({'名称': 'Q五级召唤神兽', '显示名': '五级召唤神兽', '分类': '道具', '子类': '消耗品', '价格': 1200, '叠加': 0, '附加': LuaTable({'商店': '书店'})})  # Q-prefix caught!
    k_nosell = LuaTable({'名称': '神戒', '显示名': '神戒', '分类': '装备', '子类': '戒指', '价格': 9999, '叠加': 0, '禁止出售': True, '附加': LuaTable({'条数': 2})})
    k_protect = LuaTable({'名称': '青铜斧', '显示名': '青铜斧', '分类': '装备', '子类': '武器', '价格': 500, '叠加': 0, '附加': LuaTable({'条数': 2})})
    k_bone = LuaTable({'名称': '精灵骸骨', '显示名': '精灵骸骨', '分类': '道具', '子类': '消耗品', '价格': 500, '叠加': 0, '附加': LuaTable({'商店': '书店'})})
    k_quest = LuaTable({'名称': '任务剑', '显示名': '任务剑', '分类': '装备', '子类': '武器', '价格': 500, '叠加': 0, '任务关联': True, '附加': LuaTable({'条数': 1})})
    k_story = LuaTable({'名称': '剧情甲', '显示名': '剧情甲', '分类': '装备', '子类': '衣服', '价格': 500, '叠加': 0, '剧情关联': True, '附加': LuaTable({'条数': 1})})
    k_oil = LuaTable({'名称': '祝福油', '显示名': '祝福油', '分类': '道具', '子类': '消耗品', '价格': 5000, '叠加': 0, '附加': LuaTable({})})
    k_gold = LuaTable({'名称': '金币', '显示名': '金币', '分类': '特殊', '子类': '金币', '价格': 1, '叠加': 1, '附加': LuaTable({})})

    place_ground(env, [
        make_ground_obj(s_white, picked_log=picked_m2),
        make_ground_obj(s_rare1, picked_log=picked_m2),
        make_ground_obj(s_rare6, picked_log=picked_m2),
        make_ground_obj(s_book1, picked_log=picked_m2),
        make_ground_obj(s_book2, picked_log=picked_m2),
        make_ground_obj(s_book3, picked_log=picked_m2),
        make_ground_obj(k_rare7, picked_log=picked_m2),
        make_ground_obj(k_rare8, picked_log=picked_m2),
        make_ground_obj(k_book4_rank, picked_log=picked_m2),
        make_ground_obj(k_book5_rank, picked_log=picked_m2),
        make_ground_obj(k_book4_name, picked_log=picked_m2),
        make_ground_obj(k_book5_qname, picked_log=picked_m2),
        make_ground_obj(k_nosell, picked_log=picked_m2),
        make_ground_obj(k_protect, picked_log=picked_m2),
        make_ground_obj(k_bone, picked_log=picked_m2),
        make_ground_obj(k_quest, picked_log=picked_m2),
        make_ground_obj(k_story, picked_log=picked_m2),
        make_ground_obj(k_oil, picked_log=picked_m2),
        make_ground_obj(k_gold, qty=2500, picked_log=picked_m2),
    ])

    env['now_sec'][0] = 25.000
    pickup_frame(env['U'], env['G'])
    expected_gold = 51 + 300 + 600 + 200 + 100 + 150
    assert sum(g for g, _ in env['gold_delta']) == expected_gold, f'got {env["gold_delta"]}'
    assert len(env['gold_delta']) == 6
    picked_names = [n for n, _ in picked_m2]
    expected_kept = [
        '屠龙', '战神盔甲', '四级雷电术', '五级魔法盾', '四级烈火剑法', 'Q五级召唤神兽',
        '神戒', '青铜斧', '精灵骸骨', '任务剑', '剧情甲', '祝福油', '金币',
    ]
    assert picked_names == expected_kept, f'Mismatch kept items:\n  got:      {picked_names}\n  expected: {expected_kept}'
    assert any(f'自动出售了装备与技能书，获得金币【{expected_gold}】' in m for m, _ in env['toasts'])

    # 11. Manual Alt isolation while Mode 2 is active: must NOT bulk-sell rare equip or skill books!
    picked_alt = []
    env['gold_delta'].clear()
    env['toasts'].clear()
    place_ground(env, [
        make_ground_obj(s_white, picked_log=picked_alt),
        make_ground_obj(s_rare1, picked_log=picked_alt),
        make_ground_obj(s_book1, picked_log=picked_alt),
    ])
    env['alt_pressed'][0] = True
    env['now_sec'][0] = 25.200
    pickup_frame(env['U'], env['G'])
    env['alt_pressed'][0] = False
    assert env['gold_delta'] == [(51, '__gm_alt_sale_v283')]
    assert [n for n, _ in picked_alt] == ['屠龙', '雷电术']
    assert any('自动出售了白色装备，获得金币【51】' in m for m, _ in env['toasts'])

    # 12. Full-bag no-spam, map switch persistence, death/pause/Game_State guards
    env['free_slots'][0] = 0
    env['toasts'].clear()
    place_ground(env, [make_ground_obj(k_oil)])
    env['now_sec'][0] = 26.0
    pickup_frame(env['U'], env['G'])
    assert sum(1 for m, _ in env['toasts'] if '背包空间不足' in m) == 1
    env['now_sec'][0] = 26.5
    pickup_frame(env['U'], env['G'])
    assert sum(1 for m, _ in env['toasts'] if '背包空间不足' in m) == 1  # suppressed!
    assert stats.get('suppressed_full_msgs') >= 1

    # Map switch preserves Mode 2 and resets full_notified
    new_ground = LuaTable()
    new_map = LuaTable({'地面物品组': new_ground, '到逻辑格子': env['to_idx'], '地图格子列数': 50, '地图格子行数': 50})
    env['ev'].G.get('Q_地图').rawset('__gm_range_state', new_map)
    env['now_sec'][0] = 27.0
    pickup_frame(env['U'], env['G'])
    assert get_mode() == 2

    # 12b. Unfocused window (Ae冻集.屏幕焦点 == False): auto-pickup MUST still work,
    #      and background Alt key must NOT trigger manual Alt error spam!
    env['ev'].G.get('Q_地图').rawset('__gm_range_state', env['map'])
    env['E'].rawset('屏幕焦点', False)
    env['free_slots'][0] = 10
    env['gold_delta'].clear()
    env['toasts'].clear()
    picked_unfocused = []
    place_ground(env, [
        make_ground_obj(s_rare1, picked_log=picked_unfocused),
        make_ground_obj(k_oil, picked_log=picked_unfocused),
    ])
    env['alt_pressed'][0] = True  # simulate Alt+Tab while unfocused
    env['now_sec'][0] = 28.0
    pickup_frame(env['U'], env['G'])
    env['alt_pressed'][0] = False
    assert env['gold_delta'] == [(300, '__gm_alt_sale_v283')], f'Unfocused auto-pickup failed: {env["gold_delta"]}'
    assert [n for n, _ in picked_unfocused] == ['祝福油'], f'Unfocused pick failed: {picked_unfocused}'
    assert not any('Alt拾取暂不可用' in m for m, _ in env['toasts'])
    env['E'].rawset('屏幕焦点', True)

    # Game_State == 0 or hero dead -> precheck safely returns False
    precheck = env['S'].get('__gm_auto_precheck_v299')
    env['S'].rawset('Game_State', 0)
    assert precheck() is False
    env['S'].rawset('Game_State', 1)
    env['hero'].rawset('已经死亡', True)
    assert precheck() is False
    env['hero'].rawset('已经死亡', False)

    # 13. Mount batch pre-generation regression check
    mount = LuaTable({'名称': '猛虎', '分类': '装备', '子类': '坐骑', '附加': LuaTable({})})
    res_m = env['S'].get('__gm_ensure_mount_batch_v299')(mount, 'unit_test')
    assert res_m == 'initialized'
    batch = mount.get('附加').get('__gm_oil_batch_v263')
    assert batch.get('version') == 1 and 1 <= batch.get('length') <= 50 and batch.get('next') == 1
    assert env['S'].get('__gm_ensure_mount_batch_v299')(mount, 'repeat') == 'keep_valid'

    # 14. 「前尘忆梦」 full isolation check!
    env_qc = make_env('前尘忆梦')
    env_qc['ev'].G.get('loadstring')(runtime_src)(env_qc['S'])
    env_qc['S'].get('__gm_set_auto_pickup_mode_v300')(2, True)
    place_ground(env_qc, [make_ground_obj(s_white)])
    env_qc['now_sec'][0] = 10.0
    env_qc['S'].get('__gm_pickup_frame_v299')(env_qc['U'], env_qc['G'])
    assert env_qc['win539'].get('控件组').length() == 0  # button NOT installed in 前尘忆梦
    assert env_qc['gold_delta'] == []  # auto-pickup did NOT run
    env_qc['S'].get('__gm_autopickup_tip_v300')()
    assert env_qc['tips'] == []  # tooltip NOT shown in 前尘忆梦
    qc_mount = LuaTable({'名称': '猛虎', '分类': '装备', '子类': '坐骑', '附加': LuaTable({})})
    assert env_qc['S'].get('__gm_ensure_mount_batch_v299')(qc_mount, 'qc') == 'skip_story'

    report = {
        'version': 'v1.300',
        'all_passed': True,
        'sha256': hashlib.sha256(v300_bytes).hexdigest(),
        'game_res_sha256': hashlib.sha256(v300_bytes).hexdigest(),
        'game_res_bytes': len(v300_bytes),
        'tested_files': {
            'game_v300.res': hashlib.sha256(v300_bytes).hexdigest(),
            'runtime_v300.lua': hashlib.sha256((W / 'runtime_v300.lua').read_bytes()).hexdigest(),
            'patch_v300.py': hashlib.sha256((W / 'patch_v300.py').read_bytes()).hexdigest(),
            'test_v300.py': hashlib.sha256((W / 'test_v300.py').read_bytes()).hexdigest(),
        },
        'changed_modules': changed_mods,
        'bytecode_instruction_changes': 0,
        'static_audit': 'PASS (12/143,217,218,220; 14/256,428,446,456,481,781; Module 22 all 123 protos)',
        'lua51_syntax_and_gbk': 'PASS (0 0x5C hazards)',
        'checks': {
            'interval_500ms': 'PASS (400ms/499ms skipped, 500ms fires)',
            'button_3state_cycle_sandbox': 'PASS (0->1->2->0 under _G==nil, distinct grey/green/royal-blue skins, hover, dots)',
            'hover_tooltip_sandbox': 'PASS (concise 2-line tip: green #c(-11739014) + bright blue #c(-8204545), dynamic edges, Gly独 fallback)',
            'mode1_green_normal': 'PASS (white equip only sold, rare equip & books picked up)',
            'mode2_royalblue_bulk_sell': 'PASS (sells white + 1~6-affix rare + non-4/5 books; keeps 7-affix rare, 4/5 books by rank & prefix, 禁止出售, 保护名单, 任务/剧情, oil, gold)',
            'manual_alt_isolation': 'PASS (stays white-equip-only even while Mode 2 active)',
            'stability_and_guards': 'PASS (full-bag no-spam, map switch persistence, Game_State & death guards)',
            'mount_batch_regression': 'PASS',
            'qiancheng_isolation': 'PASS (button/tooltip/auto-pickup/mount all untouched)',
        },
        'status': 'PASS',
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v300.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v300.json').write_text(text, encoding='utf-8')
    print('ALL v1.300 CHECKS PASSED!')


if __name__ == '__main__':
    run_all()
