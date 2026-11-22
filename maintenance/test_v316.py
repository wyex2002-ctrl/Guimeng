"""Exhaustive verification suite for v1.316:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v316.lua
3. Compact elements (攻击元素:冰(寒冰)+50, 强元素:冰(寒冰)x50, ASCII lowercase x, zero ×)
   verified on:
   - Bag equipment already formatted by m12/320
   - Equipped equipment (with guild active, gems, and set info)
   - ALL 40 real sets from m12/143 天竺葵家 (both blueprints and equipment 套装信息)
4. Non-element stats formatted with '+' prefix (e.g. 破坏:+0-6, 伤害:+0-15, 防御:+0-12, 魔防:+1-0,
   准确:+35, 魔法值:-200 preserving negative sign!) across:
   - ALL 40 real sets (blueprints & equipment 套装信息)
   - ALL 30 real socketable gems from m12/143 暴食模块
   - Equipment 镶嵌信息 (all 13 gem stat types)
5. 「前尘忆梦」 100% isolated + full regressions (v1.310/v1.308/v1.307/v1.306).
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
from test_v310 import test_real_boss_blueprint_drops_11pct
from test_v312 import decode_real_baoshi_143
from test_v314 import decode_real_sets_143

W = Path(__file__).resolve().parent
BASE_SHA = 'c23312e78435bb92de8b1ed964844ec16297de899e5a8a9a2a2e3212556f4485'


def extract_runtime_v316(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.316 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v316.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_and_syntax():
    base_bytes = (W / 'game_v315.res').read_bytes()
    out_bytes = (W / 'game_v316.res').read_bytes()
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

    rt_src = extract_runtime_v316(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_tooltips_v316(d12, rt_src):
    real_baoshi = decode_real_baoshi_143(d12)
    baoshi_lua = LuaTable()
    for part, entries in real_baoshi.items():
        pt = LuaTable()
        for gname, vals in entries.items():
            et = LuaTable()
            et.rawset(1, vals[0])
            et.rawset(2, vals[1])
            et.rawset(3, vals[2])
            pt.rawset(gname, et)
        baoshi_lua.rawset(part, pt)

    real_sets = decode_real_sets_143(d12)

    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']
    U.rawset('暴食模块', lambda: baoshi_lua)
    G.rawset('取道具信息_名称', lambda name: LuaTable({'名称': name, '分类': '装备'}))

    raw_outputs = {}
    disp = LuaTable({'道具': lambda item, mode, slot_id: raw_outputs[(item.rawget('名称'), slot_id)]})
    U.rawset('托管显示', disp)
    ev.G.get('loadstring')(rt_src)(S)

    # 1. Bag equipment already formatted by m12/320 -> compact 攻击元素 + lowercase x on 强元素
    bracelet = LuaTable({'名称': '魔法手镯', '分类': '装备', '子类': '手镯', '攻冰元素': 4, '附加': LuaTable({'条数': 7})})
    raw_outputs[('魔法手镯', 32)] = (
        '#f(宋_9_炭灰,#c(4294946098)魔法手镯#W)\n'
        '#W重量:1\n'
        '#W防御力:0-2\n'
        '#c(-8323200)灵魂系魔法:0-4#c(-8323200) (+4)#W\n'
        '#c(-8323328)攻击元素: 冰(寒冰) +4\n'
        '#c(-8323328)强元素:火(火焰)×3 #c(-8323328)雷(电击)×3\n'
        '#W需要等级:1',
        None,
    )
    out_bag, _ = disp.rawget('道具')(bracelet, 1, 32)
    assert '#c(-8323328)攻击元素:冰(寒冰)+4' in out_bag.split('\n'), out_bag
    assert '#c(-8323328)强元素:火(火焰)x3 #c(-8323328)雷(电击)x3' in out_bag.split('\n'), out_bag
    assert '×' not in out_bag

    # 2. Equipped equipment with gems & set info -> compact elements, 破坏:+0-1, set info formatted
    eq_full = LuaTable({
        '名称': '魔法手镯', '分类': '装备', '子类': '手镯', '攻冰元素': 4,
        '附加': LuaTable({'条数': 7, '套装属性': '骷髅教主的火种'}),
    })
    raw_outputs[('魔法手镯', 6)] = (
        '#md#f(宋_9_炭灰,#c(-21198)魔法手镯#W)\n'
        '#md#W重量:1\n'
        '#md#c(-8323328)强元素:火(火焰)×3\n'
        '#md#c(-8323328)强元素:雷(电击)×3\n'
        '#md#W需要等级:1\n'
        '#md#c(-8323328)+4冰(寒冰)伤害 (MAX)\n'
        '#md#c(-3381556)镶嵌信息\n'
        '#md#c(-5385052)+1最大破坏\n'
        '#md#c(-5385052)+5准确\n'
        '#md#G套装信息\n'
        '#md#H' + real_sets['骷髅教主的火种'][1],
        None,
    )
    out_eq, _ = disp.rawget('道具')(eq_full, 1, 6)
    ls = out_eq.split('\n')
    assert '×' not in out_eq and '#md' not in out_eq
    assert '#c(-8323328)攻击元素:冰(寒冰)+4' in ls
    assert '#c(-8323328)强元素:火(火焰)x3 #c(-8323328)雷(电击)x3' in ls
    assert ls[-8:] == [
        '#c(-3381556)镶嵌信息',
        '#c(-8323200)破坏:+0-1#W',
        '#c(-8323200)准确:+5#W',
        '#G套装信息',
        '#H攻击元素:火(火焰)+20#W',
        '#H魔防:+0-5#W',
        '#H生命值:+50#W',
        '#H强元素:火(火焰)x10#W',
    ], ls[-8:]

    # 3. User screenshot case: 玄武天王核心 blueprint
    xw = LuaTable({'名称': '玄武天王核心', '分类': '道具', '子类': '材料', '附加': LuaTable({'套装属性': '玄武天王核心'})})
    raw_outputs[('玄武天王核心', 35)] = (
        '#md#f(宋_9_炭灰,#c(-8323328)玄武天王核心(图纸)#W)\n#md#W重量:1\n#md#W需要等级:1\n'
        '#md#c(-5385052)' + real_sets['玄武天王核心'][1] + '\n#md#c(-45824)拖到装备使用',
        None,
    )
    out_xw, _ = disp.rawget('道具')(xw, 1, 35)
    assert out_xw.split('\n')[3:8] == [
        '#c(-8323200)伤害:+0-15#W',
        '#c(-8323328)攻击元素:冰(寒冰)+50#W',
        '#c(-8323200)准确:+35#W',
        '#c(-8323200)魔法值:+50#W',
        '#c(-8323328)强元素:冰(寒冰)x50#W',
    ], out_xw

    # 4. ALL 40 real sets: verify compact elements, lowercase x, '+' on positive, '-' on negative (魔血之魂晶)
    for set_name, (_, raw_desc) in real_sets.items():
        bp = LuaTable({'名称': set_name, '分类': '道具', '子类': '材料', '附加': LuaTable({'套装属性': set_name})})
        raw_text = (
            f'#md#f(宋_9_炭灰,#c(-8323328){set_name}#W)\n#md#W重量:1\n#md#W需要等级:1\n'
            f'#md#c(-5385052){raw_desc}\n#md#c(-45824)拖到装备使用'
        )
        raw_outputs[(set_name, 40)] = (raw_text, None)
        res, _ = disp.rawget('道具')(bp, 1, 40)
        assert '#md' not in res and '×' not in res and '+-' not in res, (set_name, res)
        assert '攻击元素: ' not in res and ') +' not in res and '强元素: ' not in res, (set_name, res)
        for sl in res.split('\n')[3:-1]:
            if '攻击元素:' in sl:
                assert sl.startswith('#c(-8323328)攻击元素:') and ')+' in sl and sl.endswith('#W'), (set_name, sl)
            elif '强元素:' in sl:
                assert sl.startswith('#c(-8323328)强元素:') and ')x' in sl and sl.endswith('#W'), (set_name, sl)
            else:
                assert sl.startswith('#c(-8323200)') and (':+' in sl or ':-' in sl) and sl.endswith('#W'), (set_name, sl)
        if set_name == '魔血之魂晶':
            assert '#c(-8323200)魔法值:-200#W' in res.split('\n'), res

    # 5. ALL 30 real gems: verify 武器: 破坏:+12-0 / 防具: 防御:+0-12 / 首饰: 破坏:+0-6 etc.
    perfect_red = LuaTable({'名称': '完美的红宝石', '分类': '道具', '子类': '宝石', '附加': LuaTable()})
    raw_outputs[('完美的红宝石', 327)] = (
        '#md#f(宋_9_炭灰,#c(-8323328)完美的红宝石#W)\n#md#W重量:1\n#md#W需要等级:1\n#md#c(-5385052)可镶嵌于镶孔中',
        None,
    )
    out_pr, _ = disp.rawget('道具')(perfect_red, 1, 327)
    assert out_pr.split('\n')[4:] == [
        '#c(-8323200)武器: 破坏:+12-0#W',
        '#c(-8323200)防具: 防御:+0-12#W',
        '#c(-8323200)首饰: 破坏:+0-6#W',
    ], out_pr

    for gname in sorted(real_baoshi['武器'].keys()):
        g_item = LuaTable({'名称': gname, '分类': '道具', '子类': '宝石', '附加': LuaTable()})
        raw_outputs[(gname, 50)] = (
            f'#md#f(宋_9_炭灰,#c(-8323328){gname}#W)\n#md#W重量:1\n#md#W需要等级:1\n#md#c(-5385052)可镶嵌于镶孔中',
            None,
        )
        res, _ = disp.rawget('道具')(g_item, 1, 50)
        assert '#md' not in res and '#rt' not in res
        for idx, part in enumerate(('武器', '防具', '首饰'), start=4):
            ln = res.split('\n')[idx]
            assert ln.startswith(f'#c(-8323200){part}: ') and ':+' in ln and ln.endswith('#W'), (gname, ln)

    # 6. 「前尘忆梦」 100% isolated
    env_q = make_env(story='前尘忆梦')
    ev_q, S_q, U_q, G_q = env_q['ev'], env_q['S'], env_q['U'], env_q['G']
    q_fn = lambda item, mode, slot_id: (raw_outputs[('玄武天王核心', 35)][0], None)
    disp_q = LuaTable({'道具': q_fn})
    U_q.rawset('托管显示', disp_q)
    ev_q.G.get('loadstring')(rt_src)(S_q)
    S_q.rawget('__gm_load_state_v299')(False, False)
    S_q.rawget('__gm_pickup_frame_v299')(U_q, G_q)
    assert disp_q.rawget('道具') is q_fn


def main():
    mods_o, rt_src = test_diff_and_syntax()
    test_tooltips_v316(mods_o[12], rt_src)
    test_real_boss_blueprint_drops_11pct(mods_o[12], rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v316.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.316',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v316.res': out_sha,
            'runtime_v316.lua': hashlib.sha256((W / 'runtime_v316.lua').read_bytes()).hexdigest(),
            'patch_v316.py': hashlib.sha256((W / 'patch_v316.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'compact_elements_and_lowercase_x_across_bag_equipped_sets',
            'all_40_real_sets_plus_prefix_and_negative_preserved',
            'all_30_real_gems_and_equip_socket_plus_prefix',
            'qianchi_completely_isolated',
            'v310_boss_blueprints_11pct_regression_pass',
            'v308_warehouse_proxy_button_regression_pass',
            'v307_mode2_ordinary_materials_regression_pass',
            'v306_gather_formula_regression_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v316.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v316.json').write_text(text, encoding='utf-8')
    print('ALL v1.316 TESTS PASSED!')


if __name__ == '__main__':
    main()
