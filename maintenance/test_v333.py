"""Exhaustive verification suite for v1.333:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v333.lua
3. m12/37 (qs_item_box.Main) still has ZERO JMP instructions with A < params
4. 7 Hero/Merc shared ranged weapons tooltip note 「主角/佣兵（远程）通用」:
   - Appended on all 7 装备通用=0 ranged weapons (inserted before Shift+左键放入备用背包 or at bottom), idempotent
   - Not added to pure Merc ranged (玄月), pure Merc melee (潜龙双剑), or non-shared Hero weapons (屠龙)
   - Refreshes cached tooltips in both Hero and Merc slots once on load
   - 「前尘忆梦」 untouched
5. Auto-sell safety hardening (Alt pickup + Mode 1 + Mode 2):
   - Non-white 颜色值 blocked in safe_sell (even if 条数=0 and stats match template)
   - 坐骑 (坐骑号角_铜 / Q猛虎 with 禁止出售=false), 符咒, 时装, 宝石, 灵石 blocked in BOTH safe_sell & Mode 2
   - 禁止丢弃=true blocked in BOTH safe_sell & Mode 2
   - Mode 2 protects enchanted (套装属性), transmogged (幻化), reinforced (强化装备), unsavable (不可保存), lucky (幸运>0) equipment
6. Plain white 青铜斧, 魔法长袍_女, 精灵骸骨 sellable in Mode 2 【拾取+出售】:
   - White rolls of those 3 items are sold in Mode 2; jipin/non-white rolls of those 3 items are KEPT in Mode 2
   - Alt pickup and Mode 1 still protect all 3 items (white or jipin); 鹤嘴锄 always protected
7. Full v1.332 + v1.331 + v1.330 + v1.319 + v1.317 + v1.308 + v1.307 + v1.306 regressions.
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
from test_v332 import make_weapon_tpl, test_v332_corpse_drop_jipin_stats

W = Path(__file__).resolve().parent
BASE_SHA = '6020ecc9263ff5c3db70fd2418f6a17a422b30452cab11d3c5793ebfe81ee00f'


def extract_runtime_v333(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.333 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v333.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_syntax_and_m12_37():
    base_bytes = (W / 'game_v332.res').read_bytes()
    out_bytes = (W / 'game_v333.res').read_bytes()
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

    rt_src = extract_runtime_v333(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_v333_shared_weapon_tooltip_note(rt_src):
    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']
    ev.G.get('loadstring')(rt_src)(S)
    fmt = S.rawget('__gm_format_equip_tooltip_v311')

    shared_7 = (
        '纯净的白灵之刃', '威武的狂战之刃', '不朽的法老之刃',
        '恐怖的亡灵之刃', '锋利的灵魂之刃', '精灵骸骨', '拍拍手',
    )
    for nm in shared_7:
        w = make_weapon_tpl(nm, '不限', {'装备通用': 0, '绑定技能': '刺客普通攻击'})
        # Without Shift hint -> appended at bottom
        base_tip = f'#f(宋_9_炭灰,#c(-1){nm})\n重量:1\n破坏:8-30\n需要等级:1'
        res1 = fmt(base_tip, w, 0, 35)
        assert res1.endswith('\n#c(-7543041)主角/佣兵（远程）通用#W'), f'{nm}: {res1!r}'
        # Idempotent
        res2 = fmt(res1, w, 0, 35)
        assert res2.count('主角/佣兵（远程）通用') == 1

        # With Shift hint -> inserted immediately before Shift line
        shift_tip = f'#f(宋_9_炭灰,#c(-1){nm})\n重量:1\n破坏:8-30\n需要等级:1\n#YShift+左键放入备用背包#W'
        res_s = fmt(shift_tip, w, 0, 35)
        lines = res_s.split('\n')
        assert lines[-2] == '#c(-7543041)主角/佣兵（远程）通用#W', lines
        assert lines[-1] == '#YShift+左键放入备用背包#W', lines

    # Pure Merc ranged, pure Merc melee, pure Hero warrior -> MUST NOT get the note
    for w in (
        make_weapon_tpl('玄月', '刺客', {'绑定技能': '刺客普通攻击'}),
        make_weapon_tpl('潜龙双剑', '刺客', {'绑定技能': '刺客双手攻击'}),
        make_weapon_tpl('屠龙', '战士', {}),
    ):
        nm = w.rawget('名称')
        tip = f'#f(宋_9_炭灰,#c(-1){nm})\n重量:1\n需要等级:1'
        out = fmt(tip, w, 0, 35)
        assert '主角/佣兵（远程）通用' not in out, f'Unexpected note on {nm}: {out!r}'

    # Post-load refresh covers BOTH Hero bag (35) and Merc equip (397) for 精灵骸骨
    bag = S.rawget('包裹物品组')
    bag.rawset(35, LuaTable({'道具': make_weapon_tpl('精灵骸骨', '不限', {'装备通用': 0, '绑定技能': '刺客普通攻击'})}))
    bag.rawset(397, LuaTable({'道具': make_weapon_tpl('精灵骸骨', '不限', {'装备通用': 0, '绑定技能': '刺客普通攻击'})}))
    refreshed = []
    ctrls = LuaTable()
    for cid in (35, 397):
        def make_cb(slot_i):
            return lambda self_obj=None: refreshed.append(slot_i)
        ctrls.rawset(f'物品格子{cid}', LuaTable({
            '格子ID': cid,
            '对象': LuaTable({'焦点': False, '更新道具属性': make_cb(cid)}),
        }))
    S.rawset('tbl_controls', ctrls)
    n = S.rawget('__gm_refresh_non_merc_weapon_tooltips_v332')()
    assert n == 2 and set(refreshed) == {35, 397}, (n, refreshed)


    # Also verify full v1.332 merc ranged weapon tag rules (plus Merc slot 397 tooltip refresh for shared weapons)
    env_m = make_env(story='来世续缘')
    ev_m, S_m, U_m, G_m = env_m['ev'], env_m['S'], env_m['U'], env_m['G']
    ss_m = S_m.rawget('script_setting')
    orig_calls = []

    def orig_merc_name(item, display_name, slot_id=None):
        orig_calls.append((display_name, slot_id))
        return (display_name + '（远程）') if isinstance(display_name, str) and not display_name.endswith('（远程）') else display_name

    ev_m.G.rawset('__gm_merc_name_v253', orig_merc_name)
    ss_m.rawset('__gm_merc_name_v253', orig_merc_name)
    bag_m = S_m.rawget('包裹物品组')
    stale_bone = make_weapon_tpl('精灵骸骨', '不限', {'装备通用': 0, '绑定技能': '刺客普通攻击'})
    stale_bone.rawset('显示名', '精灵骸骨（远程）')
    bag_m.rawset(35, LuaTable({'道具': stale_bone}))
    bag_m.rawset(397, LuaTable({'道具': make_weapon_tpl('精灵骸骨', '不限', {'装备通用': 0, '绑定技能': '刺客普通攻击'})}))
    refreshed_m = []
    ctrls_m = LuaTable()
    for cid in (35, 397):
        def make_cb_m(slot_i):
            return lambda self_obj=None: refreshed_m.append(slot_i)
        ctrls_m.rawset(f'物品格子{cid}', LuaTable({
            '格子ID': cid,
            '对象': LuaTable({'焦点': False, '更新道具属性': make_cb_m(cid)}),
        }))
    S_m.rawset('tbl_controls', ctrls_m)
    ev_m.G.get('loadstring')(rt_src)(S_m)
    fn_m = ev_m.G.rawget('__gm_merc_name_v253')
    assert fn_m(make_weapon_tpl('玄月', '刺客', {'绑定技能': '刺客普通攻击'}), '玄月', 35) == '玄月（远程）'
    assert fn_m(make_weapon_tpl('潜龙双剑', '刺客', {'绑定技能': '刺客双手攻击'}), '潜龙双剑', 397) == '潜龙双剑'
    assert fn_m(make_weapon_tpl('精灵骸骨', '不限', {'装备通用': 0, '绑定技能': '刺客普通攻击'}), '精灵骸骨（远程）', 35) == '精灵骸骨'
    assert fn_m(make_weapon_tpl('精灵骸骨', '不限', {'装备通用': 0, '绑定技能': '刺客普通攻击'}), '精灵骸骨', 397) == '精灵骸骨（远程）'
    S_m.rawget('__gm_pickup_frame_v299')(U_m, G_m)
    assert stale_bone.rawget('显示名') == '精灵骸骨'
    assert set(refreshed_m) == {35, 397}, refreshed_m
    U_m.rawset('版本选择', '前尘忆梦')
    orig_calls.clear()
    assert fn_m(make_weapon_tpl('精灵骸骨', '不限', {'装备通用': 0, '绑定技能': '刺客普通攻击'}), '精灵骸骨', 35) == '精灵骸骨（远程）'
    assert len(orig_calls) == 1


def make_ground_equip_obj(name, sub, price, color=4294967295, attrs=None, extra=None, flags=None, picked_list=None):
    it = LuaTable({
        '名称': name,
        '显示名': name,
        '分类': '装备',
        '子类': sub,
        '价格': price,
        '颜色值': color,
        '叠加': 0,
        '禁止出售': False,
        '禁止丢弃': False,
        '属性': LuaTable(attrs or {'最小破坏': 5, '最大破坏': 10}),
        '附加': LuaTable(extra or {}),
    })
    if flags:
        for k, v in flags.items():
            it.rawset(k, v)
    obj = LuaTable({
        '物品': it, '数量': 1, '已经消失': False, '格子': LuaTable({'x': 10, 'y': 10}),
        'Hero': LuaTable({'回调脚本': LuaTable({'拾取': lambda *a: (False, False)})}),
    })

    def pickup_fn(self_o, mode):
        self_o.rawset('已经消失', True)
        if picked_list is not None:
            picked_list.append(name + ('_jipin' if (extra and extra.get('条数', 0) > 0) else ''))
        return True

    obj.rawset('拾取', pickup_fn)
    return obj


def test_v333_autosell_hardening_and_white_bulk(rt_src):
    # Template database for G['取道具信息_名称']
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

    # --- Case A: Mode 2 【拾取+出售】 sells WHITE 青铜斧/魔法长袍_女/精灵骸骨, KEEPS jipin ones & special items ---
    def items_mode2(picked):
        return [
            # 3 plain white items -> MUST BE SOLD (1750 + 5000 + 2500 = 9250)
            make_ground_equip_obj('青铜斧', '武器', 3500, 4294967295, {'最小破坏': 5, '最大破坏': 10}, {}, None, picked),
            make_ground_equip_obj('魔法长袍_女', '衣服', 10000, -1, {'最小防御': 3, '最大防御': 5}, {}, None, picked),
            make_ground_equip_obj('精灵骸骨', '武器', 5000, 4294967295, {'最小破坏': 8, '最大破坏': 30}, {'装备通用': 0, '绑定技能': '刺客普通攻击'}, None, picked),
            # 3 jipin / non-white items of the same 3 names -> MUST BE KEPT!
            make_ground_equip_obj('青铜斧', '武器', 3500, 4287090411, {'最小破坏': 5, '最大破坏': 18}, {'条数': 3}, None, picked),
            make_ground_equip_obj('魔法长袍_女', '衣服', 10000, 4287090411, {'最小防御': 3, '最大防御': 9}, {'条数': 3}, None, picked),
            make_ground_equip_obj('精灵骸骨', '武器', 5000, 4287090411, {'最小破坏': 8, '最大破坏': 42}, {'条数': 3, '装备通用': 0, '绑定技能': '刺客普通攻击'}, None, picked),
            # Special color only (条数=0, stats identical to template) on 精灵骸骨 -> MUST BE KEPT!
            make_ground_equip_obj('精灵骸骨', '武器', 5000, 4294828058, {'最小破坏': 8, '最大破坏': 30}, {'装备通用': 0, '绑定技能': '刺客普通攻击'}, None, picked),
            # Mounts with 禁止出售=false -> MUST BE KEPT!
            make_ground_equip_obj('坐骑号角_铜', '坐骑', 5000000, 4294828058, {'最小破坏': 0, '最大破坏': 0}, {'外观': '枣红马'}, None, picked),
            make_ground_equip_obj('Q猛虎', '坐骑', 2800, 4286643968, {'最小破坏': 0, '最大破坏': 0}, {}, None, picked),
            # 禁止丢弃=true (with 禁止出售=false) -> MUST BE KEPT!
            make_ground_equip_obj('乌木剑', '武器', 1000, 4294967295, {'最小破坏': 4, '最大破坏': 8}, {}, {'禁止丢弃': True}, picked),
            # Enchanted / transmogged / reinforced / lucky normal equip -> MUST BE KEPT in Mode 2!
            make_ground_equip_obj('乌木剑', '武器', 1000, 4287090411, {'最小破坏': 4, '最大破坏': 12}, {'条数': 3, '套装属性': '虎战领主之爪'}, None, picked),
            make_ground_equip_obj('乌木剑', '武器', 1000, 4287090411, {'最小破坏': 4, '最大破坏': 12}, {'条数': 3, '幻化': '赤龙'}, None, picked),
            make_ground_equip_obj('乌木剑', '武器', 1000, 4287090411, {'最小破坏': 4, '最大破坏': 12}, {'条数': 3, '强化装备': 5}, None, picked),
            make_ground_equip_obj('乌木剑', '武器', 1000, 4294967295, {'最小破坏': 4, '最大破坏': 8, '幸运': 3}, {}, None, picked),
            # 鹤嘴锄 -> ALWAYS KEPT!
            make_ground_equip_obj('鹤嘴锄', '武器', 700, 4294967295, {'最小破坏': 1, '最大破坏': 5}, {}, None, picked),
        ]

    gold2, picked2 = run_case(True, 2, items_mode2)
    assert gold2 == 9250, f'Expected 9250 gold (white 青铜斧+魔法长袍_女+精灵骸骨 only), got {gold2}, picked={picked2}'
    assert len(picked2) == 12, f'Expected 12 protected items kept, got {len(picked2)}: {picked2}'
    assert '坐骑号角_铜' in picked2 and 'Q猛虎' in picked2 and '鹤嘴锄' in picked2
    assert '精灵骸骨_jipin' in picked2 and '青铜斧_jipin' in picked2 and '魔法长袍_女_jipin' in picked2

    # --- Case B: Manual Alt & Mode 1 (green) KEEP white 青铜斧/魔法长袍_女/精灵骸骨, block non-white color, mounts, 禁止丢弃; SELL normal white 乌木剑 ---
    def items_white_modes(picked):
        return [
            make_ground_equip_obj('青铜斧', '武器', 3500, 4294967295, {'最小破坏': 5, '最大破坏': 10}, {}, None, picked),         # KEEP
            make_ground_equip_obj('魔法长袍_女', '衣服', 10000, 4294967295, {'最小防御': 3, '最大防御': 5}, {}, None, picked),    # KEEP
            make_ground_equip_obj('精灵骸骨', '武器', 5000, 4294967295, {'最小破坏': 8, '最大破坏': 30}, {'装备通用': 0, '绑定技能': '刺客普通攻击'}, None, picked),  # KEEP
            make_ground_equip_obj('坐骑号角_铜', '坐骑', 5000000, 4294828058, {'最小破坏': 0, '最大破坏': 0}, {'外观': '枣红马'}, None, picked),  # KEEP
            make_ground_equip_obj('Q猛虎', '坐骑', 2800, 4286643968, {'最小破坏': 0, '最大破坏': 0}, {}, None, picked),           # KEEP
            # Same stats as white 乌木剑, 条数=0, ONLY 颜色值 is non-white -> MUST BE KEPT!
            make_ground_equip_obj('乌木剑', '武器', 1000, 4287090411, {'最小破坏': 4, '最大破坏': 8}, {}, None, picked),           # KEEP (non-white color)
            # White 乌木剑 with 禁止丢弃=true -> MUST BE KEPT!
            make_ground_equip_obj('乌木剑', '武器', 1000, 4294967295, {'最小破坏': 4, '最大破坏': 8}, {}, {'禁止丢弃': True}, picked),  # KEEP
            # Normal white 乌木剑 -> MUST BE SOLD (500g)!
            make_ground_equip_obj('乌木剑', '武器', 1000, 4294967295, {'最小破坏': 4, '最大破坏': 8}, {}, None, picked),           # SELL -> 500g
        ]

    for is_auto, mode, label in ((False, 0, 'Alt'), (True, 1, 'Mode1')):
        g_amt, p_list = run_case(is_auto, mode, items_white_modes)
        assert g_amt == 500, f'[{label}] expected 500g (only white 乌木剑), got {g_amt}, picked={p_list}'
        assert len(p_list) == 7, f'[{label}] expected 7 kept items, got {len(p_list)}: {p_list}'
        assert '青铜斧' in p_list and '魔法长袍_女' in p_list and '精灵骸骨' in p_list
        assert '坐骑号角_铜' in p_list and 'Q猛虎' in p_list


def main():
    mods_o, rt_src = test_diff_syntax_and_m12_37()
    test_v333_shared_weapon_tooltip_note(rt_src)
    test_v333_autosell_hardening_and_white_bulk(rt_src)
    test_v332_corpse_drop_jipin_stats(rt_src)
    test_v331_gem_tooltip_cache_refresh(rt_src)
    test_v330_split_bracelet_ring_gems(mods_o[12], rt_src)
    test_real_boss_blueprint_drops_5_5pct(mods_o[12], rt_src)
    test_compact_equip_spaces_v317(rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v333.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.333',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v333.res': out_sha,
            'runtime_v333.lua': hashlib.sha256((W / 'runtime_v333.lua').read_bytes()).hexdigest(),
            'patch_v333.py': hashlib.sha256((W / 'patch_v333.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'm12_37_zero_jmp_below_params_preserved',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'seven_shared_ranged_weapons_append_tooltip_note_and_refresh_hero_merc_slots',
            'autosell_blocks_non_white_color_mounts_charms_no_drop_and_special_state_gear',
            'mode2_sells_plain_white_qingtongfu_mofachangpao_jinglinghaigu_while_keeping_jipin_and_alt_mode1_protected',
            'v332_v331_v330_v319_v317_v308_v307_v306_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v333.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v333.json').write_text(text, encoding='utf-8')
    print('ALL v1.333 TESTS PASSED!')


if __name__ == '__main__':
    main()
