"""Exhaustive verification suite for v1.325:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v325.lua
3. m12/37 (qs_item_box.Main) LuaJIT BC_JMP A-slot snapshot-safety verification:
   - ZERO JMP instructions with A < params (5)
   - Exact live-slot counts at all 9 fixed PCs (4398/4401/4404/4411/4418/4421 -> 5, 4427 -> 11, 4440 -> 13, 4451 -> 6)
   - Identical nbc, jump targets, opcodes, constants, and lineinfo vs game_v324.res
4. Save-load tooltip refresh deferral:
   - During S.__gm_loading_save_v299 == true, wrapped_box(1/2, ...) skips redundant refresh_slot_tooltip_v322
   - During normal gameplay (S.__gm_loading_save_v299 false/nil), wrapped_box(1/2, ...) immediately refreshes tooltips
5. All v1.324 outlined title font (#f(宋_9_炭灰,...)), v1.323 3-slot rules (武器/衣服/鞋子),
   S.fun/S.shelp right-click gem UI, 29 附魔卷 renames, 「前尘忆梦」 isolation,
   and prior regressions (5.5% Boss drops, v1.317, v1.308, v1.307, v1.306).
"""
import hashlib
import json
from pathlib import Path

from ljdis import OPS
from ljtool import Dump
from lua51_eval import LuaTable, syntax_check
from native_test_utils import trees
from patch_v325 import M12_37_JMP_FIXES
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
BASE_SHA = '27568ce22e989e95f33fcc0d442241f30b8257cddc52427c8f8146a9ddd41ca0'


