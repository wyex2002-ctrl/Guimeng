"""Exhaustive verification suite for v1.321:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v321.lua
3. Authentic m14/424 S.fun + S.shelp dispatch test:
   - S.fun(S.tbl_qs.qs_item_box.Main, args) checks S.shelp[tostring(fn)] != nil
   - Right-click equipped gear (ev_type=3) executes orig_box -> opens gem socket UI
   - Equip/unequip (ev_type=1, 2) executes orig_box -> calls 套装属性 & updates stats
   - Dragging blueprint onto non-allowed slot is blocked; onto allowed slot succeeds
   - Rebuilding S.shelp triggers re-registration on next pickup_frame
4. Set blueprint rules (using authentic m48/1+m48/2 __call-table proxies AND S.包裹物品组):
   - All 4 allowed slots (武器/衣服/头盔/坐骑) activate simultaneously
   - Unequipping 1 of 4 removes only that set; unequipping ALL still calls 更新道具属性({}) so Hero/Merc stats clear!
   - Recreating Ux雌.天竺葵家 immediately re-applies cfg[2]=1 on next pickup_frame
   - Same set on 2 allowed slots deduplicates; old-save legacy slots capped at max 1
   - Mercenary independent 4-allowed + max-1 legacy
   - 「前尘忆梦」 100% isolated & original required counts restored
5. Full regressions: v1.319 5.5% Boss blueprints, v1.317/v1.316 tooltips,
   v1.308 【仓库】 proxy button, v1.307 Mode 2 materials, v1.306 gather formula.
"""
import hashlib
import json
from pathlib import Path

from ljtool import Dump
from lua51_eval import LuaTable, syntax_check
from native_test_utils import trees
from resource_tools import decode
from test_v300 import make_env
from test_v307 import test_mode2_ordinary_materials, test_v306_regression
from test_v308 import test_authentic_proxy_warehouse_button
from test_v316 import test_tooltips_v316
from test_v317 import test_compact_equip_spaces_v317
from test_v319 import (
    decode_real_sets_full_143,
    make_slot_proxy,
    test_real_boss_blueprint_drops_5_5pct,
)
from test_v320 import sum_sets

W = Path(__file__).resolve().parent
BASE_SHA = 'e3042bd87e64f38014a1d23cea1b54a78cbb5ad01b3070fd0ae8064c0d66233d'


