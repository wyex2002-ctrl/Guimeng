"""Targeted verification suite for v1.345:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees() + m12/76 window title
   & m12/22232 login UI version string checks ('1.345', '不烧心版 1.345', zero leftover '1.344')
2. Strict Lua 5.1 syntax parse, GBK 0x5C check, ZERO rawset in runtime_v345.lua, and LuaJIT 2.0
   200-active-local limit AST audit across every function/block (<= 195 active locals)
3. m12/37 zero JMP A < params + m14/253 (Gly独.存档), m14/99 (Gly独.结束游戏), and m14/256 (Gly独.读档)
   bytecode hooks verified with exact opcodes, constants, and jump targets
4. Zero-mutation Gly独 test: installs hostile throwing traps on global rawset AND on both
   S.script_setting.Gly独 and _G.Gly独 __newindex metatables, then runs full runtime boot,
   __gm_wal_on_load_state_v343(false), GMWAL1 sliced fast-save, AFK skip, manual [Save],
   3-second continuous auto-save, all safety guards, crash recovery, fallbacks, normal exit
   vanilla flush (simulating exact m14/253 & m14/99 bytecode dispatch), C: backup, numeric-string
   slot, 前尘忆梦 isolation, and 200x hoisted repetition loop — verifying zero traps ever fire
5. Direct & recent regressions: v1.342 manual [Save] button + v1.341 + v1.340 + v1.339 + v1.338 + v1.335.
"""
import hashlib
import json
from pathlib import Path

from ljdis import OPS, dis
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
from test_v343 import _make_wal_env, _md5_hex
from test_v344 import assert_luajit20_local_limits

W = Path(__file__).resolve().parent
PREV_SHA = '61c6a22b90694b45f777a444893e812dde6fa1e6a9e636b4698400e5b5761f98'


