"""Exhaustive verification suite for v1.309:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v309.lua
3. Real m12/6488 monster database verification (wrapped in 数据保护 __数据 proxies):
   - All 34 Boss set blueprint entries (covering all 32 Boss set blueprints) rewritten to 110,110
   - Every non-blueprint item on those Bosses preserved byte-for-byte
   - All 24 non-Boss trash-mob blueprint entries (10000/50000/100000) untouched
   - Ux雌.伯伯扣扣() drop cache cleared on transition
   - Exact 10.00% baseline probability (11/110) verified against real 247-callback roll <= 11 rule
   - 「前尘忆梦」 untouched & story switch restores original 20/30/50 strings verbatim
4. v1.308 authentic proxy 【仓库】 button + Mode 2 ordinary materials + v1.306 gather formula regressions
"""
import hashlib
import json
import math
from pathlib import Path

from ljtool import Dump
from lua51_eval import LuaTable, syntax_check
from native_test_utils import trees
from patch_v239 import OPS
from resource_tools import decode
from test_v300 import make_env
from test_v307 import test_mode2_ordinary_materials, test_v306_regression
from test_v308 import test_authentic_proxy_warehouse_button

W = Path(__file__).resolve().parent
BASE_SHA = 'd0119c26a4f3d3bab3de28d1f5dcbd74334bb3211ac46cc63da021fe7b206763'

ALL_32_BLUEPRINTS = {
    '沃玛教主的利爪', '触龙神的毒囊', '骷髅教主的火种', '魔血之魂晶',
    '赤月恶魔的尖刺', '祖玛教主的怒火', '金刚不朽光环', '罪孽教主的长舌',
    '罪孽证据的钥匙', '牛魔王的尖角', '震天魔神的权杖', '霸王教主的巨刃',
    '诺玛族之物', '地灭天王的荆棘', '火影的光辉', '冥影魔王的羽翼',
    '骷髅魔王的火种', '杀魔', '师玉', '九梦',
    '玄武天王核心', '青龙天王核心', '朱雀天王核心', '白虎天王核心',
    '魔灵神主核心', '阎昆魔素', '赤龙的法器', '赤龙的心脏',
    '卧龙的逆鳞', '虎战领主之爪', '皇陵鲲吾剑', '毁灭之爪',
}


