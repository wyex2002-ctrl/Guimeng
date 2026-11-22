"""Exhaustive verification suite for v1.337:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v337.lua
3. m12/37 (qs_item_box.Main) still has ZERO JMP instructions with A < params
4. Enchant Scroll Tooltip (v1.337, 「来世续缘」 only):
   - Appends '#Y同名附魔不重复叠加#W' right below '#Y拖到武器/衣服/头盔使用#W' (idempotent).
5. Duplicate Equipped Enchant Priority (武器 -> 衣服 -> 头盔, Hero & Merc independent):
   - 武器(A) + 衣服(A): 武器 active green, 衣服 inactive grey + '#R同名附魔不重复叠加#W'.
   - 武器(A) + 头盔(A): 武器 active green, 头盔 inactive grey + '#R同名附魔不重复叠加#W'.
   - 衣服(A) + 头盔(A): 衣服 active green, 头盔 inactive grey + '#R同名附魔不重复叠加#W'.
   - 武器(A) + 衣服(A) + 头盔(A): 武器 active, 衣服 & 头盔 both inactive; stats summed once.
   - 武器(A) + 衣服(B) + 头盔(A): 武器 & 衣服 active, 头盔 inactive; stats = A + B.
   - Hero 武器(A) + Merc 衣服(A): both active (actor-independent).
   - Merc 武器(A) + Merc 衣服(A) + Merc 头盔(A): Merc 武器 active, 衣服 & 头盔 inactive.
   - Unequipping 武器(A) (ev_type=2 or lifted on Q_鼠标) immediately flips 衣服(A) to active green.
   - Bag 衣服(A) while Hero wears 武器(A) stays active green; invalid slots keep '#R附魔仅在武器/衣服/头盔生效#W'.
6. Enchant Overwrite Confirmation Dialog (v1.337, 「来世续缘」 only):
   - Dragging scroll onto unenchanted 武器/衣服/头盔 applies immediately without dialog.
   - Dragging scroll onto already-enchanted 武器/衣服/头盔 releases Q_鼠标 and opens Gly独.询问:
     '该装备已有【<旧附魔名>】的附魔。\n确认是否覆盖？'
   - Cancel leaves old enchant intact and scroll unconsumed; late confirm is a no-op.
   - Confirm verifies persistent S.包裹物品组 items (even when 从ID取格子 returns fresh UI copies),
     overwrites 套装属性, consumes scroll via 重置道具(nil), recalculates sets, and refreshes tooltips.
   - Stale/moved item or scroll before confirm aborts safely with red prompt.
   - Already-open Q_提示框 blocks safely with red prompt.
   - 「前尘忆梦」 delegates untouched without dialog or tooltip changes.
7. Full v1.336..v1.306 regressions (including v1.328).
"""
import hashlib
import json
from pathlib import Path

from ljdis import OPS
from ljtool import Dump
from lua51_eval import LuaTable, syntax_check
from native_test_utils import trees
from resource_tools import decode
from test_v300 import make_env
from test_v307 import test_mode2_ordinary_materials, test_v306_regression
from test_v308 import test_authentic_proxy_warehouse_button
from test_v317 import test_compact_equip_spaces_v317
from test_v319 import (
    decode_real_sets_full_143,
    make_slot_proxy,
    test_real_boss_blueprint_drops_5_5pct,
)
from test_v320 import sum_sets
from test_v322 import decode_real_blueprint_templates
from test_v328 import test_v328_weapon_armor_helmet_rules
from test_v330 import test_v330_split_bracelet_ring_gems
from test_v331 import test_v331_gem_tooltip_cache_refresh
from test_v332 import test_v332_corpse_drop_jipin_stats
from test_v333 import test_v333_shared_weapon_tooltip_note
from test_v334 import test_v334_mode2_qingtongfu_mofachangpao_non7
from test_v335 import test_v335_repeat_autocast_ux
from test_v336 import (
    test_v336_corpse_drop_jipin_hardening,
    test_v336_ordinary_materials_ground_white,
)

W = Path(__file__).resolve().parent
BASE_SHA = 'c8034e8e15459d8dd28a2c9ce3308d2ecacd166f588e12554bbcc51b7b9da715'


