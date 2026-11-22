"""Exhaustive verification suite for v1.307:
1. Outer resource diff restricted strictly to modules [12, 14, 30] + rebuild + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v307.lua
3. Remote 【仓库】 button upgrade (「来世续缘」 only, tested with S.script_setting split):
   - Guild NOT activated: click 1 -> 普通仓库 (warm amber tint); click 2 -> close (default grey)
   - Guild ACTIVATED: click 1 -> 普通仓库 (warm amber); click 2 -> close 普通 + open 行会仓库 (cool teal tint); click 3 -> close (default grey)
   - External close (X / ESC / NPC) immediately restores default grey tint
   - Opening warehouse via NPC does not falsely tint the button
   - 「前尘忆梦」 100% isolated (original 远程仓库按钮 untouched; switching story restores it)
4. Mode 2 【自动拾取+自动出售】 also sells all 36 ordinary-mob corpse-dig materials:
   - All 36 materials accepted across 分类 ('道具'/'材料'/'消耗品')
   - Boss/rare/quest/seal items (沃玛号角, 精灵骸骨, 飞龙剑碎片, 火影晶体, 震天魔印, 商会物资, *_印记) & 禁止出售/任务关联/剧情关联 strictly kept
   - Mode 2 end-to-end ground auto-sell pays exact gold and updates notification text
   - Mode 1 (green) and manual Alt keep ordinary-mob materials in bag (do NOT auto-sell)
   - 「前尘忆梦」 100% isolated
5. v1.306 regression check (gather drop formula intact)
"""
import hashlib
import json
from pathlib import Path

from ljtool import Dump
from lua51_eval import LuaTable, syntax_check
from native_test_utils import trees
from patch_v305 import ORDINARY_MOB_MATERIALS
from resource_tools import decode
from test_v300 import make_env

W = Path(__file__).resolve().parent
BASE_SHA = '0575204f1f4017a6e647b77cdc600cae5aebb9e5dcf2afef7780abcb034e0497'