def extract_runtime_v309(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.309 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v309.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_and_syntax():
    base_bytes = (W / 'game_v308.res').read_bytes()
    out_bytes = (W / 'game_v309.res').read_bytes()
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

    rt_src = extract_runtime_v309(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def decode_real_monsters_6488(d12):
    """Decode every monster template from real m12/6488 in game_v309.res."""
    p6488 = d12.protos[6488]
    monsters = {}
    regs = {}
    for w in p6488.bc:
        op = OPS[w & 255]
        a, d = (w >> 8) & 255, w >> 16
        if op == 'KSTR':
            regs[a] = p6488.gc(d).decode('gbk', 'replace')
        elif op == 'CALL':
            mname, ini_hex = regs.get(1), regs.get(2)
            if mname and ini_hex and ini_hex.startswith('4BD5'):
                hex_part = ini_hex[:-33] if ini_hex.endswith('*') else ini_hex
                ini_txt = bytes(x ^ 0x10 for x in bytes.fromhex(hex_part)).decode('gbk', 'replace')
                drop_line, extra_line = '', ''
                for line in ini_txt.splitlines():
                    line = line.strip()
                    if line.startswith('物品掉落文本='):
                        drop_line = line[len('物品掉落文本='):]
                    elif line.startswith('附加='):
                        extra_line = line[len('附加='):]
                monsters[mname] = (drop_line, 'BOSSぅ' in extra_line)
    return monsters


def test_real_boss_blueprint_drops(d12, rt_src):
    # Verify all 247 monster spawn callbacks still use roll <= 11
    cb_11x = [
        pid for pid, p in enumerate(d12.protos)
        if len(p.bc) == 1178 and OPS[p.bc[1174] & 255] == 'KSHORT'
        and ((p.bc[1174] >> 8) & 255) == 14 and (p.bc[1174] >> 16) == 11
    ]
    assert len(cb_11x) == 247, f'Expected 247 11x spawn callbacks, got {len(cb_11x)}'

    real_monsters = decode_real_monsters_6488(d12)
    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']

    # Populate S.游戏属性组 with 数据保护-style __数据 proxies from real m12/6488!
    char_group = LuaTable()
    orig_map = {}
    for mname, (drop_str, is_boss) in real_monsters.items():
        if not drop_str:
            continue
        orig_map[mname] = (drop_str, is_boss)
        extra_raw = LuaTable({'BOSS': 0}) if is_boss else LuaTable()
        extra_proxy = LuaTable({'__数据': extra_raw})
        raw_cfg = LuaTable({'名称': mname, 'drop_item': drop_str, '附加': extra_proxy})
        cfg_proxy = LuaTable({'__数据': raw_cfg})
        char_group.rawset(mname, cfg_proxy)
    S.rawset('游戏属性组', char_group)

    drop_cache = LuaTable({'沃玛教主': 'STALE_CACHED_20', '赤龙魔王': 'STALE_CACHED_30', '天狼蜘蛛': 'KEEP_MOB_CACHE'})
    U.rawset('伯伯扣扣', lambda: drop_cache)

    ev.G.get('loadstring')(rt_src)(S)

    # Trigger via load_state (before map spawn!)
    S.rawget('__gm_load_state_v299')(True, False)

    # Verify cache cleared for Bosses and preserved for non-Boss mob
    assert drop_cache.rawget('沃玛教主') is None
    assert drop_cache.rawget('赤龙魔王') is None
    assert drop_cache.rawget('天狼蜘蛛') == 'KEEP_MOB_CACHE'

    boss_bp_entries_checked = 0
    mob_bp_entries_checked = 0
    covered_bps = set()

    for mname, (orig_str, is_boss) in orig_map.items():
        cur_str = char_group.rawget(mname).rawget('__数据').rawget('drop_item')
        orig_parts = [e for e in orig_str.split('|') if e]
        cur_parts = [e for e in cur_str.split('|') if e]
        assert len(orig_parts) == len(cur_parts), f'{mname}: entry count mismatch'

        for oe, ce in zip(orig_parts, cur_parts):
            op = oe.split(',')
            cp = ce.split(',')
            if op[0] in ALL_32_BLUEPRINTS:
                if is_boss:
                    assert cp == [op[0], op[1], '110', '110'], f'Boss {mname} {op[0]}: expected 110,110 got {cp}'
                    # Verify exact baseline probability under 11x drop rule:
                    eff_n = math.ceil(int(cp[2]) / 1)
                    eff_p = min(11, eff_n) / eff_n
                    assert abs(eff_p - 0.10) < 1e-12, f'{mname} {op[0]}: expected 10%, got {eff_p}'
                    boss_bp_entries_checked += 1
                    covered_bps.add(op[0])
                else:
                    assert ce == oe, f'Non-boss mob {mname} {op[0]} must stay untouched: {oe} vs {ce}'
                    mob_bp_entries_checked += 1
            else:
                assert ce == oe, f'Non-blueprint item on {mname} changed: {oe} -> {ce}'

    assert boss_bp_entries_checked == 34, f'Expected 34 Boss blueprint entries, got {boss_bp_entries_checked}'
    assert mob_bp_entries_checked == 24, f'Expected 24 non-Boss mob entries, got {mob_bp_entries_checked}'
    assert covered_bps == ALL_32_BLUEPRINTS, f'Missing blueprints: {ALL_32_BLUEPRINTS - covered_bps}'

    # Switch to 「前尘忆梦」 -> must restore ALL 34 Boss drop_item strings verbatim!
    U.rawset('版本选择', '前尘忆梦')
    drop_cache.rawset('沃玛教主', 'LAISHI_CACHED_110')
    S.rawget('__gm_pickup_frame_v299')(U, G)
    assert drop_cache.rawget('沃玛教主') is None
    for mname, (orig_str, _) in orig_map.items():
        cur_str = char_group.rawget(mname).rawget('__数据').rawget('drop_item')
        assert cur_str == orig_str, f'前尘忆梦 restore mismatch on {mname}'

    # Fresh 「前尘忆梦」 session never modifies any Boss template
    env_old = make_env(story='前尘忆梦')
    ev_o, S_o, U_o, G_o = env_old['ev'], env_old['S'], env_old['U'], env_old['G']
    wm_orig = orig_map['沃玛教主'][0]
    cg_o = LuaTable({'沃玛教主': LuaTable({'__数据': LuaTable({'名称': '沃玛教主', 'drop_item': wm_orig, '附加': LuaTable({'__数据': LuaTable({'BOSS': 0})})})})})
    S_o.rawset('游戏属性组', cg_o)
    ev_o.G.get('loadstring')(rt_src)(S_o)
    S_o.rawget('__gm_load_state_v299')(True, False)
    S_o.rawget('__gm_pickup_frame_v299')(U_o, G_o)
    assert cg_o.rawget('沃玛教主').rawget('__数据').rawget('drop_item') == wm_orig


def main():
    mods_o, rt_src = test_diff_and_syntax()
    test_real_boss_blueprint_drops(mods_o[12], rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v309.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.309',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v309.res': out_sha,
            'runtime_v309.lua': hashlib.sha256((W / 'runtime_v309.lua').read_bytes()).hexdigest(),
            'patch_v309.py': hashlib.sha256((W / 'patch_v309.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'all_247_spawn_callbacks_11x_verified',
            'all_34_boss_entries_covering_32_blueprints_rewritten_to_110_exact_10pct',
            'all_non_blueprint_boss_drops_byte_identical',
            'all_24_non_boss_trash_mob_blueprint_entries_untouched',
            'drop_cache_cleared_on_story_transition',
            'qianchi_isolated_and_story_switch_restores_original_drop_item',
            'v308_warehouse_proxy_button_regression_pass',
            'v307_mode2_ordinary_materials_regression_pass',
            'v306_gather_formula_regression_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v309.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v309.json').write_text(text, encoding='utf-8')
    print('ALL v1.309 TESTS PASSED!')


if __name__ == '__main__':
    main()
