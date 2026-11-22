"""Exhaustive verification suite for v1.319:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v319.lua
3. Blueprint drag restriction via S.tbl_qs.qs_item_box.Main:
   - Allowed only on 武器 / 衣服 / 头盔 / 坐骑 (immediate recalc if applied on equipped slot)
   - Blocked on 项链 / 手镯 / 戒指 / 鞋子 / 勋章 / 饰品 with red prompt; blueprint NOT consumed
   - Non-blueprints & 装备操作 >= 1 pass through untouched
4. 1-piece activation across all 40 real sets in m12/143 天竺葵家 (restored on 「前尘忆梦」)
5. Whole-body max-1 active set bonus (Hero 1..13 -> 物品格子14 & Merc 397..409 -> 物品格子410,
   using authentic m48/1+m48/2 __call-table proxies!):
   - Single allowed piece activates immediately
   - Two different sets on allowed slots -> only 1st activates, 2nd inactive (grey tooltip)
   - Unequipping 1st (ev_type=3) immediately activates 2nd
   - Two identical sets -> stats applied ONCE (never doubled)
   - Old save with 2 legacy slots (手镯 + 戒指) -> max 1 activates
   - Old save with legacy slot (手镯) + allowed slot (坐骑) -> allowed slot prioritized, max 1 total
   - Mercenary independent from Hero, also capped at max 1
6. Real m12/6488 Boss blueprint drop rate = 5.50% (all 34 Boss entries rewritten to 200,200;
   11/200 = 5.50% exact under 11x rule; 24 trash-mob entries untouched; 「前尘忆梦」 restored)
7. Blueprint tooltip yellow hint = #Y拖到武器/衣服/头盔/坐骑使用#W
8. 「前尘忆梦」 100% isolated + full regressions (v1.317/v1.316/v1.308/v1.307/v1.306).
"""
import hashlib
import json
import math
import re
from pathlib import Path

from ljdis import dis
from ljtool import Dump
from lua51_eval import LuaTable, syntax_check
from native_test_utils import trees
from patch_v239 import OPS
from resource_tools import decode
from test_v300 import make_env
from test_v307 import test_mode2_ordinary_materials, test_v306_regression
from test_v308 import test_authentic_proxy_warehouse_button
from test_v309 import ALL_32_BLUEPRINTS, decode_real_monsters_6488
from test_v316 import test_tooltips_v316
from test_v317 import test_compact_equip_spaces_v317

W = Path(__file__).resolve().parent
BASE_SHA = 'e048d215fec806c874d208d2e97d841dc487939598ef86774b1a58fcfb9607b7'


