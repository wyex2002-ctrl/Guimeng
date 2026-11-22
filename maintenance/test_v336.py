"""Exhaustive verification suite for v1.336:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v336.lua
3. m12/37 (qs_item_box.Main) still has ZERO JMP instructions with A < params
4. Ordinary Materials Ground-Drop White Label Color (v1.336, 「来世续缘」 only):
   - All 36 ORDINARY_MOB_MATERIALS (plain table & 数据保护 proxy & Q-prefixed) render
     white (-1 / #FFFFFF) during 地图物品类.初始化 and set __gm_ground_label_color_v287 = -1.
   - item.颜色值 is restored immediately after 地图物品类.初始化 returns (bag/tooltip/auto-sell intact).
   - Non-ordinary materials (Boss/rare/quest/enchant/gem/ores/equipment/skill books) keep original color.
   - pickup_frame re-installs the 地图物品类.初始化 wrapper if 地图物品类 is recreated.
   - 「前尘忆梦」 delegates 100% untouched (ordinary materials keep original 4286643968 green).
5. Corpse-Digging Direct-Drop 极品 Hardening (v1.336):
   - Coerces numeric mlv (even string '35' -> 35, nil -> 15) and passes arg4 == 1 (matching m12/10323).
   - Unwraps BOTH .__数据 and __call-only 数据保护 proxies in build_live_drop_item.
   - Preserves rolled 极品 stats in out.属性, out.附加.条数, out.颜色值, and encrypted out.道具说明
     across 精灵骸骨 (武器), 冰之印记 (饰品), 屠龙 (武器), and 赤龙宝甲_男 (衣服).
   - Accurately tracks S.__gm_corpse_jipin_stats_v336 counters (rolls/jipin/white/errors).
6. Full v1.335 + v1.334 + v1.333 + v1.332 + v1.331 + v1.330 + v1.319 + v1.317 + v1.308 + v1.307 + v1.306 regressions.
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
from test_v333 import test_v333_shared_weapon_tooltip_note
from test_v334 import test_v334_mode2_qingtongfu_mofachangpao_non7
from test_v335 import test_v335_repeat_autocast_ux

W = Path(__file__).resolve().parent
BASE_SHA = '43fa1cf89756e180773336659e00822a677b5d728c6dc3d9ade9243f78fe4504'

ALL_36_ORDINARY_MATERIALS = [
    '僵尸骨头', '兔肉', '号角', '夜明珠', '宝玉', '思念珍珠', '指甲',
    '毒蛇胆汁', '毒蜘蛛牙齿', '潘夜之泪', '牙齿', '牛肉', '狼肉',
    '猪肉', '皮', '神灵雕像', '羊毛', '羊肉', '羊角', '蚂蚁卵', '蛆卵',
    '蜘蛛线', '蝎子的尾巴', '褐色栗子', '跳蚤皮', '遗物', '金色栗子',
    '铜色栗子', '银色栗子', '食人花果实', '食人花树叶', '骷髅骨',
    '鸡肉', '鸡血', '鹿肉', '鹿茸',
]


def extract_runtime_v336(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.336 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v336.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_syntax_and_m12_37():
    base_bytes = (W / 'game_v335.res').read_bytes()
    out_bytes = (W / 'game_v336.res').read_bytes()
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

    rt_src = extract_runtime_v336(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def make_protected_proxy(raw_tbl, call_only=False):
    proxy = LuaTable()
    if not call_only:
        proxy.rawset('__数据', raw_tbl)
    mt = LuaTable({
        '__index': lambda self_p, k: raw_tbl.rawget(k),
        '__newindex': lambda self_p, k, v: raw_tbl.rawset(k, v),
        '__call': lambda self_p: raw_tbl,
    })
    proxy._mt = mt
    return proxy


def test_v336_ordinary_materials_ground_white(rt_src):
    GREEN = 4286643968  # 0xFF80FF00 original bright green

    # 1. 「来世续缘」 tests
    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']

    seen_colors = []

    def orig_init(self_g, item, x, y, count, mode):
        self_g.rawset('物品', item)
        self_g.rawset('数量', count)
        # Simulate m76/1 pc 467: reads self.物品.颜色值
        col = item.get('颜色值')
        seen_colors.append((item.get('名称'), col))
        self_g.rawset('名称颜色', col)
        return self_g

    map_item_cls = LuaTable({'初始化': orig_init})
    ev.G.rawset('地图物品类', map_item_cls)

    ev.G.get('loadstring')(rt_src)(S)
    assert map_item_cls.rawget('初始化') is not orig_init, '地图物品类.初始化 must be wrapped'

    # Test ALL 36 ordinary materials (plain + proxy) + Q-prefixed
    for idx, nm in enumerate(ALL_36_ORDINARY_MATERIALS):
        raw_item = LuaTable({'名称': nm, '分类': '道具', '子类': '其他', '颜色值': GREEN})
        item_arg = make_protected_proxy(raw_item, call_only=(idx % 3 == 1)) if idx % 2 == 1 else raw_item
        gobj = LuaTable()
        map_item_cls.rawget('初始化')(gobj, item_arg, 10, 20, 1, 0)
        assert seen_colors[-1] == (nm, -1), f'Expected white (-1) during init for {nm}, got {seen_colors[-1]}'
        assert gobj.rawget('名称颜色') == -1, f'Ground label color must be -1 for {nm}'
        assert gobj.rawget('__gm_ground_label_color_v287') == -1, f'Stack-shrink color must be -1 for {nm}'
        assert raw_item.rawget('颜色值') == GREEN, f'item.颜色值 must be restored to {GREEN} after init for {nm}'

    # Q-prefixed ordinary material
    q_item = LuaTable({'名称': 'Q鸡肉', '分类': '道具', '子类': '其他', '颜色值': GREEN})
    qg = LuaTable()
    map_item_cls.rawget('初始化')(qg, q_item, 10, 20, 1, 0)
    assert qg.rawget('名称颜色') == -1 and qg.rawget('__gm_ground_label_color_v287') == -1
    assert q_item.rawget('颜色值') == GREEN

    # Non-ordinary materials MUST keep their original color!
    non_ordinary = [
        ('沃玛号角', '道具', '其他', GREEN),
        ('飞龙剑碎片', '道具', '其他', GREEN),
        ('赤龙的心脏', '道具', '其他', GREEN),
        ('卧龙的逆鳞', '道具', '其他', GREEN),
        ('火影晶体', '道具', '其他', GREEN),
        ('震天魔印', '道具', '其他', GREEN),
        ('精炼原石', '道具', '其他', GREEN),
        ('魔晶石', '道具', '其他', GREEN),
        ('商会物资', '道具', '其他', GREEN),
        ('黑铁', '道具', '其他', GREEN),
        ('金矿', '道具', '其他', GREEN),
        ('屠龙', '装备', '武器', -256),
        ('冰之印记', '装备', '饰品', -7876885),
        ('四级烈火剑法', '道具', '消耗品', GREEN),
    ]
    for nm, cat, sub, col in non_ordinary:
        it = LuaTable({'名称': nm, '分类': cat, '子类': sub, '颜色值': col})
        gobj = LuaTable()
        map_item_cls.rawget('初始化')(gobj, it, 10, 20, 1, 0)
        assert gobj.rawget('名称颜色') == col, f'Non-ordinary {nm} must keep original color {col}, got {gobj.rawget("名称颜色")}'
        assert gobj.rawget('__gm_ground_label_color_v287') is None, f'Non-ordinary {nm} must not get -1 override'
        assert it.rawget('颜色值') == col

    # Re-install check in pickup_frame if 地图物品类 is recreated
    fresh_cls = LuaTable({'初始化': orig_init})
    ev.G.rawset('地图物品类', fresh_cls)
    S.rawget('__gm_pickup_frame_v299')(U, G)
    assert fresh_cls.rawget('初始化') is not orig_init, 'pickup_frame must re-wrap 地图物品类.初始化'
    g2 = LuaTable()
    chicken2 = LuaTable({'名称': '鸡肉', '分类': '道具', '子类': '其他', '颜色值': GREEN})
    fresh_cls.rawget('初始化')(g2, chicken2, 1, 2, 1, 0)
    assert g2.rawget('名称颜色') == -1 and chicken2.rawget('颜色值') == GREEN

    # 2. 「前尘忆梦」 isolation test: MUST remain 100% original green!
    env_q = make_env(story='前尘忆梦')
    ev_q, S_q = env_q['ev'], env_q['S']
    q_seen = []

    def orig_init_q(self_g, item, x, y, count, mode):
        self_g.rawset('物品', item)
        q_seen.append((item.get('名称'), item.get('颜色值')))
        self_g.rawset('名称颜色', item.get('颜色值'))
        return self_g

    cls_q = LuaTable({'初始化': orig_init_q})
    ev_q.G.rawset('地图物品类', cls_q)
    ev_q.G.get('loadstring')(rt_src)(S_q)
    for nm in ('鸡肉', '僵尸骨头', '鹿肉', '夜明珠'):
        it_q = LuaTable({'名称': nm, '分类': '道具', '子类': '其他', '颜色值': GREEN})
        gq = LuaTable()
        cls_q.rawget('初始化')(gq, it_q, 5, 5, 1, 0)
        assert gq.rawget('名称颜色') == GREEN, f'前尘忆梦 {nm} must stay green {GREEN}, got {gq.rawget("名称颜色")}'
        assert gq.rawget('__gm_ground_label_color_v287') is None
        assert it_q.rawget('颜色值') == GREEN


def test_v336_corpse_drop_jipin_hardening(rt_src):
    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']

    # Build authentic protected templates (including __call-only proxy!) in S.游戏道具组
    def make_tpl(name, sub, base_attrs):
        raw_attr = LuaTable(base_attrs)
        raw_ex = LuaTable({'等级': 1})
        raw_item = LuaTable({
            '名称': name, '分类': '装备', '子类': sub, '颜色值': 4294967295, '价格': 5000,
            '需要等级': 35, '道具说明': '默认说明',
            '地面精灵': f'ground_{name}', '精灵': f'icon_{name}',
            '属性': make_protected_proxy(raw_attr, call_only=(name == '冰之印记')),
            '附加': make_protected_proxy(raw_ex, call_only=(name == '冰之印记')),
        })
        return make_protected_proxy(raw_item, call_only=(name == '冰之印记'))

    items_db = LuaTable({
        '精灵骸骨': make_tpl('精灵骸骨', '武器', {'最大破坏': 30, '最小破坏': 8, '攻火元素': 0, '暴击几率': 0}),
        '冰之印记': make_tpl('冰之印记', '饰品', {'最大破坏': 0, '最大自然': 0, '攻冰元素': 5, '防冰元素': 5}),
        '屠龙': make_tpl('屠龙', '武器', {'最大破坏': 40, '最小破坏': 10, '攻雷元素': 0, '暴击几率': 0}),
        '赤龙宝甲_男': make_tpl('赤龙宝甲_男', '衣服', {'最大防御': 15, '最大魔防': 10, '防火元素': 0}),
    })
    S.rawset('游戏道具组', items_db)

    roll_calls = []

    def fake_roll(name, mlv, forced_cnt, flag4, mon_extra=None):
        roll_calls.append((name, type(mlv).__name__, mlv, forced_cnt, flag4))
        assert isinstance(mlv, (int, float)), f'mlv must be numeric, got {mlv!r}'
        assert flag4 is None, f'arg4 should stay nil to avoid overwriting 道具说明, got {flag4!r}'
        if name == '冰之印记':
            # Simulate 5-affix jipin seal (饰品)
            return LuaTable({
                '名称': name, '分类': '装备', '子类': '饰品', '颜色值': -256, '价格': 12500,
                '需要等级': 30, '道具说明': 'ENC_BACKUP_5AFFIX_SEAL',
                '最大破坏': 12, '最大自然': 10, '攻冰元素': 18, '防冰元素': 20,
                '附加': LuaTable({'等级': mlv, '条数': 5, '卡里钱': 'ENC_K', '咯扣盘': 'ENC_L'}),
            })
        elif name == '精灵骸骨':
            # Simulate 3-affix jipin weapon
            return LuaTable({
                '名称': name, '分类': '装备', '子类': '武器', '颜色值': -7876885, '价格': 7500,
                '需要等级': 1, '道具说明': 'ENC_BACKUP_3AFFIX_BONE',
                '最大破坏': 42, '最小破坏': 8, '攻火元素': 11, '暴击几率': 6,
                '附加': LuaTable({'等级': mlv, '条数': 3}),
            })
        else:
            # Simulate white roll (0 affixes)
            return LuaTable({
                '名称': name, '分类': '装备', '子类': '武器', '颜色值': 4294967295, '价格': 5000,
                '需要等级': 35, '道具说明': '默认说明',
                '最大破坏': 40, '最小破坏': 10, '攻雷元素': 0, '暴击几率': 0,
                '附加': LuaTable({'等级': mlv}),
            })

    U.rawset('窗口相关', LuaTable({'全图窗口': fake_roll}))
    U.rawset('岗位上的', lambda: LuaTable({
        '骷髅精灵': LuaTable({1: LuaTable({1: '精灵骸骨', 2: 1})}),
        '魔灵神主': LuaTable({1: LuaTable({1: '冰之印记', 2: 1})}),
        '震天魔神': LuaTable({1: LuaTable({1: '屠龙', 2: 1})}),
    }))
    U.rawset('啾啾啵啵', lambda: LuaTable({'技能': LuaTable({'采集': LuaTable({1: 3})})}))
    G.rawset('取道具信息_名称', lambda nm: LuaTable({'名称': nm, '分类': '装备'}))

    ev.G.get('loadstring')(rt_src)(S)
    corpse_drop = ev.G.rawget('__gm_corpse_drop_v301')

    # Case 1: 魔灵神主 with string mlv='60' and __call-only proxy template -> 5-affix jipin 冰之印记!
    drops1 = LuaTable()
    actor1 = LuaTable({'id': 101, '属性': LuaTable({'名称': '魔灵神主', '附加': LuaTable({'等级': '60'})})})
    added1 = corpse_drop(actor1, drops1)
    assert added1 == 1
    seal = drops1.rawget(1).rawget('物品道具')
    assert seal.rawget('颜色值') == -256
    assert seal.rawget('道具说明') == 'ENC_BACKUP_5AFFIX_SEAL'
    assert seal.rawget('附加').rawget('条数') == 5
    assert seal.rawget('属性').rawget('攻冰元素') == 18
    assert seal.rawget('属性').rawget('最大破坏') == 12
    assert roll_calls[-1] == ('冰之印记', 'int', 60, None, None)

    # Case 2: 骷髅精灵 with nil mlv -> defaults to 15 -> 3-affix jipin 精灵骸骨!
    drops2 = LuaTable()
    actor2 = LuaTable({'id': 102, '属性': LuaTable({'名称': '骷髅精灵'})})
    added2 = corpse_drop(actor2, drops2)
    assert added2 == 1
    bone = drops2.rawget(1).rawget('物品道具')
    assert bone.rawget('颜色值') == -7876885
    assert bone.rawget('道具说明') == 'ENC_BACKUP_3AFFIX_BONE'
    assert bone.rawget('附加').rawget('条数') == 3
    assert bone.rawget('属性').rawget('最大破坏') == 42
    assert bone.rawget('属性').rawget('暴击几率') == 6
    assert roll_calls[-1] == ('精灵骸骨', 'int', 15, None, None)

    # Case 3: 震天魔神 white roll -> white counter increments, no errors
    drops3 = LuaTable()
    actor3 = LuaTable({'id': 103, '属性': LuaTable({'名称': '震天魔神', '附加': LuaTable({'等级': 55})})})
    added3 = corpse_drop(actor3, drops3)
    assert added3 == 1
    tl = drops3.rawget(1).rawget('物品道具')
    assert tl.rawget('颜色值') == 4294967295
    assert tl.rawget('附加').rawget('条数') is None

    # Verify diagnostic counters
    stats = S.rawget('__gm_corpse_jipin_stats_v336')
    assert stats.rawget('rolls') == 3
    assert stats.rawget('jipin') == 2
    assert stats.rawget('white') == 1
    assert stats.rawget('errors') == 0


def main():
    mods_o, rt_src = test_diff_syntax_and_m12_37()
    test_v336_ordinary_materials_ground_white(rt_src)
    test_v336_corpse_drop_jipin_hardening(rt_src)
    # Full regressions
    test_v335_repeat_autocast_ux(rt_src)
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

    out_bytes = (W / 'game_v336.res').read_bytes()
    tested = {
        name: hashlib.sha256((W / name).read_bytes()).hexdigest()
        for name in ('game_v336.res', 'runtime_v336.lua', 'patch_v336.py', 'test_v336.py')
    }
    report = {
        'version': 'v1.336',
        'all_passed': True,
        'base_sha256': BASE_SHA,
        'sha256': hashlib.sha256(out_bytes).hexdigest(),
        'bytes': len(out_bytes),
        'tested_files': tested,
        'checks': [
            'outer_diff_strictly_12_14_30',
            'dump_rebuild_roundtrip_and_trees',
            'm12_37_zero_bad_jmp_A',
            'runtime_v336_syntax_and_zero_gbk_0x5c',
            'v1336_36_ordinary_materials_ground_white_and_color_restored',
            'v1336_non_ordinary_materials_keep_original_ground_color',
            'v1336_pickup_frame_rewraps_ground_init',
            'v1336_qianchi_ground_color_untouched',
            'v1336_corpse_drop_jipin_mlv_coerce_arg4_1_and_call_proxy',
            'v1335_repeat_autocast_ux_regression',
            'v1334_mode2_qingtongfu_mofachangpao_non7_regression',
            'v1333_shared_weapon_note_and_autosell_safety_regression',
            'v1332_corpse_drop_jipin_stats_regression',
            'v1331_gem_tooltip_cache_refresh_regression',
            'v1330_split_bracelet_ring_gems_regression',
            'v1319_real_boss_blueprint_drops_5_5pct_regression',
            'v1317_compact_equip_spaces_regression',
            'v1308_authentic_proxy_warehouse_button_regression',
            'v1307_mode2_ordinary_materials_regression',
            'v1306_regression',
        ],
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v336.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v336.json').write_text(report_text, encoding='utf-8')
    print('ALL v1.336 TESTS PASSED!', report['sha256'], report['bytes'])


if __name__ == '__main__':
    main()