def extract_runtime_v337(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.337 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v337.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_syntax_and_m12_37():
    base_bytes = (W / 'game_v336.res').read_bytes()
    out_bytes = (W / 'game_v337.res').read_bytes()
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

    p37 = mods_o[12].protos[37]
    for pc, ins in enumerate(p37.bc):
        if OPS[ins & 0xFF] == 'JMP':
            a = (ins >> 8) & 0xFF
            assert a >= p37.params, f'm12/37 pc={pc} has JMP A={a} < params={p37.params}'

    rt_src = extract_runtime_v337(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def make_raw_equip_tip(name, enchant_name, desc_text, trailing=None):
    lines = [
        f'#md#G{enchant_name}',
        f'#md#f(宋_9_炭灰,#c(-1){name}#W)',
        '#md#W重量:10',
        '#md#W需要等级:1',
        '#md#G套装信息',
        '#md#c(-5385052)' + desc_text,
    ]
    if trailing:
        lines.append(trailing)
    return '\n'.join(lines)


def assert_active_enchant(tip_text, enchant_name):
    ls = tip_text.split('\n')
    hi = ls.index('#f(宋_9_炭灰,#c(-7350017)附魔属性#W)')
    assert ls[hi + 1] == f'#f(宋_9_炭灰,#c(-16711936){enchant_name}#W)', ls[hi:hi + 4]
    assert '同名附魔不重复叠加' not in tip_text, tip_text
    assert '附魔仅在武器/衣服/头盔生效' not in tip_text, tip_text
    assert any(l.startswith('#c(-8323200)') or l.startswith('#c(-8323328)') for l in ls[hi + 2:]), ls[hi:]


def assert_duplicate_inactive_enchant(tip_text, enchant_name):
    ls = tip_text.split('\n')
    hi = ls.index('#f(宋_9_炭灰,#c(-7350017)附魔属性#W)')
    assert ls[hi + 1] == f'#f(宋_9_炭灰,#c(-5592406){enchant_name}#W)', ls[hi:hi + 4]
    assert ls[-1] == '#R同名附魔不重复叠加#W', ls[-3:]
    assert tip_text.count('同名附魔不重复叠加') == 1, tip_text
    for stat_ln in ls[hi + 2:-1]:
        assert stat_ln.startswith('#H'), f'Expected grey #H stat line, got {stat_ln!r}'


def test_v337_enchant_rules_and_confirm(d12, rt_src):
    real_sets = decode_real_sets_full_143(d12)
    real_tpls = decode_real_blueprint_templates(d12)

    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']

    hero_obj = LuaTable({'名称': '测试主角'})
    S.rawset('hero', hero_obj)
    S.rawset('get', lambda k: hero_obj if k == 'hero' else S.rawget(k))

    item_db = LuaTable()
    for nm, dn in real_tpls.items():
        item_db.rawset(nm, LuaTable({'名称': nm, '显示名': dn}))
    S.rawset('游戏道具组', item_db)

    bag = LuaTable()
    S.rawset('包裹物品组', bag)

    sets_lua = LuaTable()
    for name, (hsh, req, desc) in real_sets.items():
        e = LuaTable()
        e.rawset(1, LuaTable(hsh))
        e.rawset(2, req)
        e.rawset(3, desc)
        sets_lua.rawset(name, e)
    U.rawset('天竺葵家', lambda: sets_lua)
    U.rawset('胚子考虑', lambda: LuaTable({'装备操作': 0}))

    prompts = []
    asks = []
    dialog = LuaTable({'可视': False})
    ev.G.rawset('Q_提示框', dialog)

    def mock_ask(prompt_text, ok_fn=None, cancel_fn=None):
        dialog.rawset('可视', True)
        dialog.rawset('提示内容', prompt_text)
        dialog.rawset('确定_回调方法', ok_fn)
        dialog.rawset('取消_回调方法', cancel_fn)
        asks.append({'text': prompt_text, 'ok': ok_fn, 'cancel': cancel_fn})

    G.rawset('询问', mock_ask)

    mouse_src = LuaTable({'拿起': False})
    q_mouse = LuaTable({'被占用': False, '格子标识': 0, '物品来源': mouse_src})
    ev.G.rawset('Q_鼠标', q_mouse)

    def raw_tip_fn(item, mode, slot_id):
        if item.rawget('分类') == '装备':
            ex = item.rawget('附加')
            sn = ex.rawget('套装属性') if isinstance(ex, LuaTable) else None
            if sn and sn in real_sets:
                trailing = '#md#WShift+左键放入备用背包' if (slot_id is None or (14 <= slot_id <= 396)) else None
                return make_raw_equip_tip(item.rawget('名称'), sn, real_sets[sn][2], trailing), None
            return f"#md#W{item.rawget('名称')}", None
        ex = item.rawget('附加')
        sn = ex.rawget('套装属性') if isinstance(ex, LuaTable) else None
        if sn and sn in real_sets:
            return (
                f'#md#f(宋_9_炭灰,#c(-16711936){sn}(图纸)#W)\n'
                f'#md#W重量:1\n'
                f'#md#c(-5385052){real_sets[sn][2]}\n'
                f'#md#c(-45824)拖到装备使用\n'
                f'#md#WShift+左键放入备用背包'
            ), None
        return '#md#W普通道具', None

    disp = LuaTable({
        '道具': raw_tip_fn,
        '屏幕提示': lambda m, c=None: prompts.append((m, c)),
    })
    U.rawset('托管显示', disp)

    ui_calls = {'elem_icon': 0, 'merc_win': 0, 'orig_box_ev4': 0}
    wr = LuaTable({
        '套装属性': lambda a, b: None,
        '佣兵套装': lambda a, b: None,
        '元素图标': lambda: ui_calls.__setitem__('elem_icon', ui_calls['elem_icon'] + 1),
        '佣兵窗口': lambda a=None, b=None: ui_calls.__setitem__('merc_win', ui_calls['merc_win'] + 1),
    })
    U.rawset('窗口相关', wr)

    # Simulate realistic UI cell proxy where .道具 returns a fresh copy wrapper referencing the same 附加
    fresh_copy_mode = {'on': False}
    reset_log = []

    def make_cell_proxy(sid):
        cell = LuaTable()

        def do_reset(val=None):
            reset_log.append((sid, val))
            bs = bag.rawget(sid)
            if isinstance(bs, LuaTable):
                bs.rawset('道具', val)

        def cell_index(self_t, k):
            if k == '道具':
                bs = bag.rawget(sid)
                it = bs.rawget('道具') if isinstance(bs, LuaTable) else None
                if it is None:
                    return None
                if fresh_copy_mode['on']:
                    # Fresh display copy wrapper (like real engine UI cell!)
                    cp = LuaTable()
                    for kk, vv in it._data.items():
                        cp.rawset(kk, vv)
                    return cp
                return it
            if k == '重置道具':
                return do_reset
            return None

        cell._mt = LuaTable({'__index': cell_index})
        return cell

    G.rawset('从ID取格子', make_cell_proxy)
    G.rawset('鼠标道具', 0)

    def orig_box(ev_type, slot_id, a3=None, a4=None, a5=None):
        if ev_type == 4:
            ui_calls['orig_box_ev4'] += 1
            mid = G.rawget('鼠标道具')
            tc = bag.rawget(slot_id)
            sc = bag.rawget(mid)
            if tc and sc and tc.rawget('道具') and sc.rawget('道具'):
                sex = sc.rawget('道具').rawget('附加')
                if sex and sex.rawget('套装属性') is not None:
                    ti = tc.rawget('道具')
                    if ti.rawget('附加') is None:
                        ti.rawset('附加', LuaTable())
                    ti.rawget('附加').rawset('套装属性', sex.rawget('套装属性'))
                    sc.rawset('道具', None)
                    return True
        if ev_type in (1, 2) and slot_id is not None:
            if 1 <= slot_id <= 13:
                wr.rawget('套装属性')(slot_id, ev_type)
            elif 397 <= slot_id <= 409:
                wr.rawget('佣兵套装')(slot_id, ev_type)
        return None

    lua_tostring = ev.G.get('tostring')
    shelp = LuaTable()
    shelp.rawset(lua_tostring(orig_box), LuaTable({'msg': '【全局事件/物品格子】', 'fname': 'Main', 'sid': 5}))
    S.rawset('shelp', shelp)
    box_tbl = LuaTable({'Main': orig_box})
    S.rawset('tbl_qs', LuaTable({'qs_item_box': box_tbl}))

    # Controls to capture live tooltip refreshes and rendered tooltip text
    rendered_tips = {}
    refresh_events = []
    tbl_controls = LuaTable()
    for cid in (1, 2, 3, 4, 35, 40, 397, 398, 399):
        def make_updater(slot_num):
            def upd(self_obj=None):
                refresh_events.append(slot_num)
                bs = bag.rawget(slot_num)
                it = bs.rawget('道具') if isinstance(bs, LuaTable) else None
                if it is not None:
                    txt, _ = disp.rawget('道具')(it, 1, slot_num)
                    rendered_tips[slot_num] = txt
            return upd
        ctrl = LuaTable({
            '格子ID': cid,
            '对象': LuaTable({'焦点': False, '更新道具属性': make_updater(cid)}),
        })
        tbl_controls.rawset(f'物品格子{cid}', ctrl)
    S.rawset('tbl_controls', tbl_controls)

    h14_internal, h14_proxy = make_slot_proxy(ev)
    m410_internal, m410_proxy = make_slot_proxy(ev)
    ss = S.rawget('script_setting')
    ss.rawset('Gly独', G)
    ss.rawset('物品格子14', h14_proxy)
    ss.rawset('物品格子410', m410_proxy)

    ev.G.get('loadstring')(rt_src)(S)

    # ------------------------------------------------------------------
    # 1. Scroll tooltip appends '#Y同名附魔不重复叠加#W' right below usage line
    # ------------------------------------------------------------------
    scroll_a = LuaTable({'名称': '虎战领主之爪_图纸', '分类': '消耗', '子类': '消耗',
                         '附加': LuaTable({'套装属性': '虎战领主之爪'})})
    out_scroll, _ = disp.rawget('道具')(scroll_a, 1, 40)
    sls = out_scroll.split('\n')
    idx_use = sls.index('#Y拖到武器/衣服/头盔使用#W')
    assert sls[idx_use + 1] == '#Y同名附魔不重复叠加#W', sls
    assert out_scroll.count('同名附魔不重复叠加') == 1
    assert sls[-1] == '#WShift+左键放入备用背包'

    # ------------------------------------------------------------------
    # 2. Duplicate equipped enchant priority: 武器 > 衣服 > 头盔
    # ------------------------------------------------------------------
    # Deliberately place 衣服 at slot 1, 头盔 at slot 2, 武器 at slot 3 to prove
    # priority follows 武器->衣服->头盔 by 子类, NOT numeric slot ID!
    sA = '虎战领主之爪'
    sB = '沃玛教主的利爪'
    armor_a = LuaTable({'名称': '赤龙宝甲_男', '分类': '装备', '子类': '衣服',
                        '附加': LuaTable({'套装属性': sA})})
    helm_a = LuaTable({'名称': '黑铁头盔', '分类': '装备', '子类': '头盔',
                       '附加': LuaTable({'套装属性': sA})})
    weapon_a = LuaTable({'名称': '屠龙', '分类': '装备', '子类': '武器',
                         '附加': LuaTable({'套装属性': sA})})
    bag_armor_a = LuaTable({'名称': '天魔神甲', '分类': '装备', '子类': '衣服',
                            '附加': LuaTable({'套装属性': sA})})
    boots_a = LuaTable({'名称': '赤飞靴子', '分类': '装备', '子类': '鞋子',
                        '附加': LuaTable({'套装属性': sA})})

    # 2a. All three equipped with same enchant A -> 武器 active, 衣服 & 头盔 inactive
    bag.rawset(1, LuaTable({'道具': armor_a}))
    bag.rawset(2, LuaTable({'道具': helm_a}))
    bag.rawset(3, LuaTable({'道具': weapon_a}))
    bag.rawset(4, LuaTable({'道具': boots_a}))
    bag.rawset(35, LuaTable({'道具': bag_armor_a}))
    wr.rawget('套装属性')(3, 1)
    assert dict(h14_internal.rawget('stats')._data) == sum_sets(real_sets, [sA])

    tip_w, _ = disp.rawget('道具')(weapon_a, 1, 3)
    tip_a, _ = disp.rawget('道具')(armor_a, 1, 1)
    tip_h, _ = disp.rawget('道具')(helm_a, 1, 2)
    tip_bag_a, _ = disp.rawget('道具')(bag_armor_a, 1, 35)
    tip_boots, _ = disp.rawget('道具')(boots_a, 1, 4)
    assert_active_enchant(tip_w, sA)
    assert_duplicate_inactive_enchant(tip_a, sA)
    assert_duplicate_inactive_enchant(tip_h, sA)
    assert_active_enchant(tip_bag_a, sA)  # bag item stays active preview
    assert '#R附魔仅在武器/衣服/头盔生效#W' in tip_boots and '同名附魔不重复叠加' not in tip_boots

    # 2b. Unequipping 武器 (ev_type=2 on slot 3) immediately refreshes 衣服->active, 头盔->still duplicate!
    refresh_events.clear()
    rendered_tips.clear()
    box_tbl.rawget('Main')(2, 3, '屠龙')
    assert 1 in refresh_events and 2 in refresh_events, refresh_events
    assert_active_enchant(rendered_tips[1], sA)
    assert_duplicate_inactive_enchant(rendered_tips[2], sA)

    # Now actually remove 武器 from slot 3 and check 衣服(A) + 头盔(A)
    bag.rawset(3, LuaTable({'道具': None}))
    tip_a2, _ = disp.rawget('道具')(armor_a, 1, 1)
    tip_h2, _ = disp.rawget('道具')(helm_a, 1, 2)
    assert_active_enchant(tip_a2, sA)
    assert_duplicate_inactive_enchant(tip_h2, sA)

    # 2c. 武器(A) + 衣服(B) + 头盔(A) -> 武器 & 衣服 active, 头盔 inactive; stats = A + B
    armor_b = LuaTable({'名称': '赤龙宝甲_男', '分类': '装备', '子类': '衣服',
                        '附加': LuaTable({'套装属性': sB})})
    bag.rawset(3, LuaTable({'道具': weapon_a}))
    bag.rawset(1, LuaTable({'道具': armor_b}))
    wr.rawget('套装属性')(1, 1)
    assert dict(h14_internal.rawget('stats')._data) == sum_sets(real_sets, [sA, sB])
    assert_active_enchant(disp.rawget('道具')(weapon_a, 1, 3)[0], sA)
    assert_active_enchant(disp.rawget('道具')(armor_b, 1, 1)[0], sB)
    assert_duplicate_inactive_enchant(disp.rawget('道具')(helm_a, 1, 2)[0], sA)

    # 2d. Mercenary independent from Hero, and follows 武器 -> 衣服 -> 头盔
    merc_armor_a = LuaTable({'名称': '佣兵战甲', '分类': '装备', '子类': '衣服',
                             '附加': LuaTable({'套装属性': sA})})
    merc_helm_a = LuaTable({'名称': '佣兵头盔', '分类': '装备', '子类': '头盔',
                            '附加': LuaTable({'套装属性': sA})})
    bag.rawset(398, LuaTable({'道具': merc_armor_a}))
    bag.rawset(399, LuaTable({'道具': merc_helm_a}))
    # Hero wears 武器(A), Merc wears 衣服(A) + 头盔(A) -> Merc 衣服(A) MUST be active, Merc 头盔(A) inactive
    assert_active_enchant(disp.rawget('道具')(merc_armor_a, 1, 398)[0], sA)
    assert_duplicate_inactive_enchant(disp.rawget('道具')(merc_helm_a, 1, 399)[0], sA)
    # Equip Merc 武器(A) -> Merc 武器 active, Merc 衣服 & 头盔 both inactive
    merc_weapon_a = LuaTable({'名称': '佣兵利刃', '分类': '装备', '子类': '武器',
                              '附加': LuaTable({'套装属性': sA})})
    bag.rawset(397, LuaTable({'道具': merc_weapon_a}))
    box_tbl.rawget('Main')(1, 397, '佣兵利刃')
    assert_active_enchant(disp.rawget('道具')(merc_weapon_a, 1, 397)[0], sA)
    assert_duplicate_inactive_enchant(rendered_tips[398], sA)
    assert_duplicate_inactive_enchant(rendered_tips[399], sA)

    # 2e. Lifting 武器 onto Q_鼠标 also treats 武器 as absent when hovering 衣服
    bag.rawset(1, LuaTable({'道具': armor_a}))
    q_mouse.rawset('被占用', True)
    q_mouse.rawset('格子标识', 3)
    assert_active_enchant(disp.rawget('道具')(armor_a, 1, 1)[0], sA)
    q_mouse.rawset('被占用', False)
    q_mouse.rawset('格子标识', 0)

    # ------------------------------------------------------------------
    # 3. Overwrite Confirmation Dialog (including fresh UI display copy mode!)
    # ------------------------------------------------------------------
    fresh_copy_mode['on'] = True

    # 3a. Unenchanted item -> direct enchant without dialog
    plain_helm = LuaTable({'名称': '圣战头盔', '分类': '装备', '子类': '头盔', '附加': LuaTable()})
    scroll_b1 = LuaTable({'名称': '沃玛教主的利爪_图纸', '分类': '消耗', '子类': '消耗',
                          '附加': LuaTable({'套装属性': sB})})
    bag.rawset(2, LuaTable({'道具': plain_helm}))
    bag.rawset(40, LuaTable({'道具': scroll_b1}))
    G.rawset('鼠标道具', 40)
    asks.clear()
    ui_calls['orig_box_ev4'] = 0
    box_tbl.rawget('Main')(4, 2)
    assert len(asks) == 0, 'Unenchanted item must not open overwrite dialog'
    assert ui_calls['orig_box_ev4'] == 1
    assert plain_helm.rawget('附加').rawget('套装属性') == sB

    # 3b. Already-enchanted item -> releases Q_鼠标, opens dialog with exact prompt
    scroll_c = LuaTable({'名称': '骷髅教主的火种_图纸', '分类': '消耗', '子类': '消耗',
                         '附加': LuaTable({'套装属性': '骷髅教主的火种'})})
    bag.rawset(40, LuaTable({'道具': scroll_c}))
    G.rawset('鼠标道具', 40)
    q_mouse.rawset('被占用', True)
    q_mouse.rawset('格子标识', 40)
    mouse_src.rawset('拿起', True)
    asks.clear()
    ui_calls['orig_box_ev4'] = 0

    ret = box_tbl.rawget('Main')(4, 2)
    assert ret is True
    assert ui_calls['orig_box_ev4'] == 0, 'Must NOT immediately call orig_box before confirmation'
    assert q_mouse.rawget('被占用') is False and q_mouse.rawget('格子标识') == 0 and mouse_src.rawget('拿起') is False
    assert len(asks) == 1
    assert asks[0]['text'] == f'该装备已有【{sB}】的附魔。\n确认是否覆盖？', asks[0]['text']
    assert plain_helm.rawget('附加').rawget('套装属性') == sB
    assert bag.rawget(40).rawget('道具') is scroll_c

    # 3c. Already-open dialog guard
    prompts.clear()
    box_tbl.rawget('Main')(4, 2)
    assert len(asks) == 1
    assert prompts and prompts[-1][0] == '请先关闭当前提示窗口', prompts

    # 3d. Cancel leaves everything untouched, and late confirm is a no-op
    asks[0]['cancel']()
    dialog.rawset('可视', False)
    asks[0]['ok']()
    assert plain_helm.rawget('附加').rawget('套装属性') == sB
    assert bag.rawget(40).rawget('道具') is scroll_c

    # 3e. Confirm overwrites enchant, consumes scroll, recalculates Hero sets & refreshes sibling tooltips
    # Setup: Hero 武器(slot 3) has sA, Hero 衣服(slot 1) has sA (duplicate inactive!),
    # overwrite 武器(slot 3) with 骷髅教主的火种 -> 衣服(slot 1) MUST flip to active green!
    bag.rawset(1, LuaTable({'道具': armor_a}))
    bag.rawset(3, LuaTable({'道具': weapon_a}))
    bag.rawset(2, LuaTable({'道具': plain_helm}))
    bag.rawset(40, LuaTable({'道具': scroll_c}))
    G.rawset('鼠标道具', 40)
    asks.clear()
    reset_log.clear()
    refresh_events.clear()
    rendered_tips.clear()

    assert box_tbl.rawget('Main')(4, 3) is True
    assert len(asks) == 1
    assert asks[0]['text'] == f'该装备已有【{sA}】的附魔。\n确认是否覆盖？'
    asks[0]['ok']()
    dialog.rawset('可视', False)

    assert weapon_a.rawget('附加').rawget('套装属性') == '骷髅教主的火种'
    assert bag.rawget(40).rawget('道具') is None, 'Scroll must be consumed on confirm'
    assert reset_log == [(40, None)], reset_log
    assert dict(h14_internal.rawget('stats')._data) == sum_sets(real_sets, ['骷髅教主的火种', sA, sB])
    assert 3 in refresh_events and 1 in refresh_events, refresh_events
    assert_active_enchant(rendered_tips[3], '骷髅教主的火种')
    assert_active_enchant(rendered_tips[1], sA)

    # 3f. Stale/moved item guard: move scroll before confirm -> safely aborted with red prompt
    scroll_d = LuaTable({'名称': '毁灭之爪_图纸', '分类': '消耗', '子类': '消耗',
                         '附加': LuaTable({'套装属性': '毁灭之爪'})})
    bag.rawset(40, LuaTable({'道具': scroll_d}))
    G.rawset('鼠标道具', 40)
    asks.clear()
    prompts.clear()
    assert box_tbl.rawget('Main')(4, 3) is True
    assert len(asks) == 1
    # Player moves scroll away before clicking confirm
    bag.rawset(40, LuaTable({'道具': None}))
    asks[0]['ok']()
    dialog.rawset('可视', False)
    assert weapon_a.rawget('附加').rawget('套装属性') == '骷髅教主的火种'
    assert prompts and prompts[-1][0] == '装备或附魔卷位置已变化，请重新操作', prompts

    # ------------------------------------------------------------------
    # 4. 「前尘忆梦」 100% isolated
    # ------------------------------------------------------------------
    U.rawset('版本选择', '前尘忆梦')
    out_scroll_qc, _ = disp.rawget('道具')(scroll_a, 1, 40)
    assert '同名附魔不重复叠加' not in out_scroll_qc
    bag.rawset(40, LuaTable({'道具': scroll_d}))
    G.rawset('鼠标道具', 40)
    asks.clear()
    ui_calls['orig_box_ev4'] = 0
    box_tbl.rawget('Main')(4, 3)
    assert len(asks) == 0, '前尘忆梦 must not trigger overwrite dialog'
    assert ui_calls['orig_box_ev4'] == 1


def main():
    mods_o, rt_src = test_diff_syntax_and_m12_37()
    test_v337_enchant_rules_and_confirm(mods_o[12], rt_src)
    # Full regressions v1.336..v1.306
    test_v336_ordinary_materials_ground_white(rt_src)
    test_v336_corpse_drop_jipin_hardening(rt_src)
    test_v335_repeat_autocast_ux(rt_src)
    test_v334_mode2_qingtongfu_mofachangpao_non7(rt_src)
    test_v333_shared_weapon_tooltip_note(rt_src)
    test_v332_corpse_drop_jipin_stats(rt_src)
    test_v331_gem_tooltip_cache_refresh(rt_src)
    test_v330_split_bracelet_ring_gems(mods_o[12], rt_src)
    test_v328_weapon_armor_helmet_rules(mods_o[12], rt_src)
    test_real_boss_blueprint_drops_5_5pct(mods_o[12], rt_src)
    test_compact_equip_spaces_v317(rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v337.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.337',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v337.res': out_sha,
            'runtime_v337.lua': hashlib.sha256((W / 'runtime_v337.lua').read_bytes()).hexdigest(),
            'patch_v337.py': hashlib.sha256((W / 'patch_v337.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'm12_37_zero_jmp_below_params_preserved',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'v337_scroll_tooltip_appends_non_stack_note',
            'v337_duplicate_enchant_priority_weapon_armor_helmet_hero_and_merc',
            'v337_unequip_and_mouse_lift_immediately_flip_duplicate_tooltip',
            'v337_overwrite_confirm_dialog_ok_cancel_stale_open_and_fresh_copy',
            'v337_qianchi_isolated',
            'v336_v335_v334_v333_v332_v331_v330_v328_v319_v317_v308_v307_v306_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v337.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v337.json').write_text(text, encoding='utf-8')
    print('ALL v1.337 TESTS PASSED!')


if __name__ == '__main__':
    main()
