"""Exhaustive verification suite for v1.329:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v329.lua
3. m12/37 (qs_item_box.Main) still has ZERO JMP instructions with A < params (v1.325 fix preserved)
4. Equipment 极品附加属性 section (red box between 需要等级 and 镶嵌属性/附魔属性):
   - All prefix +N<stat> forms (抵抗破防, 抵抗暴击, 暴击, 暴击伤害, 破防几率, 抵抗后仰, 生命值上限, 魔法值上限,
     提升攻击速度, 更佳的机会取得魔法装备, %伤害减免, %怪物金币掉落量) -> 属性:+数字 / 属性:+数字%
   - All suffix <stat>+N forms (击中生命恢复+30, 击中魔法恢复+30, 生命药水恢复量+85, 魔法药水恢复量+50,
     每10秒恢复体力+10, 每10秒恢复法力+10, 击杀生命恢复+50, 击杀魔法恢复+38, 击杀怪物获得经验+20) -> 属性:+数字
   - 等级需求降低5 -> 等级需求降低:5
   - All reformatted lines colored 柔和暖金 #c(-7558)...#W (#FFE27A)
   - Base stats (#W, #c(-8323200), #c(-8323328), #c(-16711681)), gem section (#c(-8323200)), and enchant section untouched!
5. Full v1.328 (武器/衣服/头盔) + v1.325 + S.shelp + 「前尘忆梦」 isolation + regressions (5.5% drops, v1.317, v1.308, v1.307, v1.306).
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
from test_v319 import (
    decode_real_sets_full_143,
    make_slot_proxy,
    test_real_boss_blueprint_drops_5_5pct,
)
from test_v320 import sum_sets
from test_v322 import decode_real_blueprint_templates

W = Path(__file__).resolve().parent
BASE_SHA = 'ab36ffbda8c3685920d8d2d3dc440155537e20f22d4d6f9a08045a1f3235f8cf'


def extract_runtime_v329(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.329 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v329.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_syntax_and_m12_37():
    base_bytes = (W / 'game_v328.res').read_bytes()
    out_bytes = (W / 'game_v329.res').read_bytes()
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

    rt_src = extract_runtime_v329(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_v329_affix_format_and_warm_gold(d12, rt_src):
    real_sets = decode_real_sets_full_143(d12)
    real_tpls = decode_real_blueprint_templates(d12)

    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']

    item_db = LuaTable()
    for nm, dn in real_tpls.items():
        item_db.rawset(nm, LuaTable({'名称': nm, '显示名': dn}))
    S.rawset('游戏道具组', item_db)
    bag = LuaTable()
    S.rawset('包裹物品组', bag)

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
    orig_calls = {'hero': 0, 'gem_ui': 0, 'box_ev1': 0, 'box_ev4': 0}
    wr = LuaTable({
        '套装属性': lambda a, b: orig_calls.__setitem__('hero', orig_calls['hero'] + 1),
        '佣兵套装': lambda a, b: None,
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
        if ev_type == 1:
            orig_calls['box_ev1'] += 1
        if ev_type == 4:
            orig_calls['box_ev4'] += 1
        if ev_type in (1, 2) and slot_id is not None and 1 <= slot_id <= 13:
            wr.rawget('套装属性')(slot_id, ev_type)
        return None

    lua_tostring = ev.G.get('tostring')
    shelp = LuaTable()
    shelp.rawset(lua_tostring(orig_box), LuaTable({'msg': '【全局事件/物品格子】', 'fname': 'Main', 'sid': 5}))
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

    # 1. Exact user screenshot case: 血花落照 (武器) with 4 red-box affixes + gems + enchant
    weapon = LuaTable({'名称': '血花落照', '分类': '装备', '子类': '武器',
                       '附加': LuaTable({'套装属性': '虎战领主之爪'})})
    raw_tips[('血花落照', 1)] = (
        '#md#G虎战领主之爪\n'
        '#md#f(宋_9_炭灰,#c(4294946098)血花落照#W)\n'
        '#md#W重量:1\n'
        '#md#c(-8323200)防御力:45-0 (+45)\n'
        '#md#c(-8323200)破坏:51-63 (+90)\n'
        '#md#W需要等级:1\n'
        '#md#c(-5385052)+75抵抗破防\n'
        '#md#c(-5385052)+75抵抗暴击\n'
        '#md#c(-5385052)击中生命恢复+30\n'
        '#md#c(-5385052)击中魔法恢复+30\n'
        '#md#c(-3381556)镶嵌信息\n'
        '#md#c(-5385052)+6最大破坏\n'
        '#md#c(-5385052)+30准确\n'
        '#md#c(-5385052)+30生命值上限\n'
        '#md#G套装信息\n'
        '#md#c(-5385052)' + real_sets['虎战领主之爪'][2]
    )
    out_w, _ = disp.rawget('道具')(weapon, 1, 1)
    wls = out_w.split('\n')
    assert '#c(-7558)抵抗破防:+75#W' in wls, wls
    assert '#c(-7558)抵抗暴击:+75#W' in wls, wls
    assert '#c(-7558)击中生命恢复:+30#W' in wls, wls
    assert '#c(-7558)击中魔法恢复:+30#W' in wls, wls
    # Base stats and gem stats MUST remain untouched bright green (-8323200)
    assert '#c(-8323200)破坏:51-63 (+90)' in wls, wls
    gi = wls.index('#f(宋_9_炭灰,#c(-22312)镶嵌属性#W)')
    assert wls[gi + 1] == '#c(-8323200)破坏:+0-6#W', wls[gi:gi + 4]
    assert wls[gi + 2] == '#c(-8323200)准确:+30#W'
    assert wls[gi + 3] == '#c(-8323200)生命值:+30#W'
    # Enchant stats MUST remain bright green (-8323200)
    ei = wls.index('#f(宋_9_炭灰,#c(-7350017)附魔属性#W)')
    assert wls[ei + 1] == '#f(宋_9_炭灰,#c(-16711936)虎战领主之爪#W)'
    assert wls[ei + 2] == '#c(-8323200)伤害:+0-50#W'
    assert '-5385052' not in out_w

    # 2. Comprehensive affix coverage (all remaining m12/321 patterns + luck line untouched)
    omni = LuaTable({'名称': '全词条测试甲', '分类': '装备', '子类': '衣服'})
    raw_tips[('全词条测试甲', 2)] = (
        '#md#f(宋_9_炭灰,#c(4293446776)全词条测试甲#W)\n'
        '#md#W重量:1\n'
        '#md#W需要等级:1\n'
        '#md#c(-16711681)幸运:+3\n'
        '#md#c(-5385052)+12破防几率\n'
        '#md#c(-5385052)+15暴击\n'
        '#md#c(-5385052)+40暴击伤害\n'
        '#md#c(-5385052)+25抵抗后仰\n'
        '#md#c(-5385052)+100生命值上限\n'
        '#md#c(-5385052)+80魔法值上限\n'
        '#md#c(-5385052)+35更佳的机会取得魔法装备\n'
        '#md#c(-5385052)+10%伤害减免\n'
        '#md#c(-5385052)+25%怪物金币掉落量\n'
        '#md#c(-5385052)+2提升攻击速度\n'
        '#md#c(-5385052)生命药水恢复量+85\n'
        '#md#c(-5385052)魔法药水恢复量+50\n'
        '#md#c(-5385052)每10秒恢复体力+10\n'
        '#md#c(-5385052)每10秒恢复法力+10\n'
        '#md#c(-5385052)击杀生命恢复+50\n'
        '#md#c(-5385052)击杀魔法恢复+38\n'
        '#md#c(-5385052)击杀怪物获得经验+20\n'
        '#md#c(-5385052)等级需求降低5\n'
        '#md#c(-3090223)Shift+左键放入备用背包'
    )
    out_o, _ = disp.rawget('道具')(omni, 1, 2)
    ols = out_o.split('\n')
    expected_affixes = [
        '#c(-16711681)幸运:+3',  # luck stays cyan untouched
        '#c(-7558)破防几率:+12#W',
        '#c(-7558)暴击:+15#W',
        '#c(-7558)暴击伤害:+40#W',
        '#c(-7558)抵抗后仰:+25#W',
        '#c(-7558)生命值:+100#W',
        '#c(-7558)魔法值:+80#W',
        '#c(-7558)更佳的机会取得魔法装备:+35#W',
        '#c(-7558)伤害减免:+10%#W',
        '#c(-7558)怪物金币掉落量:+25%#W',
        '#c(-7558)攻击速度:+2#W',
        '#c(-7558)生命药水恢复量:+85#W',
        '#c(-7558)魔法药水恢复量:+50#W',
        '#c(-7558)每10秒恢复体力:+10#W',
        '#c(-7558)每10秒恢复法力:+10#W',
        '#c(-7558)击杀生命恢复:+50#W',
        '#c(-7558)击杀魔法恢复:+38#W',
        '#c(-7558)击杀怪物获得经验:+20#W',
        '#c(-7558)等级需求降低:5#W',
        '#c(-3090223)Shift+左键放入备用背包',
    ]
    for exp in expected_affixes:
        assert exp in ols, f'Missing {exp!r} in {ols}'

    # 3. Verify v1.328 武器/衣服/头盔 rules + ineligible slot red note still pass
    boots = LuaTable({'名称': '赤飞靴子', '分类': '装备', '子类': '鞋子',
                      '附加': LuaTable({'套装属性': '骷髅教主的火种'})})
    raw_tips[('赤飞靴子', 36)] = (
        '#md#G骷髅教主的火种\n'
        '#md#f(宋_9_炭灰,#c(-1)赤飞靴子#W)\n'
        '#md#W重量:1\n'
        '#md#c(-5385052)生命药水恢复量+41\n'
        '#md#G套装信息\n'
        '#md#c(-5385052)' + real_sets['骷髅教主的火种'][2] + '\n'
        '#md#WShift+左键放入备用背包'
    )
    out_b, _ = disp.rawget('道具')(boots, 1, 36)
    bls = out_b.split('\n')
    assert '#c(-7558)生命药水恢复量:+41#W' in bls, bls
    assert '#f(宋_9_炭灰,#c(-5592406)骷髅教主的火种#W)' in bls
    assert '#R附魔仅在武器/衣服/头盔生效#W' in bls

    for sid, sub, sn in ((1, '武器', '虎战领主之爪'), (2, '衣服', '沃玛教主的利爪'),
                         (3, '头盔', '骷髅教主的火种'), (10, '鞋子', '毁灭之爪')):
        bag.rawset(sid, LuaTable({'道具': LuaTable({'名称': '测试' + sub, '分类': '装备', '子类': sub,
                                                   '附加': LuaTable({'套装属性': sn})})}))
    wr.rawget('套装属性')(3, 1)
    assert dict(h14_internal.rawget('stats')._data) == sum_sets(real_sets, ['虎战领主之爪', '沃玛教主的利爪', '骷髅教主的火种'])

    # 4. 「前尘忆梦」 isolation: tooltip returns raw unmodified text
    U.rawset('版本选择', '前尘忆梦')
    out_qc, _ = disp.rawget('道具')(weapon, 1, 1)
    assert out_qc == raw_tips[('血花落照', 1)], '前尘忆梦 tooltip must remain completely untouched'


def main():
    mods_o, rt_src = test_diff_syntax_and_m12_37()
    test_v329_affix_format_and_warm_gold(mods_o[12], rt_src)
    test_real_boss_blueprint_drops_5_5pct(mods_o[12], rt_src)
    test_compact_equip_spaces_v317(rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v329.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.329',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v329.res': out_sha,
            'runtime_v329.lua': hashlib.sha256((W / 'runtime_v329.lua').read_bytes()).hexdigest(),
            'patch_v329.py': hashlib.sha256((W / 'patch_v329.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'm12_37_zero_jmp_below_params_preserved',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'equip_affixes_reformatted_to_stat_colon_plus_val_and_warm_gold_FFE27A',
            'all_m12_321_affix_variants_including_pct_and_lv_reduce_verified',
            'base_stats_luck_gem_and_enchant_colors_untouched',
            'v328_weapon_armor_helmet_rules_and_qianchi_isolation_pass',
            'v319_5_5pct_v317_v308_v307_v306_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v329.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v329.json').write_text(text, encoding='utf-8')
    print('ALL v1.329 TESTS PASSED!')


if __name__ == '__main__':
    main()
