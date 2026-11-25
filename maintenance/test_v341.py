"""Targeted verification suite for v1.341:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees() + version string checks
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v341.lua
3. m12/37 (qs_item_box.Main) still has ZERO JMP instructions with A < params
4. Mercenary ranged skill responsiveness fixes (v1.341, 来世续缘 only):
   - Cause 1 (Magic_04.empak <技能>_命中 hit-effect startup lag via 特效类.初始化):
     * Strips leading invisible 4x4 / placeholder blank frames (图片大小<=256 or 帧宽/高<=4)
       into a fresh copy of 动画配置.key without mutating shared 动作组 tables, updates 总帧数,
       resets 延迟时间=0, tightens 播放速度=0.65, and primes frame 1 via 置当前帧.
     * Edge cases: all-blank keeps >=1 frame; non-Magic_04, non-hit-FX, and 「前尘忆梦」 untouched.
   - Cause 2 (Ranged skill cast-action 跳斩/跳刺 speed scaling via 类_事件.播放指定动作):
     * Scales 跳斩/跳刺 with 攻击速度 matching 横切 (~24f at atk_spd>=14 instead of fixed 0.5 / ~41f),
       never slower than 0.5; leaves 横切, melee two-handed assassin (刺客双手攻击), Hero/enemies,
       and 「前尘忆梦」 100% untouched.
   - Cause 3 (Target-switch 蝉舞 launch unblock + arrival epsilon alignment):
     * Clears stale actor.播放动作=true when 蝉舞 prepares on a live ranged merc (unblocking m22/4
       PC 485), while keeping non-蝉舞 and 「前尘忆梦」 untouched.
     * state.命中动画延迟 = (延迟dt or 0) - 1e-9 fires synchronously on exact arrival frame.
   - pickup_frame auto-rewraps both 类_事件.播放指定动作 and 特效类.初始化 after simulated reload.
   - 200x continuous repetition across all 6 ranged skills (刺客普通攻击/蝉舞/盛开/白莲/红莲/月桂)
     combining projectile arrival, hit-FX priming, cast-action scaling, and v1.340 timing checks.
5. Core regressions: v1.340 ranged timing, v1.339 hero/merc boundary & heal, v1.338 enchants, v1.335 repeat autocast.
"""
import hashlib
import json
import math
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
from test_v340 import _run_ranged_sim, test_v340_merc_ranged_hit_timing

W = Path(__file__).resolve().parent
BASE_SHA = '772c68e5d127c0cbfa910e937623d68d8bdf7cfd6a6bed950b1fdf9b76f7ade4'
HIT_FX_NAMES = ('盛开_命中', '白莲_命中', '红莲_命中', '月桂_命中', '蝉舞_命中')


