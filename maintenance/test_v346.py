"""Targeted verification suite for v1.346:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees() + m12/76 window title
   & m12/22232 login UI version string checks ('1.346', '不烧心版 1.346', zero leftover '1.345')
2. Strict Lua 5.1 syntax parse, GBK 0x5C check, ZERO rawset in runtime_v346.lua, and LuaJIT 2.0
   200-active-local limit AST audit across every function/block (<= 195 active locals)
3. m12/37 zero JMP A < params + m14/253, m14/99, and m14/256 WAL bytecode hooks intact
4. Native in-game auto-save suppression (v1.346, 来世续缘 only, with rawset & Gly独.__newindex
   traps armed):
   - In-game (底部窗口.可视 == true, base .dat exists) native 存档读档('存档', slot, backup, ...)
     calls (including C: backup triggers) are suppressed (native_autosaves_suppressed increments,
     zero WAL jobs, zero vanilla saves, zero INI writes)
   - Manual [Save] button click (S.__gm_save_btn_click_v342) passes through and commits WAL
   - Normal Quit Game (Gly独.结束游戏 -> wal_flush_vanilla_on_exit) passes through and flushes
     one synchronous vanilla .dat + deletes .wal
   - Out-of-game (底部窗口.可视 == false), missing base .dat (brand-new char), and '读档' load
     calls pass through untouched
   - 3-second silent WAL auto-save still operates normally every 3,000ms
   - Overwritten Ux雌.窗口相关.存档读档 auto-reinstalls wrapper on next wal_frame_tick_v343
   - 「前尘忆梦」 never suppresses 存档读档('存档', ...)
   - 200x hoisted repetition loop across native auto-save suppression + 3s WAL auto-save
5. Direct & recent regressions: v1.345 zero-mutation WAL + v1.342 [Save] + v1.341 + v1.340 +
   v1.339 + v1.338 + v1.335.
"""
import hashlib
import json
from pathlib import Path

from ljdis import OPS
from ljtool import Dump
from lua51_eval import LuaTable, syntax_check
from native_test_utils import trees
from resource_tools import decode
from test_v335 import test_v335_repeat_autocast_ux
from test_v338 import test_v338_mount_medal_seal_enchants_and_confirm
from test_v339 import test_v339_hero_merc_boundary_and_heal
from test_v340 import _run_ranged_sim
from test_v341 import test_v341_merc_hit_fx_and_action_speed
from test_v342 import test_v342_settings_save_btn
from test_v344 import assert_luajit20_local_limits
from test_v345 import _make_trapped_wal_env, test_v345_zero_mutation_wal_and_3s_autosave

W = Path(__file__).resolve().parent
PREV_SHA = '319d761dd161aeb02cac0a4f9dbdd0da07a6c4dc5b8954e71069e819dad54ce6'


