"""Exhaustive verification suite for v1.332:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v332.lua
3. m12/37 (qs_item_box.Main) still has ZERO JMP instructions with A < params
4. Corpse-digging direct-drop 极品 stats fix (v1.332):
   - build_live_drop_item writes flattened rolled stat fields from wr.全图窗口 into out.属性[k]
     (matching m14/86 & m14/447), preserves out.颜色值/价格/物品腕力/附加/live sprites, and does not mutate S.游戏道具组.
   - corpse_drop_v301 supports gly.取道具信息_名称 as function, callable table, or nil (fallback to S.游戏道具组),
     calls wr.全图窗口(item_name, mlv, nil, nil, mon_extra), and preserves rolled 极品 stats on dropped equipment.
   - saved_dig fallback branch also preserves flattened/nested 极品 stats in out.属性.
5. Mercenary single-handed ranged weapon 「（远程）」 display tag fix (v1.332):
   - Pure Merc ranged weapons (职业要求=='刺客' & 绑定技能=='刺客普通攻击', e.g. 玄月): show 「（远程）」 everywhere.
   - Pure Merc two-handed melee weapons (职业要求=='刺客' & 绑定技能=='刺客双手攻击', e.g. 潜龙双剑): never show 「（远程）」.
   - Hero / general weapons (职业要求=='不限', 装备通用=0, 绑定技能=='刺客普通攻击', e.g. 精灵骸骨, 拍拍手, 纯净的白灵之刃):
     never show 「（远程）」 on ground (nil), Hero equip (1), Hero bag (35), and strip stale 「（远程）」 if already present;
     ONLY show 「（远程）」 in Merc slots (333..410).
   - Pure Hero weapons (职业要求=='战士', no 装备通用): never show 「（远程）」 even if stored in Merc bag (340).
   - pickup_frame restores __gm_merc_name_v253 if clobbered by m14/420, and refreshes stale non-刺客 weapon tooltips once after load.
   - 「前尘忆梦」 delegates untouched to original __gm_merc_name_v253.
6. Full v1.331 + v1.330 + v1.319 + v1.317 + v1.308 + v1.307 + v1.306 regressions.
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
from test_v330 import test_v330_split_bracelet_ring_gems
from test_v331 import test_v331_gem_tooltip_cache_refresh

W = Path(__file__).resolve().parent
BASE_SHA = 'b9d05b41d64f2dbfd657c4c2a466f3bcb90b8af63a009aeded60b9a2dea385d2'


def extract_runtime_v332(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.332 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v332.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_syntax_and_m12_37():
    base_bytes = (W / 'game_v331.res').read_bytes()
    out_bytes = (W / 'game_v332.res').read_bytes()
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

    rt_src = extract_runtime_v332(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def make_weapon_tpl(name, job, extra_dict, min_atk=8, max_atk=30):
    return LuaTable({
        '名称': name,
        '显示名': name,
        '分类': '装备',
        '子类': '武器',
        '职业要求': job,
        '价格': 1000,
        '颜色值': 4294967295,
        '物品腕力': 15,
        '地面精灵': f'ground_sprite_{name}',
        '精灵': f'icon_sprite_{name}',
        '属性': LuaTable({
            '最小破坏': min_atk,
            '最大破坏': max_atk,
            '暴击': 0,
            '抵抗暴击': 0,
            '攻火元素': 0,
            '生命药水恢复量': 0,
        }),
        '附加': LuaTable(extra_dict),
    })


def test_v332_corpse_drop_jipin_stats(rt_src):
    for info_mode in ('function', 'callable_table', 'nil_fallback'):
        env = make_env(story='来世续缘')
        ev, S, U, G = env['ev'], env['S'], env['U'], env['G']

        tpl = make_weapon_tpl('精灵骸骨', '不限', {'装备通用': 0, '绑定技能': '刺客普通攻击'})
        S.rawset('游戏道具组', LuaTable({'精灵骸骨': tpl}))

        # Mock 岗位上的() returning 骷髅精灵 -> 精灵骸骨 (denom 1 = guaranteed)
        dig_tbl = LuaTable({
            '骷髅精灵': LuaTable({1: LuaTable({1: '精灵骸骨', 2: 1})}),
        })
        U.rawset('岗位上的', lambda: dig_tbl)

        roll_calls = []

        def fake_roll(name, mlv, arg3=None, arg4=None, mon_extra=None):
            roll_calls.append((name, mlv, arg3, arg4, mon_extra))
            # Exact flattened format returned by m12/196 (wr.全图窗口)
            return LuaTable({
                '名称': name,
                '显示名': name,
                '分类': '装备',
                '子类': '武器',
                '职业要求': '不限',
                '价格': 4500,
                '颜色值': 4287090411,
                '物品腕力': 1,
                '最小破坏': 12,
                '最大破坏': 42,
                '暴击': 15,
                '抵抗暴击': 25,
                '攻火元素': 5,
                '生命药水恢复量': 80,
                '地面精灵': 'should_be_ignored',
                '附加': LuaTable({'条数': 3, '等级': mlv, '装备通用': 0, '绑定技能': '刺客普通攻击'}),
            })

        U.rawset('窗口相关', LuaTable({'全图窗口': fake_roll}))

        if info_mode == 'function':
            G.rawset('取道具信息_名称', lambda nm: LuaTable({'名称': nm, '分类': '装备', '子类': '武器'}))
        elif info_mode == 'callable_table':
            callable_tbl = LuaTable()
            callable_tbl.mt = LuaTable({'__call': lambda self_t, nm: LuaTable({'名称': nm, '分类': '装备', '子类': '武器'})})
            G.rawset('取道具信息_名称', callable_tbl)
        else:
            G.rawset('取道具信息_名称', None)

        ev.G.get('loadstring')(rt_src)(S)

        mon_extra = LuaTable({'等级': 35, 'BOSS': 1})
        actor = LuaTable({
            'id': 77,
            '属性': LuaTable({'名称': '骷髅精灵', '等级': 35, '附加': mon_extra}),
            '附加': LuaTable(),
        })
        drops = LuaTable()
        added = S.rawget('__gm_corpse_drop_v301')(actor, drops)
        assert added == 1, f'[{info_mode}] expected 1 drop, got {added}'
        assert len(roll_calls) == 1, f'[{info_mode}] wr.全图窗口 not called!'
        assert roll_calls[0][0] == '精灵骸骨'
        assert roll_calls[0][1] == 35
        assert roll_calls[0][2] is None
        assert roll_calls[0][3] is None, f'[{info_mode}] arg4 should be nil like normal drops, got {roll_calls[0][3]}'
        assert roll_calls[0][4] is mon_extra

        drop_entry = drops.rawget(1)
        out = drop_entry.rawget('物品道具')
        assert out is not None
        # Critical check: ALL rolled 极品 stats MUST live inside out.属性 (so pickup + m14/224 preserves them!)
        out_props = out.rawget('属性')
        assert out_props.rawget('最小破坏') == 12, f'[{info_mode}] 最小破坏={out_props.rawget("最小破坏")}'
        assert out_props.rawget('最大破坏') == 42, f'[{info_mode}] 最大破坏={out_props.rawget("最大破坏")}'
        assert out_props.rawget('暴击') == 15, f'[{info_mode}] 暴击={out_props.rawget("暴击")}'
        assert out_props.rawget('抵抗暴击') == 25, f'[{info_mode}] 抵抗暴击={out_props.rawget("抵抗暴击")}'
        assert out_props.rawget('攻火元素') == 5
        assert out_props.rawget('生命药水恢复量') == 80
        # Top-level metadata & live sprites preserved
        assert out.rawget('颜色值') == 4287090411
        assert out.rawget('价格') == 4500
        assert out.rawget('物品腕力') == 1
        assert out.rawget('地面精灵') == 'ground_sprite_精灵骸骨'
        assert out.rawget('精灵') == 'icon_sprite_精灵骸骨'
        assert out.rawget('附加').rawget('条数') == 3
        # Template in S.游戏道具组 MUST NOT be mutated
        assert tpl.rawget('属性').rawget('最大破坏') == 30
        assert tpl.rawget('属性').rawget('暴击') == 0

    # Also test saved_dig fallback path preserves flattened 极品 stats
    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']
    S.rawset('游戏道具组', LuaTable({'精灵骸骨': make_weapon_tpl('精灵骸骨', '不限', {'装备通用': 0})}))
    U.rawset('岗位上的', lambda: LuaTable())
    ev.G.get('loadstring')(rt_src)(S)
    saved_item = LuaTable({'名称': '精灵骸骨', '最大破坏': 44, '暴击': 18, '颜色值': 4287090411, '附加': LuaTable({'条数': 2})})
    actor2 = LuaTable({'id': 78, '属性': LuaTable({'名称': '神秘怪'}), '附加': LuaTable({'挖取': LuaTable({1: saved_item})})})
    drops2 = LuaTable()
    assert S.rawget('__gm_corpse_drop_v301')(actor2, drops2) == 1
    out2 = drops2.rawget(1).rawget('物品道具')
    assert out2.rawget('属性').rawget('最大破坏') == 44
    assert out2.rawget('属性').rawget('暴击') == 18
    assert out2.rawget('附加').rawget('条数') == 2


def test_v332_merc_ranged_weapon_tag(rt_src):
    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']
    ss = S.rawget('script_setting')

    # Simulate original buggy m14/408 __gm_merc_name_v253
    orig_calls = []

    def orig_merc_name(item, display_name, slot_id=None):
        orig_calls.append((display_name, slot_id))
        if not isinstance(display_name, str):
            return display_name
        ex = item.rawget('附加') if isinstance(item, LuaTable) else None
        bind = ex.rawget('绑定技能') if isinstance(ex, LuaTable) else '刺客普通攻击'
        if bind != '刺客普通攻击':
            return display_name
        explicit = isinstance(ex, LuaTable) and ex.rawget('绑定技能') is not None
        if not explicit and not (isinstance(slot_id, (int, float)) and 333 <= slot_id <= 410):
            return display_name
        if display_name.endswith('（远程）'):
            return display_name
        return display_name + '（远程）'

    ev.G.rawset('__gm_merc_name_v253', orig_merc_name)
    ss.rawset('__gm_merc_name_v253', orig_merc_name)

    # Templates for fallback lookup
    S.rawset('游戏道具组', LuaTable({
        '玄月': make_weapon_tpl('玄月', '刺客', {'绑定技能': '刺客普通攻击'}),
        '潜龙双剑': make_weapon_tpl('潜龙双剑', '刺客', {'绑定技能': '刺客双手攻击'}),
        '精灵骸骨': make_weapon_tpl('精灵骸骨', '不限', {'装备通用': 0, '绑定技能': '刺客普通攻击'}),
        '拍拍手': make_weapon_tpl('拍拍手', '不限', {'装备通用': 0, '绑定技能': '刺客普通攻击'}),
        '纯净的白灵之刃': make_weapon_tpl('纯净的白灵之刃', '不限', {'装备通用': 0, '绑定技能': '刺客普通攻击'}),
        '屠龙': make_weapon_tpl('屠龙', '战士', {}),
    }))

    # Existing bag item in Hero bag (slot 35) with stale 「（远程）」 baked in
    bag = S.rawget('包裹物品组')
    stale_bone = make_weapon_tpl('精灵骸骨', '不限', {'装备通用': 0, '绑定技能': '刺客普通攻击'})
    stale_bone.rawset('显示名', '精灵骸骨（远程）')
    bag.rawset(35, LuaTable({'道具': stale_bone}))
    bag.rawset(397, LuaTable({'道具': make_weapon_tpl('精灵骸骨', '不限', {'装备通用': 0, '绑定技能': '刺客普通攻击'})}))

    refreshed_slots = []
    ctrls = LuaTable()
    for cid in (35, 397):
        def make_cb(slot_i):
            return lambda self_obj=None: refreshed_slots.append(slot_i)
        ctrls.rawset(f'物品格子{cid}', LuaTable({
            '格子ID': cid,
            '对象': LuaTable({'焦点': False, '更新道具属性': make_cb(cid)}),
        }))
    S.rawset('tbl_controls', ctrls)

    ev.G.get('loadstring')(rt_src)(S)
    fn_g = ev.G.rawget('__gm_merc_name_v253')
    fn_s = ss.rawget('__gm_merc_name_v253')
    assert fn_g is fn_s and fn_g is not orig_merc_name

    # 1. Pure Merc ranged weapon (玄月): ALWAYS shows （远程）
    xuanyue = make_weapon_tpl('玄月', '刺客', {'绑定技能': '刺客普通攻击'})
    assert fn_g(xuanyue, '玄月', None) == '玄月（远程）'
    assert fn_g(xuanyue, '玄月', 35) == '玄月（远程）'
    assert fn_g(xuanyue, '玄月', 397) == '玄月（远程）'
    assert fn_g(xuanyue, '玄月（远程）', 397) == '玄月（远程）'  # no double tag

    # 2. Pure Merc two-handed melee weapon (潜龙双剑): NEVER shows （远程）
    qianlong = make_weapon_tpl('潜龙双剑', '刺客', {'绑定技能': '刺客双手攻击'})
    assert fn_g(qianlong, '潜龙双剑', None) == '潜龙双剑'
    assert fn_g(qianlong, '潜龙双剑', 35) == '潜龙双剑'
    assert fn_g(qianlong, '潜龙双剑', 397) == '潜龙双剑'

    # 3. General / Hero weapons (精灵骸骨, 拍拍手, 纯净的白灵之刃):
    #    NO （远程） on ground, Hero equip (1), Hero bag (35); strips stale （远程）;
    #    ONLY shows （远程） in Merc slots (333..410).
    for nm in ('精灵骸骨', '拍拍手', '纯净的白灵之刃'):
        w = make_weapon_tpl(nm, '不限', {'装备通用': 0, '绑定技能': '刺客普通攻击'})
        assert fn_g(w, nm, None) == nm
        assert fn_g(w, nm, 1) == nm
        assert fn_g(w, nm, 35) == nm
        assert fn_g(w, nm + '（远程）', 35) == nm, f'Failed to strip stale tag on {nm}'
        assert fn_g(w, nm, 333) == nm + '（远程）'
        assert fn_g(w, nm, 397) == nm + '（远程）'
        assert fn_g(w, nm + '（远程）', 397) == nm + '（远程）'

    # 4. Fallback job lookup from S.游戏道具组 when item.职业要求 is nil
    w_nojob = LuaTable({'名称': '精灵骸骨', '分类': '装备', '子类': '武器', '附加': LuaTable({'装备通用': 0, '绑定技能': '刺客普通攻击'})})
    assert fn_g(w_nojob, '精灵骸骨', 35) == '精灵骸骨'
    assert fn_g(w_nojob, '精灵骸骨', 397) == '精灵骸骨（远程）'

    # 5. Pure Hero warrior weapon (屠龙, no 装备通用): NEVER shows （远程） even stored in Merc bag (340)
    tulong = make_weapon_tpl('屠龙', '战士', {})
    assert fn_g(tulong, '屠龙', 35) == '屠龙'
    assert fn_g(tulong, '屠龙', 340) == '屠龙'

    # 6. pickup_frame recovers from m14/420 clobbering AND refreshes stale Hero bag 精灵骸骨 tooltip once
    ev.G.rawset('__gm_merc_name_v253', orig_merc_name)
    ss.rawset('__gm_merc_name_v253', orig_merc_name)
    S.rawget('__gm_pickup_frame_v299')(U, G)
    fn_re = ev.G.rawget('__gm_merc_name_v253')
    assert fn_re is not orig_merc_name
    assert ss.rawget('__gm_merc_name_v253') is fn_re
    assert fn_re(make_weapon_tpl('精灵骸骨', '不限', {'装备通用': 0, '绑定技能': '刺客普通攻击'}), '精灵骸骨', 35) == '精灵骸骨'
    assert stale_bone.rawget('显示名') == '精灵骸骨'
    assert refreshed_slots == [35], f'Expected only Hero slot 35 refreshed, got {refreshed_slots}'

    # Next frame does NOT redundantly refresh
    refreshed_slots.clear()
    S.rawget('__gm_pickup_frame_v299')(U, G)
    assert refreshed_slots == []

    # 7. 「前尘忆梦」 delegates untouched to orig_merc_name
    U.rawset('版本选择', '前尘忆梦')
    orig_calls.clear()
    bone = make_weapon_tpl('精灵骸骨', '不限', {'装备通用': 0, '绑定技能': '刺客普通攻击'})
    res_qc = fn_g(bone, '精灵骸骨', 35)
    assert res_qc == '精灵骸骨（远程）' and len(orig_calls) == 1


def main():
    mods_o, rt_src = test_diff_syntax_and_m12_37()
    test_v332_corpse_drop_jipin_stats(rt_src)
    test_v332_merc_ranged_weapon_tag(rt_src)
    test_v331_gem_tooltip_cache_refresh(rt_src)
    test_v330_split_bracelet_ring_gems(mods_o[12], rt_src)
    test_real_boss_blueprint_drops_5_5pct(mods_o[12], rt_src)
    test_compact_equip_spaces_v317(rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v332.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.332',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v332.res': out_sha,
            'runtime_v332.lua': hashlib.sha256((W / 'runtime_v332.lua').read_bytes()).hexdigest(),
            'patch_v332.py': hashlib.sha256((W / 'patch_v332.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'm12_37_zero_jmp_below_params_preserved',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'corpse_drop_merges_flattened_jipin_stats_into_out_shuxing_across_function_callable_table_and_fallback',
            'corpse_drop_passes_normal_drop_args_to_wr_quantuchuangko_and_preserves_saved_dig_jipin_stats',
            'merc_ranged_tag_only_global_on_pure_assassin_ranged_weapons_and_merc_slot_only_on_general_weapons',
            'stale_ranged_tag_stripped_and_cached_hero_bag_weapon_tooltips_refreshed_once_on_load',
            'pickup_frame_restores_merc_name_wrapper_after_m14_420_clobber_and_qianchi_isolated',
            'v331_v330_v319_v317_v308_v307_v306_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v332.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v332.json').write_text(text, encoding='utf-8')
    print('ALL v1.332 TESTS PASSED!')


if __name__ == '__main__':
    main()