def extract_runtime_v341(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.341 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v341.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_syntax_and_m12_37():
    base_bytes = (W / 'game_v340.res').read_bytes()
    out_bytes = (W / 'game_v341.res').read_bytes()
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

    rt_src = extract_runtime_v341(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def _setup_v341_env(rt_src, *, story='来世续缘', merc_binding='刺客普通攻击', atk_spd=14):
    merc_src = (W / 'merc_mode_v288.lua').read_text(encoding='utf-8')
    env = make_env(story=story)
    ev, S = env['ev'], env['S']
    ss = S.rawget('script_setting')
    ev.G.rawset('dt', 1.0 / 66.0)
    ev.G.rawget('math').rawset('pi', math.pi)
    ev.G.rawget('math').rawset('sqrt', math.sqrt)
    fireball = LuaTable({'子弹速度': 450 if story == '来世续缘' else 350})
    ev.G.rawset('Sys', LuaTable({
        'get': lambda kind, key=None: fireball if kind == 'skill' and '火球术' in str(key) else None,
        'add': lambda *a: None,
    }))

    action_calls = []

    def orig_play_action(self_actor, action, mode, speed, cb=None):
        action_calls.append({
            'id': self_actor.rawget('id'),
            'action': action,
            'mode': mode,
            'speed': speed,
        })
        self_actor.rawset('播放动作', True)
        self_actor.rawset('指定动作', action)
        self_actor.rawset('播放速度', speed)
        return True

    def orig_fx_init(self_fx, path, kind, x, y, w, h, count, target, t, rad, act_tag, direction, speed, pos, delay):
        self_fx.rawset('特效文件', path)
        self_fx.rawset('动作标识', act_tag)
        self_fx.rawset('延迟时间', (delay or 0) / 1000.0)
        self_fx.rawset('播放速度', speed if speed is not None else 1.0)
        # Simulate authentic m42/0: 动画配置.key directly references shared 动作组[act_tag].帧数组[dir]
        shared_frames = self_fx.rawget('_shared_frames')
        self_fx.rawset('动画配置', LuaTable({'state': 1, 'fps': 80, 'key': shared_frames}))
        self_fx.rawset('总帧数', shared_frames.length())
        return 'init-ok'

    ev.G.rawset('类_事件', LuaTable({'播放指定动作': orig_play_action}))
    ev.G.rawset('特效类', LuaTable({'初始化': orig_fx_init}))

    w_item = LuaTable({
        '名称': '玄月' if merc_binding == '刺客普通攻击' else '双手刀',
        '分类': '装备', '子类': '武器',
        '地面图标': LuaTable({'宽度': 32, '高度': 32}),
        '附加': LuaTable({'绑定技能': merc_binding}),
    })
    S.rawget('包裹物品组').rawset(397, LuaTable({'道具': w_item, '拿起': False}))

    merc = LuaTable({
        'id': 501, '绑定技能': merc_binding, '方向': 3, '锚点x': 0.0, '锚点y': 0.0,
        '播放动作': False,
        '地图格子': LuaTable({'x': 10, 'y': 10}),
        '地图坐标': LuaTable({'x': 0.0, 'y': 320.0}),
        '属性': LuaTable({'hp': 1000, '中心Y偏移': 30.0, '模型大小': 1.0, '攻击速度': atk_spd}),
    })
    env['U'].rawset('佣兵对象', merc)

    ev.G.get('loadstring')(merc_src)()(S, ss)
    ev.G.get('loadstring')(rt_src)(S)
    return env, merc, action_calls, orig_play_action, orig_fx_init


def _make_fx_obj(path, act_tag, frame_specs):
    """Build a realistic 特效类 instance with shared 动作组 frame array & PAK信息组."""
    pak_info = LuaTable()
    shared_key = LuaTable()
    for idx, (fid, fw, fh, sz) in enumerate(frame_specs, start=1):
        shared_key.rawset(idx, fid)
        pak_info.rawset(fid, LuaTable({'帧宽': fw, '帧高': fh, '图片大小': sz}))

    primed = []
    anim = LuaTable({
        '动画资源': LuaTable({'PAK信息组': pak_info}),
        '当前帧': 1,
        '置当前帧': lambda self_a, fid: (primed.append(fid), self_a.rawset('当前帧', fid)),
    })
    fx = LuaTable({
        '特效动画': anim,
        '_shared_frames': shared_key,
    })
    return fx, shared_key, anim, primed


def test_v341_merc_hit_fx_and_action_speed(rt_src):
    # --- 1. Magic_04.empak <技能>_命中 hit-FX blank stripping, delay reset, speed tighten & priming ---
    env, merc, action_calls, _, _ = _setup_v341_env(rt_src, story='来世续缘', atk_spd=14)
    ev = env['ev']
    fx_init = ev.G.rawget('特效类').rawget('初始化')

    # 1a. All 5 <技能>_命中 skills with realistic unloaded (fw=0,fh=0,sz=144) & loaded (fw=4,fh=4,sz=512) leading blanks
    for idx, act_tag in enumerate(HIT_FX_NAMES):
        specs = (
            [(65, 0, 0, 144), (66, 0, 0, 144), (67, 0, 0, 12800), (68, 0, 0, 24000), (69, 0, 0, 18000)]
            if idx % 2 == 0 else
            [(145, 4, 4, 512), (146, 4, 4, 144), (147, 96, 120, 31136), (148, 128, 140, 44816)]
        )
        delay_ms = -50 if act_tag == '蝉舞_命中' else 80
        fx, shared_key, anim, primed = _make_fx_obj(f'Dat/动画/GM_归梦/Magic/Magic_04.empak,{act_tag}', act_tag, specs)
        ret = fx_init(fx, f'Dat/动画/GM_归梦/Magic/Magic_04.empak,{act_tag}', '跟随目标', 100, 100, 1, 1, 1, None, 0, 0, act_tag, 1, 1.0, 0, delay_ms)
        assert ret == 'init-ok' or (isinstance(ret, tuple) and ret[0] == 'init-ok'), repr(ret)
        # Shared 动作组 table must NEVER be mutated!
        assert shared_key.length() == len(specs), f'Shared frame array was mutated for {act_tag}'
        assert shared_key.rawget(1) == specs[0][0]
        # Instance cfg.key is trimmed to start at the first visible frame!
        cfg_key = fx.rawget('动画配置').rawget('key')
        expected_ids = [s[0] for s in specs[2:]]
        assert cfg_key.length() == len(expected_ids) == fx.rawget('总帧数'), (act_tag, cfg_key.length(), fx.rawget('总帧数'))
        assert [cfg_key.rawget(i) for i in range(1, cfg_key.length() + 1)] == expected_ids
        assert fx.rawget('延迟时间') == 0
        assert abs(fx.rawget('播放速度') - 0.65) < 1e-9
        assert primed == [expected_ids[0]] and anim.rawget('当前帧') == expected_ids[0], (act_tag, primed)

    # 1b. Already-faster 播放速度 (0.5 < 0.65) stays 0.5
    fx_fast, _, _, primed_fast = _make_fx_obj('Magic_04.empak,盛开_命中', '盛开_命中', [(65, 0, 0, 144), (67, 0, 0, 9999)])
    fx_init(fx_fast, 'Magic_04.empak,盛开_命中', '跟随目标', 0, 0, 1, 1, 1, None, 0, 0, '盛开_命中', 1, 0.5, 0, 0)
    assert abs(fx_fast.rawget('播放速度') - 0.5) < 1e-9 and primed_fast == [67]

    # 1c. All-blank safety: keeps at least 1 frame (never empty!)
    fx_all_blank, _, _, primed_ab = _make_fx_obj('Magic_04.empak,白莲_命中', '白莲_命中', [(10, 4, 4, 144), (11, 4, 4, 144)])
    fx_init(fx_all_blank, 'Magic_04.empak,白莲_命中', '跟随目标', 0, 0, 1, 1, 1, None, 0, 0, '白莲_命中', 1, 1.0, 0, 0)
    assert fx_all_blank.rawget('总帧数') == 1 and fx_all_blank.rawget('动画配置').rawget('key').rawget(1) == 11
    assert primed_ab == [11]

    # 1d. Non-Magic_04 file & non-hit-FX tag are 100% untouched
    fx_other_pak, _, _, primed_op = _make_fx_obj('Magic_01.empak,盛开_命中', '盛开_命中', [(1, 0, 0, 144), (2, 0, 0, 9999)])
    fx_init(fx_other_pak, 'Magic_01.empak,盛开_命中', '跟随目标', 0, 0, 1, 1, 1, None, 0, 0, '盛开_命中', 1, 1.0, 0, 100)
    assert fx_other_pak.rawget('总帧数') == 2 and abs(fx_other_pak.rawget('延迟时间') - 0.1) < 1e-9
    assert abs(fx_other_pak.rawget('播放速度') - 1.0) < 1e-9 and primed_op == []

    fx_other_tag, _, _, primed_ot = _make_fx_obj('Magic_04.empak,盛开_起手', '盛开_起手', [(1, 0, 0, 144), (2, 0, 0, 9999)])
    fx_init(fx_other_tag, 'Magic_04.empak,盛开_起手', '跟随目标', 0, 0, 1, 1, 1, None, 0, 0, '盛开_起手', 1, 1.0, 0, 100)
    assert fx_other_tag.rawget('总帧数') == 2 and abs(fx_other_tag.rawget('播放速度') - 1.0) < 1e-9 and primed_ot == []

    # --- 2. Ranged merc skill cast-action speed scaling (跳斩 / 跳刺) ---
    play_act = ev.G.rawget('类_事件').rawget('播放指定动作')

    for atk_spd, expected_spd in ((10, 0.5), (11, 0.5), (12, 0.6 * 0.72), (13, 0.5 * 0.72), (14, 0.4 * 0.72), (25, 0.4 * 0.72)):
        merc.rawget('属性').rawset('攻击速度', atk_spd)
        for act in ('跳斩', '跳刺'):
            action_calls.clear()
            assert play_act(merc, act, 0, 0.5) is True
            assert len(action_calls) == 1
            assert abs(action_calls[0]['speed'] - expected_spd) < 1e-9, (atk_spd, act, action_calls[0]['speed'], expected_spd)

    # 横切 on ranged merc stays untouched
    merc.rawget('属性').rawset('攻击速度', 18)
    action_calls.clear()
    play_act(merc, '横切', 0, 0.4)
    assert abs(action_calls[0]['speed'] - 0.4) < 1e-9

    # Non-merc actor (Hero / monster) stays untouched
    other_actor = LuaTable({'id': 999, '绑定技能': '刺客普通攻击', '属性': LuaTable({'攻击速度': 20})})
    action_calls.clear()
    play_act(other_actor, '跳斩', 0, 0.5)
    assert abs(action_calls[0]['speed'] - 0.5) < 1e-9

    # Melee two-handed assassin (刺客双手攻击) stays 100% untouched!
    env_m, merc_m, calls_m, _, _ = _setup_v341_env(rt_src, story='来世续缘', merc_binding='刺客双手攻击', atk_spd=20)
    play_act_m = env_m['ev'].G.rawget('类_事件').rawget('播放指定动作')
    for act in ('跳斩', '跳刺'):
        calls_m.clear()
        play_act_m(merc_m, act, 0, 0.5)
        assert abs(calls_m[0]['speed'] - 0.5) < 1e-9, f'Melee assassin {act} must remain untouched!'

    # --- 3. Target-switch 蝉舞 launch unblock (clears stale actor.播放动作=true) ---
    target = LuaTable({
        'id': 1001, '所属阵营': '敌方', '不可选中': False, '是否有效': True, '已经消失': False,
        '方向': 7, '地图格子': LuaTable({'x': 15, 'y': 10}), '地图坐标': LuaTable({'x': 240.0, 'y': 320.0}),
        '属性': LuaTable({'hp': 5000, '中心Y偏移': 35.0, '模型大小': 1.0}),
    })
    prep_fn = ev.G.rawget('__gm_merc_visual_prepare_v255')
    # 蝉舞 clears stale 播放动作=true
    merc.rawset('播放动作', True)
    st_cw = LuaTable({'施法者': merc, '目标': target, '对象': LuaTable({'名称': '蝉舞'}),
                      '起手动画延迟': 0.0, '命中动画延迟': 0.15, '伤害进度': LuaTable({1: 0.30})})
    prep_fn(st_cw, LuaTable({'刷新': lambda: False}))
    assert merc.rawget('播放动作') is False, '蝉舞 prepare must clear stale actor.播放动作=true'
    # Non-蝉舞 (盛开) does NOT clear 播放动作
    merc.rawset('播放动作', True)
    st_sk = LuaTable({'施法者': merc, '目标': target, '对象': LuaTable({'名称': '盛开'}),
                      '起手动画延迟': 0.0, '命中动画延迟': 0.15, '伤害进度': LuaTable({1: 0.30})})
    prep_fn(st_sk, LuaTable({'刷新': lambda: False}))
    assert merc.rawget('播放动作') is True, 'Non-蝉舞 prepare must not clear actor.播放动作'

    # --- 4. pickup_frame auto-rewrap after simulated game_start / save reload ---
    fresh_action_calls = []
    def reloaded_play_action(self_actor, action, mode, speed, cb=None):
        fresh_action_calls.append(speed)
        return True
    def reloaded_fx_init(self_fx, path, kind, x, y, w, h, count, target, t, rad, act_tag, direction, speed, pos, delay):
        self_fx.rawset('特效文件', path)
        self_fx.rawset('动作标识', act_tag)
        self_fx.rawset('延迟时间', (delay or 0) / 1000.0)
        self_fx.rawset('播放速度', speed if speed is not None else 1.0)
        sf = self_fx.rawget('_shared_frames')
        self_fx.rawset('动画配置', LuaTable({'state': 1, 'fps': 80, 'key': sf}))
        self_fx.rawset('总帧数', sf.length())
    ev.G.rawget('类_事件').rawset('播放指定动作', reloaded_play_action)
    ev.G.rawget('特效类').rawset('初始化', reloaded_fx_init)
    ev.G.rawget('__gm_pickup_frame_v299')(env['U'], env['G'])
    # Both hooks must now be re-wrapped!
    ev.G.rawget('类_事件').rawget('播放指定动作')(merc, '跳斩', 0, 0.5)
    assert len(fresh_action_calls) == 1 and abs(fresh_action_calls[0] - 0.288) < 1e-9
    fx_re, _, _, primed_re = _make_fx_obj('Magic_04.empak,月桂_命中', '月桂_命中', [(200, 0, 0, 144), (201, 0, 0, 22000)])
    ev.G.rawget('特效类').rawget('初始化')(fx_re, 'Magic_04.empak,月桂_命中', '跟随目标', 0, 0, 1, 1, 1, None, 0, 0, '月桂_命中', 1, 1.0, 0, 50)
    assert fx_re.rawget('总帧数') == 1 and fx_re.rawget('延迟时间') == 0 and abs(fx_re.rawget('播放速度') - 0.65) < 1e-9 and primed_re == [201]

    # --- 5. 「前尘忆梦」 100% isolated across ALL 3 v1.341 fixes ---
    env_q, merc_q, calls_q, _, _ = _setup_v341_env(rt_src, story='前尘忆梦', atk_spd=20)
    ev_q = env_q['ev']
    # Hit FX untouched
    fx_q, _, _, primed_q = _make_fx_obj('Magic_04.empak,蝉舞_命中', '蝉舞_命中', [(65, 0, 0, 144), (66, 0, 0, 144), (67, 0, 0, 15000)])
    ev_q.G.rawget('特效类').rawget('初始化')(fx_q, 'Magic_04.empak,蝉舞_命中', '跟随目标', 0, 0, 1, 1, 1, None, 0, 0, '蝉舞_命中', 1, 1.0, 0, -50)
    assert fx_q.rawget('总帧数') == 3 and abs(fx_q.rawget('延迟时间') - (-0.05)) < 1e-9
    assert abs(fx_q.rawget('播放速度') - 1.0) < 1e-9 and primed_q == []
    # Action speed untouched
    ev_q.G.rawget('类_事件').rawget('播放指定动作')(merc_q, '跳斩', 0, 0.5)
    assert abs(calls_q[0]['speed'] - 0.5) < 1e-9
    # 蝉舞 prepare does NOT clear 播放动作
    merc_q.rawset('播放动作', True)
    st_q = LuaTable({'施法者': merc_q, '目标': target, '对象': LuaTable({'名称': '蝉舞'}),
                     '起手动画延迟': 0.0, '命中动画延迟': 0.15, '伤害进度': LuaTable({1: 0.30})})
    ev_q.G.rawget('__gm_merc_visual_prepare_v255')(st_q, LuaTable({'刷新': lambda: False}))
    assert merc_q.rawget('播放动作') is True

    # --- 6. 200x repetition across all 5 hit-FX + action speed + epsilon alignment ---
    for i in range(200):
        tag = HIT_FX_NAMES[i % len(HIT_FX_NAMES)]
        spd_in = 10 + (i % 10)
        merc.rawget('属性').rawset('攻击速度', spd_in)
        act_in = '跳刺' if tag == '月桂_命中' else '跳斩'
        fresh_action_calls.clear()
        ev.G.rawget('类_事件').rawget('播放指定动作')(merc, act_in, 0, 0.5)
        exp = min(0.5, (0.8 - min(4, max(0, spd_in - 10)) / 10.0) * 0.72)
        assert abs(fresh_action_calls[0] - exp) < 1e-9
        fx_i, sk_i, _, pr_i = _make_fx_obj(f'Magic_04.empak,{tag}', tag, [(1, 0, 0, 144), (2, 0, 0, 144), (3, 0, 0, 20000)])
        ev.G.rawget('特效类').rawget('初始化')(fx_i, f'Magic_04.empak,{tag}', '跟随目标', 0, 0, 1, 1, 1, None, 0, 0, tag, 1, 1.0, 0, -50)
        assert sk_i.length() == 3 and fx_i.rawget('总帧数') == 1 and pr_i == [3] and fx_i.rawget('延迟时间') == 0

    # Verify epsilon alignment in wrapped_step_v340 (state.命中动画延迟 < state.延迟dt on arrival)
    ev_res, st_res, _ = _run_ranged_sim(rt_src, skill='蝉舞', dx_px=240.0, fps=66.0, reload_merc_mode=True)
    assert ev_res['dmg_count'] == 1 and ev_res['dmg_frame'] == ev_res['end_frame'] == ev_res['hit_fx_frame']
    assert float(st_res.rawget('命中动画延迟')) < float(st_res.rawget('延迟dt'))

    print('MERC_SKILL_RESP_V341_PASS (200x): hit-FX blank strip + prime, 跳斩/跳刺 speed scaling (0.5 -> 0.288), 蝉舞 unblock, reload re-wrap & 前尘忆梦 isolation OK!')


def main():
    mods_o, rt_src = test_diff_syntax_and_m12_37()
    test_v341_merc_hit_fx_and_action_speed(rt_src)
    # Full v1.340 projectile hit-timing suite (200x across all 6 skills) + recent regressions
    test_v340_merc_ranged_hit_timing(rt_src)
    test_v339_hero_merc_boundary_and_heal(mods_o[12], rt_src)
    test_v338_mount_medal_seal_enchants_and_confirm(mods_o[12], rt_src)
    test_v335_repeat_autocast_ux(rt_src)

    out_bytes = (W / 'game_v341.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.341',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v341.res': out_sha,
            'runtime_v341.lua': hashlib.sha256((W / 'runtime_v341.lua').read_bytes()).hexdigest(),
            'patch_v341.py': hashlib.sha256((W / 'patch_v341.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'm12_37_zero_jmp_below_params_preserved',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'v341_magic04_hit_fx_blank_strip_delay_reset_speed_tighten_prime_pass',
            'v341_ranged_merc_skill_action_speed_scaling_and_melee_isolation_pass',
            'v341_chanwu_launch_unblock_epsilon_align_and_reload_rewrap_pass',
            'v341_qianchi_isolated_pass',
            'v340_merc_ranged_hit_timing_200x_pass',
            'v339_v338_v335_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v341.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v341.json').write_text(text, encoding='utf-8')
    print('ALL v1.341 TESTS PASSED!')


if __name__ == '__main__':
    main()
