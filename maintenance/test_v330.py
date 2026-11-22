"""Exhaustive verification suite for v1.330:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v330.lua
3. m12/37 (qs_item_box.Main) still has ZERO JMP instructions with A < params (v1.325 fix preserved)
4. Left/right bracelet & left/right ring independent gem socketing for BOTH Hero and Mercenary:
   - Old save migration: old 手镯/戒指 sockets & gems moved to 左手镯/左戒指; 右手镯/右戒指 fresh locked {0,0,0,0,0};
     old 手镯/戒指 cleared; idempotent on already-migrated saves.
   - Right-click (ev_type=3) on Hero 5/6/7/8 opens 宝石窗口 with titles 左手镯/右手镯/左戒指/右戒指宝石镶嵌 and
     populates slots 327..331 independently; right-click on Hero 1 (武器) delegates to orig_box.
   - Right-click (ev_type=3) on Merc 401/402/403/404 opens 佣兵窗口('宝石', true) with independent titles and
     populates slots 411..415 independently, returning True.
   - Stat recalculation (宝石属性 -> 物品格子332, 佣兵宝石 -> 物品格子416) sums ALL 11 parts using correct
     暴食模块 category (首饰 for all 4 split keys, NOT 武器!), applies 专升/佣兵专升 multiplier, ignores
     non-part guild fields (名称/血条/缴纳/佳能).
   - Equipment tooltips show ONLY the hovered slot's own side gems (slot 5 vs 6, 7 vs 8, 401 vs 402, 403 vs 404)
     under '#f(宋_9_炭灰,#c(-22312)镶嵌属性#W)' right before 附魔属性; empty right slot shows NO 镶嵌属性;
     bag bracelet/ring shows NO 镶嵌属性.
   - 「前尘忆梦」 complete isolation: guild tables untouched, original callbacks & raw tooltips preserved.
5. Full regressions (v1.329 warm-gold affixes, v1.328 武器/衣服/头盔, v1.325, v1.319 5.5% Boss drops, v1.317, v1.308, v1.307, v1.306).
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

W = Path(__file__).resolve().parent
BASE_SHA = '6e43c1c991eeef054f6ab836a6051a37676fa878547c022abf94cdf2556aa86c'


def extract_runtime_v330(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.330 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v330.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_syntax_and_m12_37():
    base_bytes = (W / 'game_v329.res').read_bytes()
    out_bytes = (W / 'game_v330.res').read_bytes()
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

    rt_src = extract_runtime_v330(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def make_gem_slot_cell():
    state = {'locked': None, 'reset_args': None}
    cell = LuaTable()

    def reset_fn(a=None, b=None, c=None, d=None):
        state['reset_args'] = (a, b, c, d._data if isinstance(d, LuaTable) else d)

    cell.rawset('重置道具', reset_fn)
    cell.rawset('禁止拖放', False)
    return cell, state


def test_v330_split_bracelet_ring_gems(d12, rt_src, expected_invalid_note='#R附魔仅在武器/衣服/头盔生效#W'):
    real_sets = decode_real_sets_full_143(d12)
    real_tpls = decode_real_blueprint_templates(d12)

    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']

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

    # Faithful 暴食模块 tables: note 武器 vs 防具 vs 首饰 map the SAME gem to DIFFERENT stats!
    bs_tbl = LuaTable({
        '武器': LuaTable({
            '完美的红宝石': LuaTable({1: '最小破坏', 2: '最小破坏', 3: 12}),
            '完美的绿宝石': LuaTable({1: '准确几率', 2: '准确', 3: 20}),
        }),
        '防具': LuaTable({
            '完美的红宝石': LuaTable({1: '最大防御', 2: '最大防御力', 3: 12}),
            '完美的蓝宝石': LuaTable({1: '最大魔防', 2: '最大魔法防御', 3: 12}),
        }),
        '首饰': LuaTable({
            '完美的红宝石': LuaTable({1: '最大破坏', 2: '最大破坏', 3: 6}),
            '完美的绿宝石': LuaTable({1: '准确几率', 2: '准确', 3: 30}),
            '完美的紫宝石': LuaTable({1: '生命值', 2: '生命值上限', 3: 30}),
            '完美的蓝宝石': LuaTable({1: '法力值', 2: '魔法值上限', 3: 30}),
        }),
    })
    U.rawset('暴食模块', lambda: bs_tbl)

    # Old-save guild data (Hero + Merc) with legacy shared 手镯/戒指 + non-part guild metadata
    save_data = LuaTable({
        '专升': LuaTable({1: 6}),       # Hero mult = 1 + 6/6 = 2.0
        '佣兵专升': LuaTable({1: 3}),   # Merc mult = 1 + 3/6 = 1.5
        '行会': LuaTable({
            '名称': '测试行会',
            '血条': LuaTable({1: 100}),
            '缴纳': LuaTable({1: 50}),
            '佳能': LuaTable({1: 1}),
            '武器': LuaTable({1: '完美的红宝石', 2: 1, 3: 0, 4: 0, 5: 0}),
            '衣服': LuaTable({1: '完美的蓝宝石', 2: 0, 3: 0, 4: 0, 5: 0}),
            '手镯': LuaTable({1: '完美的红宝石', 2: '完美的绿宝石', 3: 1, 4: 0, 5: 0}),
            '戒指': LuaTable({1: '完美的紫宝石', 2: 0, 3: 0, 4: 0, 5: 0}),
        }),
        '佣兵行会': LuaTable({
            '武器': LuaTable({1: '完美的绿宝石', 2: 0, 3: 0, 4: 0, 5: 0}),
            '手镯': LuaTable({1: '完美的紫宝石', 2: 1, 3: 0, 4: 0, 5: 0}),
            '戒指': LuaTable({1: '完美的红宝石', 2: 0, 3: 0, 4: 0, 5: 0}),
        }),
    })
    U.rawset('啾啾啵啵', lambda: save_data)

    raw_tips = {}
    disp = LuaTable({
        '道具': lambda item, mode, slot_id: (raw_tips[(item.rawget('名称'), slot_id)], None),
        '屏幕提示': lambda m, c=None: None,
    })
    U.rawset('托管显示', disp)

    calls = {'orig_hero_gem': 0, 'orig_merc_gem': 0, 'orig_box_rclick': 0, 'hero_win_open': 0, 'merc_win_open': []}
    wr = LuaTable({
        '套装属性': lambda a, b: None,
        '佣兵套装': lambda a, b: None,
        '元素图标': lambda: None,
        '佣兵窗口': lambda tab=None, show=None: calls['merc_win_open'].append((tab, show)),
        '宝石属性': lambda: calls.__setitem__('orig_hero_gem', calls['orig_hero_gem'] + 1),
        '佣兵宝石': lambda: calls.__setitem__('orig_merc_gem', calls['orig_merc_gem'] + 1),
    })
    U.rawset('窗口相关', wr)

    # Gem UI cells 327..331 (Hero) and 411..415 (Merc) + hidden stat cells 332 and 416
    cells = {}
    cell_states = {}
    for cid in list(range(327, 332)) + list(range(411, 416)):
        c, st = make_gem_slot_cell()
        cells[cid] = c
        cell_states[cid] = st

    # Equipped bracelets & rings on Hero (5,6,7,8) and Merc (401,402,403,404)
    for sid, nm, sub in (
        (1, '血花落照', '武器'),
        (5, '金手镯左', '手镯'), (6, '金手镯右', '手镯'),
        (7, '巨龙戒指左', '戒指'), (8, '巨龙戒指右', '戒指'),
        (401, '佣兵手镯左', '手镯'), (402, '佣兵手镯右', '手镯'),
        (403, '佣兵戒指左', '戒指'), (404, '佣兵戒指右', '戒指'),
    ):
        bag.rawset(sid, LuaTable({'道具': LuaTable({'名称': nm, '分类': '装备', '子类': sub})}))
        cells[sid] = bag.rawget(sid)

    G.rawset('从ID取格子', lambda sid: cells.get(sid) or bag.rawget(sid))
    G.rawset('鼠标道具', 0)

    def orig_box(ev_type, slot_id, a3=None, a4=None, a5=None):
        if ev_type == 3:
            calls['orig_box_rclick'] += 1
            return 'orig_rclick'
        return None

    lua_tostring = ev.G.get('tostring')
    shelp = LuaTable()
    shelp.rawset(lua_tostring(orig_box), LuaTable({'msg': '【全局事件/物品格子】', 'fname': 'Main', 'sid': 5}))
    S.rawset('shelp', shelp)
    box_tbl = LuaTable({'Main': orig_box})
    S.rawset('tbl_qs', LuaTable({'qs_item_box': box_tbl}))

    hidden332, st332 = make_gem_slot_cell()
    hidden416, st416 = make_gem_slot_cell()
    gem_win = LuaTable({'打开': lambda: calls.__setitem__('hero_win_open', calls['hero_win_open'] + 1)})
    hero_lbl = LuaTable({'标题': ''})
    merc_lbl = LuaTable({'标题': ''})

    h14_internal, h14_proxy = make_slot_proxy(ev)
    m410_internal, m410_proxy = make_slot_proxy(ev)
    ss = S.rawget('script_setting')
    ss.rawset('Gly独', G)
    ss.rawset('物品格子14', h14_proxy)
    ss.rawset('物品格子410', m410_proxy)
    ss.rawset('物品格子332', hidden332)
    ss.rawset('物品格子416', hidden416)
    ss.rawset('宝石窗口', gem_win)
    ss.rawset('宝石标签', hero_lbl)
    ss.rawset('佣兵宝石标签', merc_lbl)

    # Load runtime_v330.lua -> automatically wraps & runs initial migration + recalc!
    ev.G.get('loadstring')(rt_src)(S)

    # 1. Verify old-save migration (Hero + Merc)
    hg = save_data.rawget('行会')
    mg = save_data.rawget('佣兵行会')
    assert hg.rawget('手镯') is None and hg.rawget('戒指') is None
    assert mg.rawget('手镯') is None and mg.rawget('戒指') is None
    assert [hg.rawget('左手镯').rawget(i) for i in range(1, 6)] == ['完美的红宝石', '完美的绿宝石', 1, 0, 0]
    assert [hg.rawget('右手镯').rawget(i) for i in range(1, 6)] == [0, 0, 0, 0, 0]
    assert [hg.rawget('左戒指').rawget(i) for i in range(1, 6)] == ['完美的紫宝石', 0, 0, 0, 0]
    assert [hg.rawget('右戒指').rawget(i) for i in range(1, 6)] == [0, 0, 0, 0, 0]
    assert [mg.rawget('左手镯').rawget(i) for i in range(1, 6)] == ['完美的紫宝石', 1, 0, 0, 0]
    assert [mg.rawget('右手镯').rawget(i) for i in range(1, 6)] == [0, 0, 0, 0, 0]
    assert [mg.rawget('左戒指').rawget(i) for i in range(1, 6)] == ['完美的红宝石', 0, 0, 0, 0]
    assert [mg.rawget('右戒指').rawget(i) for i in range(1, 6)] == [0, 0, 0, 0, 0]

    # 2. Verify initial stat calculation on 332 (mult=2.0) and 416 (mult=1.5)
    # Hero: 武器(最小破坏 12) + 衣服(最大魔防 12) + 左手镯(最大破坏 6, 准确几率 30) + 左戒指(生命值 30) all * 2.0
    assert st332['reset_args'][0] == '背包格子'
    assert st332['reset_args'][3] == {'最小破坏': 24.0, '最大魔防': 24.0, '最大破坏': 12.0, '准确几率': 60.0, '生命值': 60.0}, st332['reset_args']
    # Merc: 武器(准确几率 20) + 左手镯(生命值 30) + 左戒指(最大破坏 6) all * 1.5
    assert st416['reset_args'][3] == {'准确几率': 30.0, '生命值': 45.0, '最大破坏': 9.0}, st416['reset_args']

    # 3. Socket new gems on RIGHT bracelet & RIGHT ring (Hero + Merc) and verify BOTH sides sum independently!
    hg.rawget('右手镯').rawset(1, '完美的蓝宝石')  # 首饰: 法力值 +30 -> *2 = 60
    hg.rawget('右戒指').rawset(1, '完美的红宝石')  # 首饰: 最大破坏 +6 -> *2 = 12 (total 最大破坏 = 24)
    mg.rawget('右手镯').rawset(1, '完美的绿宝石')  # 首饰: 准确几率 +30 -> *1.5 = 45 (total 准确几率 = 75)
    mg.rawget('右戒指').rawset(1, '完美的蓝宝石')  # 首饰: 法力值 +30 -> *1.5 = 45
    wr.rawget('宝石属性')()
    wr.rawget('佣兵宝石')()
    assert st332['reset_args'][3] == {'最小破坏': 24.0, '最大魔防': 24.0, '最大破坏': 24.0, '准确几率': 60.0, '生命值': 60.0, '法力值': 60.0}, st332['reset_args']
    assert st416['reset_args'][3] == {'准确几率': 75.0, '生命值': 45.0, '最大破坏': 9.0, '法力值': 45.0}, st416['reset_args']

    # 4. Verify right-click opening gem window for Hero 5/6/7/8, Merc 401/402/403/404, and passthrough for slot 1
    assert box_tbl.rawget('Main')(3, 5) is None
    assert calls['hero_win_open'] == 1
    assert hero_lbl.rawget('标题') == '左手镯宝石镶嵌'
    assert cell_states[327]['reset_args'] == ('完美的红宝石', 1, False, None) and cells[327].rawget('禁止拖放') is False
    assert cell_states[328]['reset_args'] == ('完美的绿宝石', 1, False, None) and cells[328].rawget('禁止拖放') is False
    assert cell_states[329]['reset_args'] == (None, None, None, None) and cells[329].rawget('禁止拖放') is False
    assert cell_states[330]['reset_args'] == ('背包格子', 1, False, {'显示名': '宝石格子'}) and cells[330].rawget('禁止拖放') is True

    assert box_tbl.rawget('Main')(3, 6) is None
    assert hero_lbl.rawget('标题') == '右手镯宝石镶嵌'
    assert cell_states[327]['reset_args'] == ('完美的蓝宝石', 1, False, None) and cells[327].rawget('禁止拖放') is False
    assert cell_states[328]['reset_args'] == ('背包格子', 1, False, {'显示名': '宝石格子'}) and cells[328].rawget('禁止拖放') is True

    assert box_tbl.rawget('Main')(3, 7) is None and hero_lbl.rawget('标题') == '左戒指宝石镶嵌'
    assert box_tbl.rawget('Main')(3, 8) is None and hero_lbl.rawget('标题') == '右戒指宝石镶嵌'

    assert box_tbl.rawget('Main')(3, 401) is True and merc_lbl.rawget('标题') == '左手镯宝石镶嵌'
    assert cell_states[411]['reset_args'] == ('完美的紫宝石', 1, False, None)
    assert cell_states[412]['reset_args'] == (None, None, None, None)
    assert box_tbl.rawget('Main')(3, 402) is True and merc_lbl.rawget('标题') == '右手镯宝石镶嵌'
    assert cell_states[411]['reset_args'] == ('完美的绿宝石', 1, False, None)
    assert box_tbl.rawget('Main')(3, 403) is True and merc_lbl.rawget('标题') == '左戒指宝石镶嵌'
    assert box_tbl.rawget('Main')(3, 404) is True and merc_lbl.rawget('标题') == '右戒指宝石镶嵌'
    assert calls['merc_win_open'] == [('宝石', True)] * 4

    # Non-split slot (weapon slot 1) delegates to orig_box!
    assert box_tbl.rawget('Main')(3, 1) == 'orig_rclick' and calls['orig_box_rclick'] == 1

    # 5. Verify independent tooltips for Left vs Right (Hero & Merc) + warm gold affixes (v1.329) + red note (v1.328)
    ring_l = LuaTable({'名称': '巨龙戒指左', '分类': '装备', '子类': '戒指',
                       '附加': LuaTable({'套装属性': '骷髅教主的火种'})})
    ring_r = LuaTable({'名称': '巨龙戒指右', '分类': '装备', '子类': '戒指'})
    raw_tips[('巨龙戒指左', 7)] = (
        '#md#G骷髅教主的火种\n'
        '#md#f(宋_9_炭灰,#c(4287090411)巨龙戒指#W)\n'
        '#md#W重量:1\n'
        '#md#c(-5385052)+75抵抗破防\n'
        '#md#G套装信息\n'
        '#md#c(-5385052)' + real_sets['骷髅教主的火种'][2]
    )
    raw_tips[('巨龙戒指右', 8)] = (
        '#md#f(宋_9_炭灰,#c(4287090411)巨龙戒指#W)\n'
        '#md#W重量:1\n'
        '#md#c(-5385052)击中生命恢复+30'
    )
    raw_tips[('巨龙戒指右', 35)] = raw_tips[('巨龙戒指右', 8)] + '\n#md#WShift+左键放入备用背包'

    out_rl, _ = disp.rawget('道具')(ring_l, 1, 7)
    rls = out_rl.split('\n')
    assert '#c(-7558)抵抗破防:+75#W' in rls
    gi = rls.index('#f(宋_9_炭灰,#c(-22312)镶嵌属性#W)')
    assert rls[gi + 1] == '#c(-8323200)生命值:+30#W', rls[gi:gi + 3]  # ONLY 左戒指's 紫宝石!
    assert rls[gi + 2] == '#f(宋_9_炭灰,#c(-7350017)附魔属性#W)'
    assert rls[-1] == expected_invalid_note, rls[-3:]

    out_rr, _ = disp.rawget('道具')(ring_r, 1, 8)
    rrs = out_rr.split('\n')
    assert '#c(-7558)击中生命恢复:+30#W' in rrs
    gi2 = rrs.index('#f(宋_9_炭灰,#c(-22312)镶嵌属性#W)')
    assert rrs[gi2 + 1] == '#c(-8323200)破坏:+0-6#W', rrs[gi2:]  # ONLY 右戒指's 红宝石!
    assert '生命值:+30' not in out_rr

    # Clear 右戒指 -> NO 镶嵌属性 shown on slot 8!
    hg.rawget('右戒指').rawset(1, 1)
    out_rr_empty, _ = disp.rawget('道具')(ring_r, 1, 8)
    assert '镶嵌属性' not in out_rr_empty

    # Bag ring (slot 35) -> NO 镶嵌属性 shown!
    out_bag_ring, _ = disp.rawget('道具')(ring_r, 1, 35)
    assert '镶嵌属性' not in out_bag_ring

    # Merc slot 402 (右手镯) shows ONLY 绿宝石 (准确:+30), NOT 左手镯's 紫宝石!
    mb_r = LuaTable({'名称': '佣兵手镯右', '分类': '装备', '子类': '手镯'})
    raw_tips[('佣兵手镯右', 402)] = '#md#f(宋_9_炭灰,#c(-1)佣兵手镯#W)\n#md#W重量:1'
    out_mbr, _ = disp.rawget('道具')(mb_r, 1, 402)
    assert '#f(宋_9_炭灰,#c(-22312)镶嵌属性#W)\n#c(-8323200)准确:+30#W' in out_mbr
    assert '生命值' not in out_mbr

    # 6. Verify 「前尘忆梦」 isolation: legacy guild untouched, original handlers called
    U.rawset('版本选择', '前尘忆梦')
    qc_save = LuaTable({'行会': LuaTable({'手镯': LuaTable({1: '完美的红宝石', 2: 0, 3: 0, 4: 0, 5: 0})})})
    U.rawset('啾啾啵啵', lambda: qc_save)
    S.rawget('__gm_sync_gem_split_v330')(True)
    assert qc_save.rawget('行会').rawget('手镯') is not None
    assert qc_save.rawget('行会').rawget('左手镯') is None
    wr.rawget('宝石属性')()
    wr.rawget('佣兵宝石')()
    assert calls['orig_hero_gem'] == 1 and calls['orig_merc_gem'] == 1
    assert box_tbl.rawget('Main')(3, 5) == 'orig_rclick' and calls['orig_box_rclick'] == 2
    out_qc, _ = disp.rawget('道具')(ring_l, 1, 7)
    assert out_qc == raw_tips[('巨龙戒指左', 7)]


def main():
    mods_o, rt_src = test_diff_syntax_and_m12_37()
    test_v330_split_bracelet_ring_gems(mods_o[12], rt_src)
    test_real_boss_blueprint_drops_5_5pct(mods_o[12], rt_src)
    test_compact_equip_spaces_v317(rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v330.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.330',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v330.res': out_sha,
            'runtime_v330.lua': hashlib.sha256((W / 'runtime_v330.lua').read_bytes()).hexdigest(),
            'patch_v330.py': hashlib.sha256((W / 'patch_v330.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'm12_37_zero_jmp_below_params_preserved',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'hero_and_merc_old_save_gem_migration_to_left_and_fresh_locked_right',
            'hero_and_merc_right_click_split_gem_window_titles_and_slots',
            'hero_and_merc_11part_gem_stat_recalc_with_reincarnation_multiplier',
            'independent_left_right_tooltip_gem_sections_and_v329_warm_gold_affixes',
            'qianchi_complete_isolation_and_v319_v317_v308_v307_v306_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v330.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v330.json').write_text(text, encoding='utf-8')
    print('ALL v1.330 TESTS PASSED!')


if __name__ == '__main__':
    main()
