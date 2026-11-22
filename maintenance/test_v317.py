"""Exhaustive verification suite for v1.317:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v317.lua
3. Equipment bonus-parenthesis spaces removed (防御力:0-15(+9), 自然系魔法:13-0(+13),
   negative (-2), elemental (+1)) on both bag and equipped items, while preserving the
   separator space between multiple strong elements on one line (火(火焰)x3 雷(电击)x3)
4. Full regressions: v1.316 all 40 sets & all 30 gems & equip 镶嵌信息,
   v1.310 11% Boss blueprints, v1.308 【仓库】 proxy button, v1.307 Mode 2 materials, v1.306 gather.
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
from test_v316 import test_tooltips_v316

W = Path(__file__).resolve().parent
BASE_SHA = 'fb8cfd5dfef2cf1540e641f92c29d5b7fcf94e225874609aeae9d7c0336ba2b0'


def extract_runtime_v317(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.317 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v317.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_and_syntax():
    base_bytes = (W / 'game_v316.res').read_bytes()
    out_bytes = (W / 'game_v317.res').read_bytes()
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

    rt_src = extract_runtime_v317(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_compact_equip_spaces_v317(rt_src):
    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']
    G.rawset('取道具信息_名称', lambda name: LuaTable({'名称': name, '分类': '装备'}))

    raw_outputs = {}
    disp = LuaTable({'道具': lambda item, mode, slot_id: raw_outputs[(item.rawget('名称'), slot_id)]})
    U.rawset('托管显示', disp)
    ev.G.get('loadstring')(rt_src)(S)

    # Exact user screenshot case: 黑皮手套
    glove = LuaTable({'名称': '黑皮手套', '分类': '装备', '子类': '手镯', '攻神元素': 7, '附加': LuaTable({'条数': 3})})
    raw_outputs[('黑皮手套', 32)] = (
        '#f(宋_9_炭灰,#c(4287090411)黑皮手套#W)\n'
        '#W重量:1\n'
        '#c(-8323200)防御力:0-15#c(-8323200) (+9)#W\n'
        '#W魔法防御:0-6\n'
        '#c(-8323200)自然系魔法:13-0#c(-8323200) (+13)#W\n'
        '#c(-8323200)舒适:1#c(-45824) (-1)#W\n'
        '#c(-8323328)攻击元素: 圣(神圣) +7\n'
        '#c(-8323328)强元素:火(火焰)×3#c(-8323328) (+1)#W #c(-8323328)雷(电击)×3\n'
        '#W需要等级:1',
        None,
    )
    out, _ = disp.rawget('道具')(glove, 1, 32)
    lines = out.split('\n')
    assert lines == [
        '#f(宋_9_炭灰,#c(4287090411)黑皮手套#W)',
        '#W重量:1',
        '#c(-8323200)防御力:0-15#c(-8323200)(+9)#W',
        '#W魔法防御:0-6',
        '#c(-8323200)自然系魔法:13-0#c(-8323200)(+13)#W',
        '#c(-8323200)舒适:1#c(-45824)(-1)#W',
        '#c(-8323328)攻击元素:圣(神圣)+7',
        '#c(-8323328)强元素:火(火焰)x3#c(-8323328)(+1)#W #c(-8323328)雷(电击)x3',
        '#W需要等级:1',
    ], lines


def main():
    mods_o, rt_src = test_diff_and_syntax()
    test_compact_equip_spaces_v317(rt_src)
    test_tooltips_v316(mods_o[12], rt_src)
    test_real_boss_blueprint_drops_11pct(mods_o[12], rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v317.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.317',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v317.res': out_sha,
            'runtime_v317.lua': hashlib.sha256((W / 'runtime_v317.lua').read_bytes()).hexdigest(),
            'patch_v317.py': hashlib.sha256((W / 'patch_v317.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'equip_bonus_parenthesis_spaces_removed_positive_negative_elemental',
            'v316_all_40_sets_and_30_gems_regression_pass',
            'v310_boss_blueprints_11pct_regression_pass',
            'v308_warehouse_proxy_button_regression_pass',
            'v307_mode2_ordinary_materials_regression_pass',
            'v306_gather_formula_regression_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v317.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v317.json').write_text(text, encoding='utf-8')
    print('ALL v1.317 TESTS PASSED!')


if __name__ == '__main__':
    main()
