"""Exhaustive verification suite for v1.327:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v327.lua
3. m12/37 (qs_item_box.Main) still has ZERO JMP instructions with A < params (v1.325 fix preserved)
4. Soft luminous outlined header colors on equipment tooltips:
   - 「镶嵌属性」 -> #f(宋_9_炭灰,#c(-22312)镶嵌属性#W) (柔樱粉 #FFA8D8)
   - 「附魔属性」 -> #f(宋_9_炭灰,#c(-7350017)附魔属性#W) (浅天蓝 #8FD8FF)
5. Eligible slot (武器/衣服/鞋子): active green outlined scroll name (#c(-16711936)), NO eligibility note.
6. Ineligible slots (both equipped 戒指 ending at enchant stats, and bag 头盔 with trailing Shift line):
   - Grey outlined scroll name: #f(宋_9_炭灰,#c(-5592406)<scroll_name>#W)
   - Grey enchant stats starting with #H
   - Appended RED '#R附魔仅在武器/衣服/鞋子生效#W' right after last enchant stat line (exactly once)
7. Save-load deferral + live instant refresh (v1.325), v1.323 3-slot rules, S.fun/S.shelp right-click gem UI,
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
BASE_SHA = '2454d5b3e318921e14b29f951cb9b464969fb9fd7c8623b1ae053df40544033b'


def extract_runtime_v327(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.327 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v327.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_syntax_and_m12_37():
    base_bytes = (W / 'game_v326.res').read_bytes()
    out_bytes = (W / 'game_v327.res').read_bytes()
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

    rt_src = extract_runtime_v327(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_v327_red_ineligible_note(d12, rt_src):
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
    orig_calls = {'hero': 0, 'gem_ui': 0, 'box_ev1': 0}
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

    # 1. Save-load deferral + live tooltip refresh (v1.325)
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

    # 2. Eligible slot (衣服, 赤龙宝甲_男): soft luminous header colors + green outlined name, NO note
    armor = bag.rawget(2).rawget('道具')
    raw_tips[('赤龙宝甲_男', 2)] = (
        '#md#G虎战领主之爪\n'
        '#md#f(宋_9_炭灰,#c(4287090411)赤龙宝甲(男)#W)\n'
        '#md#W重量:1\n'
        '#md#c(-8323200)防御力:38-55 (+8)\n'
        '#md#W需要等级:1\n'
        '#md#c(-3381556)镶嵌信息\n'
        '#md#c(-5385052)+12最大防御力\n'
        '#md#G套装信息\n'
        '#md#c(-5385052)' + real_sets['虎战领主之爪'][2]
    )
    out_armor, _ = disp.rawget('道具')(armor, 1, 2)
    ls = out_armor.split('\n')
    assert ls[0] == '#f(宋_9_炭灰,#c(4287090411)赤龙宝甲(男)#W)'
    assert '#f(宋_9_炭灰,#c(-22312)镶嵌属性#W)' in ls, ls
    idx_fm = ls.index('#f(宋_9_炭灰,#c(-7350017)附魔属性#W)')
    assert ls[idx_fm + 1] == '#f(宋_9_炭灰,#c(-16711936)虎战领主之爪#W)', ls[idx_fm:idx_fm + 3]
    assert ls[idx_fm + 2] == '#c(-8323200)伤害:+0-50#W'
    assert '附魔仅在武器/衣服/鞋子生效' not in out_armor

    # 3. Ineligible equipped slot (戒指, 巨龙戒指 with 骷髅教主的火种, ending at enchant stats)
    ring = LuaTable({'名称': '巨龙戒指', '分类': '装备', '子类': '戒指',
                     '附加': LuaTable({'套装属性': '骷髅教主的火种'})})
    raw_tips[('巨龙戒指', 8)] = (
        '#md#G骷髅教主的火种\n'
        '#md#f(宋_9_炭灰,#c(4287090411)巨龙戒指#W)\n'
        '#md#W重量:1\n'
        '#md#W破坏:0-10\n'
        '#md#W需要等级:1\n'
        '#md#c(-8323200)生命药水恢复量+41\n'
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
    assert rls[-1] == '#R附魔仅在武器/衣服/鞋子生效#W', rls[-3:]
    assert out_ring.count('附魔仅在武器/衣服/鞋子生效') == 1

    # 4. Ineligible slot in bag with trailing '#WShift+左键放入备用背包' line (黑铁头盔 at slot 35)
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
    assert hls[hi + 1] == '#f(宋_9_炭灰,#c(-5592406)骷髅教主的火种#W)', hls[hi:hi + 3]
    note_idx = hls.index('#R附魔仅在武器/衣服/鞋子生效#W')
    assert note_idx > hi + 2
    assert hls[note_idx - 1].startswith('#H'), hls[hi:note_idx + 2]
    assert hls[note_idx + 1] == '#WShift+左键放入备用背包', hls[note_idx:]
    assert out_helm.count('附魔仅在武器/衣服/鞋子生效') == 1

    # 5. Verify 武器/衣服/鞋子 activation & old-save other slots ignored
    for sid, sub, sn in ((1, '武器', '虎战领主之爪'), (2, '衣服', '沃玛教主的利爪'),
                         (10, '鞋子', '骷髅教主的火种'), (3, '头盔', '毁灭之爪'), (13, '坐骑', '皇陵鲲吾剑')):
        bag.rawset(sid, LuaTable({'道具': LuaTable({'名称': '测试' + sub, '分类': '装备', '子类': sub,
                                                   '附加': LuaTable({'套装属性': sn})})}))
    wr.rawget('套装属性')(10, 1)
    assert dict(h14_internal.rawget('stats')._data) == sum_sets(real_sets, ['虎战领主之爪', '沃玛教主的利爪', '骷髅教主的火种'])

    # 6. Verify S.shelp + right-click gem UI & 「前尘忆梦」 isolation
    assert shelp.rawget(lua_tostring(box_tbl.rawget('Main'))) is not None
    assert box_tbl.rawget('Main')(3, 1) is True and orig_calls['gem_ui'] == 1
    U.rawset('版本选择', '前尘忆梦')
    S.rawget('__gm_pickup_frame_v299')(U, G)
    for nm, orig_dn in real_tpls.items():
        assert item_db.rawget(nm).rawget('显示名') == orig_dn


def main():
    mods_o, rt_src = test_diff_syntax_and_m12_37()
    test_v327_red_ineligible_note(mods_o[12], rt_src)
    test_real_boss_blueprint_drops_5_5pct(mods_o[12], rt_src)
    test_compact_equip_spaces_v317(rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v327.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.327',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v327.res': out_sha,
            'runtime_v327.lua': hashlib.sha256((W / 'runtime_v327.lua').read_bytes()).hexdigest(),
            'patch_v327.py': hashlib.sha256((W / 'patch_v327.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'm12_37_zero_jmp_below_params_preserved',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'soft_luminous_header_colors_pink_FFA8D8_blue_8FD8FF',
            'ineligible_slots_grey_outlined_scroll_name_AAAAAA_and_red_eligibility_note_once',
            'eligible_slots_active_green_scroll_name_and_no_eligibility_note',
            'save_load_deferral_live_refresh_3slot_rules_and_qianchi_isolation_pass',
            'v319_5_5pct_v317_v308_v307_v306_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v327.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v327.json').write_text(text, encoding='utf-8')
    print('ALL v1.327 TESTS PASSED!')


if __name__ == '__main__':
    main()