def extract_runtime_v319(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.319 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v319.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def decode_real_sets_full_143(m12):
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
                    sets[s] = (last_hsh, last_arr[2], last_arr[3])
                    last_arr = None
                    last_hsh = None
    assert len(sets) == 40
    return sets


def make_slot_proxy(ev):
    """Authentic m48/1+m48/2 callable proxy table for 物品格子14 / 物品格子410."""
    code = """
    local internal = { resets = 0, updates = 0, stats = {}, item = { 名称 = '背包格子', 附加 = {} } }
    function internal:重置道具(name, cnt, flag)
     self.resets = self.resets + 1
     self.stats = {}
     self.item = { 名称 = name, 附加 = {} }
    end
    function internal:更新道具属性(stats_tbl)
     self.updates = self.updates + 1
     local copy = {}
     for k, v in pairs(stats_tbl) do copy[k] = v end
     self.stats = copy
    end
    local proxy = {}
    setmetatable(proxy, {
     __index = function(t, k)
      if k == '道具' then return internal.item end
      if k == '重置道具' or k == '更新道具属性' then
       rawset(t, 'k', k)
       return t
      end
      return nil
     end,
     __call = function(t, a1, a2, a3)
      local m = rawget(t, 'k')
      return internal[m](internal, a1, a2, a3)
     end,
    })
    return internal, proxy
    """
    return ev.G.get('loadstring')(code)()


def test_diff_and_syntax():
    base_bytes = (W / 'game_v318.res').read_bytes()
    out_bytes = (W / 'game_v319.res').read_bytes()
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

    rt_src = extract_runtime_v319(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_set_rules_v319(d12, rt_src):
    real_sets = decode_real_sets_full_143(d12)
    sets_lua = LuaTable()
    for name, (hsh, req, desc) in real_sets.items():
        st = LuaTable(hsh)
        entry = LuaTable()
        entry.rawset(1, st)
        entry.rawset(2, req)
        entry.rawset(3, desc)
        sets_lua.rawset(name, entry)

    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']

    U.rawset('天竺葵家', lambda: sets_lua)
    op_cfg = LuaTable({'装备操作': 0})
    U.rawset('胚子考虑', lambda: op_cfg)

    prompts = []
    disp = LuaTable({'屏幕提示': lambda msg, col=None: prompts.append((msg, col))})
    U.rawset('托管显示', disp)

    orig_calls = {'hero': 0, 'merc': 0, 'box': 0}
    wr = LuaTable({
        '套装属性': lambda a, b: orig_calls.__setitem__('hero', orig_calls['hero'] + 1),
        '佣兵套装': lambda a, b: orig_calls.__setitem__('merc', orig_calls['merc'] + 1),
    })
    U.rawset('窗口相关', wr)

    cells = {}

    def get_cell(sid):
        return cells.get(sid)

    G.rawset('从ID取格子', get_cell)
    G.rawset('鼠标道具', 0)

    def orig_box_main(ev_type, slot_id, a3=None, a4=None, a5=None):
        orig_calls['box'] += 1
        # Simulate native m12/37 pc=2998..3019 applying blueprint
        mid = G.rawget('鼠标道具')
        if ev_type == 4 and mid and mid > 0:
            tc = cells.get(slot_id)
            sc = cells.get(mid)
            if tc and sc and tc.rawget('道具') and sc.rawget('道具'):
                sex = sc.rawget('道具').rawget('附加')
                if sex and sex.rawget('套装属性') is not None:
                    tc.rawget('道具').rawget('附加').rawset('套装属性', sex.rawget('套装属性'))
                    sc.rawset('道具', None)
                    return True
        return None

    box_tbl = LuaTable({'Main': orig_box_main})
    S.rawset('tbl_qs', LuaTable({'qs_item_box': box_tbl}))

    h14_internal, h14_proxy = make_slot_proxy(ev)
    m410_internal, m410_proxy = make_slot_proxy(ev)
    ss = S.rawget('script_setting')
    ss.rawset('Gly独', G)
    ss.rawset('物品格子14', h14_proxy)
    ss.rawset('物品格子410', m410_proxy)

    def stats_dict(internal):
        return dict(internal.rawget('stats')._data)

    def holder_extra(internal):
        return internal.rawget('item').rawget('附加')

    # Load runtime_v319.lua
    ev.G.get('loadstring')(rt_src)(S)

    # 1. Verify all 40 sets now require 1 piece
    for name in real_sets:
        assert sets_lua.rawget(name).rawget(2) == 1, f'Expected req=1 for {name}'

    # 2. Verify blueprint drag restrictions on all 10 equipment subclasses
    def make_eq(sub, sname=None):
        ex = LuaTable({'套装属性': sname}) if sname else LuaTable()
        return LuaTable({'道具': LuaTable({'名称': '测试' + sub, '分类': '装备', '子类': sub, '附加': ex})})

    def make_bp(sname):
        return LuaTable({'道具': LuaTable({'名称': sname, '分类': '道具', '子类': '材料', '附加': LuaTable({'套装属性': sname})})})

    for disallowed in ('项链', '手镯', '戒指', '鞋子', '勋章', '饰品'):
        cells[32] = make_eq(disallowed)
        cells[33] = make_bp('虎战领主之爪')
        G.rawset('鼠标道具', 33)
        prompts.clear()
        prev_box_calls = orig_calls['box']
        ret = box_tbl.rawget('Main')(4, 32)
        assert ret is True, f'Expected blocked return true for {disallowed}'
        assert orig_calls['box'] == prev_box_calls, f'orig_box must NOT run for {disallowed}'
        assert cells[32].rawget('道具').rawget('附加').rawget('套装属性') is None
        assert cells[33].rawget('道具') is not None, f'Blueprint must NOT be consumed for {disallowed}'
        assert len(prompts) == 1 and '武器、衣服、头盔或坐骑' in prompts[0][0], prompts

    for allowed in ('武器', '衣服', '头盔', '坐骑'):
        cells[32] = make_eq(allowed)
        cells[33] = make_bp('虎战领主之爪')
        G.rawset('鼠标道具', 33)
        prompts.clear()
        ret = box_tbl.rawget('Main')(4, 32)
        assert ret is True
        assert cells[32].rawget('道具').rawget('附加').rawget('套装属性') == '虎战领主之爪'
        assert cells[33].rawget('道具') is None, f'Blueprint should be consumed for {allowed}'
        assert len(prompts) == 0

    # 3. Single piece activation on Hero (slot 1 武器 = 虎战领主之爪, originally required 6 pieces!)
    cells.clear()
    cells[1] = make_eq('武器', '虎战领主之爪')
    wr.rawget('套装属性')(1, 1)
    assert stats_dict(h14_internal) == real_sets['虎战领主之爪'][0], stats_dict(h14_internal)
    assert holder_extra(h14_internal).rawget('虎战领主之爪') == 1

    # 4. Two allowed pieces with DIFFERENT sets -> ONLY 1st activates (max 1 whole-body!)
    cells[2] = make_eq('衣服', '沃玛教主的利爪')
    wr.rawget('套装属性')(2, 1)
    assert stats_dict(h14_internal) == real_sets['虎战领主之爪'][0], stats_dict(h14_internal)
    assert holder_extra(h14_internal).rawget('虎战领主之爪') == 1
    assert holder_extra(h14_internal).rawget('沃玛教主的利爪') is None

    # 5. Unequipping slot 1 (ev_type=3) immediately promotes slot 2 (沃玛教主的利爪) as sole active set
    wr.rawget('套装属性')(1, 3)
    assert stats_dict(h14_internal) == real_sets['沃玛教主的利爪'][0], stats_dict(h14_internal)
    assert holder_extra(h14_internal).rawget('沃玛教主的利爪') == 1
    assert holder_extra(h14_internal).rawget('虎战领主之爪') is None

    # 6. Two allowed pieces with SAME set -> stats applied ONCE (never doubled!)
    cells[1] = make_eq('武器', '虎战领主之爪')
    cells[2] = make_eq('衣服', '虎战领主之爪')
    wr.rawget('套装属性')(2, 1)
    assert stats_dict(h14_internal) == real_sets['虎战领主之爪'][0], stats_dict(h14_internal)

    # 7. Old save scenario A: ONLY 2 legacy slots equipped (手镯 + 戒指) -> max 1 active!
    cells.clear()
    cells[6] = make_eq('手镯', '沃玛教主的利爪')
    cells[8] = make_eq('戒指', '触龙神的毒囊')
    wr.rawget('套装属性')(None, None)
    assert stats_dict(h14_internal) == real_sets['沃玛教主的利爪'][0], stats_dict(h14_internal)
    assert holder_extra(h14_internal).rawget('沃玛教主的利爪') == 1
    assert holder_extra(h14_internal).rawget('触龙神的毒囊') is None

    # 8. Old save scenario B: legacy slot (手镯) + allowed slot (坐骑 at slot 13) -> allowed slot prioritized, max 1 total!
    cells[13] = make_eq('坐骑', '虎战领主之爪')
    wr.rawget('套装属性')(13, 1)
    assert stats_dict(h14_internal) == real_sets['虎战领主之爪'][0], stats_dict(h14_internal)
    assert holder_extra(h14_internal).rawget('虎战领主之爪') == 1
    assert holder_extra(h14_internal).rawget('沃玛教主的利爪') is None

    # 9. Applying blueprint directly onto equipped allowed slot (slot 3 头盔) triggers immediate recalc
    cells.clear()
    cells[3] = make_eq('头盔')
    cells[35] = make_bp('骷髅教主的火种')
    G.rawset('鼠标道具', 35)
    box_tbl.rawget('Main')(4, 3)
    assert stats_dict(h14_internal) == real_sets['骷髅教主的火种'][0], stats_dict(h14_internal)

    # 10. Mercenary independent max-1 enforcement (slots 397..409 -> 物品格子410)
    cells[397] = make_eq('武器', '毁灭之爪')
    cells[398] = make_eq('衣服', '皇陵鲲吾剑')
    wr.rawget('佣兵套装')(398, 1)
    assert stats_dict(m410_internal) == real_sets['毁灭之爪'][0], stats_dict(m410_internal)
    assert holder_extra(m410_internal).rawget('毁灭之爪') == 1
    assert holder_extra(m410_internal).rawget('皇陵鲲吾剑') is None
    assert stats_dict(h14_internal) == real_sets['骷髅教主的火种'][0], 'Hero set must stay independent from Merc'

    # 11. Blueprint tooltip hint shows updated yellow allowed-slot text
    bp_item = LuaTable({'名称': '虎战领主之爪', '分类': '道具', '子类': '材料', '附加': LuaTable({'套装属性': '虎战领主之爪'})})
    raw_bp = '#md#W重量:1\n#md#c(-5385052)+50最大伤害值\n#md#c(-45824)拖到装备使用'
    fmt_bp = S.rawget('__gm_format_equip_tooltip_v311')(raw_bp, bp_item, 1, 32)
    assert '#Y拖到武器/衣服/头盔/坐骑使用#W' in fmt_bp.split('\n'), fmt_bp

    # 12. Switching to 「前尘忆梦」 restores all 40 original required counts & delegates to original handlers
    U.rawset('版本选择', '前尘忆梦')
    S.rawget('__gm_pickup_frame_v299')(U, G)
    for name, (_, orig_req, _) in real_sets.items():
        assert sets_lua.rawget(name).rawget(2) == orig_req, f'Expected restored req={orig_req} for {name}'
    prev_h = orig_calls['hero']
    wr.rawget('套装属性')(1, 1)
    assert orig_calls['hero'] == prev_h + 1
    # Drag onto bracelet in 「前尘忆梦」 is NOT blocked by v319
    cells[40] = make_eq('手镯')
    cells[41] = make_bp('沃玛教主的利爪')
    G.rawset('鼠标道具', 41)
    box_tbl.rawget('Main')(4, 40)
    assert cells[40].rawget('道具').rawget('附加').rawget('套装属性') == '沃玛教主的利爪'


def test_real_boss_blueprint_drops_5_5pct(d12, rt_src):
    cb_11x = [
        pid for pid, p in enumerate(d12.protos)
        if len(p.bc) == 1178 and OPS[p.bc[1174] & 255] == 'KSHORT'
        and ((p.bc[1174] >> 8) & 255) == 14 and (p.bc[1174] >> 16) == 11
    ]
    assert len(cb_11x) == 247

    real_monsters = decode_real_monsters_6488(d12)
    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']

    char_group = LuaTable()
    orig_map = {}
    for mname, (drop_str, is_boss) in real_monsters.items():
        if not drop_str:
            continue
        orig_map[mname] = (drop_str, is_boss)
        extra_raw = LuaTable({'BOSS': 0}) if is_boss else LuaTable()
        raw_cfg = LuaTable({'名称': mname, 'drop_item': drop_str, '附加': LuaTable({'__数据': extra_raw})})
        char_group.rawset(mname, LuaTable({'__数据': raw_cfg}))
    S.rawset('游戏属性组', char_group)

    drop_cache = LuaTable({'沃玛教主': 'STALE', '赤龙魔王': 'STALE', '天狼蜘蛛': 'KEEP'})
    U.rawset('伯伯扣扣', lambda: drop_cache)

    ev.G.get('loadstring')(rt_src)(S)
    S.rawget('__gm_load_state_v299')(True, False)

    assert drop_cache.rawget('沃玛教主') is None
    assert drop_cache.rawget('赤龙魔王') is None
    assert drop_cache.rawget('天狼蜘蛛') == 'KEEP'

    boss_bp_entries = 0
    mob_bp_entries = 0
    covered = set()
    for mname, (orig_str, is_boss) in orig_map.items():
        cur_str = char_group.rawget(mname).rawget('__数据').rawget('drop_item')
        for oe, ce in zip([e for e in orig_str.split('|') if e], [e for e in cur_str.split('|') if e]):
            op, cp = oe.split(','), ce.split(',')
            if op[0] in ALL_32_BLUEPRINTS:
                if is_boss:
                    assert cp == [op[0], op[1], '200', '200'], f'{mname} {op[0]}: expected 200,200 got {cp}'
                    eff_n = math.ceil(int(cp[2]) / 1)
                    eff_p = min(11, eff_n) / eff_n
                    assert abs(eff_p - 0.055) < 1e-12, f'{mname} {op[0]}: expected 5.5%, got {eff_p}'
                    boss_bp_entries += 1
                    covered.add(op[0])
                else:
                    assert ce == oe
                    mob_bp_entries += 1
            else:
                assert ce == oe

    assert boss_bp_entries == 34 and mob_bp_entries == 24 and covered == ALL_32_BLUEPRINTS

    U.rawset('版本选择', '前尘忆梦')
    S.rawget('__gm_pickup_frame_v299')(U, G)
    for mname, (orig_str, _) in orig_map.items():
        assert char_group.rawget(mname).rawget('__数据').rawget('drop_item') == orig_str


def main():
    mods_o, rt_src = test_diff_and_syntax()
    test_set_rules_v319(mods_o[12], rt_src)
    test_real_boss_blueprint_drops_5_5pct(mods_o[12], rt_src)
    test_compact_equip_spaces_v317(rt_src)
    test_tooltips_v316(mods_o[12], rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v319.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.319',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v319.res': out_sha,
            'runtime_v319.lua': hashlib.sha256((W / 'runtime_v319.lua').read_bytes()).hexdigest(),
            'patch_v319.py': hashlib.sha256((W / 'patch_v319.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'blueprint_drag_restricted_to_weapon_armor_helmet_mount',
            'all_40_sets_require_1_piece_and_restore_on_qianchi',
            'whole_body_max_1_set_hero_and_merc_with_authentic_m48_proxies',
            'old_save_legacy_slots_capped_at_max_1_and_deprioritized_below_allowed_slots',
            'all_34_boss_entries_covering_32_blueprints_rewritten_to_200_exact_5_5pct',
            'blueprint_tooltip_yellow_hint_lists_4_allowed_slots',
            'qianchi_completely_isolated',
            'v317_v316_v308_v307_v306_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v319.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v319.json').write_text(text, encoding='utf-8')
    print('ALL v1.319 TESTS PASSED!')


if __name__ == '__main__':
    main()
