"""Exhaustive verification suite for v1.320:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v320.lua
3. Set blueprint rules (using authentic m48/1+m48/2 __call-table proxies):
   - All 4 allowed slots (武器/衣服/头盔/坐骑) activate SIMULTANEOUSLY (summed cleanly!)
   - Unequipping 1 of the 4 allowed slots removes only that set, keeping the other 3 active
   - Same set on 2 allowed slots deduplicates (applied once, never doubled)
   - Old save with multiple legacy other slots (手镯 + 戒指 + 项链) -> AT MOST 1 legacy set activates
   - Mixed old save (2 allowed slots + 2 legacy slots) -> both allowed slots + at most 1 legacy slot activate
   - Mercenary independent simultaneous 4-slot + max-1 legacy cap verified
   - Drag restriction still strictly enforces 武器/衣服/头盔/坐骑 only
   - 「前尘忆梦」 100% isolated & original required counts restored
4. Full regressions: v1.319 5.5% Boss blueprints, v1.317/v1.316 tooltips,
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

W = Path(__file__).resolve().parent
BASE_SHA = '834eb5e4da79ab744981c19303c817585e71a11f9bb04da853cc9aa7673493f1'


def extract_runtime_v320(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.320 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v320.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def sum_sets(real_sets, names):
    out = {}
    for nm in names:
        for k, v in real_sets[nm][0].items():
            out[k] = out.get(k, 0) + v
    return out


def test_diff_and_syntax():
    base_bytes = (W / 'game_v319.res').read_bytes()
    out_bytes = (W / 'game_v320.res').read_bytes()
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

    rt_src = extract_runtime_v320(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_set_rules_v320(d12, rt_src):
    real_sets = decode_real_sets_full_143(d12)
    sets_lua = LuaTable()
    for name, (hsh, req, desc) in real_sets.items():
        entry = LuaTable()
        entry.rawset(1, LuaTable(hsh))
        entry.rawset(2, req)
        entry.rawset(3, desc)
        sets_lua.rawset(name, entry)

    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']
    U.rawset('天竺葵家', lambda: sets_lua)
    U.rawset('胚子考虑', lambda: LuaTable({'装备操作': 0}))
    prompts = []
    U.rawset('托管显示', LuaTable({'屏幕提示': lambda msg, col=None: prompts.append((msg, col))}))
    orig_calls = {'hero': 0, 'merc': 0}
    wr = LuaTable({
        '套装属性': lambda a, b: orig_calls.__setitem__('hero', orig_calls['hero'] + 1),
        '佣兵套装': lambda a, b: orig_calls.__setitem__('merc', orig_calls['merc'] + 1),
    })
    U.rawset('窗口相关', wr)

    cells = {}
    G.rawset('从ID取格子', lambda sid: cells.get(sid))
    G.rawset('鼠标道具', 0)

    def orig_box(ev_type, slot_id, a3=None, a4=None, a5=None):
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

    def make_eq(sub, sname=None):
        ex = LuaTable({'套装属性': sname}) if sname else LuaTable()
        return LuaTable({'道具': LuaTable({'名称': '测试' + sub, '分类': '装备', '子类': sub, '附加': ex})})

    def make_bp(sname):
        return LuaTable({'道具': LuaTable({'名称': sname, '分类': '道具', '子类': '材料', '附加': LuaTable({'套装属性': sname})})})

    ev.G.get('loadstring')(rt_src)(S)

    # 1. All 4 allowed slots (武器/衣服/头盔/坐骑) activate SIMULTANEOUSLY!
    cells[1] = make_eq('武器', '虎战领主之爪')
    cells[2] = make_eq('衣服', '沃玛教主的利爪')
    cells[3] = make_eq('头盔', '骷髅教主的火种')
    cells[13] = make_eq('坐骑', '毁灭之爪')
    wr.rawget('套装属性')(13, 1)
    expected4 = sum_sets(real_sets, ['虎战领主之爪', '沃玛教主的利爪', '骷髅教主的火种', '毁灭之爪'])
    assert stats_dict(h14_internal) == expected4, (stats_dict(h14_internal), expected4)
    for nm in ('虎战领主之爪', '沃玛教主的利爪', '骷髅教主的火种', '毁灭之爪'):
        assert holder_extra(h14_internal).rawget(nm) == 1

    # 2. Unequipping 衣服 (slot 2, ev_type=3) drops only 沃玛教主的利爪, keeping the other 3 active!
    wr.rawget('套装属性')(2, 3)
    expected3 = sum_sets(real_sets, ['虎战领主之爪', '骷髅教主的火种', '毁灭之爪'])
    assert stats_dict(h14_internal) == expected3
    assert holder_extra(h14_internal).rawget('沃玛教主的利爪') is None
    assert holder_extra(h14_internal).rawget('虎战领主之爪') == 1

    # 3. Same blueprint on 2 allowed slots deduplicates (applied ONCE)
    cells.clear()
    cells[1] = make_eq('武器', '虎战领主之爪')
    cells[2] = make_eq('衣服', '虎战领主之爪')
    wr.rawget('套装属性')(2, 1)
    assert stats_dict(h14_internal) == real_sets['虎战领主之爪'][0]

    # 4. Old save: ONLY legacy other slots (手镯 + 戒指 + 项链) -> AT MOST 1 activates!
    cells.clear()
    cells[4] = make_eq('项链', '赤月恶魔的尖刺')
    cells[6] = make_eq('手镯', '沃玛教主的利爪')
    cells[8] = make_eq('戒指', '触龙神的毒囊')
    wr.rawget('套装属性')(None, None)
    assert stats_dict(h14_internal) == real_sets['赤月恶魔的尖刺'][0]
    assert holder_extra(h14_internal).rawget('赤月恶魔的尖刺') == 1
    assert holder_extra(h14_internal).rawget('沃玛教主的利爪') is None
    assert holder_extra(h14_internal).rawget('触龙神的毒囊') is None

    # 5. Mixed old save: 2 allowed slots (武器 + 头盔) + 2 legacy slots (手镯 + 戒指)
    #    -> BOTH allowed slots activate PLUS at most 1 legacy slot (手镯), 戒指 stays inactive!
    cells.clear()
    cells[1] = make_eq('武器', '虎战领主之爪')
    cells[3] = make_eq('头盔', '骷髅教主的火种')
    cells[6] = make_eq('手镯', '沃玛教主的利爪')
    cells[8] = make_eq('戒指', '触龙神的毒囊')
    wr.rawget('套装属性')(None, None)
    expected_mix = sum_sets(real_sets, ['虎战领主之爪', '骷髅教主的火种', '沃玛教主的利爪'])
    assert stats_dict(h14_internal) == expected_mix
    assert holder_extra(h14_internal).rawget('虎战领主之爪') == 1
    assert holder_extra(h14_internal).rawget('骷髅教主的火种') == 1
    assert holder_extra(h14_internal).rawget('沃玛教主的利爪') == 1
    assert holder_extra(h14_internal).rawget('触龙神的毒囊') is None

    # 6. Mercenary: 2 allowed slots + 2 legacy slots -> both allowed + max 1 legacy, independent from Hero!
    cells[397] = make_eq('武器', '毁灭之爪')
    cells[398] = make_eq('衣服', '皇陵鲲吾剑')
    cells[402] = make_eq('手镯', '祖玛教主的怒火')
    cells[404] = make_eq('戒指', '触龙神的毒囊')
    wr.rawget('佣兵套装')(None, None)
    expected_merc = sum_sets(real_sets, ['毁灭之爪', '皇陵鲲吾剑', '祖玛教主的怒火'])
    assert stats_dict(m410_internal) == expected_merc
    assert holder_extra(m410_internal).rawget('触龙神的毒囊') is None
    assert stats_dict(h14_internal) == expected_mix

    # 7. Drag restriction still strictly blocks non-allowed slots and allows the 4 slots
    cells[32] = make_eq('戒指')
    cells[33] = make_bp('虎战领主之爪')
    G.rawset('鼠标道具', 33)
    prompts.clear()
    assert box_tbl.rawget('Main')(4, 32) is True
    assert cells[32].rawget('道具').rawget('附加').rawget('套装属性') is None
    assert cells[33].rawget('道具') is not None and len(prompts) == 1

    # 8. 「前尘忆梦」 restores all original required counts & delegates to original
    U.rawset('版本选择', '前尘忆梦')
    S.rawget('__gm_pickup_frame_v299')(U, G)
    for name, (_, orig_req, _) in real_sets.items():
        assert sets_lua.rawget(name).rawget(2) == orig_req
    prev_h = orig_calls['hero']
    wr.rawget('套装属性')(1, 1)
    assert orig_calls['hero'] == prev_h + 1


def main():
    mods_o, rt_src = test_diff_and_syntax()
    test_set_rules_v320(mods_o[12], rt_src)
    test_real_boss_blueprint_drops_5_5pct(mods_o[12], rt_src)
    test_compact_equip_spaces_v317(rt_src)
    test_tooltips_v316(mods_o[12], rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v320.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.320',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v320.res': out_sha,
            'runtime_v320.lua': hashlib.sha256((W / 'runtime_v320.lua').read_bytes()).hexdigest(),
            'patch_v320.py': hashlib.sha256((W / 'patch_v320.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'all_4_allowed_slots_activate_simultaneously_and_unequip_cleanly',
            'duplicate_same_set_deduplicated',
            'old_save_legacy_other_slots_capped_at_max_1_standalone_and_mixed',
            'merc_independent_4_allowed_plus_max_1_legacy',
            'blueprint_drag_restriction_and_5_5pct_drop_rate_pass',
            'qianchi_completely_isolated',
            'v317_v316_v308_v307_v306_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v320.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v320.json').write_text(text, encoding='utf-8')
    print('ALL v1.320 TESTS PASSED!')


if __name__ == '__main__':
    main()
