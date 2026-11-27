"""Targeted verification suite for v1.347:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees() + m12/76 window title
   & m12/22232 login UI version string checks ('1.347', '不烧心版 1.347', zero leftover '1.346')
2. Strict Lua 5.1 syntax parse, GBK 0x5C check, ZERO rawset in runtime_v347.lua, and LuaJIT 2.0
   200-active-local limit AST audit across every function/block (<= 195 active locals)
3. m12/37 zero JMP A < params + m14/253, m14/99, and m14/256 WAL bytecode hooks intact
4. Boss respawn verification:
   - m12/18558 #1497 (冥影魔王, 事件标识=1377) unpacked config has 刷新间隔=45
   - All 247 copies of 随着剧烈的震动 timer proto in m12 have KSHORT 1, 45 at PC 9, 17, 26
   - S.__gm_boss_cycle_boot_v347 wraps 类_事件.死亡 (re-checked in pickup_frame) with rawset &
     Gly独.__newindex traps armed: killing 赤龙魔王 in 赤龙城 (来世续缘) triggers screen shake,
     red toast '随着剧烈的震动,赤龙女王会在45秒后苏醒', and 45,000ms timer spawning ID 1477
     at (50, 24) via Ux雌.窗口相关.经验倍率; duplicate death / pet / non-赤龙城 / 前尘忆梦
     ignored; leaving 赤龙城 or loading cancels timer; 200x hoisted cycle loop passes
5. Direct & recent regressions: v1.346 native autosave suppression + v1.345 WAL + v1.342
   [Save] + v1.341 + v1.340 + v1.339 + v1.338 + v1.335.
"""
import hashlib
import json
from pathlib import Path

from ljdis import OPS
from ljtool import Dump
from lua51_eval import LuaTable, syntax_check
from native_test_utils import trees
from patch_v139 import ad
from patch_v201 import unpack_config
from resource_tools import decode
from test_v335 import test_v335_repeat_autocast_ux
from test_v338 import test_v338_mount_medal_seal_enchants_and_confirm
from test_v339 import test_v339_hero_merc_boundary_and_heal
from test_v340 import _run_ranged_sim
from test_v341 import test_v341_merc_hit_fx_and_action_speed
from test_v342 import test_v342_settings_save_btn
from test_v344 import assert_luajit20_local_limits
from test_v345 import _make_trapped_wal_env, test_v345_zero_mutation_wal_and_3s_autosave
from test_v346 import test_v346_suppress_native_autosaves

W = Path(__file__).resolve().parent
PREV_SHA = '16e5b454ae9f58764924d07e9eef10ba48d17579db87130dfd211b8e1c86be09'


