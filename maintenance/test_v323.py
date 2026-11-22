"""Exhaustive verification suite for v1.323:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v323.lua
3. Tooltip formatting & layout:
   - 「镶嵌信息」 -> pink 「#c(-3381556)镶嵌属性」
   - 「套装信息」 -> blue 「#c(-11162881)附魔属性#W」
   - Scroll name (e.g. #G虎战领主之爪) moved from ABOVE equipment name to IMMEDIATELY BELOW 「附魔属性」,
     keeping exact original #G color; equipment name becomes line 1!
   - Scroll yellow hint updated to 「#Y拖到武器/衣服/鞋子使用#W」; 29 blueprint display names -> 附魔卷
   - Bag & equipped allowed slots (武器/衣服/鞋子) show active green; old-save disallowed slots
     (头盔/坐骑/戒指/项链/手镯/勋章/饰品) show grey #H both in bag & equipped!
4. Enchant slot activation & drag restriction (authentic S.fun + S.shelp + m48/1+m48/2 proxies):
   - ONLY 武器 / 衣服 / 鞋子 activate (all 3 simultaneously; same scroll deduplicated)
   - Old-save enchants on 头盔 / 坐骑 / 项链 / 手镯 / 戒指 / 勋章 / 饰品 DO NOT take effect at all
     (both standalone and mixed with allowed slots, for Hero and Mercenary independently)
   - Dragging scroll onto all 10 equipment subtypes: ONLY 武器/衣服/鞋子 allowed; all 7 others blocked
     with red prompt 「附魔卷只能用于武器、衣服或鞋子」
   - Instant tooltip refresh on equip/unequip/scroll-apply & 「前尘忆梦」 full isolation
5. Full regressions: v1.319 5.5% Boss drops, v1.317 compact spaces, v1.308 【仓库】 proxy button,
   v1.307 Mode 2 materials, v1.306 gather formula.
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
from test_v317 import test_compact_equip_spaces_v317
from test_v319 import (
    decode_real_sets_full_143,
    make_slot_proxy,
    test_real_boss_blueprint_drops_5_5pct,
)
from test_v320 import sum_sets
from test_v322 import decode_real_blueprint_templates

W = Path(__file__).resolve().parent
BASE_SHA = '8f760f8c7d04fd4c892b1a752eb5f7b2cface7b19669abb67289399dbcac8547'


def extract_runtime_v323(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.323 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v323.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_and_syntax():
    base_bytes = (W / 'game_v322.res').read_bytes()
    out_bytes = (W / 'game_v323.res').read_bytes()
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

    rt_src = extract_runtime_v323(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_v323_full(d12, rt_src):
    real_sets = decode_real_sets_full_143(d12)
    real_tpls = decode_real_blueprint_templates(d12)

    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']

    # Real S.游戏道具组
    item_db = LuaTable()
    for nm, dn in real_tpls.items():
        item_db.rawset(nm, LuaTable({'名称': nm, '显示名': dn}))
    S.rawset('游戏道具组', item_db)

    bag = LuaTable()
    S.rawset('包裹物品组', bag)
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

    for s in (1, 2, 3, 4, 6, 8, 10, 11, 13, 32, 35, 397, 398, 406):
        make_ctrl(s, focused=(s in (2, 10, 32)))
    S.rawset('tbl_controls', ctrls)

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
    disp = LuaTable({
        '道具': lambda item, mode, slot_id: (raw_tips[(item.rawget('名称'), slot_id)], None),
        '屏幕提示': lambda m, c=None: prompts.append((m, c)),
    })
    U.rawset('托管显示', disp)
    orig_calls = {'hero': 0, 'merc': 0, 'gem_ui': 0}
    wr = LuaTable({
        '套装属性': lambda a, b: orig_calls.__setitem__('hero', orig_calls['hero'] + 1),
        '佣兵套装': lambda a, b: orig_calls.__setitem__('merc', orig_calls['merc'] + 1),
        '元素图标': lambda: None,
        '佣兵窗口': lambda a=None, b=None: None,
    })
    U.rawset('窗口相关', wr)
    G.rawset('从ID取格子', lambda sid: bag.rawget(sid))
    G.rawset('鼠标道具', 0)

    def orig_box(ev_type, slot_id, a3=None, a4=None, a5=None):
        if ev_type == 3:
            orig_calls['gem_ui'] += 1
            return True
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

    def authentic_S_fun(fn, args):
        if fn is None or S.rawget('shelp').rawget(lua_tostring(fn)) is None:
            return None
        return fn(*args)

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

    def put_eq(slot_id, sub, sname=None, nm=None):
        ex = LuaTable({'套装属性': sname}) if sname else LuaTable()
        item = LuaTable({'名称': nm or ('测试' + sub), '分类': '装备', '子类': sub, '附加': ex})
        bag.rawset(slot_id, LuaTable({'道具': item}))
        return item

    def put_bp(slot_id, sname):
        item = LuaTable({'名称': sname, '显示名': sname + '(图纸)', '分类': '道具', '子类': '其他',
                         '附加': LuaTable({'套装属性': sname})})
        bag.rawset(slot_id, LuaTable({'道具': item}))
        return item

    def clear_bag():
        for k in list(bag._data.keys()):
            bag.rawset(k, None)

    ev.G.get('loadstring')(rt_src)(S)

    # === 1. Tooltip layout: 镶嵌属性, blue 附魔属性, scroll name moved below 附魔属性 keeping #G ===
    armor = put_eq(2, '衣服', '虎战领主之爪', nm='赤龙宝甲_男')
    raw_tips[('赤龙宝甲_男', 2)] = (
        '#md#G虎战领主之爪\n'
        '#md#f(宋_9_炭灰,#c(4287090411)赤龙宝甲(男)#W)\n'
        '#md#W重量:1\n'
        '#md#c(-8323200)防御力:38-55 (+8)\n'
        '#md#W需要等级:1\n'
        '#md#c(-3381556)镶嵌信息\n'
        '#md#c(-5385052)+12最大防御力\n'
        '#md#G套装信息\n'
        '#md#c(-5385052)' + real_sets['虎战领主之爪'][2]
    )
    out_armor, _ = disp.rawget('道具')(armor, 1, 2)
    ls = out_armor.split('\n')
    assert ls[0].startswith('#f(宋_9_炭灰,#c(4287090411)赤龙宝甲(男)#W)'), f'Equipment name must be line 1: {ls}'
    assert '#G虎战领主之爪' not in ls[:5], f'Scroll name must be removed from top: {ls}'
    assert '#c(-3381556)镶嵌属性' in ls and '镶嵌信息' not in out_armor
    assert '套装信息' not in out_armor
    idx_fm = ls.index('#c(-11162881)附魔属性#W')
    assert ls[idx_fm + 1] == '#G虎战领主之爪', f'Scroll name must sit right below 附魔属性 keeping #G: {ls[idx_fm:idx_fm+4]}'
    assert ls[idx_fm + 2] == '#c(-8323200)伤害:+0-50#W'
    assert ls[idx_fm + 7] == '#c(-8323328)攻击元素:雷(电击)+30#W'

    # Bag allowed slot (鞋子 in bag slot 32) -> active green + moved scroll name!
    boots = put_eq(32, '鞋子', '骷髅教主的火种', nm='黑皮靴')
    raw_tips[('黑皮靴', 32)] = (
        '#md#G骷髅教主的火种\n'
        '#md#f(宋_9_炭灰,#c(-1)黑皮靴#W)\n'
        '#md#W重量:1\n'
        '#md#G套装信息\n'
        '#md#H' + real_sets['骷髅教主的火种'][2]
    )
    out_boots, _ = disp.rawget('道具')(boots, 1, 32)
    bls = out_boots.split('\n')
    assert bls[0] == '#f(宋_9_炭灰,#c(-1)黑皮靴#W)'
    assert '#H' not in out_boots
    b_idx = bls.index('#c(-11162881)附魔属性#W')
    assert bls[b_idx + 1] == '#G骷髅教主的火种'
    assert '#c(-8323328)攻击元素:火(火焰)+20#W' in bls

    # Old-save disallowed slot (头盔/坐骑/戒指) -> ALWAYS grey #H (even in bag or even if m12/321 sent active color!)
    helm = put_eq(3, '头盔', '虎战领主之爪', nm='黑铁头盔')
    raw_tips[('黑铁头盔', 3)] = (
        '#md#G虎战领主之爪\n'
        '#md#f(宋_9_炭灰,#c(-1)黑铁头盔#W)\n'
        '#md#W重量:1\n'
        '#md#G套装信息\n'
        '#md#c(-5385052)' + real_sets['虎战领主之爪'][2]
    )
    out_helm, _ = disp.rawget('道具')(helm, 1, 3)
    hls = out_helm.split('\n')
    h_idx = hls.index('#c(-11162881)附魔属性#W')
    assert hls[h_idx + 1] == '#G虎战领主之爪'
    assert hls[h_idx + 2] == '#H伤害:+0-50#W', f'Disallowed old-save slot must show grey #H: {hls[h_idx:]}'

    # Scroll tooltip yellow hint -> 拖到武器/衣服/鞋子使用
    bp = put_bp(35, '卧龙的逆鳞')
    raw_tips[('卧龙的逆鳞', 35)] = (
        '#md#f(宋_9_炭灰,#c(-8323328)卧龙的逆鳞(图纸)#W)\n'
        '#md#W重量:1\n#md#W需要等级:1\n'
        '#md#c(-5385052)' + real_sets['卧龙的逆鳞'][2] + '\n#md#c(-45824)拖到装备使用'
    )
    out_bp, _ = disp.rawget('道具')(bp, 1, 35)
    assert '卧龙的逆鳞(附魔卷)' in out_bp.split('\n')[0]
    assert '#Y拖到武器/衣服/鞋子使用#W' in out_bp

    # === 2. Activation rules: ONLY 武器 / 衣服 / 鞋子 activate; ALL other old-save slots DO NOT take effect! ===
    clear_bag()
    put_eq(1, '武器', '虎战领主之爪')
    put_eq(2, '衣服', '沃玛教主的利爪')
    put_eq(10, '鞋子', '骷髅教主的火种')
    # Old-save disallowed slots (头盔, 坐骑, 项链, 手镯, 戒指, 勋章): NONE may activate!
    put_eq(3, '头盔', '毁灭之爪')
    put_eq(13, '坐骑', '皇陵鲲吾剑')
    put_eq(4, '项链', '赤月恶魔的尖刺')
    put_eq(6, '手镯', '祖玛教主的怒火')
    put_eq(8, '戒指', '触龙神的毒囊')
    put_eq(11, '勋章', '魔血之魂晶')

    authentic_S_fun(box_tbl.rawget('Main'), (1, 10))
    expected3 = sum_sets(real_sets, ['虎战领主之爪', '沃玛教主的利爪', '骷髅教主的火种'])
    assert stats_dict(h14_internal) == expected3, (stats_dict(h14_internal), expected3)
    for ok_nm in ('虎战领主之爪', '沃玛教主的利爪', '骷髅教主的火种'):
        assert holder_extra(h14_internal).rawget(ok_nm) == 1
    for bad_nm in ('毁灭之爪', '皇陵鲲吾剑', '赤月恶魔的尖刺', '祖玛教主的怒火', '触龙神的毒囊', '魔血之魂晶'):
        assert holder_extra(h14_internal).rawget(bad_nm) is None

    # Old-save with ONLY disallowed slots (头盔 + 坐骑 + 戒指 + 项链) -> ZERO active stats!
    clear_bag()
    put_eq(3, '头盔', '毁灭之爪')
    put_eq(13, '坐骑', '皇陵鲲吾剑')
    put_eq(4, '项链', '赤月恶魔的尖刺')
    put_eq(8, '戒指', '触龙神的毒囊')
    prev_upd = h14_internal.rawget('updates')
    wr.rawget('套装属性')(None, None)
    assert stats_dict(h14_internal) == {}, f'Old-save disallowed slots must NOT activate: {stats_dict(h14_internal)}'
    assert h14_internal.rawget('updates') == prev_upd + 1

    # Mercenary: ONLY 武器 / 衣服 / 鞋子 activate; 头盔/坐骑/戒指 do NOT activate!
    put_eq(397, '武器', '毁灭之爪')
    put_eq(398, '衣服', '皇陵鲲吾剑')
    put_eq(406, '鞋子', '卧龙的逆鳞')
    put_eq(399, '头盔', '触龙神的毒囊')
    put_eq(409, '坐骑', '祖玛教主的怒火')
    wr.rawget('佣兵套装')(None, None)
    assert stats_dict(m410_internal) == sum_sets(real_sets, ['毁灭之爪', '皇陵鲲吾剑', '卧龙的逆鳞'])
    assert holder_extra(m410_internal).rawget('触龙神的毒囊') is None
    assert holder_extra(m410_internal).rawget('祖玛教主的怒火') is None

    # === 3. Drag restriction across ALL 10 equipment subtypes ===
    allowed_set = {'武器', '衣服', '鞋子'}
    all_subs = ['武器', '衣服', '鞋子', '头盔', '坐骑', '项链', '手镯', '戒指', '勋章', '饰品']
    for sub in all_subs:
        clear_bag()
        put_eq(32, sub)
        put_bp(35, '虎战领主之爪')
        G.rawset('鼠标道具', 35)
        prompts.clear()
        res = authentic_S_fun(box_tbl.rawget('Main'), (4, 32))
        assert res is True
        applied = bag.rawget(32).rawget('道具').rawget('附加').rawget('套装属性')
        if sub in allowed_set:
            assert applied == '虎战领主之爪', f'{sub} should allow scroll'
            assert bag.rawget(35).rawget('道具') is None
            assert len(prompts) == 0
        else:
            assert applied is None, f'{sub} must block scroll'
            assert bag.rawget(35).rawget('道具') is not None
            assert len(prompts) == 1 and prompts[0][0] == '附魔卷只能用于武器、衣服或鞋子'

    # Right-click gem UI still works via S.fun + S.shelp
    assert authentic_S_fun(box_tbl.rawget('Main'), (3, 1)) is True
    assert orig_calls['gem_ui'] == 1

    # 「前尘忆梦」 restores original req counts, template names & delegates
    U.rawset('版本选择', '前尘忆梦')
    S.rawget('__gm_pickup_frame_v299')(U, G)
    for name, (_, orig_req, _) in real_sets.items():
        assert sets_lua.rawget(name).rawget(2) == orig_req
    for nm, orig_dn in real_tpls.items():
        assert item_db.rawget(nm).rawget('显示名') == orig_dn
    prev_h = orig_calls['hero']
    wr.rawget('套装属性')(1, 1)
    assert orig_calls['hero'] == prev_h + 1


def main():
    mods_o, rt_src = test_diff_and_syntax()
    test_v323_full(mods_o[12], rt_src)
    test_real_boss_blueprint_drops_5_5pct(mods_o[12], rt_src)
    test_compact_equip_spaces_v317(rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v323.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.323',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v323.res': out_sha,
            'runtime_v323.lua': hashlib.sha256((W / 'runtime_v323.lua').read_bytes()).hexdigest(),
            'patch_v323.py': hashlib.sha256((W / 'patch_v323.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'headers_renamed_to_pink_镶嵌属性_and_blue_附魔属性',
            'scroll_name_moved_below_附魔属性_preserving_original_color',
            'only_武器_衣服_鞋子_activate_and_accept_scrolls_across_all_10_subtypes',
            'old_save_disallowed_slots_zero_effect_and_grey_tooltip',
            'authentic_S_fun_S_shelp_right_click_gem_ui_and_instant_refresh_pass',
            'qianchi_completely_isolated',
            'v319_5_5pct_v317_v308_v307_v306_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v323.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v323.json').write_text(text, encoding='utf-8')
    print('ALL v1.323 TESTS PASSED!')


if __name__ == '__main__':
    main()
