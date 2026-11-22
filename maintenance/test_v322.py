"""Exhaustive verification suite for v1.322:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v322.lua
3. Bag/unequipped equipment 「套装信息」 renders active green; equipped slots preserve real active/grey state
4. All 29 real blueprint templates from m12/4111 rename 显示名 图纸 -> 附魔卷 (preserving internal 名称!),
   old-save items in S.包裹物品组 migrate immediately, tooltip title & red prompt use 附魔卷,
   and switching to 「前尘忆梦」 restores all original template 显示名!
5. Instant tooltip refresh: dropping equipment onto equip slot (ev_type=1), unequipping onto bag slot
   (ev_type=1), unequipping equip slot (ev_type=2 refreshing focused sibling), and applying scroll
   (ev_type=4) immediately call ctrl.对象:更新道具属性() on the exact frame!
6. Full v1.321 S.shelp/S.fun + 4-allowed-slot + max-1 legacy + 5.5% Boss drops + prior regressions.
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
from test_v316 import test_tooltips_v316
from test_v317 import test_compact_equip_spaces_v317
from test_v319 import (
    decode_real_sets_full_143,
    make_slot_proxy,
    test_real_boss_blueprint_drops_5_5pct,
)
from test_v321 import test_shelp_and_sets_v321

W = Path(__file__).resolve().parent
BASE_SHA = '61ccae9bc211bfe86e0540a2c6d2e848987b0e8ffdeab370ed63e9b06fd35f78'


def extract_runtime_v322(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.322 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v322.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def decode_real_blueprint_templates(d12):
    """Extract all item templates whose 显示名 contains 图纸 from real m12."""
    out = {}
    for p in d12.protos:
        for kg in p.kgc:
            if isinstance(kg, tuple) and kg[0] == 'table':
                h = dict(kg[2])
                nm = h.get(b'\xc3\xfb\xb3\xc6')
                dn = h.get(b'\xcf\xd4\xca\xbe\xc3\xfb')
                if isinstance(nm, bytes) and isinstance(dn, bytes) and b'\xcd\xbc\xd6\xbd' in dn:
                    out[nm.decode('gbk')] = dn.decode('gbk')
    assert len(out) == 29, f'Expected 29 real 图纸 templates, got {len(out)}'
    return out


def test_diff_and_syntax():
    base_bytes = (W / 'game_v321.res').read_bytes()
    out_bytes = (W / 'game_v322.res').read_bytes()
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

    rt_src = extract_runtime_v322(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_v322_features(d12, rt_src):
    real_sets = decode_real_sets_full_143(d12)
    real_tpls = decode_real_blueprint_templates(d12)

    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']

    # Build real S.游戏道具组 with all 29 blueprint templates + a normal item
    item_db = LuaTable()
    for nm, dn in real_tpls.items():
        item_db.rawset(nm, LuaTable({
            '名称': nm,
            '显示名': dn,
            '风格提示': LuaTable({'原始内容': dn, '托管标识': 1}),
        }))
    item_db.rawset('金创药_小', LuaTable({'名称': '金创药_小', '显示名': '金创药(小)'}))
    S.rawset('游戏道具组', item_db)

    # Pre-populate S.包裹物品组 with an old-save blueprint (slot 35) and equipment (slot 2 & 32)
    bag = LuaTable()
    saved_bp = LuaTable({
        '名称': '卧龙的逆鳞',
        '显示名': '卧龙的逆鳞(图纸)',
        '分类': '道具',
        '子类': '其他',
        '附加': LuaTable({'套装属性': '卧龙的逆鳞'}),
        '风格提示': LuaTable({'原始内容': '卧龙的逆鳞(图纸)', '托管标识': 1}),
    })
    bag.rawset(35, LuaTable({'道具': saved_bp}))

    armor_eq = LuaTable({
        '名称': '赤龙宝甲_男',
        '显示名': '赤龙宝甲(男)',
        '分类': '装备',
        '子类': '衣服',
        '附加': LuaTable({'套装属性': '虎战领主之爪'}),
    })
    ring_eq = LuaTable({
        '名称': '红宝石戒指',
        '显示名': '红宝石戒指',
        '分类': '装备',
        '子类': '戒指',
        '附加': LuaTable({'套装属性': '触龙神的毒囊'}),
    })
    bag.rawset(2, LuaTable({'道具': armor_eq}))
    bag.rawset(32, LuaTable({'道具': armor_eq}))
    bag.rawset(8, LuaTable({'道具': ring_eq}))
    S.rawset('包裹物品组', bag)

    # Set up slot controls with 更新道具属性() trackers in S.tbl_controls
    refresh_counts = {}
    ctrls = LuaTable()

    def make_ctrl(sid, focused=False):
        refresh_counts[sid] = 0
        obj = LuaTable({
            '焦点': focused,
            '更新道具属性': lambda self_obj=None, _s=sid: refresh_counts.__setitem__(_s, refresh_counts[_s] + 1),
        })
        c = LuaTable({'格子ID': sid, '对象': obj})
        ctrls.rawset(f'物品格子{sid}', c)
        return c

    make_ctrl(2, focused=True)
    make_ctrl(8, focused=True)
    make_ctrl(32, focused=True)
    make_ctrl(35, focused=False)
    S.rawset('tbl_controls', ctrls)

    # Set up sets table, tooltip hook, and qs_item_box with authentic S.shelp
    sets_lua = LuaTable()
    for name, (hsh, req, desc) in real_sets.items():
        e = LuaTable()
        e.rawset(1, LuaTable(hsh))
        e.rawset(2, req)
        e.rawset(3, desc)
        sets_lua.rawset(name, e)
    U.rawset('天竺葵家', lambda: sets_lua)
    U.rawset('胚子考虑', lambda: LuaTable({'装备操作': 0}))
    prompts = []
    raw_tips = {}

    def orig_tip(item, mode, slot_id):
        return raw_tips[(item.rawget('名称'), slot_id)], None

    disp = LuaTable({'道具': orig_tip, '屏幕提示': lambda m, c=None: prompts.append((m, c))})
    U.rawset('托管显示', disp)
    wr = LuaTable({'套装属性': lambda a, b: None, '佣兵套装': lambda a, b: None, '元素图标': lambda: None})
    U.rawset('窗口相关', wr)

    G.rawset('从ID取格子', lambda sid: bag.rawget(sid))
    G.rawset('鼠标道具', 0)

    def orig_box(ev_type, slot_id, a3=None, a4=None, a5=None):
        if ev_type in (1, 2) and slot_id is not None and 1 <= slot_id <= 13:
            wr.rawget('套装属性')(slot_id, ev_type)
        mid = G.rawget('鼠标道具')
        if ev_type == 4 and mid and mid > 0:
            tc, sc = bag.rawget(slot_id), bag.rawget(mid)
            if tc and sc and tc.rawget('道具') and sc.rawget('道具'):
                sex = sc.rawget('道具').rawget('附加')
                if sex and sex.rawget('套装属性') is not None:
                    tc.rawget('道具').rawget('附加').rawset('套装属性', sex.rawget('套装属性'))
                    sc.rawset('道具', None)
                    return True
        return None

    lua_tostring = ev.G.get('tostring')
    shelp = LuaTable()
    shelp.rawset(lua_tostring(orig_box), LuaTable({'msg': '【全局事件/物品格子】', 'fname': 'Main', 'sid': 13}))
    S.rawset('shelp', shelp)
    box_tbl = LuaTable({'Main': orig_box})
    S.rawset('tbl_qs', LuaTable({'qs_item_box': box_tbl}))

    h14_internal, h14_proxy = make_slot_proxy(ev)
    m410_internal, m410_proxy = make_slot_proxy(ev)
    ss = S.rawget('script_setting')
    ss.rawset('Gly独', G)
    ss.rawset('物品格子14', h14_proxy)
    ss.rawset('物品格子410', m410_proxy)

    ev.G.get('loadstring')(rt_src)(S)

    # 1. Verify all 29 templates renamed 图纸 -> 附魔卷 while internal 名称 untouched!
    for nm, orig_dn in real_tpls.items():
        ent = item_db.rawget(nm)
        assert ent.rawget('名称') == nm
        assert ent.rawget('显示名') == orig_dn.replace('图纸', '附魔卷'), (nm, ent.rawget('显示名'))
        assert '图纸' not in ent.rawget('显示名')
        assert ent.rawget('风格提示').rawget('托管标识') == 0
    assert item_db.rawget('金创药_小').rawget('显示名') == '金创药(小)'

    # 2. Verify old-save item in S.包裹物品组 migrated immediately!
    assert saved_bp.rawget('名称') == '卧龙的逆鳞'
    assert saved_bp.rawget('显示名') == '卧龙的逆鳞(附魔卷)'
    assert refresh_counts[35] >= 1

    # 3. Verify bag equipment 套装信息 displays as ACTIVE GREEN (even when m12/321 emitted #H!)
    raw_tips[('赤龙宝甲_男', 32)] = (
        '#md#f(宋_9_炭灰,#c(-8323200)赤龙宝甲(男)#W)\n'
        '#md#W重量:1\n'
        '#md#G套装信息\n'
        '#md#H' + real_sets['虎战领主之爪'][2]
    )
    out_bag, _ = disp.rawget('道具')(armor_eq, 1, 32)
    assert '#H' not in out_bag, f'Bag equipment set info must NOT be grey #H:\n{out_bag}'
    assert '#c(-8323200)伤害:+0-50#W' in out_bag
    assert '#c(-8323328)攻击元素:雷(电击)+30#W' in out_bag

    # 4. Verify EQUIPPED slot (slot 8, inactive 2nd legacy ring) STILL displays #H grey when m12/321 emits #H!
    raw_tips[('红宝石戒指', 8)] = (
        '#md#f(宋_9_炭灰,#c(-8323200)红宝石戒指#W)\n'
        '#md#W重量:1\n'
        '#md#G套装信息\n'
        '#md#H' + real_sets['触龙神的毒囊'][2]
    )
    out_eq_inactive, _ = disp.rawget('道具')(ring_eq, 1, 8)
    assert '#H' in out_eq_inactive, f'Inactive equipped legacy slot must stay #H grey:\n{out_eq_inactive}'

    # 5. Verify tooltip title fallback replaces 图纸 -> 附魔卷 on line 1
    raw_tips[('卧龙的逆鳞', 35)] = (
        '#md#f(宋_9_炭灰,#c(-8323328)卧龙的逆鳞(图纸)#W)\n'
        '#md#W重量:1\n#md#W需要等级:1\n'
        '#md#c(-5385052)' + real_sets['卧龙的逆鳞'][2] + '\n#md#c(-45824)拖到装备使用'
    )
    out_bp, _ = disp.rawget('道具')(saved_bp, 1, 35)
    assert '卧龙的逆鳞(附魔卷)' in out_bp.split('\n')[0] and '图纸' not in out_bp
    assert '#Y拖到武器/衣服/头盔/坐骑使用#W' in out_bp

    # 6. Verify instant tooltip refresh on equip (ev_type=1 on slot 2), unequip to bag (ev_type=1 on slot 32),
    #    unequip from equip slot (ev_type=2 on slot 2 -> refreshes focused sibling slot 8), and scroll drag (ev_type=4)
    c2_before = refresh_counts[2]
    c8_before = refresh_counts[8]
    c32_before = refresh_counts[32]
    wrapped_main = box_tbl.rawget('Main')
    assert shelp.rawget(lua_tostring(wrapped_main)) is not None

    # Equip onto slot 2 -> refreshes slot 2 immediately AND focused sibling slot 8!
    wrapped_main(1, 2)
    assert refresh_counts[2] == c2_before + 1
    assert refresh_counts[8] == c8_before + 1

    # Drop onto bag slot 32 (unequipping from body to bag) -> refreshes bag slot 32 immediately!
    wrapped_main(1, 32)
    assert refresh_counts[32] == c32_before + 1

    # Take off slot 2 (ev_type=2) -> refreshes focused sibling slot 8!
    c8_before2 = refresh_counts[8]
    wrapped_main(2, 2)
    assert refresh_counts[8] == c8_before2 + 1

    # Dragging scroll onto disallowed ring shows updated 附魔卷 prompt!
    G.rawset('鼠标道具', 35)
    prompts.clear()
    assert wrapped_main(4, 8) is True
    assert len(prompts) == 1 and '附魔卷只能用于武器、衣服、头盔或坐骑' in prompts[0][0]

    # Dragging scroll onto allowed slot 2 refreshes slot 2 immediately!
    c2_before2 = refresh_counts[2]
    assert wrapped_main(4, 2) is True
    assert refresh_counts[2] == c2_before2 + 1

    # 7. 「前尘忆梦」 restores all 29 original template 显示名!
    U.rawset('版本选择', '前尘忆梦')
    S.rawget('__gm_pickup_frame_v299')(U, G)
    for nm, orig_dn in real_tpls.items():
        assert item_db.rawget(nm).rawget('显示名') == orig_dn


def main():
    mods_o, rt_src = test_diff_and_syntax()
    test_v322_features(mods_o[12], rt_src)
    test_shelp_and_sets_v321(mods_o[12], rt_src)
    test_real_boss_blueprint_drops_5_5pct(mods_o[12], rt_src)
    test_compact_equip_spaces_v317(rt_src)
    test_tooltips_v316(mods_o[12], rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v322.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.322',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v322.res': out_sha,
            'runtime_v322.lua': hashlib.sha256((W / 'runtime_v322.lua').read_bytes()).hexdigest(),
            'patch_v322.py': hashlib.sha256((W / 'patch_v322.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'bag_equipment_set_info_active_green_and_equipped_inactive_preserved',
            'all_29_blueprint_templates_and_saved_bag_items_renamed_to_附魔卷_preserving_internal_名称',
            'instant_slot_tooltip_refresh_on_equip_unequip_and_scroll_apply',
            'qianchi_restores_original_blueprint_names_and_set_rules',
            'v321_shelp_v319_5_5pct_v317_v316_v308_v307_v306_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v322.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v322.json').write_text(text, encoding='utf-8')
    print('ALL v1.322 TESTS PASSED!')


if __name__ == '__main__':
    main()
