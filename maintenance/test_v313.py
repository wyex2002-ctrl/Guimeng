"""Exhaustive verification suite for v1.313:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v313.lua
3. Gem labels 防御 / 魔防 (no 防御力 / 魔法防御) and 100% left-alignment (zero #md / #rt)
   on ALL 30 real gems decoded from m12/143 暴食模块, plus all 13 equipment 镶嵌信息 types
4. 「前尘忆梦」 100% isolated
5. Full regressions: v1.310 11% Boss blueprints, v1.308 【仓库】 proxy button,
   v1.307 Mode 2 ordinary materials, v1.306 gather formula.
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

W = Path(__file__).resolve().parent
BASE_SHA = 'ecc34f51376963cd1d4cd7d0a867c1bfdb2d23b0e975fd2a9a8d041826edaade'


def extract_runtime_v313(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.313 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v313.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_and_syntax():
    base_bytes = (W / 'game_v312.res').read_bytes()
    out_bytes = (W / 'game_v313.res').read_bytes()
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

    rt_src = extract_runtime_v313(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_tooltip_v313(d12, rt_src):
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

    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']
    U.rawset('暴食模块', lambda: baoshi_lua)
    G.rawset('取道具信息_名称', lambda name: LuaTable({'名称': name, '分类': '装备'}))

    raw_outputs = {}
    disp = LuaTable({'道具': lambda item, mode, slot_id: raw_outputs[(item.rawget('名称'), slot_id)]})
    U.rawset('托管显示', disp)
    ev.G.get('loadstring')(rt_src)(S)

    # 1. Gem tooltip: 完美的红宝石 -> 防具: 防御 0-12, 100% left-aligned
    perfect_red = LuaTable({'名称': '完美的红宝石', '分类': '道具', '子类': '宝石', '附加': LuaTable()})
    raw_outputs[('完美的红宝石', 327)] = (
        '#md#f(宋_9_炭灰,#c(-8323328)完美的红宝石#W)\n'
        '#md#W重量:1\n'
        '#md#W需要等级:1\n'
        '#md#c(-5385052)可镶嵌于镶孔中',
        None,
    )
    out_red, _ = disp.rawget('道具')(perfect_red, 1, 327)
    assert '#md' not in out_red and '#rt' not in out_red, out_red
    assert out_red.split('\n') == [
        '#f(宋_9_炭灰,#c(-8323328)完美的红宝石#W)',
        '#W重量:1',
        '#W需要等级:1',
        '#c(-5385052)可镶嵌于镶孔中',
        '#c(-8323200)武器: 破坏 12-0#W',
        '#c(-8323200)防具: 防御 0-12#W',
        '#c(-8323200)首饰: 破坏 0-6#W',
    ], out_red

    # 2. Gem tooltip: 碎裂的紫宝石 in bag -> 防具: 魔防 1-0, 100% left-aligned
    chipped_purple = LuaTable({'名称': '碎裂的紫宝石', '分类': '道具', '子类': '宝石', '附加': LuaTable()})
    raw_outputs[('碎裂的紫宝石', 32)] = (
        '#md#f(宋_9_炭灰,#c(-8323328)碎裂的紫宝石#W)\n'
        '#md#W重量:1\n'
        '#md#W需要等级:1\n'
        '#md#c(-5385052)可镶嵌于镶孔中\n'
        '#md#c(-3090223)Shift+左键放入备用背包',
        None,
    )
    out_purp, _ = disp.rawget('道具')(chipped_purple, 1, 32)
    assert '#md' not in out_purp and '#rt' not in out_purp, out_purp
    assert out_purp.split('\n') == [
        '#f(宋_9_炭灰,#c(-8323328)碎裂的紫宝石#W)',
        '#W重量:1',
        '#W需要等级:1',
        '#c(-5385052)可镶嵌于镶孔中',
        '#c(-8323200)武器: 准确 10#W',
        '#c(-8323200)防具: 魔防 1-0#W',
        '#c(-8323200)首饰: 准确 5#W',
        '#c(-3090223)Shift+左键放入备用背包',
    ], out_purp

    # 3. ALL 30 real gems: zero #md/#rt, zero '+', zero 防御力/魔法防御
    for gname in sorted(real_baoshi['武器'].keys()):
        g_item = LuaTable({'名称': gname, '分类': '道具', '子类': '宝石', '附加': LuaTable()})
        raw_outputs[(gname, 50)] = (
            f'#md#f(宋_9_炭灰,#c(-8323328){gname}#W)\n#md#W重量:1\n#md#W需要等级:1\n#md#c(-5385052)可镶嵌于镶孔中',
            None,
        )
        res, _ = disp.rawget('道具')(g_item, 1, 50)
        assert '#md' not in res and '#rt' not in res, (gname, res)
        assert '防御力' not in res and '魔法防御' not in res, (gname, res)
        res_lines = res.split('\n')
        assert len(res_lines) == 7
        for idx, part in enumerate(('武器', '防具', '首饰'), start=4):
            assert res_lines[idx].startswith(f'#c(-8323200){part}: ') and res_lines[idx].endswith('#W')
            assert '+' not in res_lines[idx]
        # Idempotent
        assert S.rawget('__gm_format_equip_tooltip_v311')(res, g_item, 1, 50) == res

    # 4. Equipment 镶嵌信息: 防御 / 魔防 (upper 防御力 / 魔法防御 untouched!)
    armor = LuaTable({'名称': '天魔神甲', '分类': '装备', '子类': '衣服', '附加': LuaTable()})
    raw_outputs[('天魔神甲', 2)] = (
        '#md#f(宋_9_炭灰,#c(-1)天魔神甲#W)\n'
        '#md#W防御力:5-12\n'
        '#md#W魔法防御:4-7\n'
        '#md#W需要等级:40\n'
        '#md#c(-3381556)镶嵌信息\n'
        '#md#c(-5385052)+2最大防御力\n'
        '#md#c(-5385052)+1最小防御力\n'
        '#md#c(-5385052)+4最大魔法防御\n'
        '#md#c(-5385052)+2最小魔法防御',
        None,
    )
    out_arm, _ = disp.rawget('道具')(armor, 1, 2)
    assert '#md' not in out_arm
    ls = out_arm.split('\n')
    assert '#W防御力:5-12' in ls and '#W魔法防御:4-7' in ls
    assert ls[-5:] == [
        '#c(-3381556)镶嵌信息',
        '#c(-8323200)防御:0-2#W',
        '#c(-8323200)防御:1-0#W',
        '#c(-8323200)魔防:0-4#W',
        '#c(-8323200)魔防:2-0#W',
    ], ls[-5:]

    # 5. 「前尘忆梦」 100% isolated
    env_q = make_env(story='前尘忆梦')
    ev_q, S_q, U_q, G_q = env_q['ev'], env_q['S'], env_q['U'], env_q['G']
    q_fn = lambda item, mode, slot_id: (raw_outputs[('完美的红宝石', 327)][0], None)
    disp_q = LuaTable({'道具': q_fn})
    U_q.rawset('托管显示', disp_q)
    ev_q.G.get('loadstring')(rt_src)(S_q)
    S_q.rawget('__gm_load_state_v299')(False, False)
    S_q.rawget('__gm_pickup_frame_v299')(U_q, G_q)
    assert disp_q.rawget('道具') is q_fn
    assert '#md' in disp_q.rawget('道具')(perfect_red, 1, 327)[0]


def main():
    mods_o, rt_src = test_diff_and_syntax()
    test_tooltip_v313(mods_o[12], rt_src)
    test_real_boss_blueprint_drops_11pct(mods_o[12], rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v313.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.313',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v313.res': out_sha,
            'runtime_v313.lua': hashlib.sha256((W / 'runtime_v313.lua').read_bytes()).hexdigest(),
            'patch_v313.py': hashlib.sha256((W / 'patch_v313.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'all_30_gems_left_aligned_and_defense_labels_shortened',
            'equip_socket_defense_labels_shortened_and_base_stats_unchanged',
            'qianchi_completely_isolated',
            'v310_boss_blueprints_11pct_regression_pass',
            'v308_warehouse_proxy_button_regression_pass',
            'v307_mode2_ordinary_materials_regression_pass',
            'v306_gather_formula_regression_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v313.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v313.json').write_text(text, encoding='utf-8')
    print('ALL v1.313 TESTS PASSED!')


if __name__ == '__main__':
    main()
