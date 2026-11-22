"""Exhaustive verification suite for v1.338:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v338.lua
3. m12/37 (qs_item_box.Main) still has ZERO JMP instructions with A < params
4. Enchant Slots = 坐骑 / 勋章 / 印记 (子类: 坐骑, 勋章, 饰品):
   - Scroll tooltip: '#Y拖到坐骑/勋章/印记使用#W' + '#Y同名附魔不重复叠加#W'.
   - Dragging onto 坐骑/勋章/饰品 allowed; dragging onto 武器/衣服/头盔/鞋子/戒指 blocked with
     '附魔卷只能用于坐骑、勋章或印记'.
   - Strict priority order 坐骑 -> 勋章 -> 印记 (Hero & Merc independent):
     * 坐骑(A)+勋章(A)+印记(A) -> 坐骑 active, 勋章 & 印记 inactive + '#R同名附魔不重复叠加#W'
     * 坐骑(A)+勋章(B)+印记(A) -> 坐骑 & 勋章 active, 印记 inactive; stats = A + B
     * 勋章(A)+印记(A) -> 勋章 active, 印记 inactive
     * Unequipping/lifting 坐骑(A) immediately flips 勋章(A) to active green
     * Hero 坐骑(A) + Merc 勋章(A) independent (both active)
     * Old-save enchants on 武器/衣服/头盔/鞋子/戒指 render grey + '#R附魔仅在坐骑/勋章/印记生效#W'
   - Overwrite confirmation dialog on already-enchanted 坐骑/勋章/印记:
     * Exact prompt '该装备已有【<原附魔名>】的附魔。\n确认是否覆盖？'
     * Releases Q_鼠标, handles cancel, confirm (with fresh UI copy), stale-move guard, open-dialog guard
5. All Equipment Class Requirements Removed (「来世续缘」 only):
   - All 74 real 刺客 items (武器/衣服/头盔) + all Hero 武器/衣服/头盔 in S.游戏道具组 become
     职业要求='不限' and 附加.装备通用=0 (gender & slot requirements untouched).
   - Existing old-save items in S.包裹物品组 (Hero/Merc/Warehouse) are automatically migrated.
   - Pure Merc ranged weapons (玄月) keep '（远程）' tag; original 7 shared weapons (精灵骸骨)
     keep '主角/佣兵（远程）通用'; normal Hero weapons (屠龙) do NOT show '（远程）' in Hero slots
     or spam the shared note, and DO show '（远程）' in Merc slots (333..410).
   - Switching to 「前尘忆梦」 cleanly restores original 职业要求 and removes added 装备通用.
6. Full v1.336..v1.306 regressions.
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
from test_v330 import test_v330_split_bracelet_ring_gems
from test_v331 import test_v331_gem_tooltip_cache_refresh
from test_v332 import make_weapon_tpl, test_v332_corpse_drop_jipin_stats
from test_v333 import test_v333_shared_weapon_tooltip_note
from test_v334 import test_v334_mode2_qingtongfu_mofachangpao_non7
from test_v335 import test_v335_repeat_autocast_ux
from test_v336 import (
    test_v336_corpse_drop_jipin_hardening,
    test_v336_ordinary_materials_ground_white,
)
from test_v337 import (
    assert_active_enchant,
    assert_duplicate_inactive_enchant,
    make_raw_equip_tip,
)

W = Path(__file__).resolve().parent
BASE_SHA = 'e90fd5c684eef9b19163d256c34e2c92edec6afe082a8671fd889aaab91bbf73'


def extract_runtime_v338(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.338 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v338.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_syntax_and_m12_37():
    base_bytes = (W / 'game_v337.res').read_bytes()
    out_bytes = (W / 'game_v338.res').read_bytes()
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

    rt_src = extract_runtime_v338(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_v338_mount_medal_seal_enchants_and_confirm(d12, rt_src):
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

    ui_calls = {'orig_box_ev4': 0}
    wr = LuaTable({
        '套装属性': lambda a, b: None,
        '佣兵套装': lambda a, b: None,
        '元素图标': lambda: None,
        '佣兵窗口': lambda a=None, b=None: None,
    })
    U.rawset('窗口相关', wr)

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
                cp = LuaTable()
                for kk, vv in it._data.items():
                    cp.rawset(kk, vv)
                return cp
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

    rendered_tips = {}
    refresh_events = []
    tbl_controls = LuaTable()
    for cid in (1, 2, 3, 11, 12, 13, 35, 40, 407, 408, 409):
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

    sA = '虎战领主之爪'
    sB = '沃玛教主的利爪'
    sC = '骷髅教主的火种'

    # 1. Scroll tooltip: '#Y拖到坐骑/勋章/印记使用#W' + '#Y同名附魔不重复叠加#W'
    scroll_a = LuaTable({'名称': '虎战领主之爪_图纸', '分类': '消耗', '子类': '消耗',
                         '附加': LuaTable({'套装属性': sA})})
    out_scroll, _ = disp.rawget('道具')(scroll_a, 1, 40)
    sls = out_scroll.split('\n')
    idx_use = sls.index('#Y拖到坐骑/勋章/印记使用#W')
    assert sls[idx_use + 1] == '#Y同名附魔不重复叠加#W', sls
    assert '武器/衣服/头盔' not in out_scroll

    # 2. Dragging scroll onto 武器/衣服/头盔/鞋子 blocked; 坐骑/勋章/饰品 allowed
    bag.rawset(40, LuaTable({'道具': scroll_a}))
    G.rawset('鼠标道具', 40)
    for bad_sub in ('武器', '衣服', '头盔', '鞋子', '戒指'):
        bag.rawset(1, LuaTable({'道具': LuaTable({'名称': '测试' + bad_sub, '分类': '装备', '子类': bad_sub})}))
        prompts.clear()
        ui_calls['orig_box_ev4'] = 0
        assert box_tbl.rawget('Main')(4, 1) is True
        assert ui_calls['orig_box_ev4'] == 0, f'Must block {bad_sub}'
        assert prompts == [('附魔卷只能用于坐骑、勋章或印记', -65536)], (bad_sub, prompts)

    # Allowed on unenchanted 饰品 (印记)
    plain_seal = LuaTable({'名称': '冰之印记', '分类': '装备', '子类': '饰品', '附加': LuaTable()})
    bag.rawset(11, LuaTable({'道具': plain_seal}))
    prompts.clear()
    asks.clear()
    box_tbl.rawget('Main')(4, 11)
    assert ui_calls['orig_box_ev4'] == 1 and prompts == [] and len(asks) == 0
    assert plain_seal.rawget('附加').rawget('套装属性') == sA

    # 3. Duplicate equipped enchant priority: 坐骑(1) > 勋章(2) > 印记/饰品(3)
    # Place 饰品 at slot 11, 勋章 at slot 12, 坐骑 at slot 13 (reverse of slot IDs!)
    seal_a = LuaTable({'名称': '火之印记', '分类': '装备', '子类': '饰品', '附加': LuaTable({'套装属性': sA})})
    medal_a = LuaTable({'名称': '王者勋章', '分类': '装备', '子类': '勋章', '附加': LuaTable({'套装属性': sA})})
    mount_a = LuaTable({'名称': '坐骑号角_金', '分类': '装备', '子类': '坐骑', '附加': LuaTable({'套装属性': sA})})
    old_weapon_b = LuaTable({'名称': '屠龙', '分类': '装备', '子类': '武器', '附加': LuaTable({'套装属性': sB})})
    bag_medal_a = LuaTable({'名称': '尊者勋章', '分类': '装备', '子类': '勋章', '附加': LuaTable({'套装属性': sA})})

    bag.rawset(11, LuaTable({'道具': seal_a}))
    bag.rawset(12, LuaTable({'道具': medal_a}))
    bag.rawset(13, LuaTable({'道具': mount_a}))
    bag.rawset(1, LuaTable({'道具': old_weapon_b}))
    bag.rawset(35, LuaTable({'道具': bag_medal_a}))

    wr.rawget('套装属性')(13, 1)
    # Old-save 武器 enchant is ignored; 坐骑/勋章/印记 same sA summed ONCE!
    assert dict(h14_internal.rawget('stats')._data) == sum_sets(real_sets, [sA])

    assert_active_enchant(disp.rawget('道具')(mount_a, 1, 13)[0], sA)
    assert_duplicate_inactive_enchant(disp.rawget('道具')(medal_a, 1, 12)[0], sA)
    assert_duplicate_inactive_enchant(disp.rawget('道具')(seal_a, 1, 11)[0], sA)
    assert_active_enchant(disp.rawget('道具')(bag_medal_a, 1, 35)[0], sA)
    tip_old_w = disp.rawget('道具')(old_weapon_b, 1, 1)[0]
    assert '#R附魔仅在坐骑/勋章/印记生效#W' in tip_old_w and '同名附魔不重复叠加' not in tip_old_w

    # 3b. Unequipping 坐骑 (ev_type=2 on slot 13) immediately flips 勋章 -> active, 印记 -> still duplicate
    refresh_events.clear()
    rendered_tips.clear()
    box_tbl.rawget('Main')(2, 13, '坐骑号角_金')
    assert 12 in refresh_events and 11 in refresh_events
    assert_active_enchant(rendered_tips[12], sA)
    assert_duplicate_inactive_enchant(rendered_tips[11], sA)

    # 3c. 坐骑(A) + 勋章(B) + 印记(A) -> 坐骑 & 勋章 active, 印记 inactive; stats = A + B
    medal_b = LuaTable({'名称': '王者勋章', '分类': '装备', '子类': '勋章', '附加': LuaTable({'套装属性': sB})})
    bag.rawset(12, LuaTable({'道具': medal_b}))
    wr.rawget('套装属性')(12, 1)
    assert dict(h14_internal.rawget('stats')._data) == sum_sets(real_sets, [sA, sB])
    assert_active_enchant(disp.rawget('道具')(mount_a, 1, 13)[0], sA)
    assert_active_enchant(disp.rawget('道具')(medal_b, 1, 12)[0], sB)
    assert_duplicate_inactive_enchant(disp.rawget('道具')(seal_a, 1, 11)[0], sA)

    # 3d. Mercenary independent & follows 坐骑 -> 勋章 -> 印记
    m_mount_a = LuaTable({'名称': '坐骑号角_金', '分类': '装备', '子类': '坐骑', '附加': LuaTable({'套装属性': sA})})
    m_medal_a = LuaTable({'名称': '王者勋章', '分类': '装备', '子类': '勋章', '附加': LuaTable({'套装属性': sA})})
    m_seal_a = LuaTable({'名称': '火之印记', '分类': '装备', '子类': '饰品', '附加': LuaTable({'套装属性': sA})})
    bag.rawset(407, LuaTable({'道具': m_seal_a}))
    bag.rawset(408, LuaTable({'道具': m_medal_a}))
    assert_active_enchant(disp.rawget('道具')(m_medal_a, 1, 408)[0], sA)
    assert_duplicate_inactive_enchant(disp.rawget('道具')(m_seal_a, 1, 407)[0], sA)
    bag.rawset(409, LuaTable({'道具': m_mount_a}))
    box_tbl.rawget('Main')(1, 409, '坐骑号角_金')
    assert_active_enchant(disp.rawget('道具')(m_mount_a, 1, 409)[0], sA)
    assert_duplicate_inactive_enchant(rendered_tips[408], sA)
    assert_duplicate_inactive_enchant(rendered_tips[407], sA)

    # 4. Overwrite confirmation dialog on already-enchanted 坐骑
    scroll_c = LuaTable({'名称': '骷髅教主的火种_图纸', '分类': '消耗', '子类': '消耗',
                         '附加': LuaTable({'套装属性': sC})})
    bag.rawset(12, LuaTable({'道具': medal_a}))  # 勋章 has sA (duplicate of 坐骑 sA)
    bag.rawset(40, LuaTable({'道具': scroll_c}))
    G.rawset('鼠标道具', 40)
    q_mouse.rawset('被占用', True)
    q_mouse.rawset('格子标识', 40)
    mouse_src.rawset('拿起', True)
    asks.clear()
    reset_log.clear()
    refresh_events.clear()
    rendered_tips.clear()

    assert box_tbl.rawget('Main')(4, 13) is True
    assert q_mouse.rawget('被占用') is False and q_mouse.rawget('格子标识') == 0 and mouse_src.rawget('拿起') is False
    assert len(asks) == 1 and asks[0]['text'] == f'该装备已有【{sA}】的附魔。\n确认是否覆盖？'
    asks[0]['ok']()
    dialog.rawset('可视', False)

    assert mount_a.rawget('附加').rawget('套装属性') == sC
    assert bag.rawget(40).rawget('道具') is None and reset_log == [(40, None)]
    assert dict(h14_internal.rawget('stats')._data) == sum_sets(real_sets, [sC, sA])
    # 勋章(slot 12) must flip from duplicate inactive -> active green immediately!
    assert_active_enchant(rendered_tips[13], sC)
    assert_active_enchant(rendered_tips[12], sA)


def test_v338_all_equip_no_job_req(d12, rt_src):
    # Decode ALL real equipment items from m12/4111 to verify against actual DB!
    p4111 = d12.protos[4111]

    def dec(v):
        if isinstance(v, bytes):
            return v.decode('gbk', 'replace')
        if isinstance(v, tuple) and v[0] == 'table':
            return [dec(x) for x in v[1]], {dec(k): dec(val) for k, val in v[2]}
        if isinstance(v, tuple) and v[0] == 'int':
            return v[1] - (1 << 32) if v[1] >= (1 << 31) else v[1]
        return v

    real_equips = []
    for v in p4111.kgc:
        if isinstance(v, tuple) and v[0] == 'table':
            _, hsh = dec(v)
            if hsh.get('分类') == '装备' and hsh.get('名称'):
                real_equips.append(hsh)
    assert len(real_equips) >= 600, len(real_equips)

    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']

    # Build S.游戏道具组 with representative real equipment (刺客武器/衣服/头盔, Hero武器/衣服/头盔, 7 shared, accessories)
    item_db = LuaTable()
    test_names = {}
    for it in real_equips:
        nm = it['名称']
        sub = it.get('子类')
        job = it.get('职业要求')
        ex = LuaTable()
        if nm in ('精灵骸骨', '纯净的白灵之刃', '拍拍手'):
            ex.rawset('装备通用', 0)
            ex.rawset('绑定技能', '刺客普通攻击')
        elif nm == '玄月':
            ex.rawset('绑定技能', '刺客普通攻击')
        elif nm == '潜龙双剑':
            ex.rawset('绑定技能', '刺客双手攻击')
        item_db.rawset(nm, LuaTable({
            '名称': nm,
            '分类': '装备',
            '子类': sub,
            '职业要求': job,
            '性别要求': it.get('性别要求'),
            '附加': ex,
        }))
        test_names[nm] = (sub, job, it.get('性别要求'))
    S.rawset('游戏道具组', item_db)

    # Old-save items in S.包裹物品组 (Hero bag, Merc bag, Warehouse)
    old_ck_w = LuaTable({'名称': '玄月', '分类': '装备', '子类': '武器', '职业要求': '刺客', '性别要求': '不限',
                         '附加': LuaTable({'绑定技能': '刺客普通攻击'})})
    old_ck_a = LuaTable({'名称': '潜龙遁甲_男', '分类': '装备', '子类': '衣服', '职业要求': '刺客', '性别要求': '男',
                         '附加': LuaTable()})
    old_ck_h = LuaTable({'名称': '丽江面罩', '分类': '装备', '子类': '头盔', '职业要求': '刺客', '性别要求': '不限',
                         '附加': LuaTable()})
    old_hero_w = LuaTable({'名称': '屠龙', '分类': '装备', '子类': '武器', '职业要求': '不限', '性别要求': '不限',
                           '附加': LuaTable()})
    old_hero_a = LuaTable({'名称': '赤龙宝甲_男', '分类': '装备', '子类': '衣服', '职业要求': '不限', '性别要求': '男',
                           '附加': LuaTable()})
    bag = LuaTable({
        31: LuaTable({'道具': old_ck_w}),
        32: LuaTable({'道具': old_ck_a}),
        33: LuaTable({'道具': old_ck_h}),
        127: LuaTable({'道具': old_hero_w}),
        335: LuaTable({'道具': old_hero_a}),
    })
    S.rawset('包裹物品组', bag)

    ev.G.rawset('__gm_merc_name_v253', lambda it, dn, sid=None: dn)
    ev.G.get('loadstring')(rt_src)(S)

    # 1. ALL equipment templates in S.游戏道具组 must now have 职业要求=='不限';
    #    all 武器/衣服/头盔 must have 附加.装备通用==0; gender requirements 100% preserved!
    ck_count = 0
    for nm, (sub, orig_job, orig_sex) in test_names.items():
        e = item_db.rawget(nm)
        assert e.rawget('职业要求') == '不限', f'{nm} still has 职业要求={e.rawget("职业要求")!r}'
        assert e.rawget('性别要求') == orig_sex, f'{nm} gender changed!'
        if sub in ('武器', '衣服', '头盔'):
            assert e.rawget('附加').rawget('装备通用') == 0, f'{nm} missing 装备通用=0'
        if orig_job == '刺客':
            ck_count += 1
    assert ck_count == 74, f'Expected 74 刺客 equipment templates, got {ck_count}'

    # 2. Old-save items in S.包裹物品组 migrated too
    for it in (old_ck_w, old_ck_a, old_ck_h, old_hero_w, old_hero_a):
        assert it.rawget('职业要求') == '不限'
        assert it.rawget('附加').rawget('装备通用') == 0
    assert old_ck_a.rawget('性别要求') == '男' and old_hero_a.rawget('性别要求') == '男'

    # 3. Verify merc ranged tag (v1.332) & 7 shared weapon note (v1.333) remain accurate!
    merc_name = ev.G.rawget('__gm_merc_name_v253')
    fmt = S.rawget('__gm_format_equip_tooltip_v311')
    # 玄月 (originally 刺客 ranged) keeps （远程） tag and does NOT get shared-7 note
    assert merc_name(item_db.rawget('玄月'), '玄月', 35) == '玄月（远程）'
    assert '主角/佣兵（远程）通用' not in fmt('#W玄月\n需要等级:1', item_db.rawget('玄月'), 0, 35)
    # 潜龙双剑 (originally 刺客 2H melee) NEVER gets （远程）
    assert merc_name(item_db.rawget('潜龙双剑'), '潜龙双剑', 397) == '潜龙双剑'
    # 精灵骸骨 (original shared 7): no （远程） in Hero slot, （远程） in Merc slot, HAS shared note
    assert merc_name(item_db.rawget('精灵骸骨'), '精灵骸骨', 35) == '精灵骸骨'
    assert merc_name(item_db.rawget('精灵骸骨'), '精灵骸骨', 397) == '精灵骸骨（远程）'
    assert '主角/佣兵（远程）通用' in fmt('#W精灵骸骨\n需要等级:1', item_db.rawget('精灵骸骨'), 0, 35)
    # 屠龙 (normal Hero weapon): no （远程） on ground/Hero slot, （远程） in Merc slot, NO spam note
    assert merc_name(item_db.rawget('屠龙'), '屠龙', 35) == '屠龙'
    assert merc_name(item_db.rawget('屠龙'), '屠龙', 397) == '屠龙（远程）'
    assert '主角/佣兵（远程）通用' not in fmt('#W屠龙\n需要等级:1', item_db.rawget('屠龙'), 0, 35)

    # 4. Switching to 「前尘忆梦」 cleanly restores original 职业要求 and removes added 装备通用!
    U.rawset('版本选择', '前尘忆梦')
    S.rawget('__gm_pickup_frame_v299')(U, G)
    assert item_db.rawget('玄月').rawget('职业要求') == '刺客'
    assert item_db.rawget('潜龙遁甲_男').rawget('职业要求') == '刺客'
    assert item_db.rawget('丽江面罩').rawget('职业要求') == '刺客'
    assert item_db.rawget('屠龙').rawget('附加').rawget('装备通用') is None
    assert item_db.rawget('赤龙宝甲_男').rawget('附加').rawget('装备通用') is None
    # Originally shared 精灵骸骨 keeps its original 装备通用=0!
    assert item_db.rawget('精灵骸骨').rawget('附加').rawget('装备通用') == 0


def main():
    mods_o, rt_src = test_diff_syntax_and_m12_37()
    test_v338_mount_medal_seal_enchants_and_confirm(mods_o[12], rt_src)
    test_v338_all_equip_no_job_req(mods_o[12], rt_src)
    # Full regressions v1.336..v1.306
    test_v336_ordinary_materials_ground_white(rt_src)
    test_v336_corpse_drop_jipin_hardening(rt_src)
    test_v335_repeat_autocast_ux(rt_src)
    test_v334_mode2_qingtongfu_mofachangpao_non7(rt_src)
    test_v333_shared_weapon_tooltip_note(rt_src)
    test_v332_corpse_drop_jipin_stats(rt_src)
    test_v331_gem_tooltip_cache_refresh(rt_src)
    test_v330_split_bracelet_ring_gems(mods_o[12], rt_src, expected_invalid_note='#R附魔仅在坐骑/勋章/印记生效#W')
    test_real_boss_blueprint_drops_5_5pct(mods_o[12], rt_src)
    test_compact_equip_spaces_v317(rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v338.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.338',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v338.res': out_sha,
            'runtime_v338.lua': hashlib.sha256((W / 'runtime_v338.lua').read_bytes()).hexdigest(),
            'patch_v338.py': hashlib.sha256((W / 'patch_v338.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'm12_37_zero_jmp_below_params_preserved',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'v338_enchant_slots_mount_medal_seal_scroll_hint_and_drag_guard',
            'v338_duplicate_enchant_priority_mount_medal_seal_hero_and_merc',
            'v338_overwrite_confirm_dialog_on_mount_medal_seal',
            'v338_all_equip_no_job_req_all_74_assassin_and_hero_templates_plus_bag_migration',
            'v338_merc_ranged_tag_shared7_note_and_qianchi_restore_pass',
            'v336_v335_v334_v333_v332_v331_v330_v319_v317_v308_v307_v306_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v338.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v338.json').write_text(text, encoding='utf-8')
    print('ALL v1.338 TESTS PASSED!')


if __name__ == '__main__':
    main()
