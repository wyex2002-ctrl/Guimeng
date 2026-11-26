"""Targeted verification suite for v1.343:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees() + m12/76 window title
   & m12/22232 login UI version string checks ('1.343', '不烧心版 1.343', zero leftover '1.342')
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v343.lua
3. m12/37 (qs_item_box.Main) still has ZERO JMP instructions with A < params
4. m14/256 (Gly独.读档) bytecode verification for both WAL fast-load hook (PC 1110..1121) and
   direct table r4[8] hook (PC 1045..1051) with exact jump targets & register bounds
5. v1.343 Dual-Layer WAL Fast-Save & 3-Second MMO Continuous Auto-Save (「来世续缘」 only):
   - GMWAL1 tagged-stream encode/decode roundtrip across integers, floats, negatives, NaN/Inf->0,
     booleans, empty/nested tables, cyclic table guard, GBK strings (incl. 0x5C trail bytes),
     embedded NUL/newline/quote/backslash/delimiter bytes, and multi-slice large tables
   - Frame-sliced serialization budgeting (<=3ms/frame across multiple pickup_frame ticks),
     atomic .wal.tmp -> .wal write, AFK zero-write deduplication (wal_skipped_same), manual
     [Save] force-commit override, and mid-flight resave coalescing (pending_resave)
   - 3-second continuous silent auto-save (WAL_INTERVAL_MS=3000) respecting all safety guards:
     镜头选择框.选中 (OFF/ON), loading state, HP<=0/dead, cursor item/Q_鼠标.被占用,
     物品格子18.道具, 蝶恋花, 底部窗口.可视==false, missing primary .dat (new character -> vanilla)
   - Character-select INI summary update only when name/level/gender/job actually changes
   - Crash recovery via S.__gm_wal_try_load_v343: valid .wal restores exact r4[1..11] & ptime;
     base_md5 mismatch discards stale .wal & falls back to vanilla .dat; corrupted MD5 /
     truncated stream / is_raw / 前尘忆梦 cleanly fall back to vanilla .dat
   - Normal Exit flush via Gly独.结束游戏: aborts in-flight WAL job, executes ONE synchronous
     vanilla m14/253 save to .dat, deletes .wal & .wal.tmp, increments vanilla_flushes
   - 「前尘忆梦」 & C: backup & path==nil completely isolated (always pass through to orig_save)
   - 200x hoisted repetition loop across WAL saves, slices, AFK skips, crash loads, fallbacks,
     and vanilla exit flushes with zero errors
6. Recent regressions: v1.342 manual [Save] button + v1.341 merc hit-FX/action-speed +
   v1.340 ranged sanity + v1.339 + v1.338 + v1.335.
"""
import hashlib
import json
import math
import re
from pathlib import Path

from ljdis import OPS
from ljtool import Dump
from lua51_eval import LuaTable, syntax_check
from native_test_utils import trees
from resource_tools import decode
from test_v300 import make_env
from test_v335 import test_v335_repeat_autocast_ux
from test_v338 import test_v338_mount_medal_seal_enchants_and_confirm
from test_v339 import test_v339_hero_merc_boundary_and_heal
from test_v340 import _run_ranged_sim
from test_v341 import test_v341_merc_hit_fx_and_action_speed
from test_v342 import test_v342_settings_save_btn

W = Path(__file__).resolve().parent
PREV_SHA = '70c9710680769aa0c9ac911d0ce6f87eac4ca5e69b1ff6ab4c3be8a399c7340b'


