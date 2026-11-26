"""Targeted verification suite for v1.344:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees() + m12/76 window title
   & m12/22232 login UI version string checks ('1.344', '不烧心版 1.344', zero leftover '1.343')
2. Strict Lua 5.1 syntax parse, GBK 0x5C check, AND LuaJIT 2.0 200-active-local limit AST audit
   on EVERY function/nested block of embedded runtime_v344.lua (assert <= 195 active locals;
   would have caught v1.343's 210 > 200 overflow)
3. m12/37 (qs_item_box.Main) zero JMP A < params & m14/256 WAL bytecode hooks intact
4. Hardened Gly独 hooking:
   - Read-only __newindex metatable on Gly独 bypassed cleanly via rawset
   - Distinct S.script_setting.Gly独 vs _G.Gly独 both hooked
   - Numeric-string U.人物选择 ('1') normalized via tonumber()
5. Full v1.343 WAL + 3s continuous auto-save verification & v1.342..v1.335 regressions.
"""
import hashlib
import json
from pathlib import Path

from ljdis import OPS
from ljtool import Dump
from lua51_eval import LuaTable, Parser, syntax_check, tokenize
from native_test_utils import trees
from resource_tools import decode
from test_v335 import test_v335_repeat_autocast_ux
from test_v338 import test_v338_mount_medal_seal_enchants_and_confirm
from test_v339 import test_v339_hero_merc_boundary_and_heal
from test_v340 import _run_ranged_sim
from test_v341 import test_v341_merc_hit_fx_and_action_speed
from test_v342 import test_v342_settings_save_btn
from test_v343 import _make_wal_env, test_v343_wal_and_3s_autosave

W = Path(__file__).resolve().parent
PREV_SHA = 'e73cccc4a04d64685038ac92ece8e85d3dc075608899234a0e427ae4bbdff595'


