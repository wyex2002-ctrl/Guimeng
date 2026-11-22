"""Exhaustive verification suite for v1.314:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v314.lua
3. ALL 40 real sets extracted from m12/143 天竺葵家:
   - Set blueprint tooltip (e.g. 虎战领主之爪, 魔血之魂晶, 赤龙的法器, 沃玛教主的利爪, etc.):
     100% left-aligned (zero #md / #rt), every stat line converted to Mir3 no-'+' format
     matching 镶嵌信息 (negative sign preserved on 魔血之魂晶 魔法值:-200!),
     拖到装备使用 & Shift+左键放入备用背包 preserved verbatim
   - Equipment 套装信息 (both active green/lime and inactive #H grey) formatted consistently
4. 「前尘忆梦」 100% isolated
5. Full regressions: v1.313 gems & equip 镶嵌信息, v1.310 11% Boss blueprints,
   v1.308 【仓库】 proxy button, v1.307 Mode 2 ordinary materials, v1.306 gather formula.
"""
import hashlib
import json
import re
from pathlib import Path

from ljdis import dis
from ljtool import Dump
from lua51_eval import LuaTable, syntax_check
from native_test_utils import trees
from resource_tools import decode
from test_v300 import make_env
from test_v307 import test_mode2_ordinary_materials, test_v306_regression
from test_v308 import test_authentic_proxy_warehouse_button
from test_v310 import test_real_boss_blueprint_drops_11pct
from test_v313 import test_tooltip_v313

W = Path(__file__).resolve().parent
BASE_SHA = '6b6ecec150f770e7fbbff211d2953b69f29c00e16e4c72f57aed850a7d3bf91e'


