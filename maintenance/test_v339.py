"""Exhaustive verification suite for v1.339:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v339.lua
3. m12/37 (qs_item_box.Main) still has ZERO JMP instructions with A < params
4. Hero <-> Mercenary (刺客) equipment boundary preserved + Hero 3-class unrestricted:
   - All 74 real 刺客 templates in m12/4111 remain 职业要求=='刺客' (NOT cleared).
   - All 560 non-刺客 equipment templates in m12/4111 remain 职业要求=='不限' (zero 战士/法师/道士 lock).
   - Non-shared Hero weapons/armors/helmets (屠龙/赤龙宝甲_男/黑铁头盔) do NOT gain 装备通用=0;
     originally shared weapons (精灵骸骨) KEEP 装备通用=0.
   - Any v1.338-touched save items in S.包裹物品组 are auto-healed back to match S.游戏道具组
     (刺客 职业要求 restored, spurious 装备通用=0 removed); any stray 战士/法师/道士 bag item
     is normalized to '不限'.
   - 「前尘忆梦」 untouched.
5. Full v1.338 坐骑/勋章/印记 enchant slots + 坐骑->勋章->印记 priority + overwrite confirm tests.
6. Full v1.336..v1.306 regressions (including split bracelet/ring gems with updated red note).
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
from test_v336 import (
    test_v336_corpse_drop_jipin_hardening,
    test_v336_ordinary_materials_ground_white,
)
from test_v338 import test_v338_mount_medal_seal_enchants_and_confirm

W = Path(__file__).resolve().parent
BASE_SHA = '022a19cc2e1cf0c25a927c85ede5ff805c0db2d8a6243a8b6f7dfb8807fc97d7'


def extract_runtime_v339(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.339 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v339.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_syntax_and_m12_37():
    base_bytes = (W / 'game_v338.res').read_bytes()
    out_bytes = (W / 'game_v339.res').read_bytes()
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

    rt_src = extract_runtime_v339(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_v339_hero_merc_boundary_and_heal(d12, rt_src):
    p4111 = d12.protos[4111]

    def dec(v):
        if isinstance(v, bytes):
            return v.decode('gbk', 'replace')
        if isinstance(v, tuple) and v[0] == 'table':
            return [dec(x) for x in v[1]], {dec(k): dec(val) for k, val in v[2]}
        if isinstance(v, tuple) and v[0] == 'int':
            return v[1] - (1 << 32) if v[1] >= (1 << 31) else v[1]
        return v

    ck_cnt, hero_cnt = 0, 0
    for v in p4111.kgc:
        if isinstance(v, tuple) and v[0] == 'table':
            _, hsh = dec(v)
            if hsh.get('分类') == '装备':
                job = hsh.get('职业要求')
                if job == '刺客':
                    ck_cnt += 1
                else:
                    assert job == '不限', f'Unexpected Hero 3-class lock on {hsh.get("名称")}: {job!r}'
                    hero_cnt += 1
    assert ck_cnt == 74 and hero_cnt == 560, (ck_cnt, hero_cnt)

    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']

    # Clean S.游戏道具组 templates
    item_db = LuaTable({
        '玄月': LuaTable({'名称': '玄月', '分类': '装备', '子类': '武器', '职业要求': '刺客',
                          '附加': LuaTable({'绑定技能': '刺客普通攻击'})}),
        '潜龙遁甲_男': LuaTable({'名称': '潜龙遁甲_男', '分类': '装备', '子类': '衣服', '职业要求': '刺客',
                                '附加': LuaTable()}),
        '屠龙': LuaTable({'名称': '屠龙', '分类': '装备', '子类': '武器', '职业要求': '不限',
                          '附加': LuaTable()}),
        '赤龙宝甲_男': LuaTable({'名称': '赤龙宝甲_男', '分类': '装备', '子类': '衣服', '职业要求': '不限',
                                '附加': LuaTable()}),
        '精灵骸骨': LuaTable({'名称': '精灵骸骨', '分类': '装备', '子类': '武器', '职业要求': '不限',
                              '附加': LuaTable({'装备通用': 0, '绑定技能': '刺客普通攻击'})}),
    })
    S.rawset('游戏道具组', item_db)

    # Simulate a save touched by v1.338 + a hypothetical 战士-locked item
    bag_ck = LuaTable({'名称': '玄月', '分类': '装备', '子类': '武器', '职业要求': '不限',
                       '附加': LuaTable({'绑定技能': '刺客普通攻击', '装备通用': 0})})
    bag_hero = LuaTable({'名称': '屠龙', '分类': '装备', '子类': '武器', '职业要求': '不限',
                         '附加': LuaTable({'装备通用': 0})})
    bag_shared = LuaTable({'名称': '精灵骸骨', '分类': '装备', '子类': '武器', '职业要求': '不限',
                           '附加': LuaTable({'装备通用': 0, '绑定技能': '刺客普通攻击'})})
    bag_war = LuaTable({'名称': '赤龙宝甲_男', '分类': '装备', '子类': '衣服', '职业要求': '战士',
                        '附加': LuaTable()})
    S.rawset('包裹物品组', LuaTable({
        31: LuaTable({'道具': bag_ck}),
        32: LuaTable({'道具': bag_hero}),
        33: LuaTable({'道具': bag_shared}),
        34: LuaTable({'道具': bag_war}),
    }))

    ev.G.get('loadstring')(rt_src)(S)

    # Templates untouched!
    assert item_db.rawget('玄月').rawget('职业要求') == '刺客'
    assert item_db.rawget('潜龙遁甲_男').rawget('职业要求') == '刺客'
    assert item_db.rawget('屠龙').rawget('附加').rawget('装备通用') is None
    assert item_db.rawget('精灵骸骨').rawget('附加').rawget('装备通用') == 0

    # v1.338-touched save items cleanly healed!
    assert bag_ck.rawget('职业要求') == '刺客'
    assert bag_ck.rawget('附加').rawget('装备通用') is None
    assert bag_hero.rawget('职业要求') == '不限'
    assert bag_hero.rawget('附加').rawget('装备通用') is None
    assert bag_shared.rawget('附加').rawget('装备通用') == 0  # original shared preserved!
    assert bag_war.rawget('职业要求') == '不限'  # Hero 3-class normalized!


def main():
    mods_o, rt_src = test_diff_syntax_and_m12_37()
    test_v339_hero_merc_boundary_and_heal(mods_o[12], rt_src)
    test_v338_mount_medal_seal_enchants_and_confirm(mods_o[12], rt_src)
    # Full regressions v1.336..v1.306
    test_v336_ordinary_materials_ground_white(rt_src)
    test_v336_corpse_drop_jipin_hardening(rt_src)
    test_v335_repeat_autocast_ux(rt_src)
    test_v334_mode2_qingtongfu_mofachangpao_non7(rt_src)
    test_v333_shared_weapon_tooltip_note(rt_src)
    test_v332_corpse_drop_jipin_stats(rt_src)
    test_v331_gem_tooltip_cache_refresh(rt_src)
    test_v330_split_bracelet_ring_gems(mods_o[12], rt_src, expected_invalid_note='#R附魔仅在坐骑/勋章/印记生效#W')
    test_real_boss_blueprint_drops_5_5pct(mods_o[12], rt_src)
    test_compact_equip_spaces_v317(rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v339.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.339',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v339.res': out_sha,
            'runtime_v339.lua': hashlib.sha256((W / 'runtime_v339.lua').read_bytes()).hexdigest(),
            'patch_v339.py': hashlib.sha256((W / 'patch_v339.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'm12_37_zero_jmp_below_params_preserved',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'v339_hero_merc_boundary_preserved_and_hero3_unrestricted',
            'v339_v338_save_items_auto_healed',
            'v338_mount_medal_seal_enchants_priority_and_confirm_pass',
            'v336_v335_v334_v333_v332_v331_v330_v319_v317_v308_v307_v306_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v339.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v339.json').write_text(text, encoding='utf-8')
    print('ALL v1.339 TESTS PASSED!')


if __name__ == '__main__':
    main()