def extract_runtime_v345(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.345 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v345.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_syntax_version_and_bytecode():
    base_bytes = (W / 'game_v344.res').read_bytes()
    out_bytes = (W / 'game_v345.res').read_bytes()
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
    assert '1.345' in m12_76_strs and '不烧心版 1.345' in m12_76_strs, f'm12/76 missing 1.345: {m12_76_strs}'
    m12_22232_strs = [v.decode('gbk', 'replace') for v in mods_o[12].protos[22232].kgc if isinstance(v, bytes)]
    assert '不烧心版 1.345' in m12_22232_strs, 'm12/22232 missing 不烧心版 1.345'

    for mid in (12, 14, 30):
        for p in mods_o[mid].protos:
            for v in p.kgc:
                if isinstance(v, bytes) and not v.startswith(b'-- Guimeng v1.345'):
                    assert b'v1.344' not in v, f'Leftover v1.344 in m{mid}/{p.idx}'
                    if mid == 12 and p.idx in (76, 22232):
                        assert b'1.344' not in v, f'Leftover 1.344 in m12/{p.idx}'

    p37 = mods_o[12].protos[37]
    for pc, ins in enumerate(p37.bc):
        if OPS[ins & 0xFF] == 'JMP':
            a = (ins >> 8) & 0xFF
            assert a >= p37.params, f'm12/37 pc={pc} has JMP A={a} < params={p37.params}'

    # Verify m14/253 (Gly独.存档) bytecode hooks
    p253 = mods_o[14].protos[253]
    assert OPS[p253.bc[0] & 0xFF] == 'UGET' and (p253.bc[0] >> 16) == 0
    assert OPS[p253.bc[1] & 0xFF] == 'TGETS' and p253.gc((p253.bc[1] >> 16) & 0xFF) == b'__gm_wal_try_save_v345'
    assert OPS[p253.bc[3] & 0xFF] == 'JMP' and (3 + 1 + (p253.bc[3] >> 16) - 32768) == 11
    assert OPS[p253.bc[9] & 0xFF] == 'JMP' and (9 + 1 + (p253.bc[9] >> 16) - 32768) == 11
    assert OPS[p253.bc[10] & 0xFF] == 'RET0'
    assert OPS[p253.bc[11] & 0xFF] == 'ISNEP'
    assert OPS[p253.bc[12] & 0xFF] == 'JMP' and (12 + 1 + (p253.bc[12] >> 16) - 32768) == 16
    assert OPS[p253.bc[-1] & 0xFF] == 'RET0'
    assert OPS[p253.bc[-2] & 0xFF] == 'RET1'
    assert OPS[p253.bc[-3] & 0xFF] == 'CALL'
    assert OPS[p253.bc[-7] & 0xFF] == 'TGETS' and p253.gc((p253.bc[-7] >> 16) & 0xFF) == b'__gm_wal_after_vanilla_save_v345'
    assert OPS[p253.bc[-9] & 0xFF] == 'CALL'
    assert OPS[p253.bc[-10] & 0xFF] == 'UCLO'
    assert dis(p253)

    # Verify m14/99 (Gly独.结束游戏) bytecode hook
    p99 = mods_o[14].protos[99]
    assert OPS[p99.bc[0] & 0xFF] == 'JMP' and (0 + 1 + (p99.bc[0] >> 16) - 32768) == 9
    assert OPS[p99.bc[9] & 0xFF] == 'UGET'
    assert OPS[p99.bc[10] & 0xFF] == 'TGETS' and p99.gc((p99.bc[10] >> 16) & 0xFF) == b'__gm_wal_on_exit_v345'
    assert OPS[p99.bc[12] & 0xFF] == 'JMP' and (12 + 1 + (p99.bc[12] >> 16) - 32768) == 15
    assert OPS[p99.bc[15] & 0xFF] == 'UGET'
    assert OPS[p99.bc[16] & 0xFF] == 'TGETS' and p99.gc((p99.bc[16] >> 16) & 0xFF) == b'__gm_diag_exit_v164'
    assert dis(p99)

    # Verify m14/256 (Gly独.读档) retains both v1.343 WAL hooks intact
    p256 = mods_o[14].protos[256]
    assert OPS[p256.bc[1045] & 0xFF] == 'GGET' and p256.gc((p256.bc[1045] >> 16) & 0xFFFF) == b'type'
    assert OPS[p256.bc[1111] & 0xFF] == 'TGETS' and p256.gc((p256.bc[1111] >> 16) & 0xFF) == b'__gm_wal_try_load_v343'

    rt_src = extract_runtime_v345(mods_o[14])
    assert 'rawset' not in rt_src, 'runtime_v345.lua must NEVER call or reference rawset'
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    max_locals, max_fn = assert_luajit20_local_limits(rt_src, max_limit=195)
    print(f'BYTECODE_AND_LUAJIT20_AUDIT_PASS: max_active_locals={max_locals} in {max_fn} (limit=200), zero rawset!')
    return mods_o, rt_src


def _make_trapped_wal_env(rt_src, *, story='来世续缘', with_base_dat=True):
    """Build WAL test env with trapped rawset, trapped Gly独.__newindex, and m14/253 + m14/99 bytecode dispatch."""
    w = _make_wal_env(rt_src, story=story, with_base_dat=with_base_dat)
    ev, S, G_env, G_obj = w['ev'], w['S'], w['G_env'], w['G']
    traps_triggered = []

    # Wire m14/253 (Gly独.存档) bytecode semantics: pre-hook -> orig -> post-hook
    orig_save = G_obj.rawget('存档')
    orig_exit = G_obj.rawget('结束游戏')

    def bytecode_save(path, hd, key=None):
        try_fn = S.rawget('__gm_wal_try_save_v345')
        if try_fn is not None and try_fn(path, hd, key):
            return None
        res = orig_save(path, hd, key)
        after_fn = S.rawget('__gm_wal_after_vanilla_save_v345')
        if after_fn is not None:
            after_fn(path)
        return res

    def bytecode_exit(flag=None):
        on_exit = S.rawget('__gm_wal_on_exit_v345')
        if on_exit is not None:
            on_exit(flag)
        return orig_exit(flag)

    G_obj.rawset('存档', bytecode_save)
    G_obj.rawset('结束游戏', bytecode_exit)

    # Install hostile C:\cccyyy\main:68 traps on BOTH rawset and Gly独.__newindex AFTER setting up mock
    trap_mt = LuaTable({'__newindex': lambda t, k, v: traps_triggered.append(('gly_newindex', k))})
    ev.G.rawget('setmetatable')(G_obj, trap_mt)

    g_ss = LuaTable({'鼠标道具': 0, '存档': bytecode_save, '结束游戏': bytecode_exit})
    ev.G.rawget('setmetatable')(g_ss, trap_mt)
    ss = S.rawget('script_setting')
    if not isinstance(ss, LuaTable):
        ss = LuaTable()
        S.rawset('script_setting', ss)
    ss.rawset('Gly独', g_ss)

    def trap_rawset(t, k, v):
        traps_triggered.append(('rawset', k))
        raise RuntimeError(f'TRAP_RAWSET_OSEXIT:{k}')

    # Verify reloading runtime_v345 / calling on_load_state NEVER triggers rawset or __newindex trap!
    ev.G.rawset('rawset', trap_rawset)
    S.rawset('__gm_runtime_v345_installed', False)
    ev.G.get('loadstring')(rt_src)(S)
    S.rawget('__gm_wal_on_load_state_v343')(False)
    w['st'] = S.rawget('__gm_wal_state_v343')
    w['g_ss'] = g_ss
    w['tick'] = S.rawget('__gm_wal_frame_tick_v343')
    w['try_load'] = S.rawget('__gm_wal_try_load_v343')
    w['step_job'] = S.rawget('__gm_wal_step_job_v343')
    w['decode_stream'] = S.rawget('__gm_wal_decode_stream_v343')
    w['traps_triggered'] = traps_triggered
    assert not traps_triggered, f'Traps triggered during init/on_load_state: {traps_triggered}'
    return w


def test_v345_zero_mutation_wal_and_3s_autosave(rt_src):
    # 1. Basic WAL save -> frame-sliced completion -> crash recovery load roundtrip (with active traps!)
    w = _make_trapped_wal_env(rt_src, story='来世续缘', with_base_dat=True)
    st = w['st']
    assert st.rawget('save_wrap') is None and st.rawget('exit_wrap') is None

    big_tbl = LuaTable()
    for i in range(1, 350):
        big_tbl.rawset(f'k_{i}', LuaTable({'v': i, 's': f'条目{i}:带;冒号{{花括号}}', 'f': (i % 2 == 0)}))
    w['hero_data'].rawset('大表测试', big_tbl)
    cyc = LuaTable({'name': 'cycle'})
    cyc.rawset('self', cyc)
    w['hero_data'].rawset('循环表', cyc)
    w['hero_data'].rawset('非法数', float('nan'))
    w['hero_data'].rawset('正无穷', float('inf'))

    w['auto_step_ms'][0] = 2.0
    w['G'].rawget('存档')(w['base_path'], w['hero_data'], '归梦748zuobigou作弊狗siquanjia')
    assert len(w['vanilla_saves']) == 0, 'WAL save should NOT invoke slow vanilla orig_save'
    assert st.rawget('job') is not None, 'Large table with 2ms clock step should yield mid-serialization'

    frames = 0
    while st.rawget('job') is not None:
        w['tick']()
        frames += 1
        assert frames < 200
    assert frames >= 2 and st.rawget('wal_commits') == 1
    wal_path = w['base_path'] + '.wal'
    assert wal_path in w['vfs'] and (w['base_path'] + '.wal.tmp') not in w['vfs']

    # Crash recovery via S.__gm_wal_try_load_v343
    w['auto_step_ms'][0] = 0.0
    loaded = w['try_load'](w['base_path'], w['base_md5'], False)
    assert isinstance(loaded, LuaTable) and loaded.length() == 11 and loaded.rawget(9) == 1001
    it = loaded.rawget(1).rawget('包裹格子1')
    assert it.rawget('名称') == '裁决之杖' and it.rawget('属性').rawget('幸运') == 7
    assert it.rawget('道具说明') == '神兵利器\n第二行"带引号"和\\反斜杠'
    assert loaded.rawget(2).rawget('技能快捷101').rawget(1) == '烈火剑法'
    assert loaded.rawget(5).rawget('魔法盾').rawget('减伤') == 45
    assert loaded.rawget(10).rawget('任务变量1') == 77
    hd_out = loaded.rawget(8)
    assert hd_out.rawget('特殊串') == 'a:b;c{d}e\nf\x00g\\h"i'
    assert abs(hd_out.rawget('浮点精度') - 0.123456789012345) < 1e-14
    assert hd_out.rawget('非法数') == 0 and hd_out.rawget('正无穷') == 0
    assert hd_out.rawget('大表测试').rawget('k_349').rawget('v') == 349
    assert st.rawget('wal_loads') == 1

    # 2. AFK zero-write deduplication vs manual force-commit
    w['hero_data'].rawset('大表测试', LuaTable({'k_1': 1}))
    w['G'].rawget('存档')(w['base_path'], w['hero_data'], 'k')
    while st.rawget('job') is not None:
        w['tick']()
    commits_after_change = st.rawget('wal_commits')
    assert commits_after_change == 2

    w['G'].rawget('存档')(w['base_path'], w['hero_data'], 'k')
    while st.rawget('job') is not None:
        w['tick']()
    assert st.rawget('wal_commits') == commits_after_change and st.rawget('wal_skipped_same') == 1

    st.rawset('next_save_manual', True)
    w['G'].rawget('存档')(w['base_path'], w['hero_data'], 'k')
    while st.rawget('job') is not None:
        w['tick']()
    assert st.rawget('wal_commits') == commits_after_change + 1

    # 3. Corruption & base_md5 mismatch fallbacks
    good_wal = w['vfs'][wal_path]
    w['vfs'][wal_path] = good_wal[:-1] + ('X' if good_wal[-1] != 'X' else 'Y')
    assert w['try_load'](w['base_path'], w['base_md5'], False) is None
    w['vfs'][wal_path] = good_wal[:70]
    assert w['try_load'](w['base_path'], w['base_md5'], False) is None
    w['vfs'][wal_path] = good_wal
    assert w['try_load'](w['base_path'], 'FFFFFFFFFFFFFFFFFFFFFFFF', False) is None
    assert wal_path not in w['vfs']
    w['vfs'][wal_path] = good_wal
    assert w['try_load'](w['base_path'], w['base_md5'], True) is None

    # 4. 3-second continuous MMO auto-save (incl. numeric-string slot '1') + safety guards
    w['U'].rawset('人物选择', '1')
    w['clock_ms'][0] = 50000.0
    st.rawset('last_auto_ms', 50000.0)
    w['hero_attr'].rawset('金币', 1000001)
    w['clock_ms'][0] = 52500.0
    c_before = st.rawget('wal_commits')
    w['tick']()
    assert st.rawget('wal_commits') == c_before and st.rawget('job') is None

    w['clock_ms'][0] = 53000.0
    w['tick']()
    while st.rawget('job') is not None:
        w['tick']()
    assert st.rawget('wal_commits') == c_before + 1

    ini_before = len(w['ini_updates'])
    w['fx'].rawset('等级', 53)
    w['hero_attr'].rawset('等级', 53)
    w['clock_ms'][0] = 56000.0
    w['tick']()
    while st.rawget('job') is not None:
        w['tick']()
    assert len(w['ini_updates']) == ini_before + 1 and w['U'].rawget('读取人物').rawget(1).rawget(2) == 53

    w['hero_attr'].rawset('金币', 1000002)
    w['clock_ms'][0] = 59000.0
    w['tick']()
    while st.rawget('job') is not None:
        w['tick']()
    assert len(w['ini_updates']) == ini_before + 1

    def assert_guard_blocks(setup_fn, restore_fn, label):
        c0 = st.rawget('wal_commits')
        w['hero_attr'].rawset('金币', (w['hero_attr'].rawget('金币') or 0) + 1)
        setup_fn()
        w['clock_ms'][0] += 3500.0
        w['tick']()
        assert st.rawget('job') is None and st.rawget('wal_commits') == c0, f'Guard failed: {label}'
        restore_fn()

    cb = w['G_env'].rawget('镜头选择框')
    assert_guard_blocks(lambda: cb.rawset('选中', True), lambda: cb.rawset('选中', False), 'autosave_off')
    assert_guard_blocks(lambda: w['S'].rawset('__gm_loading_save_v299', True),
                        lambda: w['S'].rawset('__gm_loading_save_v299', False), 'loading')
    assert_guard_blocks(lambda: w['fx'].rawset('HP', 0), lambda: w['fx'].rawset('HP', 880), 'dead_hp')
    assert_guard_blocks(lambda: (w['G'].rawset('鼠标道具', 1), w['g_ss'].rawset('鼠标道具', 1)),
                        lambda: (w['G'].rawset('鼠标道具', 0), w['g_ss'].rawset('鼠标道具', 0)), 'cursor_item')
    assert_guard_blocks(lambda: w['G_env'].rawget('物品格子18').rawset('道具', LuaTable()),
                        lambda: w['G_env'].rawget('物品格子18').rawset('道具', None), 'slot18')
    assert_guard_blocks(lambda: w['G_env'].rawget('底部窗口').rawset('可视', False),
                        lambda: w['G_env'].rawget('底部窗口').rawset('可视', True), 'not_ingame')

    # 5. Normal Exit (m14/99 bytecode hook -> __gm_wal_on_exit_v345 -> m14/253 -> __gm_wal_after_vanilla_save_v345)
    v_before = len(w['vanilla_saves'])
    f_before = st.rawget('vanilla_flushes')
    w['G'].rawget('结束游戏')(True)
    assert len(w['vanilla_saves']) == v_before + 1
    assert wal_path not in w['vfs'], 'Exit vanilla flush must delete .wal'
    assert w['exit_calls'] == [True]
    assert st.rawget('vanilla_flushes') == f_before + 1

    # 6. C: backup, brand-new character (missing .dat), and 前尘忆梦 isolation
    w['G'].rawget('存档')('C:/归梦_1(归梦备份存档).dat', w['hero_data'], 'k')
    assert w['vanilla_saves'][-1][0] == 'C:/归梦_1(归梦备份存档).dat'

    w_new = _make_trapped_wal_env(rt_src, story='来世续缘', with_base_dat=False)
    w_new['G'].rawget('存档')(w_new['base_path'], w_new['hero_data'], 'k')
    assert len(w_new['vanilla_saves']) == 1 and not w_new['traps_triggered']

    w_q = _make_trapped_wal_env(rt_src, story='前尘忆梦', with_base_dat=True)
    w_q['G'].rawget('存档')('GameDate/归梦_Q_1.dat', w_q['hero_data'], 'k')
    assert len(w_q['vanilla_saves']) == 1 and w_q['st'].rawget('wal_commits') == 0
    assert w_q['try_load']('GameDate/归梦_Q_1.dat', w_q['base_md5'], False) is None
    w_q['clock_ms'][0] += 5000.0
    w_q['tick']()
    assert w_q['st'].rawget('wal_commits') == 0 and not w_q['traps_triggered']

    assert not w['traps_triggered'], f'Traps triggered: {w["traps_triggered"]}'

    # 7. 200x hoisted repetition loop (with traps armed)
    w2 = _make_trapped_wal_env(rt_src, story='来世续缘', with_base_dat=True)
    st2 = w2['st']
    w2['clock_ms'][0] = 100000.0
    st2.rawset('last_auto_ms', 100000.0)
    for i in range(200):
        w2['clock_ms'][0] += 3000.0
        if i % 4 != 0:
            w2['hero_attr'].rawset('金币', 10000 + i)
        w2['tick']()
        while st2.rawget('job') is not None:
            w2['tick']()
        if i % 20 == 19:
            res_l = w2['try_load'](w2['base_path'], w2['base_md5'], False)
            assert isinstance(res_l, LuaTable) and res_l.length() == 11
    assert st2.rawget('wal_commits') == 151 and st2.rawget('wal_skipped_same') == 49
    assert st2.rawget('wal_loads') == 10
    assert not w2['traps_triggered'], f'Traps triggered in 200x loop: {w2["traps_triggered"]}'
    print('WAL_ZERO_MUTATION_AND_3S_AUTOSAVE_V345_PASS (200x hoisted, rawset & __newindex trapped)!')


def main():
    mods_o, rt_src = test_diff_syntax_version_and_bytecode()
    test_v345_zero_mutation_wal_and_3s_autosave(rt_src)
    test_v342_settings_save_btn(rt_src)
    test_v341_merc_hit_fx_and_action_speed(rt_src)
    for sk in ('刺客普通攻击', '蝉舞'):
        res, _, _ = _run_ranged_sim(rt_src, skill=sk, dx_px=240.0, fps=66.0, reload_merc_mode=True)
        assert res['dmg_count'] == 1 and res['dmg_frame'] == res['end_frame'] == res['hit_fx_frame'], (sk, res)
    test_v339_hero_merc_boundary_and_heal(mods_o[12], rt_src)
    test_v338_mount_medal_seal_enchants_and_confirm(mods_o[12], rt_src)
    test_v335_repeat_autocast_ux(rt_src)

    out_bytes = (W / 'game_v345.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.345',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v345.res': out_sha,
            'runtime_v345.lua': hashlib.sha256((W / 'runtime_v345.lua').read_bytes()).hexdigest(),
            'patch_v345.py': hashlib.sha256((W / 'patch_v345.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'm12_76_window_title_and_m12_22232_version_1_345_verified',
            'm12_37_zero_jmp_below_params_preserved',
            'm14_253_m14_99_m14_256_wal_bytecode_hooks_verified',
            'strict_lua51_syntax_zero_gbk_0x5c_zero_rawset_and_luajit20_200_local_audit_pass',
            'v345_zero_gly_mutation_trapped_rawset_and_newindex_pass',
            'v345_wal_stream_roundtrip_slicing_3s_autosave_afk_skip_guards_exit_flush_200x_pass',
            'v345_qianchi_isolated_pass',
            'v342_settings_save_btn_pass',
            'v341_merc_skill_resp_and_v340_sanity_pass',
            'v339_v338_v335_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v345.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v345.json').write_text(text, encoding='utf-8')
    print('ALL v1.345 TESTS PASSED!')


if __name__ == '__main__':
    main()