def extract_runtime_v347(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.347 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v347.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_syntax_version_and_bytecode():
    base_bytes = (W / 'game_v346.res').read_bytes()
    out_bytes = (W / 'game_v347.res').read_bytes()
    assert hashlib.sha256(base_bytes).hexdigest() == PREV_SHA

    outer_b, mods_b = decode(base_bytes, (12, 14, 30))
    outer_o, mods_o = decode(out_bytes, (12, 14, 30))

    root_b, root_o = outer_b.protos[0], outer_o.protos[0]
    changed_slots = [i for i in range(root_b.nkgc) if root_b.gc(i) != root_o.gc(i)]
    assert changed_slots == [12, 14, 30], f'Expected only [12, 14, 30] changed, got {changed_slots}'
    for mid in (12, 14, 30):
        ro = mods_o[mid].rebuild()
        assert Dump(ro).rebuild() == ro
        trees(mods_o[mid])

    m12_76_strs = [v.decode('gbk', 'replace') for v in mods_o[12].protos[76].kgc if isinstance(v, bytes)]
    assert '1.347' in m12_76_strs and '不烧心版 1.347' in m12_76_strs, f'm12/76 missing 1.347: {m12_76_strs}'
    m12_22232_strs = [v.decode('gbk', 'replace') for v in mods_o[12].protos[22232].kgc if isinstance(v, bytes)]
    assert '不烧心版 1.347' in m12_22232_strs, 'm12/22232 missing 不烧心版 1.347'

    for mid in (12, 14, 30):
        for p in mods_o[mid].protos:
            for v in p.kgc:
                if isinstance(v, bytes) and not v.startswith(b'-- Guimeng v1.347'):
                    assert b'v1.346' not in v, f'Leftover v1.346 in m{mid}/{p.idx}'
                    if mid == 12 and p.idx in (76, 22232):
                        assert b'1.346' not in v, f'Leftover 1.346 in m12/{p.idx}'

    # Verify 冥影魔王 (ID 1377) 刷新间隔=45 in m12/18558 #1497
    cfg = unpack_config(mods_o[12].protos[18558].gc(1497)).decode('gbk')
    assert '绑定属性=冥影魔王\r\n' in cfg and '事件标识=1377\r\n' in cfg
    assert '刷新间隔=45\r\n' in cfg and '刷新间隔=0\r\n' not in cfg

    # Verify all 247 copies of 随着剧烈的震动 timer proto set 45s at PC 9, 17, 26
    kw = '随着剧烈的震动'.encode('gbk')
    timer_ps = [p for p in mods_o[12].protos if any(isinstance(v, bytes) and kw in v for v in p.kgc)]
    assert len(timer_ps) == 247
    ins45 = ad('KSHORT', 1, 45)
    for tp in timer_ps:
        assert tp.bc[9] == ins45 and tp.bc[17] == ins45 and tp.bc[26] == ins45, tp.idx

    p37 = mods_o[12].protos[37]
    for pc, ins in enumerate(p37.bc):
        if OPS[ins & 0xFF] == 'JMP':
            a = (ins >> 8) & 0xFF
            assert a >= p37.params, f'm12/37 pc={pc} has JMP A={a} < params={p37.params}'

    p253 = mods_o[14].protos[253]
    assert OPS[p253.bc[1] & 0xFF] == 'TGETS' and p253.gc((p253.bc[1] >> 16) & 0xFF) == b'__gm_wal_try_save_v345'
    assert OPS[p253.bc[-7] & 0xFF] == 'TGETS' and p253.gc((p253.bc[-7] >> 16) & 0xFF) == b'__gm_wal_after_vanilla_save_v345'
    p99 = mods_o[14].protos[99]
    assert OPS[p99.bc[10] & 0xFF] == 'TGETS' and p99.gc((p99.bc[10] >> 16) & 0xFF) == b'__gm_wal_on_exit_v345'
    p256 = mods_o[14].protos[256]
    assert OPS[p256.bc[1045] & 0xFF] == 'GGET' and p256.gc((p256.bc[1045] >> 16) & 0xFFFF) == b'type'
    assert OPS[p256.bc[1111] & 0xFF] == 'TGETS' and p256.gc((p256.bc[1111] >> 16) & 0xFF) == b'__gm_wal_try_load_v343'

    rt_src = extract_runtime_v347(mods_o[14])
    assert 'rawset' not in rt_src, 'runtime_v347.lua must NEVER call or reference rawset'
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    max_locals, max_fn = assert_luajit20_local_limits(rt_src, max_limit=195)
    print(f'BOSS_BYTECODE_AND_LUAJIT20_AUDIT_PASS: max_active_locals={max_locals} in {max_fn}, 冥影=45s, 247x赤龙魔王=45s!')
    return mods_o, rt_src


def test_v347_chilong_boss_cycle(rt_src):
    w = _make_trapped_wal_env(rt_src, story='来世续缘', with_base_dat=True)
    S, U, G_env, G_obj = w['S'], w['U'], w['G_env'], w['G']
    ev_cls = G_env.rawget('类_事件')
    if not isinstance(ev_cls, LuaTable):
        ev_cls = LuaTable()
        G_env.rawset('类_事件', ev_cls)
    die_calls = []
    spawns = []
    toasts = []
    shakes = []

    def orig_die(self, killer_id=0, fx=True, drop=True):
        die_calls.append((self.rawget('属性').rawget('名称'), killer_id))

    ev_cls.rawset('死亡', orig_die)
    U.rawget('窗口相关').rawset('经验倍率', lambda x, y, a3, a4, mid, mode: spawns.append((x, y, mid, mode)))
    U.rawget('托管显示').rawset('屏幕提示', lambda msg, col, a3=0: toasts.append((msg, col)))
    G_obj.rawset('屏幕震动', lambda ms, lv, flag: shakes.append((ms, lv, flag)))
    w['g_ss'].rawset('屏幕震动', lambda ms, lv, flag: shakes.append((ms, lv, flag)))

    # Reload v347 with traps armed & clean 类_事件.死亡 -> pickup_frame rewraps automatically
    clean_wr_fn = S.rawget('__gm_wal_state_v343').rawget('orig_save_load')
    if clean_wr_fn is not None:
        U.rawget('窗口相关').rawset('存档读档', clean_wr_fn)
    S.rawset('__gm_runtime_v347_installed', False)
    G_env.get('loadstring')(rt_src)(S)
    S.rawget('__gm_wal_on_load_state_v343')(False)
    bc_st = S.rawget('__gm_boss_cycle_state_v347')
    pf = S.rawget('__gm_pickup_frame_v299')

    # Check pickup_frame re-wraps 类_事件.死亡 if reset
    ev_cls.rawset('死亡', orig_die)
    pf(U, G_obj)
    assert ev_cls.rawget('死亡') == bc_st.rawget('wrapped_die')

    # Setup map = 赤龙城
    U.rawset('地图名称', '赤龙城')
    w['ae'].rawset('地图名称', '赤龙城')

    def make_boss(name='赤龙魔王', owner=-1, pet_cfg=None):
        t = LuaTable({'属性': LuaTable({'名称': name}), '主人id': owner})
        if pet_cfg is not None:
            t.rawset('宠物配置', pet_cfg)
        return t

    # 1. Killing 赤龙魔王 in 赤龙城 schedules 45,000ms Queen respawn
    w['clock_ms'][0] = 100000.0
    boss = make_boss('赤龙魔王', owner=-1)
    ev_cls.rawget('死亡')(boss, 0, True, True)
    assert bc_st.rawget('triggers') == 1 and bc_st.rawget('due_ms') == 145000.0
    assert toasts and '赤龙女王会在45秒后苏醒' in toasts[-1][0]
    assert shakes and shakes[-1] == (3000, 2, True)

    # Duplicate death callback on same boss instance does NOT re-trigger
    w['clock_ms'][0] = 110000.0
    ev_cls.rawget('死亡')(boss, 0, True, True)
    assert bc_st.rawget('triggers') == 1 and bc_st.rawget('due_ms') == 145000.0

    # At 44,999ms: still waiting
    w['clock_ms'][0] = 144999.0
    pf(U, G_obj)
    assert len(spawns) == 0 and bc_st.rawget('due_ms') == 145000.0

    # At 45,000ms: spawns 赤龙女王 (1477) at (50, 24) once
    w['clock_ms'][0] = 145000.0
    pf(U, G_obj)
    assert spawns == [(50, 24, 1477, '指定')]
    assert bc_st.rawget('spawns') == 1 and bc_st.rawget('due_ms') is None

    # 2. Leaving 赤龙城 cancels pending countdown
    boss2 = make_boss('赤龙魔王')
    ev_cls.rawget('死亡')(boss2, 0, True, True)
    assert bc_st.rawget('due_ms') == 190000.0
    U.rawset('地图名称', '比奇县')
    w['ae'].rawset('地图名称', '比奇县')
    w['clock_ms'][0] = 195000.0
    pf(U, G_obj)
    assert len(spawns) == 1 and bc_st.rawget('due_ms') is None and bc_st.rawget('cancels') == 1
    U.rawset('地图名称', '赤龙城')
    w['ae'].rawset('地图名称', '赤龙城')

    # 3. Loading save cancels countdown; pet or unrelated boss ignored
    boss3 = make_boss('赤龙魔王')
    ev_cls.rawget('死亡')(boss3, 0, True, True)
    S.rawset('__gm_loading_save_v299', True)
    pf(U, G_obj)
    assert bc_st.rawget('due_ms') is None and bc_st.rawget('cancels') == 2
    S.rawset('__gm_loading_save_v299', False)

    ev_cls.rawget('死亡')(make_boss('赤龙魔王', owner=0), 0, True, True)
    ev_cls.rawget('死亡')(make_boss('赤龙魔王', owner=-1, pet_cfg=LuaTable({'主人': LuaTable()})), 0, True, True)
    ev_cls.rawget('死亡')(make_boss('触龙神'), 0, True, True)
    assert bc_st.rawget('due_ms') is None

    # 4. 前尘忆梦 isolated
    w_q = _make_trapped_wal_env(rt_src, story='前尘忆梦', with_base_dat=True)
    S_q, U_q = w_q['S'], w_q['U']
    q_spawns = []
    ev_q = LuaTable({'死亡': lambda *a: None})
    w_q['G_env'].rawset('类_事件', ev_q)
    U_q.rawget('窗口相关').rawset('经验倍率', lambda *a: q_spawns.append(a))
    S_q.rawset('__gm_runtime_v347_installed', False)
    w_q['ev'].G.get('loadstring')(rt_src)(S_q)
    U_q.rawset('地图名称', '赤龙城')
    w_q['ae'].rawset('地图名称', '赤龙城')
    ev_q.rawget('死亡')(make_boss('赤龙魔王'), 0, True, True)
    w_q['clock_ms'][0] += 50000.0
    S_q.rawget('__gm_pickup_frame_v299')(U_q, w_q['G'])
    assert len(q_spawns) == 0 and S_q.rawget('__gm_boss_cycle_state_v347').rawget('triggers') == 0

    # 5. 200x hoisted cycle loop with traps armed
    sp_start = bc_st.rawget('spawns')
    for i in range(200):
        w['clock_ms'][0] += 1000.0
        ev_cls.rawget('死亡')(make_boss('赤龙魔王'), 0, True, True)
        w['clock_ms'][0] += 44999.0
        pf(U, G_obj)
        assert bc_st.rawget('spawns') == sp_start + i
        w['clock_ms'][0] += 1.0
        pf(U, G_obj)
        assert bc_st.rawget('spawns') == sp_start + i + 1

    assert not w['traps_triggered'], f'Traps triggered: {w["traps_triggered"]}'
    print('CHILONG_BOSS_CYCLE_V347_PASS (200x hoisted, 冥影 45s + 赤龙女王<->魔王 45s loop)!')


def main():
    mods_o, rt_src = test_diff_syntax_version_and_bytecode()
    test_v347_chilong_boss_cycle(rt_src)
    test_v346_suppress_native_autosaves(rt_src)
    test_v345_zero_mutation_wal_and_3s_autosave(rt_src)
    test_v342_settings_save_btn(rt_src)
    test_v341_merc_hit_fx_and_action_speed(rt_src)
    for sk in ('刺客普通攻击', '蝉舞'):
        res, _, _ = _run_ranged_sim(rt_src, skill=sk, dx_px=240.0, fps=66.0, reload_merc_mode=True)
        assert res['dmg_count'] == 1 and res['dmg_frame'] == res['end_frame'] == res['hit_fx_frame'], (sk, res)
    test_v339_hero_merc_boundary_and_heal(mods_o[12], rt_src)
    test_v338_mount_medal_seal_enchants_and_confirm(mods_o[12], rt_src)
    test_v335_repeat_autocast_ux(rt_src)

    out_bytes = (W / 'game_v347.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.347',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v347.res': out_sha,
            'runtime_v347.lua': hashlib.sha256((W / 'runtime_v347.lua').read_bytes()).hexdigest(),
            'patch_v347.py': hashlib.sha256((W / 'patch_v347.py').read_bytes()).hexdigest(),
        },
        'scope': 'm12 boss timers/configs + 来世续缘 runtime boss loop',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'm12_76_window_title_and_m12_22232_version_1_347_verified',
            'm12_18558_1497_mingying_respawn_45s_verified',
            'm12_247_chilong_queen_to_demon_45s_timers_verified',
            'm12_37_zero_jmp_below_params_preserved',
            'm14_253_m14_99_m14_256_wal_bytecode_hooks_verified',
            'strict_lua51_syntax_zero_gbk_0x5c_zero_rawset_and_luajit20_200_local_audit_pass',
            'v347_chilong_demon_to_queen_45s_loop_200x_traps_and_qianchi_isolated_pass',
            'v346_native_autosave_suppression_200x_pass',
            'v345_zero_gly_mutation_wal_and_3s_autosave_200x_pass',
            'v342_settings_save_btn_pass',
            'v341_merc_skill_resp_and_v340_sanity_pass',
            'v339_v338_v335_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v347.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v347.json').write_text(text, encoding='utf-8')
    print('ALL v1.347 TESTS PASSED!')


if __name__ == '__main__':
    main()