def extract_runtime_v307(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.307 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v307.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_and_syntax():
    base_bytes = (W / 'game_v306.res').read_bytes()
    out_bytes = (W / 'game_v307.res').read_bytes()
    assert hashlib.sha256(base_bytes).hexdigest() == BASE_SHA

    outer_b, mods_b = decode(base_bytes, (12, 14, 30))
    outer_o, mods_o = decode(out_bytes, (12, 14, 30))

    root_b, root_o = outer_b.protos[0], outer_o.protos[0]
    changed_slots = [i for i in range(root_b.nkgc) if root_b.gc(i) != root_o.gc(i)]
    assert changed_slots == [12, 14, 30], f'Expected only [12, 14, 30] changed, got {changed_slots}'
    for mid in (12, 14, 30):
        ro = mods_o[mid].rebuild()
        assert Dump(ro).rebuild() == ro
        trees(mods_o[mid])

    rt_src = extract_runtime_v307(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def make_wh_env(rt_src, story='来世续缘', guild_active=False):
    env = make_env(story=story)
    ev, S, U = env['ev'], env['S'], env['U']
    ss = S.rawget('script_setting')

    # Real-client split: 仓库窗口 and 行会仓库 live ONLY in S.script_setting, NOT in _G!
    ev.G.rawset('仓库窗口', None)
    ev.G.rawset('行会仓库', None)

    norm_win = LuaTable({'可视': False})
    norm_win.rawset('打开', lambda: norm_win.rawset('可视', True))
    norm_win.rawset('关闭', lambda: norm_win.rawset('可视', False))

    guild_win = LuaTable({'可视': False})
    guild_win.rawset('打开', lambda: guild_win.rawset('可视', True))
    guild_win.rawset('关闭', lambda: guild_win.rawset('可视', False))

    ss.rawset('仓库窗口', norm_win)
    ss.rawset('行会仓库', guild_win)

    guild_flag = [guild_active]
    U.rawset('啾啾啵啵', lambda: LuaTable({'行会': LuaTable({'名称': '归梦行会'}) if guild_flag[0] else None}))

    sound_plays = []
    U.rawset('游戏音效', LuaTable({'按键音效1': LuaTable({'播放': lambda: sound_plays.append(1)})}))

    # Pre-install original 远程仓库按钮 on Window 539 with 禁用按钮 tracking
    win539 = S.rawget('取窗口对象')(539)
    old_disabled = [False]
    old_obj = LuaTable({
        '显示': lambda *a: None,
        '销毁': lambda *a: None,
        '是否有焦点': lambda: False,
        '禁用按钮': lambda flag: old_disabled.__setitem__(0, bool(flag)),
    })
    old_ctrl = LuaTable({
        '名称': '远程仓库按钮', 'x': 180, 'y': 20, 'w': 44, 'h': 22, '可视': True, '对象': old_obj,
    })
    ctrls = win539.rawget('控件组')
    ctrls.rawset(ctrls.length() + 1, old_ctrl)

    # Track rendered skin color and hover state on created buttons
    hover_flag = [False]
    rendered_colors = []
    orig_create_sprite = ev.G.rawget('Q__').rawget('创建精灵')

    def create_sprite_tracked(*args):
        sp = orig_create_sprite(*args)
        sp.rawset('置颜色', lambda col: rendered_colors.append(col))
        return sp

    ev.G.rawget('Q__').rawset('创建精灵', create_sprite_tracked)

    # Enhance win539:增加控件 to record disabled state & hover state cleanly
    orig_add = win539.rawget('增加控件')
    new_disabled = [False]

    def add_ctrl_tracked(self_w, *args):
        orig_add(self_w, *args)
        c = self_w.rawget('控件组').rawget(self_w.rawget('控件组').length())
        c.rawset('可视', True)
        obj = c.rawget('对象')
        obj.rawset('是否有焦点', lambda: hover_flag[0])
        obj.rawset('禁用按钮', lambda flag: new_disabled.__setitem__(0, bool(flag)))

    win539.rawset('增加控件', add_ctrl_tracked)

    ev.G.get('loadstring')(rt_src)(S)
    return {
        'env': env, 'ev': ev, 'S': S, 'U': U,
        'win539': win539, 'norm_win': norm_win, 'guild_win': guild_win,
        'guild_flag': guild_flag, 'old_ctrl': old_ctrl, 'old_disabled': old_disabled,
        'new_disabled': new_disabled, 'hover_flag': hover_flag,
        'rendered_colors': rendered_colors, 'sound_plays': sound_plays,
    }


def find_ctrl(win, name):
    ctrls = win.rawget('控件组')
    for i in range(1, ctrls.length() + 1):
        c = ctrls.rawget(i)
        if c and c.rawget('名称') == name:
            return c
    return None


def test_warehouse_button_upgrade(rt_src):
    COL_OFF, COL_OFF_HOVER = -5723992, -4671304
    COL_NORM, COL_NORM_HOVER = -3886976, -2834288
    COL_GUILD, COL_GUILD_HOVER = -8210232, -7026472

    # --- Case 1A: Guild NOT activated ---
    w = make_wh_env(rt_src, story='来世续缘', guild_active=False)
    S, U, G = w['S'], w['U'], w['env']['G']
    pickup_frame = S.rawget('__gm_pickup_frame_v299')
    pickup_frame(U, G)

    new_ctrl = find_ctrl(w['win539'], '远程仓库按钮_v307')
    assert new_ctrl is not None, '远程仓库按钮_v307 must be installed in 来世续缘'
    assert w['old_ctrl'].rawget('可视') is False and w['old_disabled'][0] is True
    assert new_ctrl.rawget('可视') is True and w['new_disabled'][0] is False
    assert (new_ctrl.rawget('x'), new_ctrl.rawget('y'), new_ctrl.rawget('w'), new_ctrl.rawget('h')) == (180, 20, 44, 22)

    obj = new_ctrl.rawget('对象')
    click = new_ctrl.rawget('脚本').rawget('Main')
    wh_state = S.rawget('__gm_wh_state_v307')

    # Initial render -> default grey
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_OFF

    # Click 1 -> open normal warehouse, warm amber tint
    click()
    assert w['norm_win'].rawget('可视') is True and w['guild_win'].rawget('可视') is False
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_NORM
    w['hover_flag'][0] = True
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_NORM_HOVER
    w['hover_flag'][0] = False

    # Click 2 (guild NOT active) -> close normal warehouse ONLY, guild stays closed, tint resets to default grey
    click()
    assert w['norm_win'].rawget('可视') is False and w['guild_win'].rawget('可视') is False
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_OFF
    assert len(w['sound_plays']) == 2

    # --- Case 1B: Guild ACTIVATED ---
    w['guild_flag'][0] = True
    # Click 1 -> open normal warehouse (warm amber)
    click()
    assert w['norm_win'].rawget('可视') is True and w['guild_win'].rawget('可视') is False
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_NORM

    # Click 2 -> close normal warehouse AND open guild warehouse (cool teal, distinct from grey & amber!)
    click()
    assert w['norm_win'].rawget('可视') is False and w['guild_win'].rawget('可视') is True
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_GUILD
    assert len({COL_OFF, COL_NORM, COL_GUILD}) == 3
    w['hover_flag'][0] = True
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_GUILD_HOVER
    w['hover_flag'][0] = False

    # Click 3 -> close guild warehouse (default grey)
    click()
    assert w['norm_win'].rawget('可视') is False and w['guild_win'].rawget('可视') is False
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_OFF

    # --- Case 1C: External close resets color immediately; NPC open does not falsely tint ---
    click()  # open normal
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_NORM
    w['norm_win'].rawset('可视', False)  # closed via X / ESC
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_OFF and wh_state.rawget('opened_kind') is None

    # Open guild via 2 clicks, then external close
    click(); click()
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_GUILD
    w['guild_win'].rawset('可视', False)
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_OFF and wh_state.rawget('opened_kind') is None

    # Opened by NPC directly -> stays default grey, clicking button transitions to guild warehouse
    w['norm_win'].rawset('可视', True)
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_OFF
    click()
    assert w['norm_win'].rawget('可视') is False and w['guild_win'].rawget('可视') is True
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_GUILD

    # --- Case 1D: Switch to 「前尘忆梦」 restores original button ---
    U.rawset('版本选择', '前尘忆梦')
    pickup_frame(U, G)
    assert w['old_ctrl'].rawget('可视') is True and w['old_disabled'][0] is False
    assert new_ctrl.rawget('可视') is False and w['new_disabled'][0] is True

    # Fresh 「前尘忆梦」 session never installs 远程仓库按钮_v307
    w_old = make_wh_env(rt_src, story='前尘忆梦', guild_active=True)
    w_old['S'].rawget('__gm_pickup_frame_v299')(w_old['U'], w_old['env']['G'])
    assert find_ctrl(w_old['win539'], '远程仓库按钮_v307') is None
    assert w_old['old_ctrl'].rawget('可视') is True and w_old['old_disabled'][0] is False


def make_ground_item(name, cat='道具', price=100, qty=1, extra=None, flags=None, picked_list=None):
    it = LuaTable({'名称': name, '显示名': name, '分类': cat, '子类': cat, '价格': price, '叠加': 1,
                   '附加': extra or LuaTable({'叠加上限': 99}), '属性': LuaTable()})
    if flags:
        for k, v in flags.items():
            it.rawset(k, v)
    obj = LuaTable({
        '物品': it, '数量': qty, '已经消失': False, '格子': LuaTable({'x': 10, 'y': 10}),
        'Hero': LuaTable({'回调脚本': LuaTable({'拾取': lambda *a: (False, False)})}),
    })
    def pickup_fn(self_o, mode):
        self_o.rawset('已经消失', True)
        if picked_list is not None:
            picked_list.append(name)
        return True
    obj.rawset('拾取', pickup_fn)
    return obj


def test_mode2_ordinary_materials(rt_src):
    # --- Case 2A: Exhaustive can_bulk_sell_ground predicate ---
    env = make_env(story='来世续缘')
    ev, S = env['ev'], env['S']
    ev.G.get('loadstring')(rt_src)(S)
    can_sell = S.rawget('__gm_can_bulk_sell_v300')

    assert len(ORDINARY_MOB_MATERIALS) == 36
    for idx, mat in enumerate(ORDINARY_MOB_MATERIALS):
        cat = ('道具', '材料', '消耗品')[idx % 3]
        ok, kind = can_sell(LuaTable({'名称': mat, '分类': cat, '价格': 100, '附加': LuaTable()}), 1)
        assert ok is True and kind == '材料', f'Material {mat} ({cat}) should be sellable, got {(ok, kind)}'

    # Strictly excluded rare/Boss/quest/seal/protected items
    must_keep = [
        ('沃玛号角', '道具'), ('精灵骸骨', '道具'), ('飞龙剑碎片', '道具'),
        ('火影晶体', '道具'), ('震天魔印', '道具'), ('商会物资', '道具'),
        ('火之印记', '道具'), ('冰之印记', '道具'), ('雷之印记', '道具'),
        ('强效太阳水', '消耗品'), ('祝福油', '道具'), ('四级火球术', '道具'),
        ('五级雷电术', '道具'), ('鹤嘴锄', '装备'),
    ]
    for nm, cat in must_keep:
        ok, why = can_sell(LuaTable({'名称': nm, '分类': cat, '价格': 1000, '附加': LuaTable()}), 1)
        assert ok is False, f'Excluded item {nm} MUST be kept, got {(ok, why)}'

    # Flag-protected ordinary materials MUST be kept
    for flag in ('禁止出售', '任务关联', '剧情关联'):
        ok, why = can_sell(LuaTable({'名称': '猪肉', '分类': '道具', '价格': 100, flag: True, '附加': LuaTable()}), 1)
        assert ok is False, f'猪肉 with {flag}=true MUST be kept, got {(ok, why)}'

    # --- Case 2B: End-to-end Mode 2, Mode 1, Manual Alt ---
    def run_ground_test(story, is_auto, auto_mode, extra_items=None):
        env = make_env(story=story)
        ev, S, U, G = env['ev'], env['S'], env['U'], env['G']
        ev.G.get('loadstring')(rt_src)(S)
        gold_log = []
        msg_log = []
        U.rawset('窗口相关', LuaTable({'界面切换': lambda amt, *a: gold_log.append(amt)}))
        U.rawset('托管显示', LuaTable({'屏幕提示': lambda msg, *a: msg_log.append(msg)}))
        G.rawset('取包裹空位', lambda *a: 20)
        picked = []

        bucket = LuaTable()
        items = [
            make_ground_item('猪肉', '道具', 120, 2, picked_list=picked),        # sell -> 60*2 = 120
            make_ground_item('毒蜘蛛牙齿', '材料', 80, 1, picked_list=picked),    # sell -> 40*1 = 40
            make_ground_item('沃玛号角', '道具', 500, 1, picked_list=picked),     # KEEP
            make_ground_item('精灵骸骨', '道具', 200, 1, picked_list=picked),     # KEEP
            make_ground_item('猪肉', '道具', 100, 1, flags={'禁止出售': True}, picked_list=picked),  # KEEP
        ]
        if extra_items:
            items.extend(extra_items(picked))
        for i, o in enumerate(items, 1):
            bucket.rawset(i, o)

        qmap = ev.G.rawget('Q_地图').rawget('__gm_range_state')
        qmap.rawget('地面物品组').rawset(qmap.rawget('到逻辑格子')(10, 10), bucket)

        run_fn = S.rawget('__gm_run_range_pickup_v299')
        run_fn(U, G, is_auto, auto_mode)
        return sum(gold_log), picked, msg_log

    # Mode 2 (ordinary materials only)
    gold, picked, msgs = run_ground_test('来世续缘', True, 2)
    assert gold == 160, f'Expected 160 gold, got {gold}'
    assert picked == ['沃玛号角', '精灵骸骨', '猪肉'], f'Unexpected picked: {picked}'
    assert msgs == ['自动出售了普通怪材料，获得金币【160】'], f'Unexpected msgs: {msgs}'

    # Mode 2 mixed (equip + book + material)
    def add_mixed(picked):
        return [
            make_ground_item('乌木剑', '装备', 200, 1, extra=LuaTable({'条数': 2}), picked_list=picked),  # 100
            make_ground_item('火球术', '道具', 300, 1, picked_list=picked),                                 # 150
        ]
    gold_m, picked_m, msgs_m = run_ground_test('来世续缘', True, 2, extra_items=add_mixed)
    assert gold_m == 410, f'Expected 410 gold, got {gold_m}'
    assert msgs_m == ['自动出售了装备、技能书、普通怪材料，获得金币【410】'], f'Unexpected msgs: {msgs_m}'

    # Mode 1 (normal green) -> keeps 猪肉 and 毒蜘蛛牙齿 in bag!
    gold1, picked1, _ = run_ground_test('来世续缘', True, 1)
    assert gold1 == 0 and '猪肉' in picked1 and '毒蜘蛛牙齿' in picked1

    # Manual Alt -> keeps 猪肉 and 毒蜘蛛牙齿 in bag!
    gold_alt, picked_alt, _ = run_ground_test('来世续缘', False, 0)
    assert gold_alt == 0 and '猪肉' in picked_alt and '毒蜘蛛牙齿' in picked_alt


def test_v306_regression(rt_src):
    env = make_env(story='来世续缘')
    ev, S = env['ev'], env['S']
    ev.G.get('loadstring')(rt_src)(S)
    prob_fn = S.rawget('__gm_calc_gather_prob_v306')
    assert abs(prob_fn(100, 2) - 5.0 / 100) < 1e-12


def main():
    mods_o, rt_src = test_diff_and_syntax()
    test_warehouse_button_upgrade(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v307.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.307',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v307.res': out_sha,
            'runtime_v307.lua': hashlib.sha256((W / 'runtime_v307.lua').read_bytes()).hexdigest(),
            'patch_v307.py': hashlib.sha256((W / 'patch_v307.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'warehouse_btn_guild_inactive_2click_cycle_and_color_reset',
            'warehouse_btn_guild_active_3click_cycle_distinct_colors',
            'warehouse_btn_external_close_reset_and_npc_open_handling',
            'warehouse_btn_qianchi_isolated_and_story_switch_restore',
            'mode2_sells_all_36_ordinary_mob_materials_across_categories',
            'mode2_keeps_boss_rare_quest_seal_and_flag_protected_items',
            'mode2_end_to_end_gold_and_mixed_notification',
            'mode1_and_manual_alt_keep_ordinary_materials',
            'v306_gather_formula_regression_intact',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v307.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v307.json').write_text(text, encoding='utf-8')
    print('ALL v1.307 TESTS PASSED!')


if __name__ == '__main__':
    main()
