"""Exhaustive verification suite for v1.328:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v328.lua
3. m12/37 (qs_item_box.Main) still has ZERO JMP instructions with A < params (v1.325 fix preserved)
4. Allowed enchant slots strictly 武器/衣服/头盔:
   - Scroll tooltip hint -> '#Y拖到武器/衣服/头盔使用#W'
   - Dragging scroll onto 头盔 allowed; dragging onto 鞋子/戒指/坐骑 blocked with '附魔卷只能用于武器、衣服或头盔'
   - Hero & Merc recalculation activates ONLY 武器/衣服/头盔 (each 1 piece, deduped by scroll name); 鞋子/坐骑/戒指 etc. ignored
   - Eligible slots (武器/衣服/头盔): active green outlined scroll name (#c(-16711936)), NO eligibility note
   - Ineligible slots (e.g. equipped 戒指 and bag 鞋子 with trailing Shift line):
     - Grey outlined scroll name: #f(宋_9_炭灰,#c(-5592406)<scroll_name>#W)
     - Grey enchant stats starting with #H
     - Appended RED '#R附魔仅在武器/衣服/头盔生效#W' right after last enchant stat line (exactly once)
5. Save-load deferral + live instant refresh (v1.325), S.fun/S.shelp right-click gem UI,
   29 附魔卷 renames, 「前尘忆梦」 isolation, and regressions (5.5% Boss drops, v1.317, v1.308, v1.307, v1.306).
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
BASE_SHA = '27701fc919fc4b21a8a4f63e42256aed793706dc66cc471c2d8544d408ba08fb'


def extract_runtime_v328(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.328 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v328.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_syntax_and_m12_37():
    base_bytes = (W / 'game_v327.res').read_bytes()
    out_bytes = (W / 'game_v328.res').read_bytes()
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

    # Verify v1.325 m12/37 JMP fix is still intact (ZERO JMPs with A < params)
    p37 = mods_o[12].protos[37]
    for pc, ins in enumerate(p37.bc):
        if OPS[ins & 0xFF] == 'JMP':
            a = (ins >> 8) & 0xFF
            assert a >= p37.params, f'm12/37 pc={pc} has JMP A={a} < params={p37.params}'

    rt_src = extract_runtime_v328(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_v328_weapon_armor_helmet_rules(d12, rt_src):
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

    prompts = []
    raw_tips = {}
    disp = LuaTable({
        '道具': lambda item, mode, slot_id: (raw_tips[(item.rawget('名称'), slot_id)], None),
        '屏幕提示': lambda m, c=None: prompts.append((m, c)),
    })
    U.rawset('托管显示', disp)
    orig_calls = {'hero': 0, 'gem_ui': 0, 'box_ev1': 0, 'box_ev4': 0}
    wr = LuaTable({
        '套装属性': lambda a, b: orig_calls.__setitem__('hero', orig_calls['hero'] + 1),
        '佣兵套装': lambda a, b: None,
        '元素图标': lambda: None,
        '佣兵窗口': lambda a=None, b=None: None,
    })
    U.rawset('窗口相关', wr)
    G.rawset('从ID取格子', lambda sid: bag.rawget(sid))
    G.rawset('鼠标道具', 0)

    def orig_box(ev_type, slot_id, a3=None, a4=None, a5=None):
        if ev_type == 3:
            orig_calls['gem_ui'] += 1
            return True
        if ev_type == 1:
            orig_calls['box_ev1'] += 1
        if ev_type == 4:
            orig_calls['box_ev4'] += 1
        if ev_type in (1, 2) and slot_id is not None and 1 <= slot_id <= 13:
            wr.rawget('套装属性')(slot_id, ev_type)
        return None

    lua_tostring = ev.G.get('tostring')
    shelp = LuaTable()
    shelp.rawset(lua_tostring(orig_box), LuaTable({'msg': '【全局事件/物品格子】', 'fname': 'Main', 'sid': 5}))
    S.rawset('shelp', shelp)
    box_tbl = LuaTable({'Main': orig_box})
    S.rawset('tbl_qs', LuaTable({'qs_item_box': box_tbl}))

    tooltip_refreshes = []
    ctrl2 = LuaTable({
        '格子ID': 2,
        '对象': LuaTable({
            '焦点': True,
            '更新道具属性': lambda self_obj=None: tooltip_refreshes.append(2),
        }),
    })
    ctrl166 = LuaTable({
        '格子ID': 166,
        '对象': LuaTable({
            '焦点': False,
            '更新道具属性': lambda self_obj=None: tooltip_refreshes.append(166),
        }),
    })
    S.rawset('tbl_controls', LuaTable({'物品格子2': ctrl2, '物品格子166': ctrl166}))

    h14_internal, h14_proxy = make_slot_proxy(ev)
    m410_internal, m410_proxy = make_slot_proxy(ev)
    ss = S.rawget('script_setting')
    ss.rawset('Gly独', G)
    ss.rawset('物品格子14', h14_proxy)
    ss.rawset('物品格子410', m410_proxy)

    ev.G.get('loadstring')(rt_src)(S)

    # 1. Scroll item tooltip hint: '#Y拖到武器/衣服/头盔使用#W'
    scroll = LuaTable({'名称': '虎战领主之爪_图纸', '分类': '消耗', '子类': '消耗',
                       '附加': LuaTable({'套装属性': '虎战领主之爪'})})
    raw_tips[('虎战领主之爪_图纸', 40)] = (
        '#md#f(宋_9_炭灰,#c(-16711936)虎战领主之爪(附魔卷)#W)\n'
        '#md#W重量:1\n'
        '#md#c(-5385052)' + real_sets['虎战领主之爪'][2] + '\n'
        '#md#c(-45824)拖到装备使用\n'
        '#md#WShift+左键放入备用背包'
    )
    out_scroll, _ = disp.rawget('道具')(scroll, 1, 40)
    assert '#Y拖到武器/衣服/头盔使用#W' in out_scroll, out_scroll
    assert '鞋子' not in out_scroll

    # 2. Save-load deferral + live tooltip refresh (v1.325)
    bag.rawset(166, LuaTable({'道具': LuaTable({'名称': '备份装备', '分类': '装备', '子类': '衣服'})}))
    bag.rawset(2, LuaTable({'道具': LuaTable({'名称': '赤龙宝甲_男', '分类': '装备', '子类': '衣服',
                                              '附加': LuaTable({'套装属性': '虎战领主之爪'})})}))
    S.rawset('__gm_loading_save_v299', True)
    tooltip_refreshes.clear()
    box_tbl.rawget('Main')(1, 166, '备份装备', None, 2)
    assert orig_calls['box_ev1'] == 1
    assert tooltip_refreshes == []

    S.rawset('__gm_loading_save_v299', False)
    box_tbl.rawget('Main')(1, 2, '赤龙宝甲_男', None, 1)
    assert tooltip_refreshes == [2]

    # 3. Dragging scroll onto 头盔 succeeds, while 鞋子 is blocked with '附魔卷只能用于武器、衣服或头盔'
    bag.rawset(40, LuaTable({'道具': scroll}))
    bag.rawset(3, LuaTable({'道具': LuaTable({'名称': '黑铁头盔', '分类': '装备', '子类': '头盔'})}))
    bag.rawset(10, LuaTable({'道具': LuaTable({'名称': '赤飞靴子', '分类': '装备', '子类': '鞋子'})}))
    G.rawset('鼠标道具', 40)
    prompts.clear()
    box_tbl.rawget('Main')(4, 10)
    assert orig_calls['box_ev4'] == 0, 'Dragging scroll onto 鞋子 must be blocked'
    assert prompts == [('附魔卷只能用于武器、衣服或头盔', -65536)], prompts

    prompts.clear()
    box_tbl.rawget('Main')(4, 3)
    assert orig_calls['box_ev4'] == 1, 'Dragging scroll onto 头盔 must be allowed'
    assert prompts == []
    G.rawset('鼠标道具', 0)

    # 4. Eligible slot (头盔, 黑铁头盔 in bag): active green outlined name, NO eligibility note
    helm = LuaTable({'名称': '黑铁头盔', '分类': '装备', '子类': '头盔',
                     '附加': LuaTable({'套装属性': '骷髅教主的火种'})})
    raw_tips[('黑铁头盔', 35)] = (
        '#md#G骷髅教主的火种\n'
        '#md#f(宋_9_炭灰,#c(-1)黑铁头盔#W)\n'
        '#md#W重量:1\n'
        '#md#G套装信息\n'
        '#md#c(-5385052)' + real_sets['骷髅教主的火种'][2] + '\n'
        '#md#WShift+左键放入备用背包'
    )
    out_helm, _ = disp.rawget('道具')(helm, 1, 35)
    hls = out_helm.split('\n')
    hi = hls.index('#f(宋_9_炭灰,#c(-7350017)附魔属性#W)')
    assert hls[hi + 1] == '#f(宋_9_炭灰,#c(-16711936)骷髅教主的火种#W)', hls[hi:hi + 3]
    assert '附魔仅在武器/衣服/头盔生效' not in out_helm
    assert hls[-1] == '#WShift+左键放入备用背包'

    # 5. Ineligible equipped slot (戒指, 巨龙戒指 ending at enchant stats)
    ring = LuaTable({'名称': '巨龙戒指', '分类': '装备', '子类': '戒指',
                     '附加': LuaTable({'套装属性': '骷髅教主的火种'})})
    raw_tips[('巨龙戒指', 8)] = (
        '#md#G骷髅教主的火种\n'
        '#md#f(宋_9_炭灰,#c(4287090411)巨龙戒指#W)\n'
        '#md#W重量:1\n'
        '#md#W破坏:0-10\n'
        '#md#W需要等级:1\n'
        '#md#c(-3381556)镶嵌信息\n'
        '#md#c(-5385052)+6最大破坏\n'
        '#md#G套装信息\n'
        '#md#c(-5385052)' + real_sets['骷髅教主的火种'][2]
    )
    out_ring, _ = disp.rawget('道具')(ring, 1, 8)
    rls = out_ring.split('\n')
    assert '#f(宋_9_炭灰,#c(-22312)镶嵌属性#W)' in rls, rls
    ri = rls.index('#f(宋_9_炭灰,#c(-7350017)附魔属性#W)')
    assert rls[ri + 1] == '#f(宋_9_炭灰,#c(-5592406)骷髅教主的火种#W)', rls[ri:ri + 3]
    for stat_ln in rls[ri + 2:-1]:
        assert stat_ln.startswith('#H'), f'Expected grey stat line, got {stat_ln!r}'
    assert rls[-1] == '#R附魔仅在武器/衣服/头盔生效#W', rls[-3:]
    assert out_ring.count('附魔仅在武器/衣服/头盔生效') == 1

    # 6. Ineligible slot in bag (鞋子, 赤飞靴子 with trailing '#WShift+左键放入备用背包')
    boots = LuaTable({'名称': '赤飞靴子', '分类': '装备', '子类': '鞋子',
                      '附加': LuaTable({'套装属性': '骷髅教主的火种'})})
    raw_tips[('赤飞靴子', 36)] = (
        '#md#G骷髅教主的火种\n'
        '#md#f(宋_9_炭灰,#c(-1)赤飞靴子#W)\n'
        '#md#W重量:1\n'
        '#md#G套装信息\n'
        '#md#c(-5385052)' + real_sets['骷髅教主的火种'][2] + '\n'
        '#md#WShift+左键放入备用背包'
    )
    out_boots, _ = disp.rawget('道具')(boots, 1, 36)
    bls = out_boots.split('\n')
    bi = bls.index('#f(宋_9_炭灰,#c(-7350017)附魔属性#W)')
    assert bls[bi + 1] == '#f(宋_9_炭灰,#c(-5592406)骷髅教主的火种#W)', bls[bi:bi + 3]
    note_idx = bls.index('#R附魔仅在武器/衣服/头盔生效#W')
    assert note_idx > bi + 2
    assert bls[note_idx - 1].startswith('#H'), bls[bi:note_idx + 2]
    assert bls[note_idx + 1] == '#WShift+左键放入备用背包', bls[note_idx:]
    assert out_boots.count('附魔仅在武器/衣服/头盔生效') == 1

    # 7. Verify 武器/衣服/头盔 activation & old-save 鞋子/坐骑 ignored (Hero & Merc)
    for sid, sub, sn in ((1, '武器', '虎战领主之爪'), (2, '衣服', '沃玛教主的利爪'),
                         (3, '头盔', '骷髅教主的火种'), (10, '鞋子', '毁灭之爪'), (13, '坐骑', '皇陵鲲吾剑')):
        bag.rawset(sid, LuaTable({'道具': LuaTable({'名称': '测试' + sub, '分类': '装备', '子类': sub,
                                                   '附加': LuaTable({'套装属性': sn})})}))
    wr.rawget('套装属性')(3, 1)
    assert dict(h14_internal.rawget('stats')._data) == sum_sets(real_sets, ['虎战领主之爪', '沃玛教主的利爪', '骷髅教主的火种'])

    for sid, sub, sn in ((397, '武器', '虎战领主之爪'), (398, '衣服', '沃玛教主的利爪'),
                         (399, '头盔', '骷髅教主的火种'), (406, '鞋子', '毁灭之爪')):
        bag.rawset(sid, LuaTable({'道具': LuaTable({'名称': '佣兵' + sub, '分类': '装备', '子类': sub,
                                                   '附加': LuaTable({'套装属性': sn})})}))
    wr.rawget('佣兵套装')(399, 1)
    assert dict(m410_internal.rawget('stats')._data) == sum_sets(real_sets, ['虎战领主之爪', '沃玛教主的利爪', '骷髅教主的火种'])

    # 8. Verify S.shelp + right-click gem UI & 「前尘忆梦」 isolation
    assert shelp.rawget(lua_tostring(box_tbl.rawget('Main'))) is not None
    assert box_tbl.rawget('Main')(3, 1) is True and orig_calls['gem_ui'] == 1
    U.rawset('版本选择', '前尘忆梦')
    S.rawget('__gm_pickup_frame_v299')(U, G)
    for nm, orig_dn in real_tpls.items():
        assert item_db.rawget(nm).rawget('显示名') == orig_dn


def main():
    mods_o, rt_src = test_diff_syntax_and_m12_37()
    test_v328_weapon_armor_helmet_rules(mods_o[12], rt_src)
    test_real_boss_blueprint_drops_5_5pct(mods_o[12], rt_src)
    test_compact_equip_spaces_v317(rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v328.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.328',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v328.res': out_sha,
            'runtime_v328.lua': hashlib.sha256((W / 'runtime_v328.lua').read_bytes()).hexdigest(),
            'patch_v328.py': hashlib.sha256((W / 'patch_v328.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'm12_37_zero_jmp_below_params_preserved',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'allowed_enchant_slots_weapon_armor_helmet_scroll_hint_and_drag_guard',
            'hero_and_merc_recalc_activates_only_weapon_armor_helmet_ignores_boots_mount',
            'ineligible_slots_grey_outlined_scroll_name_and_red_weapon_armor_helmet_note',
            'eligible_helmet_active_green_scroll_name_and_no_eligibility_note',
            'save_load_deferral_live_refresh_shelp_and_qianchi_isolation_pass',
            'v319_5_5pct_v317_v308_v307_v306_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v328.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v328.json').write_text(text, encoding='utf-8')
    print('ALL v1.328 TESTS PASSED!')


if __name__ == '__main__':
    main()