def extract_runtime_v325(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.325 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v325.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_syntax_and_m12_37_jmp():
    base_bytes = (W / 'game_v324.res').read_bytes()
    out_bytes = (W / 'game_v325.res').read_bytes()
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

    # Verify m12/37 bytecode diff is strictly the 9 JMP A-slot fixes
    p_b = mods_b[12].protos[37]
    p_o = mods_o[12].protos[37]
    assert p_b.nbc == p_o.nbc == 4493
    assert p_b.params == p_o.params == 5
    assert p_b.frame == p_o.frame == 22
    assert len(p_b.raw) == len(p_o.raw)
    assert p_b.raw[p_b.kend:] == p_o.raw[p_o.kend:], 'knum/lineinfo must be byte-identical'

    diff_pcs = [pc for pc in range(p_o.nbc) if p_b.bc[pc] != p_o.bc[pc]]
    assert set(diff_pcs) == set(M12_37_JMP_FIXES.keys()), f'Unexpected m12/37 bc diffs: {diff_pcs}'
    for pc, (exp_target, exp_a) in M12_37_JMP_FIXES.items():
        ins_b, ins_o = p_b.bc[pc], p_o.bc[pc]
        assert OPS[ins_o & 0xFF] == 'JMP'
        assert (ins_o & 0xFFFF00FF) == (ins_b & 0xFFFF00FF), f'pc={pc} opcode/D changed'
        assert ((ins_b >> 8) & 0xFF) == 0
        assert ((ins_o >> 8) & 0xFF) == exp_a
        assert (pc + 1 + (ins_o >> 16) - 0x8000) == exp_target

    # Verify ZERO JMP instructions in m12/37 have A < params
    for pc, ins in enumerate(p_o.bc):
        if OPS[ins & 0xFF] == 'JMP':
            a = (ins >> 8) & 0xFF
            assert a >= p_o.params, f'm12/37 pc={pc} has JMP A={a} < params={p_o.params}'

    rt_src = extract_runtime_v325(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_v325_save_load_and_outlined_rules(d12, rt_src):
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

    # Setup mock controls for slot 2 (equipped armor) and slot 166 (backup bag item)
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

    # 1. Verify save-load deferral: while __gm_loading_save_v299 is true, wrapped_box(1, 166)
    #    calls orig_box cleanly and skips redundant refresh_slot_tooltip_v322
    bag.rawset(166, LuaTable({'道具': LuaTable({'名称': '备份装备', '分类': '装备', '子类': '衣服'})}))
    bag.rawset(2, LuaTable({'道具': LuaTable({'名称': '赤龙宝甲_男', '分类': '装备', '子类': '衣服',
                                              '附加': LuaTable({'套装属性': '虎战领主之爪'})})}))
    S.rawset('__gm_loading_save_v299', True)
    tooltip_refreshes.clear()
    box_tbl.rawget('Main')(1, 166, '备份装备', None, 2)
    assert orig_calls['box_ev1'] == 1
    assert tooltip_refreshes == [], f'Expected no tooltip refresh during save load, got {tooltip_refreshes}'

    # Once save loading finishes, live equip/unequip immediately refreshes tooltip
    S.rawset('__gm_loading_save_v299', False)
    box_tbl.rawget('Main')(1, 2, '赤龙宝甲_男', None, 1)
    assert tooltip_refreshes == [2], f'Expected instant tooltip refresh on equip, got {tooltip_refreshes}'

    # 2. Verify outlined headers & outlined scroll name
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
    assert '#f(宋_9_炭灰,#c(-3381556)镶嵌属性#W)' in ls
    idx_fm = ls.index('#f(宋_9_炭灰,#c(-11162881)附魔属性#W)')
    assert ls[idx_fm + 1] == '#f(宋_9_炭灰,#c(-16711936)虎战领主之爪#W)'
    assert ls[idx_fm + 2] == '#c(-8323200)伤害:+0-50#W'

    # 3. Verify 武器/衣服/鞋子 activation & old-save other slots ignored
    for sid, sub, sn in ((1, '武器', '虎战领主之爪'), (2, '衣服', '沃玛教主的利爪'),
                         (10, '鞋子', '骷髅教主的火种'), (3, '头盔', '毁灭之爪'), (13, '坐骑', '皇陵鲲吾剑')):
        bag.rawset(sid, LuaTable({'道具': LuaTable({'名称': '测试' + sub, '分类': '装备', '子类': sub,
                                                   '附加': LuaTable({'套装属性': sn})})}))
    wr.rawget('套装属性')(10, 1)
    assert dict(h14_internal.rawget('stats')._data) == sum_sets(real_sets, ['虎战领主之爪', '沃玛教主的利爪', '骷髅教主的火种'])

    # 4. Verify S.shelp + right-click gem UI & 「前尘忆梦」 isolation
    assert shelp.rawget(lua_tostring(box_tbl.rawget('Main'))) is not None
    assert box_tbl.rawget('Main')(3, 1) is True and orig_calls['gem_ui'] == 1
    U.rawset('版本选择', '前尘忆梦')
    S.rawget('__gm_pickup_frame_v299')(U, G)
    for nm, orig_dn in real_tpls.items():
        assert item_db.rawget(nm).rawget('显示名') == orig_dn


def main():
    mods_o, rt_src = test_diff_syntax_and_m12_37_jmp()
    test_v325_save_load_and_outlined_rules(mods_o[12], rt_src)
    test_real_boss_blueprint_drops_5_5pct(mods_o[12], rt_src)
    test_compact_equip_spaces_v317(rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v325.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.325',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v325.res': out_sha,
            'runtime_v325.lua': hashlib.sha256((W / 'runtime_v325.lua').read_bytes()).hexdigest(),
            'patch_v325.py': hashlib.sha256((W / 'patch_v325.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only for gameplay/UI; m12/37 BC_JMP A-slot fix restores LuaJIT bytecode validity',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'm12_37_all_9_jmp_a0_fixed_and_zero_jmp_below_params',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'save_load_tooltip_refresh_deferred_and_live_refresh_preserved',
            'outlined_宋_9_炭灰_and_v323_3slot_rules_and_qianchi_isolation_pass',
            'v319_5_5pct_v317_v308_v307_v306_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v325.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v325.json').write_text(text, encoding='utf-8')
    print('ALL v1.325 TESTS PASSED!')


if __name__ == '__main__':
    main()
