"""Exhaustive verification suite for v1.334:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v334.lua
3. m12/37 (qs_item_box.Main) still has ZERO JMP instructions with A < params
4. Mode 2 【拾取+出售】 updated rules (v1.334):
   - White AND 1..6 affix jipin 青铜斧 & 魔法长袍_女 ARE SOLD in Mode 2.
   - 7-affix orange 青铜斧 & 魔法长袍_女 ARE KEPT in Mode 2 (plus enchanted/transmogged/reinforced/lucky).
   - White 精灵骸骨 IS SOLD in Mode 2, while jipin/non-white 精灵骸骨 IS KEPT in Mode 2.
   - Alt pickup and Mode 1 (green) still PROTECT 青铜斧, 魔法长袍_女, 精灵骸骨 (white or jipin).
   - 鹤嘴锄, 坐骑号角_铜, Q猛虎, 禁止丢弃=true, non-white 颜色值 (in Alt/Mode 1) remain strictly protected.
5. Full v1.333 tooltip + v1.332 + v1.331 + v1.330 + v1.319 + v1.317 + v1.308 + v1.307 + v1.306 regressions.
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
from test_v332 import test_v332_corpse_drop_jipin_stats
from test_v333 import make_ground_equip_obj, test_v333_shared_weapon_tooltip_note

W = Path(__file__).resolve().parent
BASE_SHA = 'd0bb5562071a543f63317488cb7764b8c77c92ef17f6782db3b4d10abf44f6bd'


def extract_runtime_v334(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.334 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v334.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_syntax_and_m12_37():
    base_bytes = (W / 'game_v333.res').read_bytes()
    out_bytes = (W / 'game_v334.res').read_bytes()
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

    rt_src = extract_runtime_v334(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_v334_mode2_qingtongfu_mofachangpao_non7(rt_src):
    ref_db = {
        '青铜斧': {'名称': '青铜斧', '分类': '装备', '子类': '武器', '颜色值': 4294967295, '价格': 3500, '最小破坏': 5, '最大破坏': 10, '附加': {}},
        '魔法长袍_女': {'名称': '魔法长袍_女', '分类': '装备', '子类': '衣服', '颜色值': 4294967295, '价格': 10000, '最小防御': 3, '最大防御': 5, '附加': {}},
        '精灵骸骨': {'名称': '精灵骸骨', '分类': '装备', '子类': '武器', '颜色值': 4294967295, '价格': 5000, '最小破坏': 8, '最大破坏': 30, '附加': {'装备通用': 0, '绑定技能': '刺客普通攻击'}},
        '乌木剑': {'名称': '乌木剑', '分类': '装备', '子类': '武器', '颜色值': 4294967295, '价格': 1000, '最小破坏': 4, '最大破坏': 8, '附加': {}},
        '坐骑号角_铜': {'名称': '坐骑号角_铜', '分类': '装备', '子类': '坐骑', '颜色值': 4294828058, '价格': 5000000, '最小破坏': 0, '最大破坏': 0, '附加': {'外观': '枣红马'}},
        'Q猛虎': {'名称': 'Q猛虎', '分类': '装备', '子类': '坐骑', '颜色值': 4286643968, '价格': 2800, '最小破坏': 0, '最大破坏': 0, '附加': {}},
        '鹤嘴锄': {'名称': '鹤嘴锄', '分类': '装备', '子类': '武器', '颜色值': 4294967295, '价格': 700, '最小破坏': 1, '最大破坏': 5, '附加': {}},
    }

    def get_ref(nm):
        d = ref_db.get(nm)
        if not d:
            return None
        out = LuaTable()
        for k, v in d.items():
            out.rawset(k, LuaTable(v) if isinstance(v, dict) else v)
        return out

    def run_case(is_auto, auto_mode, build_items):
        env = make_env(story='来世续缘')
        ev, S, U, G = env['ev'], env['S'], env['U'], env['G']
        ev.G.get('loadstring')(rt_src)(S)
        gold_log = []
        U.rawset('窗口相关', LuaTable({'界面切换': lambda amt, *a: gold_log.append(amt)}))
        U.rawset('托管显示', LuaTable({'屏幕提示': lambda *a: None}))
        U.rawset('独角兽下', lambda: LuaTable({'极品数值': LuaTable({'最大破坏': 1, '最大防御': 1})}))
        G.rawset('取道具信息_名称', get_ref)
        G.rawset('取包裹空位', lambda *a: 30)

        picked = []
        bucket = LuaTable()
        for i, o in enumerate(build_items(picked), 1):
            bucket.rawset(i, o)
        qmap = ev.G.rawget('Q_地图').rawget('__gm_range_state')
        qmap.rawget('地面物品组').rawset(qmap.rawget('到逻辑格子')(10, 10), bucket)

        S.rawget('__gm_run_range_pickup_v299')(U, G, is_auto, auto_mode)
        return sum(gold_log), picked

    # --- Case A: Mode 2 【拾取+出售】 ---
    def items_mode2(picked):
        return [
            # White 青铜斧 (1750g) + 魔法长袍_女 (5000g) + 精灵骸骨 (2500g) -> SOLD (9250g)
            make_ground_equip_obj('青铜斧', '武器', 3500, 4294967295, {'最小破坏': 5, '最大破坏': 10}, {}, None, picked),
            make_ground_equip_obj('魔法长袍_女', '衣服', 10000, -1, {'最小防御': 3, '最大防御': 5}, {}, None, picked),
            make_ground_equip_obj('精灵骸骨', '武器', 5000, 4294967295, {'最小破坏': 8, '最大破坏': 30}, {'装备通用': 0, '绑定技能': '刺客普通攻击'}, None, picked),
            # 1..6 affix jipin 青铜斧 (3500->1750g, 6000->3000g) & 魔法长袍_女 (10000->5000g, 16000->8000g) -> SOLD (+17750g -> 27000g total!)
            make_ground_equip_obj('青铜斧', '武器', 3500, 4287090411, {'最小破坏': 5, '最大破坏': 18}, {'条数': 3}, None, picked),
            make_ground_equip_obj('青铜斧', '武器', 6000, 4293446776, {'最小破坏': 5, '最大破坏': 24}, {'条数': 6}, None, picked),
            make_ground_equip_obj('魔法长袍_女', '衣服', 10000, 4287090411, {'最小防御': 3, '最大防御': 9}, {'条数': 3}, None, picked),
            make_ground_equip_obj('魔法长袍_女', '衣服', 16000, 4293446776, {'最小防御': 3, '最大防御': 14}, {'条数': 6}, None, picked),
            # 7-affix bright orange 青铜斧 & 魔法长袍_女 -> MUST BE KEPT!
            make_ground_equip_obj('青铜斧', '武器', 9000, 4294946098, {'最小破坏': 5, '最大破坏': 30}, {'条数': 7}, None, picked),
            make_ground_equip_obj('魔法长袍_女', '衣服', 20000, 4294946098, {'最小防御': 3, '最大防御': 20}, {'条数': 7}, None, picked),
            # Enchanted 3-affix 青铜斧 -> MUST BE KEPT!
            make_ground_equip_obj('青铜斧', '武器', 3500, 4287090411, {'最小破坏': 5, '最大破坏': 18}, {'条数': 3, '套装属性': '虎战领主之爪'}, None, picked),
            # Jipin 精灵骸骨 (3-affix) & non-white 精灵骸骨 -> STILL KEPT in Mode 2!
            make_ground_equip_obj('精灵骸骨', '武器', 5000, 4287090411, {'最小破坏': 8, '最大破坏': 42}, {'条数': 3, '装备通用': 0, '绑定技能': '刺客普通攻击'}, None, picked),
            make_ground_equip_obj('精灵骸骨', '武器', 5000, 4294828058, {'最小破坏': 8, '最大破坏': 30}, {'装备通用': 0, '绑定技能': '刺客普通攻击'}, None, picked),
            # Mounts, 禁止丢弃, 鹤嘴锄 -> STILL KEPT!
            make_ground_equip_obj('坐骑号角_铜', '坐骑', 5000000, 4294828058, {'最小破坏': 0, '最大破坏': 0}, {'外观': '枣红马'}, None, picked),
            make_ground_equip_obj('Q猛虎', '坐骑', 2800, 4286643968, {'最小破坏': 0, '最大破坏': 0}, {}, None, picked),
            make_ground_equip_obj('乌木剑', '武器', 1000, 4294967295, {'最小破坏': 4, '最大破坏': 8}, {}, {'禁止丢弃': True}, picked),
            make_ground_equip_obj('鹤嘴锄', '武器', 700, 4294967295, {'最小破坏': 1, '最大破坏': 5}, {}, None, picked),
        ]

    gold2, picked2 = run_case(True, 2, items_mode2)
    assert gold2 == 27000, f'Expected 27000 gold, got {gold2}, picked={picked2}'
    assert len(picked2) == 9, f'Expected 9 protected items kept, got {len(picked2)}: {picked2}'
    assert picked2.count('青铜斧_jipin') == 2  # 7-affix + enchanted 3-affix
    assert picked2.count('魔法长袍_女_jipin') == 1  # 7-affix only
    assert '精灵骸骨_jipin' in picked2 and '精灵骸骨' in picked2
    assert '坐骑号角_铜' in picked2 and 'Q猛虎' in picked2 and '鹤嘴锄' in picked2

    # --- Case B: Manual Alt & Mode 1 (green) STILL protect white 青铜斧/魔法长袍_女/精灵骸骨 ---
    def items_white_modes(picked):
        return [
            make_ground_equip_obj('青铜斧', '武器', 3500, 4294967295, {'最小破坏': 5, '最大破坏': 10}, {}, None, picked),
            make_ground_equip_obj('魔法长袍_女', '衣服', 10000, 4294967295, {'最小防御': 3, '最大防御': 5}, {}, None, picked),
            make_ground_equip_obj('精灵骸骨', '武器', 5000, 4294967295, {'最小破坏': 8, '最大破坏': 30}, {'装备通用': 0, '绑定技能': '刺客普通攻击'}, None, picked),
            make_ground_equip_obj('乌木剑', '武器', 1000, 4294967295, {'最小破坏': 4, '最大破坏': 8}, {}, None, picked),  # SELL -> 500g
        ]

    for is_auto, mode, label in ((False, 0, 'Alt'), (True, 1, 'Mode1')):
        g_amt, p_list = run_case(is_auto, mode, items_white_modes)
        assert g_amt == 500, f'[{label}] expected 500g, got {g_amt}, picked={p_list}'
        assert p_list == ['青铜斧', '魔法长袍_女', '精灵骸骨'], f'[{label}] unexpected picked: {p_list}'


def main():
    mods_o, rt_src = test_diff_syntax_and_m12_37()
    test_v334_mode2_qingtongfu_mofachangpao_non7(rt_src)
    test_v333_shared_weapon_tooltip_note(rt_src)
    test_v332_corpse_drop_jipin_stats(rt_src)
    test_v331_gem_tooltip_cache_refresh(rt_src)
    test_v330_split_bracelet_ring_gems(mods_o[12], rt_src)
    test_real_boss_blueprint_drops_5_5pct(mods_o[12], rt_src)
    test_compact_equip_spaces_v317(rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v334.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.334',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v334.res': out_sha,
            'runtime_v334.lua': hashlib.sha256((W / 'runtime_v334.lua').read_bytes()).hexdigest(),
            'patch_v334.py': hashlib.sha256((W / 'patch_v334.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'm12_37_zero_jmp_below_params_preserved',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'mode2_sells_white_and_1_to_6_affix_qingtongfu_and_mofachangpao_while_keeping_7_affix_and_special_state',
            'mode2_keeps_jipin_jinglinghaigu_and_alt_mode1_still_protect_all_three',
            'v333_v332_v331_v330_v319_v317_v308_v307_v306_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v334.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v334.json').write_text(text, encoding='utf-8')
    print('ALL v1.334 TESTS PASSED!')


if __name__ == '__main__':
    main()
