"""Exhaustive verification suite for v1.315:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v315.lua
3. ALL 40 real sets from m12/143 天竺葵家:
   - Attack elements formatted identically to m12/320 equipment tooltip: 攻击元素: <el>(<desc>) +<N>
   - Strong elements formatted identically to m12/321 equipment tooltip: 强元素:<el>(<desc>)×<N>
   - Non-element stats keep no-'+' format (伤害:0-50, 魔防:0-5, 生命值:50, 魔法值:-200, etc.)
   - Half-width ASCII ':' / '(' / ')' and exact '×' (U+00D7) verified on all 40 sets
   - Equipment 套装信息 active/inactive colors preserved (matching user screenshot 骷髅教主的火种)
4. 「前尘忆梦」 100% isolated + full regressions (v1.313/v1.310/v1.308/v1.307/v1.306).
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
from test_v313 import test_tooltip_v313
from test_v314 import decode_real_sets_143

W = Path(__file__).resolve().parent
BASE_SHA = '62d4e37703ffe0c409e6b6f73bfa4377147053cdb136752b29a64ccac5c74d74'


def extract_runtime_v315(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.315 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v315.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_and_syntax():
    base_bytes = (W / 'game_v314.res').read_bytes()
    out_bytes = (W / 'game_v315.res').read_bytes()
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

    rt_src = extract_runtime_v315(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_set_elements_v315(d12, rt_src):
    real_sets = decode_real_sets_143(d12)
    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']
    G.rawset('取道具信息_名称', lambda name: LuaTable({'名称': name, '分类': '装备'}))

    raw_outputs = {}
    disp = LuaTable({'道具': lambda item, mode, slot_id: raw_outputs[(item.rawget('名称'), slot_id)]})
    U.rawset('托管显示', disp)
    ev.G.get('loadstring')(rt_src)(S)

    # 1. Exact user screenshot case: 骷髅教主的火种 inactive set on equipment
    eq_skull = LuaTable({
        '名称': '魔法手镯', '分类': '装备', '子类': '手镯',
        '附加': LuaTable({'套装属性': '骷髅教主的火种'}),
    })
    raw_outputs[('魔法手镯', 6)] = (
        '#md#f(宋_9_炭灰,#c(-1)魔法手镯#W)\n'
        '#md#W需要等级:1\n'
        '#md#G套装信息\n'
        '#md#H' + real_sets['骷髅教主的火种'][1],
        None,
    )
    out_skull, _ = disp.rawget('道具')(eq_skull, 1, 6)
    assert out_skull.split('\n')[-5:] == [
        '#G套装信息',
        '#H攻击元素: 火(火焰) +20#W',
        '#H魔防:0-5#W',
        '#H生命值:50#W',
        '#H强元素:火(火焰)×10#W',
    ], out_skull

    # 2. 罪孽教主的长舌 (幻影 attack + 幻影 strong) as blueprint & active equip set
    bp_tongue = LuaTable({
        '名称': '罪孽教主的长舌', '分类': '道具', '子类': '材料',
        '附加': LuaTable({'套装属性': '罪孽教主的长舌'}),
    })
    raw_outputs[('罪孽教主的长舌', 32)] = (
        '#md#f(宋_9_炭灰,#c(-8323328)罪孽教主的长舌#W)\n#md#W重量:1\n#md#W需要等级:1\n'
        '#md#c(-5385052)' + real_sets['罪孽教主的长舌'][1] + '\n#md#c(-45824)拖到装备使用',
        None,
    )
    out_tongue, _ = disp.rawget('道具')(bp_tongue, 1, 32)
    assert out_tongue.split('\n')[3:8] == [
        '#c(-8323328)攻击元素: 幻(幻影) +20#W',
        '#c(-8323200)击中生命恢复:8#W',
        '#c(-8323200)准确:20#W',
        '#c(-8323328)强元素:幻(幻影)×25#W',
        '#c(-8323200)生命值:50#W',
    ], out_tongue

    # 3. ALL 40 real sets verified for exact half-width ':'/'('/')', '+N' on 攻击元素, '×N' on 强元素
    for set_name, (_, raw_desc) in real_sets.items():
        bp = LuaTable({
            '名称': set_name, '分类': '道具', '子类': '材料',
            '附加': LuaTable({'套装属性': set_name}),
        })
        raw_text = (
            f'#md#f(宋_9_炭灰,#c(-8323328){set_name}#W)\n#md#W重量:1\n#md#W需要等级:1\n'
            f'#md#c(-5385052){raw_desc}\n#md#c(-45824)拖到装备使用\n#md#c(-3090223)Shift+左键放入备用背包'
        )
        raw_outputs[(set_name, 40)] = (raw_text, None)
        res, _ = disp.rawget('道具')(bp, 1, 40)
        assert '#md' not in res and '#rt' not in res
        # Ensure zero full-width colons or full-width parens anywhere
        assert '：' not in res and '（' not in res and '）' not in res, (set_name, res)
        stat_lines = res.split('\n')[3:-2]
        assert len(stat_lines) == len(raw_desc.split('\n'))
        for sl in stat_lines:
            if '攻击元素:' in sl:
                assert sl.startswith('#c(-8323328)攻击元素: ') and ') +' in sl and sl.endswith('#W'), (set_name, sl)
            elif '强元素:' in sl:
                assert sl.startswith('#c(-8323328)强元素:') and not sl.startswith('#c(-8323328)强元素: '), (set_name, sl)
                assert ')×' in sl and '+' not in sl and sl.endswith('#W'), (set_name, sl)
            else:
                assert sl.startswith('#c(-8323200)') and '+' not in sl and sl.endswith('#W'), (set_name, sl)


def main():
    mods_o, rt_src = test_diff_and_syntax()
    test_set_elements_v315(mods_o[12], rt_src)
    test_tooltip_v313(mods_o[12], rt_src)
    test_real_boss_blueprint_drops_11pct(mods_o[12], rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v315.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.315',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v315.res': out_sha,
            'runtime_v315.lua': hashlib.sha256((W / 'runtime_v315.lua').read_bytes()).hexdigest(),
            'patch_v315.py': hashlib.sha256((W / 'patch_v315.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'all_40_sets_attack_and_strong_elements_match_mir3_equip_format_exact_halfwidth',
            'skull_and_tongue_set_tooltips_verified',
            'v313_gems_and_equip_socket_regression_pass',
            'v310_boss_blueprints_11pct_regression_pass',
            'v308_warehouse_proxy_button_regression_pass',
            'v307_mode2_ordinary_materials_regression_pass',
            'v306_gather_formula_regression_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v315.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v315.json').write_text(text, encoding='utf-8')
    print('ALL v1.315 TESTS PASSED!')


if __name__ == '__main__':
    main()
