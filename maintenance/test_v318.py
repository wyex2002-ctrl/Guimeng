"""Exhaustive verification suite for v1.318:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v318.lua
3. Set blueprint '拖到装备使用' line colored yellow (#Y拖到装备使用#W) across all 40 real sets
4. Full regressions: v1.317 compact equip parens, v1.316 all 40 sets & 30 gems,
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
from test_v314 import decode_real_sets_143
from test_v316 import test_tooltips_v316
from test_v317 import test_compact_equip_spaces_v317

W = Path(__file__).resolve().parent
BASE_SHA = '52bc5e06facc6c8c7e3bd79bf4185c8d53775fceb2dc5e8100bc344ff00d04e2'


def extract_runtime_v318(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.318 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v318.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_and_syntax():
    base_bytes = (W / 'game_v317.res').read_bytes()
    out_bytes = (W / 'game_v318.res').read_bytes()
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

    rt_src = extract_runtime_v318(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_yellow_drag_hint_v318(d12, rt_src):
    real_sets = decode_real_sets_143(d12)
    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']

    raw_outputs = {}
    disp = LuaTable({'道具': lambda item, mode, slot_id: raw_outputs[(item.rawget('名称'), slot_id)]})
    U.rawset('托管显示', disp)
    ev.G.get('loadstring')(rt_src)(S)

    for set_name, (_, raw_desc) in real_sets.items():
        bp = LuaTable({'名称': set_name, '分类': '道具', '子类': '材料', '附加': LuaTable({'套装属性': set_name})})
        raw_outputs[(set_name, 32)] = (
            f'#md#f(宋_9_炭灰,#c(-8323328){set_name}#W)\n#md#W重量:1\n#md#W需要等级:1\n'
            f'#md#c(-5385052){raw_desc}\n#md#c(-45824)拖到装备使用\n#md#c(-3090223)Shift+左键放入备用背包',
            None,
        )
        out, _ = disp.rawget('道具')(bp, 1, 32)
        lines = out.split('\n')
        assert lines[-2] == '#Y拖到装备使用#W', (set_name, lines[-2:])
        assert lines[-1] == '#c(-3090223)Shift+左键放入备用背包', (set_name, lines[-2:])


def main():
    mods_o, rt_src = test_diff_and_syntax()
    test_yellow_drag_hint_v318(mods_o[12], rt_src)
    test_compact_equip_spaces_v317(rt_src)
    test_tooltips_v316(mods_o[12], rt_src)
    test_real_boss_blueprint_drops_11pct(mods_o[12], rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v318.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.318',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v318.res': out_sha,
            'runtime_v318.lua': hashlib.sha256((W / 'runtime_v318.lua').read_bytes()).hexdigest(),
            'patch_v318.py': hashlib.sha256((W / 'patch_v318.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'all_40_set_blueprints_drag_hint_yellow',
            'v317_compact_equip_parens_regression_pass',
            'v316_all_40_sets_and_30_gems_regression_pass',
            'v310_boss_blueprints_11pct_regression_pass',
            'v308_warehouse_proxy_button_regression_pass',
            'v307_mode2_ordinary_materials_regression_pass',
            'v306_gather_formula_regression_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v318.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v318.json').write_text(text, encoding='utf-8')
    print('ALL v1.318 TESTS PASSED!')


if __name__ == '__main__':
    main()