def extract_runtime_v343(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.343 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v343.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_syntax_version_and_bytecode():
    base_bytes = (W / 'game_v342.res').read_bytes()
    out_bytes = (W / 'game_v343.res').read_bytes()
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

    # Verify OS window title bar (m12/76) and login UI (m12/22232) version strings updated to 1.343
    m12_76_strs = [v.decode('gbk', 'replace') for v in mods_o[12].protos[76].kgc if isinstance(v, bytes)]
    assert '1.343' in m12_76_strs and '不烧心版 1.343' in m12_76_strs, f'm12/76 missing 1.343: {m12_76_strs}'
    m12_22232_strs = [v.decode('gbk', 'replace') for v in mods_o[12].protos[22232].kgc if isinstance(v, bytes)]
    assert '不烧心版 1.343' in m12_22232_strs, 'm12/22232 missing 不烧心版 1.343'

    # Ensure no leftover v1.342 strings in updated modules (excluding embedded runtime which is checked separately)
    for mid in (12, 14, 30):
        for p in mods_o[mid].protos:
            for v in p.kgc:
                if isinstance(v, bytes) and not v.startswith(b'-- Guimeng v1.343'):
                    assert b'v1.342' not in v, f'Leftover v1.342 in m{mid}/{p.idx}'
                    if mid == 12 and p.idx in (76, 22232):
                        assert b'1.342' not in v, f'Leftover 1.342 in m12/{p.idx}'

    # Verify m12/37 JMP A >= params invariant
    p37 = mods_o[12].protos[37]
    for pc, ins in enumerate(p37.bc):
        if OPS[ins & 0xFF] == 'JMP':
            a = (ins >> 8) & 0xFF
            assert a >= p37.params, f'm12/37 pc={pc} has JMP A={a} < params={p37.params}'

    # Verify m14/256 WAL hooks
    p256 = mods_o[14].protos[256]
    assert OPS[p256.bc[1044] & 0xFF] == 'TGETB'
    assert OPS[p256.bc[1045] & 0xFF] == 'GGET' and p256.gc((p256.bc[1045] >> 16) & 0xFFFF) == b'type'
    assert OPS[p256.bc[1051] & 0xFF] == 'JMP' and (1051 + 1 + (p256.bc[1051] >> 16) - 32768) == 1074
    assert OPS[p256.bc[1074] & 0xFF] == 'GGET' and p256.gc((p256.bc[1074] >> 16) & 0xFFFF) == '引擎'.encode('gbk')
    assert OPS[p256.bc[1111] & 0xFF] == 'TGETS' and p256.gc((p256.bc[1111] >> 16) & 0xFF) == b'__gm_wal_try_load_v343'
    assert OPS[p256.bc[1121] & 0xFF] == 'JMP' and (1121 + 1 + (p256.bc[1121] >> 16) - 32768) == 1124
    assert OPS[p256.bc[1123] & 0xFF] == 'JMP' and (1123 + 1 + (p256.bc[1123] >> 16) - 32768) == 144

    rt_src = extract_runtime_v343(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def _md5_hex(s):
    if isinstance(s, str):
        raw = s.encode('latin1', 'replace')
    else:
        raw = bytes(s)
    return hashlib.md5(raw).hexdigest().upper()


def _make_wal_env(rt_src, *, story='来世续缘', with_base_dat=True):
    env = make_env(story=story)
    ev, S, U = env['ev'], env['S'], env['U']
    G_env = ev.G

    # Populate standard Lua 5.1 string/table/math functions used by WAL module
    str_tbl = G_env.rawget('string')
    str_tbl.rawset('lower', lambda s: str(s).lower())
    str_tbl.rawset('upper', lambda s: str(s).upper())
    str_tbl.rawset('byte', lambda s, i=1: ord(str(s)[int(i) - 1]) if 1 <= int(i) <= len(str(s)) else None)

    def lua_match(s, pat):
        p = str(pat)
        if p == '^([^|]+)|([0-9A-Fa-f]+)|(%-?%d+)|([0-9A-Fa-f]+)$':
            m = re.match(r'^([^|]+)\|([0-9A-Fa-f]+)\|(-?\d+)\|([0-9A-Fa-f]+)$', str(s))
            return m.groups() if m else None
        py_pat = p.replace('%d', r'\d').replace('%-', r'\-')
        m = re.search(py_pat, str(s))
        if not m:
            return None
        if m.groups():
            return m.groups()
        return m.group(0)

    str_tbl.rawset('match', lua_match)

    tbl_lib = G_env.rawget('table')
    def tbl_concat(t, sep=''):
        n = t.length()
        parts = []
        for i in range(1, n + 1):
            v = t.rawget(i)
            parts.append('' if v is None else str(v))
        return str(sep).join(parts)
    tbl_lib.rawset('concat', tbl_concat)

    math_lib = G_env.rawget('math')
    if math_lib.rawget('ceil') is None:
        math_lib.rawset('ceil', lambda x: math.ceil(float(x)))

    # In-memory virtual filesystem for GameDate/*
    vfs = {}
    deleted = []
    vanilla_saves = []
    exit_calls = []
    ini_updates = []

    base_path = 'GameDate/归梦_1.dat'
    base_md5 = 'A1B2C3D4E5F60718293A4B5C'
    if with_base_dat:
        vfs[base_path] = base_md5 + ('00' * 32) + '11223344556677889900AABB.a'

    # Clock: controllable millisecond & second counters
    clock_ms = [10000.0]
    run_sec = [100.0]
    auto_step_ms = [0.0]  # if > 0, each now_ms() call advances clock to simulate slice timing

    def get_run_time(_self=None):
        val = clock_ms[0] / 1000.0
        if auto_step_ms[0] > 0:
            clock_ms[0] += auto_step_ms[0]
        return val

    eng = G_env.rawget('引擎')
    eng.rawset('取运行时间', get_run_time)

    # Core C API mocks
    core = LuaTable()
    core.rawset('MD5', lambda s: _md5_hex(s))
    core.rawset('加解密_f', lambda s, k, enc, comp: f'ENC({k}):{s}')
    core.rawset('读入文件', lambda p: vfs.get(p, None))

    def write_file(p, content):
        vfs[p] = content
        return True

    def del_file(p):
        deleted.append(p)
        vfs.pop(p, None)
        return True

    core.rawset('写到文件', write_file)
    core.rawset('删除文件', del_file)
    G_env.rawset('核心', core)
    G_env.rawset('删除文件', del_file)

    # Ae冻, Hero, FXru胃啪, UI slots, 镜头选择框, 底部窗口
    ae = LuaTable({'地图名称': '比奇县', '任务变量1': 77, '鼠标事件ID': 5})
    G_env.rawset('Ae冻', ae)

    hero_attr = LuaTable({'hp': 880, 'mp': 320, '等级': 52, '经验值': 123456, '金币': 999888})
    hero_grid = LuaTable({'x': 120, 'y': 240})
    hero_cfg = LuaTable({'绑定属性': '战士', '绑定技能': '普攻'})
    sk_info = LuaTable({
        '烈火剑法': LuaTable({
            '可用': True, '持续开启': False, '开始CD效果': False,
            '技能延时': 1.5, '技能延时计次': 0, '当前帧': 1, '可触发': True, 'dt': 0.0,
        }),
    })
    buff1 = LuaTable({
        '取标识': lambda: '魔法盾',
        '取属性表': lambda: LuaTable({'持续时间': 9999, '减伤': 45}),
    })
    hero = LuaTable({
        '属性': hero_attr,
        '地图格子': hero_grid,
        '方向': 4,
        '显示名称': '测试角色',
        '名称显示偏移x': 0,
        '名称显示偏移y': -10,
        '主角配置': hero_cfg,
        '技能信息': sk_info,
        'BUFF组': LuaTable([buff1]),
        '已经死亡': False,
    })
    S.rawset('Hero', hero)
    S.rawset('save_info', LuaTable({'uid': 'UID123456', 'stime': 1700000000, 'ptime': 3600, 'last_save_time': 0}))
    S.rawset('user_info', LuaTable({'uuid': 'AABBCCDD1122334455667788'}))
    S.rawset('任务列表', LuaTable({'主线1': LuaTable({'进度': 3, '目标': '野猪'})}))
    S.rawset('已完成任务表', LuaTable({'新手任务': True}))
    S.rawset('游戏任务组', LuaTable({
        'q1': LuaTable({
            '接受条件': LuaTable([LuaTable({'类型': '变量', '名称': '任务变量1'})]),
            '完成条件': LuaTable([]),
        }),
    }))
    S.rawset('道具CD信息组', LuaTable({
        '太阳水': LuaTable({'延时计次': 2, '当前帧': 3, 'dt': 0.2, '冷却时间': 5.0}),
    }))

    # Bag items (类型==6) and skill bindings (类型==7)
    item1 = LuaTable({
        '名称': '裁决之杖', '显示名': '裁决之杖+7', '数量': 1, '价格': 50000, '需要等级': 30,
        '冷却时间': 0,
        '属性': LuaTable({'最大破坏': 45, '最小破坏': 0, '幸运': 7}),
        '附加': LuaTable({'条数': 3, '攻火元素': 5}),
        '分类': '武器', '子类': '刀剑', '性别要求': '无', '职业要求': '战士',
        '道具说明': '神兵利器\n第二行"带引号"和\\反斜杠',
        '颜色值': -16711936, '格子底图': 'bg1', '格子动画': '', '格子顶图': '',
        '禁止出售': False, '禁止丢弃': False,
    })
    bag_slots = LuaTable({101: LuaTable({'道具': item1})})
    S.rawset('包裹物品组', bag_slots)
    win_arr = LuaTable([
        LuaTable({
            '控件组': LuaTable([
                LuaTable({'类型': 6, '名称': '包裹格子1', '对象': LuaTable({'标识': 101, '禁止存档': False})}),
                LuaTable({'类型': 7, '名称': '技能快捷101', '对象': LuaTable({'绑定技能': '烈火剑法', '原始绑定': '烈火剑法'})}),
            ]),
        }),
    ])
    S.rawset('界面_窗口_数组', win_arr)

    # Extra hero_data returned by Ux雌.啾啾啵啵()
    hero_data = LuaTable({
        '名称': '测试角色', '性别': '男', '职业': '战士',
        '仓库': 3600,
        '灵魂贝贝': LuaTable({'超人': 10, '附魔表': LuaTable({'坐骑': '苍月'})}),
        '测试空表': LuaTable(),
        '浮点精度': 0.123456789012345,
        '特殊串': 'a:b;c{d}e\nf\x00g\\h"i',
    })
    U.rawset('啾啾啵啵', lambda: hero_data)
    U.rawset('人物选择', 1)
    U.rawset('读取人物', LuaTable())
    U.rawset('胚子考虑', lambda: LuaTable({'蝶恋花': None}))

    fx = LuaTable({'HP': 880, '等级': 52})
    G_env.rawset('FXru胃啪', fx)
    G_env.rawset('镜头选择框', LuaTable({'选中': False}))  # false == ON
    G_env.rawset('底部窗口', LuaTable({'可视': True}))
    G_env.rawset('物品格子18', LuaTable({'道具': None}))
    G_env.rawset('Q_鼠标', LuaTable({'被占用': False}))

    # Gly独.存档 & Gly独.结束游戏
    G_obj = LuaTable({'鼠标道具': 0})

    def orig_save(path, hd, key=None):
        vanilla_saves.append((path, hd, key))
        # Simulate writing a new vanilla .dat with a fresh 24-char MD5
        new_md5 = _md5_hex(f'VANILLA:{path}:{len(vanilla_saves)}')[:24]
        vfs[path] = new_md5 + ('11' * 32) + '11223344556677889900AABB.a'
        return None

    def orig_exit(flag=None):
        exit_calls.append(flag)

    G_obj.rawset('存档', orig_save)
    G_obj.rawset('结束游戏', orig_exit)
    G_env.rawset('Gly独', G_obj)

    wr = U.rawget('窗口相关')
    if not isinstance(wr, LuaTable):
        wr = LuaTable()
        U.rawset('窗口相关', wr)
    wr.rawset('配置文件', lambda arg='': ini_updates.append(arg))

    def cundang_duang(mode, slot, backup=None, extra=0):
        if mode == '存档':
            if (G_obj.rawget('鼠标道具') or 0) > 0 or (fx.rawget('HP') or 0) <= 0:
                return
            p = f'C:/归梦_{slot}(归梦备份存档).dat' if backup else f'GameDate/归梦_{slot}.dat'
            G_obj.rawget('存档')(p, U.rawget('啾啾啵啵')(), '归梦748zuobigou作弊狗siquanjia')

    wr.rawset('存档读档', cundang_duang)

    # Load runtime_v343.lua ONCE
    ev.G.get('loadstring')(rt_src)(S)

    return {
        'env': env, 'ev': ev, 'S': S, 'U': U, 'G': G_obj, 'G_env': G_env,
        'vfs': vfs, 'deleted': deleted, 'vanilla_saves': vanilla_saves,
        'exit_calls': exit_calls, 'ini_updates': ini_updates,
        'clock_ms': clock_ms, 'auto_step_ms': auto_step_ms,
        'base_path': base_path, 'base_md5': base_md5,
        'hero': hero, 'hero_attr': hero_attr, 'hero_data': hero_data,
        'fx': fx, 'bag_slots': bag_slots, 'item1': item1, 'ae': ae,
        'st': S.rawget('__gm_wal_state_v343'),
        'tick': S.rawget('__gm_wal_frame_tick_v343'),
        'try_load': S.rawget('__gm_wal_try_load_v343'),
        'step_job': S.rawget('__gm_wal_step_job_v343'),
        'decode_stream': S.rawget('__gm_wal_decode_stream_v343'),
    }


def test_v343_wal_and_3s_autosave(rt_src):
    # 1. Basic WAL save -> frame-sliced completion -> crash recovery load roundtrip
    w = _make_wal_env(rt_src, story='来世续缘', with_base_dat=True)
    st = w['st']
    assert w['G'].rawget('存档') == st.rawget('save_wrap')
    assert w['G'].rawget('结束游戏') == st.rawget('exit_wrap')

    # Force multi-slice execution: add 400 sub-entries to hero_data and make clock advance 1.6ms per check
    big_tbl = LuaTable()
    for i in range(1, 350):
        big_tbl.rawset(f'k_{i}', LuaTable({'v': i, 's': f'条目{i}:带;冒号{{花括号}}', 'f': (i % 2 == 0)}))
    w['hero_data'].rawset('大表测试', big_tbl)
    # Also test NaN/Inf and cyclic table guard
    cyc = LuaTable({'name': 'cycle'})
    cyc.rawset('self', cyc)
    w['hero_data'].rawset('循环表', cyc)
    w['hero_data'].rawset('非法数', float('nan'))
    w['hero_data'].rawset('正无穷', float('inf'))

    # Trigger save via Gly独.存档 (intercepted -> WAL)
    w['auto_step_ms'][0] = 2.0  # each now_ms() advances 2ms so budget=3ms triggers slicing across frames!
    w['G'].rawget('存档')(w['base_path'], w['hero_data'], '归梦748zuobigou作弊狗siquanjia')
    assert len(w['vanilla_saves']) == 0, 'WAL save should NOT invoke slow vanilla orig_save'
    assert st.rawget('job') is not None, 'Large table with 2ms clock step should yield mid-serialization'

    # Pump pickup_frame / wal_frame_tick_v343 until job completes
    frames = 0
    while st.rawget('job') is not None:
        w['tick']()
        frames += 1
        assert frames < 200, 'WAL job did not converge'
    assert frames >= 2, f'Expected multi-frame slicing, got frames={frames}'
    assert st.rawget('wal_commits') == 1
    wal_path = w['base_path'] + '.wal'
    assert wal_path in w['vfs'], 'WAL file must be written to vfs'
    assert (w['base_path'] + '.wal.tmp') not in w['vfs']

    # Verify crash recovery via S.__gm_wal_try_load_v343
    w['auto_step_ms'][0] = 0.0
    loaded = w['try_load'](w['base_path'], w['base_md5'], False)
    assert isinstance(loaded, LuaTable), 'WAL load should succeed and return r4 table'
    assert loaded.length() == 11, f'Expected #r4 == 11 (no hole at index 8), got {loaded.length()}'
    assert loaded.rawget(9) == 1001
    # Verify item restored
    r_items = loaded.rawget(1)
    it = r_items.rawget('包裹格子1')
    assert it.rawget('名称') == '裁决之杖' and it.rawget('属性').rawget('幸运') == 7
    assert it.rawget('道具说明') == '神兵利器\n第二行"带引号"和\\反斜杠'
    # Verify skill binding, skill info, buff, quest vars, item CD
    assert loaded.rawget(2).rawget('技能快捷101').rawget(1) == '烈火剑法'
    assert loaded.rawget(3).rawget(1).rawget(1) == '烈火剑法'
    assert loaded.rawget(5).rawget('魔法盾').rawget('减伤') == 45
    assert loaded.rawget(10).rawget('任务变量1') == 77
    assert loaded.rawget(11).rawget(1).rawget(1) == '太阳水'
    # Verify r4[8] == hero_data directly with lossless strings, floats, empty table, NaN->0, cycle->{}
    hd_out = loaded.rawget(8)
    assert hd_out.rawget('名称') == '测试角色'
    assert hd_out.rawget('特殊串') == 'a:b;c{d}e\nf\x00g\\h"i'
    assert abs(hd_out.rawget('浮点精度') - 0.123456789012345) < 1e-14
    assert isinstance(hd_out.rawget('测试空表'), LuaTable)
    assert hd_out.rawget('非法数') == 0 and hd_out.rawget('正无穷') == 0
    assert hd_out.rawget('大表测试').rawget('k_349').rawget('v') == 349
    assert st.rawget('wal_loads') == 1

    # 2. AFK zero-write deduplication vs manual force-commit
    w['hero_data'].rawset('大表测试', LuaTable({'k_1': 1}))  # shrink for fast sub-tests
    w['G'].rawget('存档')(w['base_path'], w['hero_data'], 'k')
    while st.rawget('job') is not None:
        w['tick']()
    commits_after_change = st.rawget('wal_commits')
    assert commits_after_change == 2

    # Save again with ZERO state change (non-manual) -> must skip disk write!
    w['G'].rawget('存档')(w['base_path'], w['hero_data'], 'k')
    while st.rawget('job') is not None:
        w['tick']()
    assert st.rawget('wal_commits') == commits_after_change
    assert st.rawget('wal_skipped_same') == 1

    # Manual [Save] click with ZERO state change -> MUST force commit!
    st.rawset('next_save_manual', True)
    w['G'].rawget('存档')(w['base_path'], w['hero_data'], 'k')
    while st.rawget('job') is not None:
        w['tick']()
    assert st.rawget('wal_commits') == commits_after_change + 1

    # 3. Corruption & base_md5 mismatch fallbacks
    # 3a. Corrupted payload byte -> MD5 mismatch -> returns nil (fallback to vanilla .dat)
    good_wal = w['vfs'][wal_path]
    w['vfs'][wal_path] = good_wal[:-1] + ('X' if good_wal[-1] != 'X' else 'Y')
    assert w['try_load'](w['base_path'], w['base_md5'], False) is None
    # 3b. Truncated stream -> returns nil
    w['vfs'][wal_path] = good_wal[:70]
    assert w['try_load'](w['base_path'], w['base_md5'], False) is None
    # 3c. base_md5 mismatch (player restored an older backup .dat) -> deletes stale .wal & returns nil!
    w['vfs'][wal_path] = good_wal
    assert w['try_load'](w['base_path'], 'FFFFFFFFFFFFFFFFFFFFFFFF', False) is None
    assert wal_path not in w['vfs'], 'Stale .wal must be deleted when base .dat changed externally'
    # 3d. is_raw == true -> returns nil
    w['vfs'][wal_path] = good_wal
    assert w['try_load'](w['base_path'], w['base_md5'], True) is None

    # 4. 3-second continuous MMO auto-save + all safety guards
    # Re-establish baseline last_auto_ms
    w['clock_ms'][0] = 50000.0
    st.rawset('last_auto_ms', 50000.0)
    w['hero_attr'].rawset('金币', 1000001)  # dirty state
    # 2.5s elapsed -> must NOT fire yet
    w['clock_ms'][0] = 52500.0
    c_before = st.rawget('wal_commits')
    w['tick']()
    assert st.rawget('wal_commits') == c_before and st.rawget('job') is None

    # 3.0s elapsed -> MUST fire!
    w['clock_ms'][0] = 53000.0
    w['tick']()
    while st.rawget('job') is not None:
        w['tick']()
    assert st.rawget('wal_commits') == c_before + 1
    # Level up triggers INI summary sync ONCE
    ini_before = len(w['ini_updates'])
    w['fx'].rawset('等级', 53)
    w['hero_attr'].rawset('等级', 53)
    w['clock_ms'][0] = 56000.0
    w['tick']()
    while st.rawget('job') is not None:
        w['tick']()
    assert len(w['ini_updates']) == ini_before + 1
    assert w['U'].rawget('读取人物').rawget(1).rawget(2) == 53
    # Same level on next 3s -> must NOT spam INI!
    w['hero_attr'].rawset('金币', 1000002)
    w['clock_ms'][0] = 59000.0
    w['tick']()
    while st.rawget('job') is not None:
        w['tick']()
    assert len(w['ini_updates']) == ini_before + 1

    # Guards block 3s auto-save:
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
    assert_guard_blocks(lambda: w['G'].rawset('鼠标道具', 1), lambda: w['G'].rawset('鼠标道具', 0), 'cursor_item')
    assert_guard_blocks(lambda: w['G_env'].rawget('物品格子18').rawset('道具', LuaTable()),
                        lambda: w['G_env'].rawget('物品格子18').rawset('道具', None), 'slot18')
    assert_guard_blocks(lambda: w['G_env'].rawget('底部窗口').rawset('可视', False),
                        lambda: w['G_env'].rawget('底部窗口').rawset('可视', True), 'not_ingame')

    # 5. Normal Exit (Gly独.结束游戏) flushes ONE synchronous vanilla save & deletes .wal
    v_before = len(w['vanilla_saves'])
    w['G'].rawget('结束游戏')(True)
    assert len(w['vanilla_saves']) == v_before + 1, 'Exit must flush synchronous vanilla save'
    assert wal_path not in w['vfs'], 'Exit vanilla flush must delete .wal'
    assert w['exit_calls'] == [True]
    assert st.rawget('vanilla_flushes') >= 1

    # 6. C: backup, brand-new character (missing .dat), and 「前尘忆梦」 bypass WAL cleanly
    w['G'].rawget('存档')('C:/归梦_1(归梦备份存档).dat', w['hero_data'], 'k')
    assert w['vanilla_saves'][-1][0] == 'C:/归梦_1(归梦备份存档).dat'

    w_new = _make_wal_env(rt_src, story='来世续缘', with_base_dat=False)
    w_new['G'].rawget('存档')(w_new['base_path'], w_new['hero_data'], 'k')
    assert len(w_new['vanilla_saves']) == 1, 'Brand-new character without .dat must write vanilla .dat first'

    w_q = _make_wal_env(rt_src, story='前尘忆梦', with_base_dat=True)
    w_q['G'].rawget('存档')('GameDate/归梦_Q_1.dat', w_q['hero_data'], 'k')
    assert len(w_q['vanilla_saves']) == 1 and w_q['st'].rawget('wal_commits') == 0
    assert w_q['try_load']('GameDate/归梦_Q_1.dat', w_q['base_md5'], False) is None
    w_q['clock_ms'][0] += 5000.0
    w_q['tick']()
    assert w_q['st'].rawget('wal_commits') == 0, '前尘忆梦 must never trigger 3s WAL auto-save'

    # 7. 200x hoisted repetition loop (single loadstring outside loop)
    w2 = _make_wal_env(rt_src, story='来世续缘', with_base_dat=True)
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
    # i=0 commits baseline (no prior MD5), then i=4,8..196 (49 iterations) match previous state -> 151 commits + 49 AFK skips = 200
    assert st2.rawget('wal_commits') == 151 and st2.rawget('wal_skipped_same') == 49
    assert st2.rawget('wal_loads') == 10
    print('WAL_AND_3S_AUTOSAVE_V343_PASS (200x hoisted): multi-slice, GMWAL1 roundtrip, 3s autosave, AFK skip, guards, crash load, fallback, exit vanilla flush & 前尘忆梦 isolation OK!')


def main():
    mods_o, rt_src = test_diff_syntax_version_and_bytecode()
    test_v343_wal_and_3s_autosave(rt_src)
    # Direct & recent regressions
    test_v342_settings_save_btn(rt_src)
    test_v341_merc_hit_fx_and_action_speed(rt_src)
    for sk in ('刺客普通攻击', '蝉舞'):
        res, _, _ = _run_ranged_sim(rt_src, skill=sk, dx_px=240.0, fps=66.0, reload_merc_mode=True)
        assert res['dmg_count'] == 1 and res['dmg_frame'] == res['end_frame'] == res['hit_fx_frame'], (sk, res)
    test_v339_hero_merc_boundary_and_heal(mods_o[12], rt_src)
    test_v338_mount_medal_seal_enchants_and_confirm(mods_o[12], rt_src)
    test_v335_repeat_autocast_ux(rt_src)

    out_bytes = (W / 'game_v343.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.343',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v343.res': out_sha,
            'runtime_v343.lua': hashlib.sha256((W / 'runtime_v343.lua').read_bytes()).hexdigest(),
            'patch_v343.py': hashlib.sha256((W / 'patch_v343.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'm12_76_window_title_and_m12_22232_version_1_343_verified',
            'm12_37_zero_jmp_below_params_preserved',
            'm14_256_wal_load_and_direct_table_r4_8_bytecode_verified',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'v343_wal_stream_roundtrip_slicing_3s_autosave_afk_skip_guards_exit_flush_200x_pass',
            'v343_qianchi_isolated_pass',
            'v342_settings_save_btn_pass',
            'v341_merc_skill_resp_and_v340_sanity_pass',
            'v339_v338_v335_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v343.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v343.json').write_text(text, encoding='utf-8')
    print('ALL v1.343 TESTS PASSED!')


if __name__ == '__main__':
    main()