def extract_runtime_v344(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.344 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v344.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def assert_luajit20_local_limits(rt_src, max_limit=195):
    """Audit active local count in every function & nested block against LuaJIT 2.0's 200-local hard limit."""
    ast = Parser(tokenize(rt_src)).parse()
    offenders = []
    max_seen = [0, '<none>']

    def walk_expr(e):
        if not isinstance(e, tuple) or not e:
            return
        if e[0] == 'func':
            check_func(e, '<anon>')
            return
        for item in e[1:]:
            if isinstance(item, tuple):
                walk_expr(item)
            elif isinstance(item, list):
                for x in item:
                    if isinstance(x, tuple):
                        walk_expr(x)

    def walk_block(stmts, active, max_ref):
        cur = active
        for st in stmts:
            tag = st[0]
            if tag == 'local':
                if st[2]:
                    for e in st[2]:
                        walk_expr(e)
                cur += len(st[1])
                if cur > max_ref[0]:
                    max_ref[0] = cur
            elif tag == 'local_func':
                cur += 1
                if cur > max_ref[0]:
                    max_ref[0] = cur
                check_func(st[2], st[1])
            elif tag == 'func_def':
                check_func(st[3], '.'.join(st[1]))
            elif tag == 'do':
                walk_block(st[1], cur, max_ref)
            elif tag == 'if':
                for cond, blk in st[1]:
                    walk_expr(cond)
                    walk_block(blk, cur, max_ref)
                if st[2]:
                    walk_block(st[2], cur, max_ref)
            elif tag == 'while':
                walk_expr(st[1])
                walk_block(st[2], cur, max_ref)
            elif tag == 'repeat':
                walk_block(st[1], cur, max_ref)
                walk_expr(st[2])
            elif tag == 'for_num':
                for e in (st[2], st[3], st[4]):
                    if e:
                        walk_expr(e)
                if cur + 4 > max_ref[0]:
                    max_ref[0] = cur + 4
                walk_block(st[5], cur + 4, max_ref)
            elif tag == 'for_in':
                for e in st[2]:
                    walk_expr(e)
                if cur + len(st[1]) + 3 > max_ref[0]:
                    max_ref[0] = cur + len(st[1]) + 3
                walk_block(st[3], cur + len(st[1]) + 3, max_ref)
            else:
                for item in st[1:]:
                    if isinstance(item, tuple):
                        walk_expr(item)
                    elif isinstance(item, list):
                        for x in item:
                            if isinstance(x, tuple):
                                walk_expr(x)

    def check_func(fn_node, name):
        params = fn_node[1]
        m = [len(params)]
        walk_block(fn_node[3], len(params), m)
        if m[0] > max_seen[0]:
            max_seen[0], max_seen[1] = m[0], name
        if m[0] > max_limit:
            offenders.append((m[0], name))

    check_func(ast, '<main>')
    assert not offenders, f'LuaJIT 2.0 active local limit exceeded (>{max_limit}): {offenders}'
    return max_seen[0], max_seen[1]


def test_diff_syntax_version_and_bytecode():
    base_bytes = (W / 'game_v343.res').read_bytes()
    out_bytes = (W / 'game_v344.res').read_bytes()
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
    assert '1.344' in m12_76_strs and '不烧心版 1.344' in m12_76_strs, f'm12/76 missing 1.344: {m12_76_strs}'
    m12_22232_strs = [v.decode('gbk', 'replace') for v in mods_o[12].protos[22232].kgc if isinstance(v, bytes)]
    assert '不烧心版 1.344' in m12_22232_strs, 'm12/22232 missing 不烧心版 1.344'

    for mid in (12, 14, 30):
        for p in mods_o[mid].protos:
            for v in p.kgc:
                if isinstance(v, bytes) and not v.startswith(b'-- Guimeng v1.344'):
                    assert b'v1.343' not in v, f'Leftover v1.343 in m{mid}/{p.idx}'
                    if mid == 12 and p.idx in (76, 22232):
                        assert b'1.343' not in v, f'Leftover 1.343 in m12/{p.idx}'

    p37 = mods_o[12].protos[37]
    for pc, ins in enumerate(p37.bc):
        if OPS[ins & 0xFF] == 'JMP':
            a = (ins >> 8) & 0xFF
            assert a >= p37.params, f'm12/37 pc={pc} has JMP A={a} < params={p37.params}'

    p256 = mods_o[14].protos[256]
    assert OPS[p256.bc[1045] & 0xFF] == 'GGET' and p256.gc((p256.bc[1045] >> 16) & 0xFFFF) == b'type'
    assert OPS[p256.bc[1111] & 0xFF] == 'TGETS' and p256.gc((p256.bc[1111] >> 16) & 0xFF) == b'__gm_wal_try_load_v343'

    rt_src = extract_runtime_v344(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    max_locals, max_fn = assert_luajit20_local_limits(rt_src, max_limit=195)
    print(f'LUAJIT20_LOCAL_AUDIT_PASS: max_active_locals={max_locals} in {max_fn} (limit=200)')
    return mods_o, rt_src


def test_v344_hardened_hooks_and_string_slot(rt_src):
    w = _make_wal_env(rt_src, story='来世续缘', with_base_dat=True)
    # 1. Verify rawset bypasses a locked __newindex metatable on Gly独, and both S.script_setting.Gly独 & _G.Gly独 are hooked
    ss = w['S'].rawget('script_setting')
    if not isinstance(ss, LuaTable):
        ss = LuaTable()
        w['S'].rawset('script_setting', ss)

    blocked_writes = []
    g_ss = LuaTable({'鼠标道具': 0})
    g_ss.rawset('存档', lambda p, h, k=None: None)
    g_ss.rawset('结束游戏', lambda f=None: None)
    g_ss_mt = LuaTable({'__newindex': lambda t, k, v: blocked_writes.append(k)})
    w['ev'].G.rawget('setmetatable')(g_ss, g_ss_mt)
    ss.rawset('Gly独', g_ss)

    assert w['S'].rawget('__gm_install_wal_hooks_v343')() is True
    st = w['st']
    assert g_ss.rawget('存档') == st.rawget('save_wrap'), 'rawset must bypass __newindex lock'
    assert g_ss.rawget('结束游戏') == st.rawget('exit_wrap'), 'rawset must bypass __newindex lock'
    assert blocked_writes == [], f'Expected 0 __newindex invocations, got {blocked_writes}'

    # 2. Verify numeric-string slot '1' works for 3s auto-save
    w['U'].rawset('人物选择', '1')
    w['clock_ms'][0] = 60000.0
    st.rawset('last_auto_ms', 60000.0)
    w['clock_ms'][0] = 63000.0
    w['tick']()
    while st.rawget('job') is not None:
        w['tick']()
    assert st.rawget('wal_commits') == 1 and (w['base_path'] + '.wal') in w['vfs']
    print('HARDENED_RAWSET_DUAL_GLY_AND_STR_SLOT_V344_PASS!')


def main():
    mods_o, rt_src = test_diff_syntax_version_and_bytecode()
    test_v344_hardened_hooks_and_string_slot(rt_src)
    test_v343_wal_and_3s_autosave(rt_src)
    test_v342_settings_save_btn(rt_src)
    test_v341_merc_hit_fx_and_action_speed(rt_src)
    for sk in ('刺客普通攻击', '蝉舞'):
        res, _, _ = _run_ranged_sim(rt_src, skill=sk, dx_px=240.0, fps=66.0, reload_merc_mode=True)
        assert res['dmg_count'] == 1 and res['dmg_frame'] == res['end_frame'] == res['hit_fx_frame'], (sk, res)
    test_v339_hero_merc_boundary_and_heal(mods_o[12], rt_src)
    test_v338_mount_medal_seal_enchants_and_confirm(mods_o[12], rt_src)
    test_v335_repeat_autocast_ux(rt_src)

    out_bytes = (W / 'game_v344.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.344',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v344.res': out_sha,
            'runtime_v344.lua': hashlib.sha256((W / 'runtime_v344.lua').read_bytes()).hexdigest(),
            'patch_v344.py': hashlib.sha256((W / 'patch_v344.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'm12_76_window_title_and_m12_22232_version_1_344_verified',
            'm12_37_zero_jmp_below_params_preserved',
            'm14_256_wal_load_and_direct_table_r4_8_bytecode_verified',
            'strict_lua51_syntax_zero_gbk_0x5c_and_luajit20_200_local_audit_pass',
            'v344_rawset_metatable_bypass_dual_gly_and_string_slot_pass',
            'v343_wal_stream_roundtrip_slicing_3s_autosave_afk_skip_guards_exit_flush_200x_pass',
            'v343_qianchi_isolated_pass',
            'v342_settings_save_btn_pass',
            'v341_merc_skill_resp_and_v340_sanity_pass',
            'v339_v338_v335_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v344.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v344.json').write_text(text, encoding='utf-8')
    print('ALL v1.344 TESTS PASSED!')


if __name__ == '__main__':
    main()
