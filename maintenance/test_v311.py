"""Exhaustive verification suite for v1.311:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v311.lua
3. v1.311 Mir3 equipment tooltip & socketed gem formatting tests (「来世续缘」 only):
   - Equipped 魔法手镯 (guild active, 1x 碎裂的红宝石): left-aligned Mir3 layout restored,
     攻击元素 moved above 需要等级, 强元素 combined on 1 line, (MAX) removed,
     镶嵌信息 kept pink and +1最大破坏 formatted as 破坏:0-1 (+1)
   - Equipped 银镜项链 (guild active, no gems): left-aligned Mir3 layout restored,
     攻击元素: 雷(电击) +9 moved above 需要等级
   - All 13 暴食模块 gem stat types (武器/防具/首饰) verified, 1 line per socketed gem
   - 3 strong elements wrapping indentation (\u3000\u3000\u3000 )
   - Set equipment (套装属性) with +10雷(雷电)伤害 inside 套装信息 preserved verbatim
   - Bag equipment already formatted by m12/320 remains byte-identical with no 镶嵌信息
   - Second return value (width) preserved; re-wrap works if Ux雌.托管显示 is recreated
   - 「前尘忆梦」 100% untouched (never wrapped; pass-through if switched back)
4. Full regressions: v1.310 11% Boss blueprints, v1.308 【仓库】 proxy button,
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

W = Path(__file__).resolve().parent
BASE_SHA = '99d7f72d7da3ee8a14da360facbd76273f2467e2bd21278982c8d9cf39b59534'


def extract_runtime_v311(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.311 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v311.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_and_syntax():
    base_bytes = (W / 'game_v310.res').read_bytes()
    out_bytes = (W / 'game_v311.res').read_bytes()
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

    rt_src = extract_runtime_v311(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_tooltip_v311(rt_src):
    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']

    templates = {
        '魔法手镯': LuaTable({'名称': '魔法手镯', '分类': '装备', '子类': '手镯', '攻冰元素': 0}),
        '银镜项链': LuaTable({'名称': '银镜项链', '分类': '装备', '子类': '项链', '攻雷元素': 0}),
        '裁决之杖': LuaTable({'名称': '裁决之杖', '分类': '装备', '子类': '武器'}),
        '天魔神甲': LuaTable({'名称': '天魔神甲', '分类': '装备', '子类': '衣服'}),
        '沃玛手镯': LuaTable({'名称': '沃玛手镯', '分类': '装备', '子类': '手镯', '攻冰元素': 0}),
    }
    G.rawset('取道具信息_名称', lambda name: templates.get(name))

    raw_outputs = {}

    def fake_orig_321(item, mode, slot_id):
        key = (item.rawget('名称'), slot_id)
        return raw_outputs[key]

    disp = LuaTable({'道具': fake_orig_321})
    U.rawset('托管显示', disp)

    ev.G.get('loadstring')(rt_src)(S)
    assert disp.rawget('道具') is not fake_orig_321, 'Expected Ux雌.托管显示.道具 to be wrapped on init'

    # --- Scenario 1: Screenshot 3 exact case (equipped 魔法手镯, guild active, 1x 碎裂的红宝石) ---
    bracelet = LuaTable({
        '名称': '魔法手镯', '分类': '装备', '子类': '手镯', '攻冰元素': 4,
        '附加': LuaTable({'条数': 7}),
    })
    raw_outputs[('魔法手镯', 6)] = (
        '#md#f(宋_9_炭灰,#c(-21198)魔法手镯#W)\n'
        '#md#W重量:1\n'
        '#md#W防御力:0-2\n'
        '#md#W魔法防御:2-4\n'
        '#md#c(-8323200)灵魂系魔法:0-4#c(-8323200) (+4)#W\n'
        '#md#c(-8323200)准确:+4#c(-8323200) (+4)#W\n'
        '#md#c(-8323328)强元素:火(火焰)×3\n'
        '#md#c(-8323328)强元素:雷(电击)×3\n'
        '#md#W需要等级:1\n'
        '#md#c(-5385052)+7破防几率\n'
        '#md#c(-8323328)+4冰(寒冰)伤害 (MAX)\n'
        '#md#c(-5385052)+6暴击 (MAX)\n'
        '#md#c(-3381556)镶嵌信息\n'
        '#md#c(-5385052)+1最大破坏',
        260,
    )
    out1, w1 = disp.rawget('道具')(bracelet, 1, 6)
    assert w1 == 260, f'Expected width 260 preserved, got {w1}'
    assert '#md' not in out1 and '#rt' not in out1 and '(MAX)' not in out1, out1
    lines1 = out1.split('\n')
    assert lines1[0] == '#f(宋_9_炭灰,#c(4294946098)魔法手镯#W)', lines1[0]
    assert '#c(-8323328)攻击元素: 冰(寒冰) +4' in lines1, lines1
    assert '#c(-8323328)强元素:火(火焰)×3 #c(-8323328)雷(电击)×3' in lines1, lines1
    atk_idx = lines1.index('#c(-8323328)攻击元素: 冰(寒冰) +4')
    str_idx = lines1.index('#c(-8323328)强元素:火(火焰)×3 #c(-8323328)雷(电击)×3')
    req_idx = lines1.index('#W需要等级:1')
    assert atk_idx < str_idx < req_idx, (atk_idx, str_idx, req_idx)
    assert not any('冰(寒冰)伤害' in ln for ln in lines1), lines1
    assert lines1[-2] == '#c(-3381556)镶嵌信息', lines1[-2:]
    assert lines1[-1] == '#c(-8323200)破坏:0-1 (+1)#W', lines1[-2:]

    # --- Scenario 2: Screenshot 4 exact case (equipped 银镜项链, guild active, NO gems) ---
    necklace = LuaTable({
        '名称': '银镜项链', '分类': '装备', '子类': '项链', '攻雷元素': 9,
        '附加': LuaTable({'条数': 7}),
    })
    raw_outputs[('银镜项链', 4)] = (
        '#md#f(宋_9_炭灰,#c(-21198)银镜项链#W)\n'
        '#md#W重量:1\n'
        '#md#c(-8323200)破坏:0-12#c(-8323200) (+12)#W\n'
        '#md#c(-8323200)自然系魔法:0-7#c(-8323200) (+7)#W\n'
        '#md#c(-8323200)灵魂系魔法:4-19#c(-8323200) (+11)#W\n'
        '#md#c(-8323200)准确:+12#c(-8323200) (+12)#W\n'
        '#md#W需要等级:1\n'
        '#md#c(-8323328)+9雷(雷电)伤害\n'
        '#md#c(-5385052)+12暴击\n'
        '#md#c(-5385052)击中生命恢复+7',
        None,
    )
    out2, w2 = disp.rawget('道具')(necklace, 1, 4)
    assert w2 is None
    assert '#md' not in out2 and '雷(雷电)伤害' not in out2, out2
    lines2 = out2.split('\n')
    assert lines2.index('#c(-8323328)攻击元素: 雷(电击) +9') < lines2.index('#W需要等级:1'), lines2
    assert '#c(-5385052)+12暴击' in lines2 and '#c(-5385052)击中生命恢复+7' in lines2

    # --- Scenario 3: All 13 暴食模块 gem stat types (one line per gem) ---
    # 3a. 首饰: 2 red + 1 blue + 1 green + 1 purple (5 gems)
    raw_outputs[('魔法手镯', 7)] = (
        '#md#f(宋_9_炭灰,#c(-21198)魔法手镯#W)\n'
        '#md#W需要等级:1\n'
        '#md#c(-3381556)镶嵌信息\n'
        '#md#c(-5385052)+1最大破坏\n'
        '#md#c(-5385052)+2最大破坏\n'
        '#md#c(-5385052)+3最大自然\n'
        '#md#c(-5385052)+4最大灵魂\n'
        '#md#c(-5385052)+15准确',
        None,
    )
    out3a, _ = disp.rawget('道具')(bracelet, 1, 7)
    assert out3a.split('\n')[-6:] == [
        '#c(-3381556)镶嵌信息',
        '#c(-8323200)破坏:0-1 (+1)#W',
        '#c(-8323200)破坏:0-2 (+2)#W',
        '#c(-8323200)自然系魔法:0-3 (+3)#W',
        '#c(-8323200)灵魂系魔法:0-4 (+4)#W',
        '#c(-8323200)准确:+15 (+15)#W',
    ], out3a

    # 3b. 武器: min 破坏/自然/灵魂 + 生命值上限 + 魔法值上限
    weapon = LuaTable({'名称': '裁决之杖', '分类': '装备', '子类': '武器', '附加': LuaTable()})
    raw_outputs[('裁决之杖', 1)] = (
        '#md#f(宋_9_炭灰,#c(-1)裁决之杖#W)\n'
        '#md#W需要等级:30\n'
        '#md#c(-3381556)镶嵌信息\n'
        '#md#c(-5385052)+2最小破坏\n'
        '#md#c(-5385052)+4最小自然\n'
        '#md#c(-5385052)+6最小灵魂\n'
        '#md#c(-5385052)+10生命值上限\n'
        '#md#c(-5385052)+20魔法值上限',
        None,
    )
    out3b, _ = disp.rawget('道具')(weapon, 1, 1)
    assert out3b.split('\n')[-6:] == [
        '#c(-3381556)镶嵌信息',
        '#c(-8323200)破坏:2-0 (+2)#W',
        '#c(-8323200)自然系魔法:4-0 (+4)#W',
        '#c(-8323200)灵魂系魔法:6-0 (+6)#W',
        '#c(-8323200)生命值:+10 (+10)#W',
        '#c(-8323200)魔法值:+20 (+20)#W',
    ], out3b

    # 3c. 防具: max/min 防御力 & max/min 魔法防御
    armor = LuaTable({'名称': '天魔神甲', '分类': '装备', '子类': '衣服', '附加': LuaTable()})
    raw_outputs[('天魔神甲', 2)] = (
        '#md#f(宋_9_炭灰,#c(-1)天魔神甲#W)\n'
        '#md#W需要等级:40\n'
        '#md#c(-3381556)镶嵌信息\n'
        '#md#c(-5385052)+2最大防御力\n'
        '#md#c(-5385052)+1最小防御力\n'
        '#md#c(-5385052)+4最大魔法防御\n'
        '#md#c(-5385052)+2最小魔法防御',
        None,
    )
    out3c, _ = disp.rawget('道具')(armor, 1, 2)
    assert out3c.split('\n')[-5:] == [
        '#c(-3381556)镶嵌信息',
        '#c(-8323200)防御力:0-2 (+2)#W',
        '#c(-8323200)防御力:1-0 (+1)#W',
        '#c(-8323200)魔法防御:0-4 (+4)#W',
        '#c(-8323200)魔法防御:2-0 (+2)#W',
    ], out3c

    # --- Scenario 4: 3 strong elements wrap cleanly with 3 ideographic spaces ---
    raw_outputs[('天魔神甲', 3)] = (
        '#md#f(宋_9_炭灰,#c(-1)天魔神甲#W)\n'
        '#md#c(-8323328)强元素:火(火焰)×3\n'
        '#md#c(-8323328)强元素:冰(寒冰)×2\n'
        '#md#c(-8323328)强元素:雷(电击)×1\n'
        '#md#W需要等级:40',
        None,
    )
    out4, _ = disp.rawget('道具')(armor, 1, 3)
    assert '#c(-8323328)强元素:火(火焰)×3 #c(-8323328)冰(寒冰)×2\n\u3000\u3000\u3000 #c(-8323328)雷(电击)×1' in out4, out4

    # --- Scenario 5: Set equipment (套装属性) + gems preserves 套装信息 elemental bonuses! ---
    set_eq = LuaTable({
        '名称': '沃玛手镯', '分类': '装备', '子类': '手镯', '攻冰元素': 4,
        '附加': LuaTable({'条数': 6, '套装属性': '沃玛教主的利爪'}),
    })
    raw_outputs[('沃玛手镯', 402)] = (
        '#md#f(宋_9_炭灰,#c(-1)沃玛手镯#W)\n'
        '#md#W需要等级:20\n'
        '#md#c(-8323328)+4冰(寒冰)伤害 (MAX)\n'
        '#md#c(-3381556)镶嵌信息\n'
        '#md#c(-5385052)+3最大破坏\n'
        '#md#G套装信息\n'
        '#md#c(-5385052)+10雷(雷电)伤害\n'
        '#md+5准确\n'
        '#md+50生命值上限\n'
        '#md+20雷(雷电)抗性',
        None,
    )
    out5, _ = disp.rawget('道具')(set_eq, 1, 402)
    assert '#md' not in out5 and '(MAX)' not in out5, out5
    lines5 = out5.split('\n')
    assert lines5[0] == '#f(宋_9_炭灰,#c(4293446776)沃玛手镯#W)', lines5[0]
    assert '#c(-8323328)攻击元素: 冰(寒冰) +4' in lines5
    assert lines5.index('#c(-8323328)攻击元素: 冰(寒冰) +4') < lines5.index('#W需要等级:20')
    assert '#c(-8323200)破坏:0-3 (+3)#W' in lines5
    # Critical check: 套装信息 lines must NOT be stripped or converted to gem format!
    assert '#G套装信息' in lines5
    assert '#c(-5385052)+10雷(雷电)伤害' in lines5, f'Set bonus element line was lost! {lines5}'
    assert '+5准确' in lines5
    assert '+50生命值上限' in lines5
    assert '+20雷(雷电)抗性' in lines5

    # --- Scenario 6: Bag equipment already formatted by m12/320 is byte-identical, no 镶嵌信息 ---
    bag_ready = (
        '#f(宋_9_炭灰,#c(4294946098)魔法手镯#W)\n'
        '#W重量:1\n'
        '#W防御力:0-2\n'
        '#W魔法防御:2-4\n'
        '#c(-8323328)攻击元素: 冰(寒冰) +4\n'
        '#c(-8323328)强元素:火(火焰)×3 #c(-8323328)雷(电击)×3\n'
        '#W需要等级:1\n'
        '#c(-5385052)+7破防几率'
    )
    raw_outputs[('魔法手镯', 32)] = (bag_ready, None)
    out6, _ = disp.rawget('道具')(bracelet, 1, 32)
    assert out6 == bag_ready, f'Bag tooltip changed unexpectedly:\n{out6}'
    assert '镶嵌信息' not in out6

    # --- Scenario 7: Recreating Ux雌.托管显示 (m12/327) is automatically re-wrapped on next tick ---
    disp2 = LuaTable({'道具': fake_orig_321})
    U.rawset('托管显示', disp2)
    S.rawget('__gm_pickup_frame_v299')(U, G)
    assert disp2.rawget('道具') is not fake_orig_321, 'Expected automatic re-wrap on pickup_frame'
    out7, _ = disp2.rawget('道具')(bracelet, 1, 6)
    assert '#c(-8323200)破坏:0-1 (+1)#W' in out7 and '#md' not in out7

    # --- Scenario 8: 「前尘忆梦」 100% isolated ---
    env_q = make_env(story='前尘忆梦')
    ev_q, S_q, U_q, G_q = env_q['ev'], env_q['S'], env_q['U'], env_q['G']
    q_raw = '#md#W前尘忆梦原版显示\n#md#c(-5385052)+1最大破坏'
    q_fn = lambda item, mode, slot_id: (q_raw, 200)
    disp_q = LuaTable({'道具': q_fn})
    U_q.rawset('托管显示', disp_q)
    ev_q.G.get('loadstring')(rt_src)(S_q)
    S_q.rawget('__gm_load_state_v299')(False, False)
    S_q.rawget('__gm_pickup_frame_v299')(U_q, G_q)
    assert disp_q.rawget('道具') is q_fn, '「前尘忆梦」 Ux雌.托管显示.道具 must NEVER be wrapped!'
    assert disp_q.rawget('道具')(bracelet, 1, 6) == (q_raw, 200)

    # Also verify switching story back to 「前尘忆梦」 passes through unmodified even if wrapped fn called
    U.rawset('版本选择', '前尘忆梦')
    out_sw, w_sw = disp2.rawget('道具')(bracelet, 1, 6)
    assert out_sw == raw_outputs[('魔法手镯', 6)][0] and w_sw == 260


def main():
    mods_o, rt_src = test_diff_and_syntax()
    test_tooltip_v311(rt_src)
    test_real_boss_blueprint_drops_11pct(mods_o[12], rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v311.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.311',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v311.res': out_sha,
            'runtime_v311.lua': hashlib.sha256((W / 'runtime_v311.lua').read_bytes()).hexdigest(),
            'patch_v311.py': hashlib.sha256((W / 'patch_v311.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'equipped_bracelet_guild_active_mir3_layout_and_gem_format',
            'equipped_necklace_guild_active_no_gems_mir3_layout',
            'all_13_baoshi_gem_stat_types_one_line_per_gem',
            'three_strong_elements_wrap_indent',
            'set_equipment_mir3_layout_preserves_set_bonus_elemental_lines',
            'bag_equipment_byte_identical_no_gem_info',
            'rewrap_after_disp_recreation_and_width_preserved',
            'qianchi_completely_isolated',
            'v310_boss_blueprints_11pct_regression_pass',
            'v308_warehouse_proxy_button_regression_pass',
            'v307_mode2_ordinary_materials_regression_pass',
            'v306_gather_formula_regression_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v311.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v311.json').write_text(text, encoding='utf-8')
    print('ALL v1.311 TESTS PASSED!')


if __name__ == '__main__':
    main()
