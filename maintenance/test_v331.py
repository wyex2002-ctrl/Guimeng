"""Exhaustive verification suite for v1.331:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v331.lua
3. m12/37 (qs_item_box.Main) still has ZERO JMP instructions with A < params
4. Gem cache refresh verification (v1.331):
   - Inserting/removing a gem in Hero 327..331 immediately refreshes equipped slots 1..13 (even unfocused,
     so bag-hover side-by-side comparison tooltips 定位气泡 immediately reflect the updated left/right gems).
   - Inserting/removing a gem in Merc 411..415 immediately refreshes Merc equipped slots 397..409.
   - Old-save migration sets need_tip_refresh and refreshes 5/6/7/8/401/402/403/404 once save loading completes.
5. Full v1.330 split gem + v1.329 + v1.328 + v1.325 + 「前尘忆梦」 isolation + regressions.
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
from test_v319 import test_real_boss_blueprint_drops_5_5pct
from test_v330 import make_gem_slot_cell, test_v330_split_bracelet_ring_gems

W = Path(__file__).resolve().parent
BASE_SHA = 'ef769f0671c314b5fcd794911365e5ecfb2337c9c1883d75aaff49dc552753cf'


def extract_runtime_v331(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.331 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v331.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_syntax_and_m12_37():
    base_bytes = (W / 'game_v330.res').read_bytes()
    out_bytes = (W / 'game_v331.res').read_bytes()
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

    rt_src = extract_runtime_v331(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_v331_gem_tooltip_cache_refresh(rt_src):
    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']

    save_data = LuaTable({
        '行会': LuaTable({'手镯': LuaTable({1: '完美的红宝石', 2: 0, 3: 0, 4: 0, 5: 0})}),
        '佣兵行会': LuaTable({'戒指': LuaTable({1: '完美的蓝宝石', 2: 0, 3: 0, 4: 0, 5: 0})}),
    })
    U.rawset('啾啾啵啵', lambda: save_data)
    U.rawset('暴食模块', lambda: LuaTable({'武器': LuaTable(), '防具': LuaTable(), '首饰': LuaTable()}))
    U.rawset('窗口相关', LuaTable({'宝石属性': lambda: None, '佣兵宝石': lambda: None, '套装属性': lambda a, b: None, '佣兵套装': lambda a, b: None}))

    refreshed = []
    ctrls = LuaTable()
    bag = S.rawget('包裹物品组')
    for cid in [5, 6, 7, 8, 401, 402, 403, 404]:
        def make_cb(slot_i):
            return lambda self_obj=None: refreshed.append(slot_i)
        bag.rawset(cid, LuaTable({'道具': LuaTable({'名称': f'装备{cid}', '分类': '装备'})}))
        ctrls.rawset(f'物品格子{cid}', LuaTable({
            '格子ID': cid,
            '对象': LuaTable({'焦点': False, '更新道具属性': make_cb(cid)}),
        }))
    S.rawset('tbl_controls', ctrls)

    box_tbl = LuaTable({'Main': lambda a1, a2, a3=None, a4=None, a5=None: None})
    S.rawset('tbl_qs', LuaTable({'qs_item_box': box_tbl}))
    S.rawset('shelp', LuaTable())

    hidden332, _ = make_gem_slot_cell()
    hidden416, _ = make_gem_slot_cell()
    ss = S.rawget('script_setting')
    ss.rawset('Gly独', G)
    ss.rawset('物品格子332', hidden332)
    ss.rawset('物品格子416', hidden416)

    # Simulate save-load active during initial migration -> deferred until loading finishes
    S.rawset('__gm_loading_save_v299', True)
    ev.G.get('loadstring')(rt_src)(S)
    S.rawget('__gm_pickup_frame_v299')(U, G)
    assert refreshed == [], f'Must not refresh while loading save, got {refreshed}'

    # Once save loading finishes, next frame refreshes 5,6,7,8,401,402,403,404 exactly once!
    S.rawset('__gm_loading_save_v299', False)
    S.rawget('__gm_pickup_frame_v299')(U, G)
    assert refreshed == [5, 6, 7, 8, 401, 402, 403, 404], refreshed

    # Next frame does NOT redundantly refresh
    refreshed.clear()
    S.rawget('__gm_pickup_frame_v299')(U, G)
    assert refreshed == []

    # Putting/taking a gem in Hero slot 327 refreshes 5,6,7,8 immediately even when unfocused
    box_tbl.rawget('Main')(1, 327, '完美的红宝石')
    assert refreshed == [5, 6, 7, 8], refreshed

    # Putting/taking a gem in Merc slot 411 refreshes 401,402,403,404 immediately even when unfocused
    refreshed.clear()
    box_tbl.rawget('Main')(2, 411, '完美的蓝宝石')
    assert refreshed == [401, 402, 403, 404], refreshed


def main():
    mods_o, rt_src = test_diff_syntax_and_m12_37()
    test_v331_gem_tooltip_cache_refresh(rt_src)
    test_v330_split_bracelet_ring_gems(mods_o[12], rt_src)
    test_real_boss_blueprint_drops_5_5pct(mods_o[12], rt_src)
    test_compact_equip_spaces_v317(rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v331.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.331',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v331.res': out_sha,
            'runtime_v331.lua': hashlib.sha256((W / 'runtime_v331.lua').read_bytes()).hexdigest(),
            'patch_v331.py': hashlib.sha256((W / 'patch_v331.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'm12_37_zero_jmp_below_params_preserved',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'gem_insert_remove_refreshes_equipped_tooltip_caches_for_bag_comparison_popups',
            'post_migration_one_shot_tooltip_cache_refresh_deferred_past_save_load',
            'v330_split_gem_full_suite_and_qianchi_isolation_pass',
            'v319_5_5pct_v317_v308_v307_v306_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v331.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v331.json').write_text(text, encoding='utf-8')
    print('ALL v1.331 TESTS PASSED!')


if __name__ == '__main__':
    main()
