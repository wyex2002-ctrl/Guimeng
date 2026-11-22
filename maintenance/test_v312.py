"""Exhaustive verification suite for v1.312:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v312.lua
3. Equipment 镶嵌信息 format (no '+' and no '(+X)'), while equipment's own top stats stay untouched
4. All 30 real socketable gem items decoded from m12/143 暴食模块:
   - Gem tooltip appends 武器 / 防具 / 首饰 effects right after 可镶嵌于镶孔中
     (and before Shift+左键放入备用背包 when in bag), with zero '+' signs
   - Idempotent on repeated calls; non-socketable items untouched
5. 「前尘忆梦」 100% isolated (both equip and gem tooltips untouched)
6. Full regressions: v1.310 11% Boss blueprints, v1.308 【仓库】 proxy button,
   v1.307 Mode 2 ordinary materials, v1.306 gather formula.
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

W = Path(__file__).resolve().parent
BASE_SHA = 'aeb6d266d97617fe974ed956983026e544c47e761b83dda883d04ae865faf17e'


def extract_runtime_v312(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.312 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v312.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def decode_real_baoshi_143(m12):
    """Extract the real 武器 / 防具 / 首饰 tables of Ux雌.暴食模块() from m12/143."""
    p = m12.protos[143]

    def dec(v):
        if isinstance(v, bytes):
            return v.decode('gbk', 'replace')
        if isinstance(v, tuple) and v[0] == 'table':
            return [dec(x) for x in v[1]]
        if isinstance(v, tuple) and v[0] == 'int':
            return v[1]
        return v

    lines = dis(p).splitlines()
    mod = {}
    cur_entries = {}
    last_arr = None
    for ln in lines[690:976]:
        m_tdup = re.search(r'TDUP\s+\d+\s+\d+\s+\d+\s+D=\s*(\d+)', ln)
        if m_tdup:
            dv = dec(p.gc(int(m_tdup.group(1))))
            if isinstance(dv, list) and len(dv) == 4 and dv[0] is None:
                last_arr = dv[1:]
        elif 'KSTR' in ln:
            m_str = re.search(r"'([^']+)'\s*$", ln)
            if not m_str:
                continue
            s = m_str.group(1)
            if s in ('武器', '防具', '首饰'):
                mod[s] = cur_entries
                cur_entries = {}
                last_arr = None
            elif s.endswith('宝石') and '的' in s and last_arr is not None:
                cur_entries[s] = last_arr
                last_arr = None
    assert set(mod.keys()) == {'武器', '防具', '首饰'}
    for part in ('武器', '防具', '首饰'):
        assert len(mod[part]) == 30, f'Expected 30 gems in {part}, got {len(mod[part])}'
    return mod


def test_diff_and_syntax():
    base_bytes = (W / 'game_v311.res').read_bytes()
    out_bytes = (W / 'game_v312.res').read_bytes()
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

    rt_src = extract_runtime_v312(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_tooltip_v312(d12, rt_src):
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

    templates = {
        '魔法手镯': LuaTable({'名称': '魔法手镯', '分类': '装备', '子类': '手镯', '攻冰元素': 0}),
        '裁决之杖': LuaTable({'名称': '裁决之杖', '分类': '装备', '子类': '武器'}),
        '天魔神甲': LuaTable({'名称': '天魔神甲', '分类': '装备', '子类': '衣服'}),
        '沃玛手镯': LuaTable({'名称': '沃玛手镯', '分类': '装备', '子类': '手镯', '攻冰元素': 0}),
    }
    G.rawset('取道具信息_名称', lambda name: templates.get(name))

    raw_outputs = {}
    disp = LuaTable({'道具': lambda item, mode, slot_id: raw_outputs[(item.rawget('名称'), slot_id)]})
    U.rawset('托管显示', disp)

    ev.G.get('loadstring')(rt_src)(S)

    # --- 1. Equipped 魔法手镯: upper stats KEEP (+X) / +, lower 镶嵌信息 has NO '+' ---
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
        None,
    )
    out1, _ = disp.rawget('道具')(bracelet, 1, 6)
    lines1 = out1.split('\n')
    assert '#md' not in out1 and '(MAX)' not in out1
    # Upper equipment stats MUST remain unchanged with (+4) / +4 / +7 / +6
    assert '#c(-8323200)灵魂系魔法:0-4#c(-8323200) (+4)#W' in lines1
    assert '#c(-8323200)准确:+4#c(-8323200) (+4)#W' in lines1
    assert '#c(-8323328)攻击元素: 冰(寒冰) +4' in lines1
    assert '#c(-5385052)+7破防几率' in lines1
    # Lower 镶嵌信息 MUST have NO '+' and NO '(+1)'
    assert lines1[-2:] == ['#c(-3381556)镶嵌信息', '#c(-8323200)破坏:0-1#W'], lines1[-2:]
    assert '+' not in lines1[-1]

    # --- 2. All 13 gem stat types in equipment 镶嵌信息 (zero '+' signs) ---
    raw_outputs[('魔法手镯', 7)] = (
        '#md#f(宋_9_炭灰,#c(-21198)魔法手镯#W)\n#md#W需要等级:1\n'
        '#md#c(-3381556)镶嵌信息\n'
        '#md#c(-5385052)+1最大破坏\n'
        '#md#c(-5385052)+2最小破坏\n'
        '#md#c(-5385052)+3最大自然\n'
        '#md#c(-5385052)+4最小自然\n'
        '#md#c(-5385052)+5最大灵魂\n'
        '#md#c(-5385052)+6最小灵魂\n'
        '#md#c(-5385052)+2最大防御力\n'
        '#md#c(-5385052)+1最小防御力\n'
        '#md#c(-5385052)+4最大魔法防御\n'
        '#md#c(-5385052)+2最小魔法防御\n'
        '#md#c(-5385052)+15准确\n'
        '#md#c(-5385052)+10生命值上限\n'
        '#md#c(-5385052)+20魔法值上限',
        None,
    )
    out2, _ = disp.rawget('道具')(bracelet, 1, 7)
    gem_lines = out2.split('\n')[-14:]
    assert gem_lines == [
        '#c(-3381556)镶嵌信息',
        '#c(-8323200)破坏:0-1#W',
        '#c(-8323200)破坏:2-0#W',
        '#c(-8323200)自然系魔法:0-3#W',
        '#c(-8323200)自然系魔法:4-0#W',
        '#c(-8323200)灵魂系魔法:0-5#W',
        '#c(-8323200)灵魂系魔法:6-0#W',
        '#c(-8323200)防御力:0-2#W',
        '#c(-8323200)防御力:1-0#W',
        '#c(-8323200)魔法防御:0-4#W',
        '#c(-8323200)魔法防御:2-0#W',
        '#c(-8323200)准确:15#W',
        '#c(-8323200)生命值:10#W',
        '#c(-8323200)魔法值:20#W',
    ], gem_lines
    for gl in gem_lines:
        assert '+' not in gl, gl

    # --- 3. Set equipment preserves 套装信息 lines with '+' untouched ---
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
        '#md+5准确',
        None,
    )
    out_set, _ = disp.rawget('道具')(set_eq, 1, 402)
    ls = out_set.split('\n')
    assert '#c(-8323200)破坏:0-3#W' in ls
    assert '#c(-5385052)+10雷(雷电)伤害' in ls and '+5准确' in ls

    # --- 4. Gem item tooltips: 完美的红宝石 (gem window, matching screenshot) ---
    perfect_red = LuaTable({'名称': '完美的红宝石', '分类': '道具', '子类': '宝石', '附加': LuaTable()})
    raw_outputs[('完美的红宝石', 327)] = (
        '#md#f(宋_9_炭灰,#c(-8323328)完美的红宝石#W)\n'
        '#md#W重量:1\n'
        '#md#W需要等级:1\n'
        '#md#c(-5385052)可镶嵌于镶孔中',
        None,
    )
    out_gem1, _ = disp.rawget('道具')(perfect_red, 1, 327)
    assert out_gem1.split('\n') == [
        '#md#f(宋_9_炭灰,#c(-8323328)完美的红宝石#W)',
        '#md#W重量:1',
        '#md#W需要等级:1',
        '#md#c(-5385052)可镶嵌于镶孔中',
        '#md#c(-8323200)武器: 破坏 12-0#W',
        '#md#c(-8323200)防具: 防御力 0-12#W',
        '#md#c(-8323200)首饰: 破坏 0-6#W',
    ], out_gem1

    # --- 5. Gem item in bag (with Shift+左键放入备用背包) ---
    chipped_purple = LuaTable({'名称': '碎裂的紫宝石', '分类': '道具', '子类': '宝石', '附加': LuaTable()})
    raw_outputs[('碎裂的紫宝石', 32)] = (
        '#md#f(宋_9_炭灰,#c(-8323328)碎裂的紫宝石#W)\n'
        '#md#W重量:1\n'
        '#md#W需要等级:1\n'
        '#md#c(-5385052)可镶嵌于镶孔中\n'
        '#md#c(-3090223)Shift+左键放入备用背包',
        None,
    )
    out_gem2, _ = disp.rawget('道具')(chipped_purple, 1, 32)
    assert out_gem2.split('\n') == [
        '#md#f(宋_9_炭灰,#c(-8323328)碎裂的紫宝石#W)',
        '#md#W重量:1',
        '#md#W需要等级:1',
        '#md#c(-5385052)可镶嵌于镶孔中',
        '#md#c(-8323200)武器: 准确 10#W',
        '#md#c(-8323200)防具: 魔法防御 1-0#W',
        '#md#c(-8323200)首饰: 准确 5#W',
        '#md#c(-3090223)Shift+左键放入备用背包',
    ], out_gem2

    # --- 6. Verify ALL 30 real gems from m12/143 暴食模块 ---
    for gname in sorted(real_baoshi['武器'].keys()):
        g_item = LuaTable({'名称': gname, '分类': '道具', '子类': '宝石', '附加': LuaTable()})
        raw_outputs[(gname, 50)] = (
            f'#md#f(宋_9_炭灰,#c(-8323328){gname}#W)\n#md#W重量:1\n#md#W需要等级:1\n#md#c(-5385052)可镶嵌于镶孔中',
            None,
        )
        res, _ = disp.rawget('道具')(g_item, 1, 50)
        res_lines = res.split('\n')
        assert len(res_lines) == 7, (gname, res_lines)
        for idx, part in enumerate(('武器', '防具', '首饰'), start=4):
            ln = res_lines[idx]
            assert ln.startswith(f'#md#c(-8323200){part}: ') and ln.endswith('#W'), (gname, ln)
            assert '+' not in ln, f'Unexpected + in gem line: {gname} -> {ln}'
        # Idempotency check
        res_twice = S.rawget('__gm_format_equip_tooltip_v311')(res, g_item, 1, 50)
        assert res_twice == res, f'Not idempotent for {gname}'

    # --- 7. Non-socketable gem-subclass item (e.g. 魔晶石) untouched ---
    crystal = LuaTable({'名称': '魔晶石', '分类': '道具', '子类': '宝石', '附加': LuaTable()})
    raw_c = '#md#W魔晶石\n#md#c(-5385052)用于解锁镶孔'
    raw_outputs[('魔晶石', 60)] = (raw_c, None)
    out_c, _ = disp.rawget('道具')(crystal, 1, 60)
    assert out_c == raw_c

    # --- 8. 「前尘忆梦」 100% isolated ---
    env_q = make_env(story='前尘忆梦')
    ev_q, S_q, U_q, G_q = env_q['ev'], env_q['S'], env_q['U'], env_q['G']
    q_fn = lambda item, mode, slot_id: (raw_outputs[('完美的红宝石', 327)][0], None)
    disp_q = LuaTable({'道具': q_fn})
    U_q.rawset('托管显示', disp_q)
    ev_q.G.get('loadstring')(rt_src)(S_q)
    S_q.rawget('__gm_load_state_v299')(False, False)
    S_q.rawget('__gm_pickup_frame_v299')(U_q, G_q)
    assert disp_q.rawget('道具') is q_fn
    assert '武器: ' not in disp_q.rawget('道具')(perfect_red, 1, 327)[0]


def main():
    mods_o, rt_src = test_diff_and_syntax()
    test_tooltip_v312(mods_o[12], rt_src)
    test_real_boss_blueprint_drops_11pct(mods_o[12], rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v312.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.312',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v312.res': out_sha,
            'runtime_v312.lua': hashlib.sha256((W / 'runtime_v312.lua').read_bytes()).hexdigest(),
            'patch_v312.py': hashlib.sha256((W / 'patch_v312.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'equip_base_stats_unchanged_with_plus_and_parens',
            'equip_socket_gem_lines_all_13_types_zero_plus_signs',
            'set_equipment_preserves_set_bonus_lines',
            'all_30_real_gems_from_m12_143_append_weapon_armor_jewelry_lines_zero_plus',
            'gem_in_bag_inserts_before_shift_backup_bag_hint',
            'gem_tooltip_idempotent_and_non_socketable_untouched',
            'qianchi_completely_isolated',
            'v310_boss_blueprints_11pct_regression_pass',
            'v308_warehouse_proxy_button_regression_pass',
            'v307_mode2_ordinary_materials_regression_pass',
            'v306_gather_formula_regression_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v312.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v312.json').write_text(text, encoding='utf-8')
    print('ALL v1.312 TESTS PASSED!')


if __name__ == '__main__':
    main()