def extract_runtime_v314(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.314 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v314.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_and_syntax():
    base_bytes = (W / 'game_v313.res').read_bytes()
    out_bytes = (W / 'game_v314.res').read_bytes()
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

    rt_src = extract_runtime_v314(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def decode_real_sets_143(m12):
    p = m12.protos[143]

    def dec(v):
        if isinstance(v, bytes):
            return v.decode('gbk', 'replace')
        if isinstance(v, tuple) and v[0] == 'table':
            return [dec(x) for x in v[1]], {dec(k): dec(val) for k, val in v[2]}
        if isinstance(v, tuple) and v[0] == 'int':
            val = v[1]
            return val - (1 << 32) if val >= (1 << 31) else val
        return v

    lines = dis(p).splitlines()
    sets = {}
    last_arr = None
    last_hsh = None
    for ln in lines[975:1300]:
        m = re.search(r'TDUP\s+\d+\s+\d+\s+\d+\s+D=\s*(\d+)', ln)
        if m:
            arr, hsh = dec(p.gc(int(m.group(1))))
            if arr and len(arr) >= 4 and isinstance(arr[3], str):
                last_arr = arr
            elif hsh:
                last_hsh = hsh
        elif 'KSTR' in ln:
            ms = re.search(r"'([^']+)'\s*$", ln)
            if ms:
                s = ms.group(1)
                if s == '天竺葵家':
                    break
                if last_arr is not None and last_hsh is not None:
                    sets[s] = (last_arr[2], last_arr[3])
                    last_arr = None
                    last_hsh = None
    assert len(sets) == 40, f'Expected 40 sets in m12/143, got {len(sets)}'
    return sets


def test_set_blueprints_v314(d12, rt_src):
    real_sets = decode_real_sets_143(d12)
    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']
    G.rawset('取道具信息_名称', lambda name: LuaTable({'名称': name, '分类': '装备'}))

    raw_outputs = {}
    disp = LuaTable({'道具': lambda item, mode, slot_id: raw_outputs[(item.rawget('名称'), slot_id)]})
    U.rawset('托管显示', disp)
    ev.G.get('loadstring')(rt_src)(S)

    # --- 1. User screenshot exact case: 虎战领主之爪 ---
    tiger = LuaTable({
        '名称': '虎战领主之爪', '分类': '道具', '子类': '材料',
        '附加': LuaTable({'套装属性': '虎战领主之爪'}),
    })
    raw_outputs[('虎战领主之爪', 32)] = (
        '#md#f(宋_9_炭灰,#c(-8323328)虎战领主之爪#W)\n'
        '#md#W重量:1\n'
        '#md#W需要等级:1\n'
        '#md#c(-5385052)' + real_sets['虎战领主之爪'][1] + '\n'
        '#md#c(-45824)拖到装备使用\n'
        '#md#c(-3090223)Shift+左键放入备用背包',
        None,
    )
    out_t, _ = disp.rawget('道具')(tiger, 1, 32)
    assert '#md' not in out_t and '#rt' not in out_t, out_t
    assert out_t.split('\n') == [
        '#f(宋_9_炭灰,#c(-8323328)虎战领主之爪#W)',
        '#W重量:1',
        '#W需要等级:1',
        '#c(-8323200)伤害:0-50#W',
        '#c(-8323200)准确:40#W',
        '#c(-8323200)伤害:20-0#W',
        '#c(-8323200)暴击伤害:50#W',
        '#c(-8323200)抵抗暴击:20#W',
        '#c(-8323328)攻击元素: 雷(电击) 30#W',
        '#c(-45824)拖到装备使用',
        '#c(-3090223)Shift+左键放入备用背包',
    ], out_t

    # --- 2. Negative value case: 魔血之魂晶 (-200魔法值上限 -> 魔法值:-200) ---
    moxue = LuaTable({
        '名称': '魔血之魂晶', '分类': '道具', '子类': '材料',
        '附加': LuaTable({'套装属性': '魔血之魂晶'}),
    })
    raw_outputs[('魔血之魂晶', 33)] = (
        '#md#f(宋_9_炭灰,#c(-8323328)魔血之魂晶#W)\n#md#W重量:1\n#md#W需要等级:1\n'
        '#md#c(-5385052)' + real_sets['魔血之魂晶'][1] + '\n#md#c(-45824)拖到装备使用',
        None,
    )
    out_m, _ = disp.rawget('道具')(moxue, 1, 33)
    assert out_m.split('\n')[3:6] == [
        '#c(-8323200)准确:10#W',
        '#c(-8323200)生命值:100#W',
        '#c(-8323200)魔法值:-200#W',
    ], out_m

    # --- 3. ALL 40 REAL SETS verified exhaustively (zero unconverted '+' stat lines!) ---
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
        assert '#md' not in res and '#rt' not in res, (set_name, res)
        res_lines = res.split('\n')
        assert res_lines[-2] == '#c(-45824)拖到装备使用', (set_name, res_lines[-2:])
        assert res_lines[-1] == '#c(-3090223)Shift+左键放入备用背包', (set_name, res_lines[-2:])
        stat_lines = res_lines[3:-2]
        assert len(stat_lines) == len(raw_desc.split('\n')), (set_name, stat_lines)
        for sl in stat_lines:
            assert (sl.startswith('#c(-8323200)') or sl.startswith('#c(-8323328)')) and sl.endswith('#W'), (set_name, sl)
            assert '+' not in sl, f'Unconverted + in set {set_name}: {sl}'
            assert ':' in sl, f'Missing colon in set {set_name}: {sl}'
            assert '防御力' not in sl and '魔法防御' not in sl, (set_name, sl)

    # --- 4. Equipment 套装信息: active (green/lime) & inactive (#H grey) ---
    eq = LuaTable({
        '名称': '沃玛手镯', '分类': '装备', '子类': '手镯', '攻冰元素': 4,
        '附加': LuaTable({'条数': 6, '套装属性': '沃玛教主的利爪'}),
    })
    raw_outputs[('沃玛手镯', 6)] = (
        '#md#f(宋_9_炭灰,#c(-1)沃玛手镯#W)\n'
        '#md#W需要等级:20\n'
        '#md#c(-8323328)+4冰(寒冰)伤害 (MAX)\n'
        '#md#c(-3381556)镶嵌信息\n'
        '#md#c(-5385052)+3最大破坏\n'
        '#md#G套装信息\n'
        '#md#c(-5385052)' + real_sets['沃玛教主的利爪'][1],
        None,
    )
    out_act, _ = disp.rawget('道具')(eq, 1, 6)
    assert out_act.split('\n')[-7:] == [
        '#c(-3381556)镶嵌信息',
        '#c(-8323200)破坏:0-3#W',
        '#G套装信息',
        '#c(-8323328)攻击元素: 雷(电击) 10#W',
        '#c(-8323200)准确:5#W',
        '#c(-8323200)生命值:50#W',
        '#c(-8323328)强元素: 雷(电击) 20#W',
    ], out_act

    raw_outputs[('沃玛手镯', 32)] = (
        '#md#f(宋_9_炭灰,#c(-1)沃玛手镯#W)\n'
        '#md#W需要等级:20\n'
        '#md#G套装信息\n'
        '#md#H' + real_sets['沃玛教主的利爪'][1],
        None,
    )
    out_inact, _ = disp.rawget('道具')(eq, 1, 32)
    assert out_inact.split('\n')[-5:] == [
        '#G套装信息',
        '#H攻击元素: 雷(电击) 10#W',
        '#H准确:5#W',
        '#H生命值:50#W',
        '#H强元素: 雷(电击) 20#W',
    ], out_inact

    # --- 5. 「前尘忆梦」 100% isolated ---
    env_q = make_env(story='前尘忆梦')
    ev_q, S_q, U_q, G_q = env_q['ev'], env_q['S'], env_q['U'], env_q['G']
    q_fn = lambda item, mode, slot_id: (raw_outputs[('虎战领主之爪', 32)][0], None)
    disp_q = LuaTable({'道具': q_fn})
    U_q.rawset('托管显示', disp_q)
    ev_q.G.get('loadstring')(rt_src)(S_q)
    S_q.rawget('__gm_load_state_v299')(False, False)
    S_q.rawget('__gm_pickup_frame_v299')(U_q, G_q)
    assert disp_q.rawget('道具') is q_fn
    assert '+50最大伤害值' in disp_q.rawget('道具')(tiger, 1, 32)[0]


def main():
    mods_o, rt_src = test_diff_and_syntax()
    test_set_blueprints_v314(mods_o[12], rt_src)
    test_tooltip_v313(mods_o[12], rt_src)
    test_real_boss_blueprint_drops_11pct(mods_o[12], rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v314.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.314',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v314.res': out_sha,
            'runtime_v314.lua': hashlib.sha256((W / 'runtime_v314.lua').read_bytes()).hexdigest(),
            'patch_v314.py': hashlib.sha256((W / 'patch_v314.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'all_40_real_set_blueprints_left_aligned_and_mir3_formatted',
            'negative_set_stat_moxue_preserved',
            'equip_set_section_active_and_inactive_colors_preserved',
            'qianchi_completely_isolated',
            'v313_gems_and_equip_socket_regression_pass',
            'v310_boss_blueprints_11pct_regression_pass',
            'v308_warehouse_proxy_button_regression_pass',
            'v307_mode2_ordinary_materials_regression_pass',
            'v306_gather_formula_regression_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v314.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v314.json').write_text(text, encoding='utf-8')
    print('ALL v1.314 TESTS PASSED!')


if __name__ == '__main__':
    main()