def extract_runtime_v346(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.346 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v346.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_syntax_version_and_bytecode():
    base_bytes = (W / 'game_v345.res').read_bytes()
    out_bytes = (W / 'game_v346.res').read_bytes()
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
    assert '1.346' in m12_76_strs and '不烧心版 1.346' in m12_76_strs, f'm12/76 missing 1.346: {m12_76_strs}'
    m12_22232_strs = [v.decode('gbk', 'replace') for v in mods_o[12].protos[22232].kgc if isinstance(v, bytes)]
    assert '不烧心版 1.346' in m12_22232_strs, 'm12/22232 missing 不烧心版 1.346'

    for mid in (12, 14, 30):
        for p in mods_o[mid].protos:
            for v in p.kgc:
                if isinstance(v, bytes) and not v.startswith(b'-- Guimeng v1.346'):
                    assert b'v1.345' not in v, f'Leftover v1.345 in m{mid}/{p.idx}'
                    if mid == 12 and p.idx in (76, 22232):
                        assert b'1.345' not in v, f'Leftover 1.345 in m12/{p.idx}'

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

    rt_src = extract_runtime_v346(mods_o[14])
    assert 'rawset' not in rt_src, 'runtime_v346.lua must NEVER call or reference rawset'
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    max_locals, max_fn = assert_luajit20_local_limits(rt_src, max_limit=195)
    print(f'BYTECODE_AND_LUAJIT20_AUDIT_PASS: max_active_locals={max_locals} in {max_fn} (limit=200), zero rawset!')
    return mods_o, rt_src


def _reload_v346_trapped(rt_src, *, story='来世续缘', with_base_dat=True):
    """Build trapped WAL env and reload v346 IIFE cleanly without double-wrapping wr.存档读档."""
    w = _make_trapped_wal_env(rt_src, story=story, with_base_dat=with_base_dat)
    first_st = w['S'].rawget('__gm_wal_state_v343')
    clean_wr_fn = first_st.rawget('orig_save_load')
    if clean_wr_fn is not None:
        w['U'].rawget('窗口相关').rawset('存档读档', clean_wr_fn)
    w['S'].rawset('__gm_runtime_v346_installed', False)
    w['ev'].G.get('loadstring')(rt_src)(w['S'])
    w['S'].rawget('__gm_wal_on_load_state_v343')(False)
    w['st'] = w['S'].rawget('__gm_wal_state_v343')
    w['tick'] = w['S'].rawget('__gm_wal_frame_tick_v343')
    assert not w['traps_triggered'], f'Traps triggered on v346 reload: {w["traps_triggered"]}'
    return w


def test_v346_suppress_native_autosaves(rt_src):
    w = _reload_v346_trapped(rt_src, story='来世续缘', with_base_dat=True)
    st = w['st']

    wr = w['U'].rawget('窗口相关')
    load_calls = []
    orig_wr = st.rawget('orig_save_load')

    def instrumented_orig(mode, slot, backup=None, extra=0):
        if mode == '读档':
            load_calls.append(slot)
            return
        orig_wr(mode, slot, backup, extra)

    # Simulate engine re-setting wr.存档读档 and let tick() re-install automatically
    wr.rawset('存档读档', instrumented_orig)
    w['tick']()
    assert wr.rawget('存档读档') == st.rawget('wrapped_save_load'), 'tick must re-wrap wr.存档读档'

    save_fn = wr.rawget('存档读档')
    wal_path = w['base_path'] + '.wal'

    # 1. In-game native automatic saves (periodic timer, quest, and C: backup) MUST BE SUPPRESSED
    save_fn('存档', 1, None, 0)
    save_fn('存档', 1, 0, 0)      # C: backup trigger (e.g. m12/286)
    save_fn('存档', '1', None, 0)
    assert st.rawget('native_autosaves_suppressed') == 3
    assert st.rawget('job') is None and wal_path not in w['vfs']
    assert len(w['vanilla_saves']) == 0 and st.rawget('wal_commits') == 0

    # 2. '读档' always passes through
    save_fn('读档', 1, None, 0)
    assert load_calls == [1] and st.rawget('native_autosaves_suppressed') == 3

    # 3. Manual [Save] button click MUST pass through and commit WAL fast-save
    w['clock_ms'][0] = 20000.0
    w['S'].rawget('__gm_save_btn_click_v342')()
    while st.rawget('job') is not None:
        w['tick']()
    assert st.rawget('wal_commits') == 1 and wal_path in w['vfs']
    assert st.rawget('native_autosaves_suppressed') == 3

    # 4. Out-of-game (底部窗口.可视 == false) allows 存档读档 through (char creation / menu)
    bot = w['G_env'].rawget('底部窗口')
    bot.rawset('可视', False)
    save_fn('存档', 1, 1, 0)
    assert len(w['vanilla_saves']) == 1 and w['vanilla_saves'][-1][0] == 'C:/归梦_1(归梦备份存档).dat'
    bot.rawset('可视', True)

    # 5. Missing base .dat (brand-new character) allows initial vanilla .dat creation through
    w_new = _reload_v346_trapped(rt_src, story='来世续缘', with_base_dat=False)
    w_new['U'].rawget('窗口相关').rawget('存档读档')('存档', 1, None, 0)
    assert len(w_new['vanilla_saves']) == 1 and w_new['st'].rawget('native_autosaves_suppressed') == 0

    # 6. Normal Quit Game exit flush MUST pass through and write synchronous vanilla .dat + delete .wal
    v_before = len(w['vanilla_saves'])
    w['G'].rawget('结束游戏')(True)
    assert len(w['vanilla_saves']) == v_before + 1 and wal_path not in w['vfs']
    assert st.rawget('vanilla_flushes') >= 1

    # 7. 「前尘忆梦」 NEVER suppresses native automatic saves
    w_q = _reload_v346_trapped(rt_src, story='前尘忆梦', with_base_dat=True)
    w_q['U'].rawget('窗口相关').rawget('存档读档')('存档', 1, None, 0)
    assert len(w_q['vanilla_saves']) == 1
    assert w_q['st'].rawget('native_autosaves_suppressed') == 0

    # 8. 200x hoisted repetition loop: native auto-saves stay suppressed while 3s WAL auto-save works
    w['clock_ms'][0] = 60000.0
    st.rawset('last_auto_ms', 60000.0)
    c_start = st.rawget('wal_commits')
    sup_start = st.rawget('native_autosaves_suppressed')
    for i in range(200):
        save_fn('存档', 1, (0 if i % 5 == 0 else None), 0)
        w['clock_ms'][0] += 3000.0
        w['hero_attr'].rawset('金币', 500000 + i)
        w['tick']()
        while st.rawget('job') is not None:
            w['tick']()
    assert st.rawget('native_autosaves_suppressed') == sup_start + 200
    assert st.rawget('wal_commits') == c_start + 200
    assert not w['traps_triggered'], f'Traps triggered: {w["traps_triggered"]}'
    print('SUPPRESS_NATIVE_AUTOSAVES_V346_PASS (200x hoisted, 3s WAL active, traps armed)!')


def main():
    mods_o, rt_src = test_diff_syntax_version_and_bytecode()
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

    out_bytes = (W / 'game_v346.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.346',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v346.res': out_sha,
            'runtime_v346.lua': hashlib.sha256((W / 'runtime_v346.lua').read_bytes()).hexdigest(),
            'patch_v346.py': hashlib.sha256((W / 'patch_v346.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'm12_76_window_title_and_m12_22232_version_1_346_verified',
            'm12_37_zero_jmp_below_params_preserved',
            'm14_253_m14_99_m14_256_wal_bytecode_hooks_verified',
            'strict_lua51_syntax_zero_gbk_0x5c_zero_rawset_and_luajit20_200_local_audit_pass',
            'v346_native_autosave_suppression_manual_exit_newchar_load_rewrap_qianchi_200x_pass',
            'v345_zero_gly_mutation_wal_and_3s_autosave_200x_pass',
            'v342_settings_save_btn_pass',
            'v341_merc_skill_resp_and_v340_sanity_pass',
            'v339_v338_v335_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v346.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v346.json').write_text(text, encoding='utf-8')
    print('ALL v1.346 TESTS PASSED!')


if __name__ == '__main__':
    main()