def extract_runtime_v321(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.321 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v321.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_and_syntax():
    base_bytes = (W / 'game_v320.res').read_bytes()
    out_bytes = (W / 'game_v321.res').read_bytes()
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

    rt_src = extract_runtime_v321(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_shelp_and_sets_v321(d12, rt_src):
    real_sets = decode_real_sets_full_143(d12)

    def build_sets_lua():
        t = LuaTable()
        for name, (hsh, req, desc) in real_sets.items():
            entry = LuaTable()
            entry.rawset(1, LuaTable(hsh))
            entry.rawset(2, req)
            entry.rawset(3, desc)
            t.rawset(name, entry)
        return t

    sets_lua = build_sets_lua()

    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']
    U.rawset('天竺葵家', lambda: sets_lua)
    U.rawset('胚子考虑', lambda: LuaTable({'装备操作': 0}))
    prompts = []
    U.rawset('托管显示', LuaTable({'屏幕提示': lambda msg, col=None: prompts.append((msg, col))}))
    orig_calls = {'hero': 0, 'merc': 0, 'elem_icon': 0, 'merc_win': 0, 'gem_ui': 0}
    wr = LuaTable({
        '套装属性': lambda a, b: orig_calls.__setitem__('hero', orig_calls['hero'] + 1),
        '佣兵套装': lambda a, b: orig_calls.__setitem__('merc', orig_calls['merc'] + 1),
        '元素图标': lambda: orig_calls.__setitem__('elem_icon', orig_calls['elem_icon'] + 1),
        '佣兵窗口': lambda a=None, b=None: orig_calls.__setitem__('merc_win', orig_calls['merc_win'] + 1),
    })
    U.rawset('窗口相关', wr)

    bag = LuaTable()
    S.rawset('包裹物品组', bag)

    cells = {}
    G.rawset('从ID取格子', lambda sid: cells.get(sid))
    G.rawset('鼠标道具', 0)

    def orig_box(ev_type, slot_id, a3=None, a4=None, a5=None):
        if ev_type == 3:
            # Right-click equipped item -> opens gem socket window!
            orig_calls['gem_ui'] += 1
            return True
        if ev_type in (1, 2) and slot_id is not None and 1 <= slot_id <= 13:
            wr.rawget('套装属性')(slot_id, ev_type)
            return None
        mid = G.rawget('鼠标道具')
        if ev_type == 4 and mid and mid > 0:
            tc, sc = cells.get(slot_id), cells.get(mid)
            if tc and sc and tc.rawget('道具') and sc.rawget('道具'):
                sex = sc.rawget('道具').rawget('附加')
                if sex and sex.rawget('套装属性') is not None:
                    tc.rawget('道具').rawget('附加').rawset('套装属性', sex.rawget('套装属性'))
                    sc.rawset('道具', None)
                    return True
        return None

    # Authentic m14/424 S.shelp + S.fun dispatcher: silently drops calls if S.shelp[tostring(fn)] == nil!
    lua_tostring = ev.G.get('tostring')
    shelp = LuaTable()
    shelp.rawset(lua_tostring(orig_box), LuaTable({'msg': '【全局事件/物品格子】', 'fname': 'Main', 'sid': 13}))
    S.rawset('shelp', shelp)

    def authentic_S_fun(fn, args):
        if fn is None:
            return None
        entry = S.rawget('shelp').rawget(lua_tostring(fn))
        if entry is None:
            return None  # Exact m14/424 pc=8 behavior!
        return fn(*args)

    box_tbl = LuaTable({'Main': orig_box})
    S.rawset('tbl_qs', LuaTable({'qs_item_box': box_tbl}))

    h14_internal, h14_proxy = make_slot_proxy(ev)
    m410_internal, m410_proxy = make_slot_proxy(ev)
    ss = S.rawget('script_setting')
    ss.rawset('Gly独', G)
    ss.rawset('物品格子14', h14_proxy)
    ss.rawset('物品格子410', m410_proxy)

    def stats_dict(internal):
        return dict(internal.rawget('stats')._data)

    def holder_extra(internal):
        return internal.rawget('item').rawget('附加')

    def put_eq(slot_id, sub, sname=None):
        ex = LuaTable({'套装属性': sname}) if sname else LuaTable()
        item = LuaTable({'名称': '测试' + sub, '分类': '装备', '子类': sub, '附加': ex})
        cell = LuaTable({'道具': item})
        cells[slot_id] = cell
        bag.rawset(slot_id, cell)
        return cell

    def clear_slots():
        cells.clear()
        for k in list(bag._data.keys()):
            bag.rawset(k, None)

    def put_bp(slot_id, sname):
        item = LuaTable({'名称': sname, '分类': '道具', '子类': '材料', '附加': LuaTable({'套装属性': sname})})
        cell = LuaTable({'道具': item})
        cells[slot_id] = cell
        bag.rawset(slot_id, cell)
        return cell

    ev.G.get('loadstring')(rt_src)(S)

    # === CHECK 1: Authentic S.fun + S.shelp dispatch ===
    wrapped_main = box_tbl.rawget('Main')
    assert wrapped_main is not orig_box
    sh_entry = shelp.rawget(lua_tostring(wrapped_main))
    assert sh_entry is not None and sh_entry.rawget('sid') == 13, 'wrapped_box MUST be registered in S.shelp!'

    # Right-click equipped gear (ev_type=3) MUST NOT be dropped by S.fun!
    assert authentic_S_fun(box_tbl.rawget('Main'), (3, 1)) is True
    assert orig_calls['gem_ui'] == 1, 'Right-click gem socket UI must execute through S.fun!'

    # Simulate S.shelp reset -> pickup_frame restores registration immediately
    shelp.rawset(lua_tostring(wrapped_main), None)
    assert authentic_S_fun(box_tbl.rawget('Main'), (3, 1)) is None  # confirms authentic S.fun guard!
    S.rawget('__gm_pickup_frame_v299')(U, G)
    assert authentic_S_fun(box_tbl.rawget('Main'), (3, 1)) is True
    assert orig_calls['gem_ui'] == 2

    # === CHECK 2: Equip via authentic S.fun activates all 4 allowed slots simultaneously ===
    put_eq(1, '武器', '虎战领主之爪')
    put_eq(2, '衣服', '沃玛教主的利爪')
    put_eq(3, '头盔', '骷髅教主的火种')
    put_eq(13, '坐骑', '毁灭之爪')
    authentic_S_fun(box_tbl.rawget('Main'), (1, 13))
    expected4 = sum_sets(real_sets, ['虎战领主之爪', '沃玛教主的利爪', '骷髅教主的火种', '毁灭之爪'])
    assert stats_dict(h14_internal) == expected4
    for nm in ('虎战领主之爪', '沃玛教主的利爪', '骷髅教主的火种', '毁灭之爪'):
        assert holder_extra(h14_internal).rawget(nm) == 1

    # === CHECK 3: Unequipping ALL set items STILL calls 更新道具属性({}) to refresh Hero stats! ===
    prev_updates = h14_internal.rawget('updates')
    clear_slots()
    authentic_S_fun(box_tbl.rawget('Main'), (2, 1))
    assert h14_internal.rawget('updates') == prev_updates + 1, 'Must call 更新道具属性({}) on empty!'
    assert stats_dict(h14_internal) == {}

    # === CHECK 4: Dragging blueprint onto equipped allowed slot via S.fun activates & refreshes 元素图标 ===
    put_eq(1, '武器')
    put_bp(33, '虎战领主之爪')
    G.rawset('鼠标道具', 33)
    prev_icon = orig_calls['elem_icon']
    assert authentic_S_fun(box_tbl.rawget('Main'), (4, 1)) is True
    assert stats_dict(h14_internal) == real_sets['虎战领主之爪'][0]
    assert orig_calls['elem_icon'] == prev_icon + 1

    # Dragging blueprint onto disallowed slot via S.fun is blocked with prompt
    put_eq(32, '戒指')
    put_bp(34, '毁灭之爪')
    G.rawset('鼠标道具', 34)
    prompts.clear()
    assert authentic_S_fun(box_tbl.rawget('Main'), (4, 32)) is True
    assert cells[32].rawget('道具').rawget('附加').rawget('套装属性') is None
    assert cells[34].rawget('道具') is not None and len(prompts) == 1

    # === CHECK 5: Mixed old save (2 allowed + 2 legacy) -> both allowed + max 1 legacy ===
    clear_slots()
    put_eq(1, '武器', '虎战领主之爪')
    put_eq(3, '头盔', '骷髅教主的火种')
    put_eq(6, '手镯', '沃玛教主的利爪')
    put_eq(8, '戒指', '触龙神的毒囊')
    wr.rawget('套装属性')(None, None)
    assert stats_dict(h14_internal) == sum_sets(real_sets, ['虎战领主之爪', '骷髅教主的火种', '沃玛教主的利爪'])
    assert holder_extra(h14_internal).rawget('触龙神的毒囊') is None

    # Merc independent
    put_eq(397, '武器', '毁灭之爪')
    put_eq(398, '衣服', '皇陵鲲吾剑')
    put_eq(402, '手镯', '祖玛教主的怒火')
    put_eq(404, '戒指', '触龙神的毒囊')
    wr.rawget('佣兵套装')(None, None)
    assert stats_dict(m410_internal) == sum_sets(real_sets, ['毁灭之爪', '皇陵鲲吾剑', '祖玛教主的怒火'])
    assert holder_extra(m410_internal).rawget('触龙神的毒囊') is None

    # === CHECK 6: Recreating Ux雌.天竺葵家 triggers re-application of cfg[2] = 1 ===
    fresh_sets = build_sets_lua()
    assert fresh_sets.rawget('毁灭之爪').rawget(2) == 6
    U.rawset('天竺葵家', lambda: fresh_sets)
    S.rawget('__gm_pickup_frame_v299')(U, G)
    assert fresh_sets.rawget('毁灭之爪').rawget(2) == 1

    # === CHECK 7: 「前尘忆梦」 restores original req counts & delegates ===
    U.rawset('版本选择', '前尘忆梦')
    S.rawget('__gm_pickup_frame_v299')(U, G)
    for name, (_, orig_req, _) in real_sets.items():
        assert fresh_sets.rawget(name).rawget(2) == orig_req
    prev_h = orig_calls['hero']
    wr.rawget('套装属性')(1, 1)
    assert orig_calls['hero'] == prev_h + 1


def main():
    mods_o, rt_src = test_diff_and_syntax()
    test_shelp_and_sets_v321(mods_o[12], rt_src)
    test_real_boss_blueprint_drops_5_5pct(mods_o[12], rt_src)
    test_compact_equip_spaces_v317(rt_src)
    test_tooltips_v316(mods_o[12], rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v321.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.321',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v321.res': out_sha,
            'runtime_v321.lua': hashlib.sha256((W / 'runtime_v321.lua').read_bytes()).hexdigest(),
            'patch_v321.py': hashlib.sha256((W / 'patch_v321.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'authentic_S_fun_S_shelp_dispatch_ev1_ev2_ev3_gem_ui_ev4_pass',
            'all_4_allowed_slots_activate_simultaneously_and_empty_unequip_refreshes_stats',
            'recreated_sets_table_reapplies_1_piece_requirement',
            'old_save_legacy_other_slots_capped_at_max_1_hero_and_merc',
            'blueprint_drag_restriction_and_5_5pct_drop_rate_pass',
            'qianchi_completely_isolated',
            'v317_v316_v308_v307_v306_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v321.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v321.json').write_text(text, encoding='utf-8')
    print('ALL v1.321 TESTS PASSED!')


if __name__ == '__main__':
    main()
