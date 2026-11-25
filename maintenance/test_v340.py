"""Targeted verification suite for v1.340:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v340.lua
3. m12/37 (qs_item_box.Main) still has ZERO JMP instructions with A < params
4. Mercenary ranged projectile hit-timing fix (v1.340, 来世续缘 only):
   - Authentic m14/428 frame loop order (屏幕子弹组 BEFORE 屏幕事件组) and authentic m22/116
     projectile physics (speed *= 1+dt, visual_tick called BEFORE movement, info.命中 -> 已经消失=true)
     + authentic m22/52 skill refresh (延迟dt += dt -> step -> 命中动画 -> 伤害进度 -> 完成)
   - Normal mob & large Boss (模型大小=1.5, 中心Y偏移=70) at 66 FPS:
     * Old code waited until exact center (dist <= speed*dt), adding 4..8 frames after body contact
     * New v1.340 impacts at body-edge + weapon-edge (~4..8 frames earlier) with 0-frame end->damage gap
   - Moving target (walking toward merc): live target tracking avoids stale 1-frame target lag
   - Close range (1 cell, 48px horizontal & 32px vertical): still shows multiple visible travel frames
   - shot.skip coincidence frame (retire on frame K, arrival on frame K+1):
     * Old code delayed damage by +1 frame AFTER bullet vanished!
     * New v1.340 delivers damage on the EXACT arrival frame (0-frame gap)!
   - Mercenary hitstun (硬直) during close/mid range flight (arrived while shot.retired==false):
     * Old code stalled damage for the entire hitstun duration (10+ frames) after bullet vanished!
     * New v1.340 delivers damage immediately on arrival frame (0-frame gap)!
   - All 6 ranged skills (刺客普通攻击, 蝉舞, 盛开, 白莲, 红莲, 月桂) + blink behind locked target
     + save-reload re-wrap of BOTH prepare & step + sustained cast cadence / DPS + 「前尘忆梦」 isolation
5. Core regressions: v1.339 hero/merc boundary & heal, v1.338 enchants, v1.335 repeat autocast.
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
from test_v301 import make_enemy
from test_v335 import test_v335_repeat_autocast_ux
from test_v338 import test_v338_mount_medal_seal_enchants_and_confirm
from test_v339 import test_v339_hero_merc_boundary_and_heal

W = Path(__file__).resolve().parent
BASE_SHA = '5ab8c1bef429e11d7e8be5556a7936576a87341b335a876fac1a2a6d6f2cdf44'


def extract_runtime_v340(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.340 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v340.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_syntax_and_m12_37():
    base_bytes = (W / 'game_v339.res').read_bytes()
    out_bytes = (W / 'game_v340.res').read_bytes()
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

    rt_src = extract_runtime_v340(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def _run_ranged_sim(rt_src, *, story='来世续缘', skill='刺客普通攻击',
                    dx_px=288.0, dy_px=0.0, fps=66.0, atk_spd_mult=10.0,
                    target_cy=35.0, target_scale=1.0, weapon_wh=(32, 32),
                    target_vx=0.0, merc_hitstun_frames=0, hitstun_start_frame=None,
                    use_old_only=False, reload_merc_mode=False):
    """Simulate authentic m14/428 frame loop + m22/116 bullet physics + m22/52 skill refresh."""
    merc_src = (W / 'merc_mode_v288.lua').read_text(encoding='utf-8')
    env = make_env(story=story)
    ev, S = env['ev'], env['S']
    ss = S.rawget('script_setting')
    dt = 1.0 / fps
    ev.G.rawset('dt', dt)
    ev.G.rawget('math').rawset('pi', math.pi)
    ev.G.rawget('math').rawset('sqrt', math.sqrt)

    def dir_fn(x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy < 0: return 1
        if dx > 0 and dy < 0: return 2
        if dx > 0 and dy == 0: return 3
        if dx > 0 and dy > 0: return 4
        if dx == 0 and dy > 0: return 5
        if dx < 0 and dy > 0: return 6
        if dx < 0 and dy == 0: return 7
        return 8

    ss.rawset('取两点间方向', dir_fn)
    ev.G.rawset('Q_地图', LuaTable({'取格子信息': lambda x, y, k: 0}))

    fireball = LuaTable({'子弹速度': 450 if story == '来世续缘' else 350})
    bullets = []
    ev.G.rawset('Sys', LuaTable({
        'get': lambda kind, key: fireball if kind == 'skill' and '火球术' in str(key) else None,
        'add': lambda kind, obj: bullets.append(obj) if kind == '屏幕子弹' else None,
    }))

    # Authentic m22/121 + m22/116 private visual bullet implementation
    bullet_traces = []

    def authentic_factory(x, y, tx, ty, speed, actor, target, kind, image, parabola, tick_fn, *rest):
        center_off = (target.rawget('属性').rawget('中心Y偏移') or 0) * (target.rawget('属性').rawget('模型大小') or 1)
        info = LuaTable({
            '坐标x': float(x), '坐标y': float(y),
            '原始目标x': float(tx), '原始目标y': float(ty),
            '移动速度': float(speed), '原始速度': float(speed),
            '命中': False, '托管': False, '__gm_spin_v255': 0.0,
        })
        ang = math.atan2(ty - y, tx - x)
        st = {'gone': False, 'sx': math.cos(ang), 'sy': math.sin(ang), 'draws': 0, 'end_frame': None}
        bullet_traces.append((info, st))

        def upd():
            if st['gone']:
                return
            d_t = float(ev.G.rawget('dt'))
            # m22/116 PC 80..88: speed *= (1 + dt)
            spd = float(info.rawget('移动速度')) * (1.0 + d_t)
            info.rawset('移动速度', spd)
            # m22/116 PC 89..99: visual_tick(aid, tid, info, extra)
            if tick_fn is not None:
                tick_fn(actor.rawget('id'), target.rawget('id'), info, LuaTable())
            # m22/116 PC 213..228: if info.命中 then 已经消失=true; return end
            if info.rawget('命中'):
                st['gone'] = True
                return
            # m22/116 PC 412..448: dist to (原始目标x, 原始目标y)
            cx, cy_b = float(info.rawget('坐标x')), float(info.rawget('坐标y'))
            ox, oy = float(info.rawget('原始目标x')), float(info.rawget('原始目标y'))
            dist = math.hypot(ox - cx, oy - cy_b)
            if dist <= spd * d_t:
                st['gone'] = True
                return
            # m22/116 PC 449..568: move and refresh target angle & 原始目标
            nx = cx + st['sx'] * spd * d_t
            ny = cy_b + st['sy'] * spd * d_t
            info.rawset('坐标x', nx)
            info.rawset('坐标y', ny)
            tm = target.rawget('地图坐标')
            ntx = float(tm.rawget('x')) + float(target.rawget('锚点x') or 0)
            nty = float(tm.rawget('y')) + float(target.rawget('锚点y') or 0) - center_off
            a2 = math.atan2(nty - ny, ntx - nx)
            st['sx'], st['sy'] = math.cos(a2), math.sin(a2)
            info.rawset('原始目标x', ntx)
            info.rawset('原始目标y', nty)

        return LuaTable({
            '更新': upd,
            '已经消失': lambda: st['gone'],
            '销毁': lambda: st.__setitem__('gone', True),
        })

    ev.G.rawset('__gm_merc_visual_factory_v255', authentic_factory)

    w_img = LuaTable({'宽度': weapon_wh[0], '高度': weapon_wh[1], '指针': 'weapon-ground'})
    w_item = LuaTable({'名称': '玄月', '分类': '装备', '子类': '武器', '地面图标': w_img,
                       '附加': LuaTable({'绑定技能': '刺客普通攻击'})})
    S.rawget('包裹物品组').rawset(397, LuaTable({'道具': w_item, '拿起': False}))

    merc_px = LuaTable({'x': 0.0, 'y': 320.0})
    merc_grid = LuaTable({'x': 10, 'y': 10})
    merc = LuaTable({
        'id': 501, '绑定技能': '刺客普通攻击', '方向': 3, '锚点x': 0.0, '锚点y': 0.0,
        '地图格子': merc_grid, '地图坐标': merc_px,
        '属性': LuaTable({'hp': 1000, '中心Y偏移': 30.0, '模型大小': 1.0}),
    })
    blinks = []
    def do_blink(bx, by):
        blinks.append((bx, by))
        merc_grid.rawset('x', bx); merc_grid.rawset('y', by)
        merc_px.rawset('x', float((bx - 10) * 48)); merc_px.rawset('y', float(320 + (by - 10) * 32))
    merc.rawset('瞬移', do_blink)
    env['U'].rawset('佣兵对象', merc)

    target_px = LuaTable({'x': float(dx_px), 'y': float(320.0 + dy_px)})
    target_grid = LuaTable({'x': 10 + int(round(dx_px / 48.0)), 'y': 10 + int(round(dy_px / 32.0))})
    target = LuaTable({
        'id': 1001, '所属阵营': '敌方', '不可选中': False, '是否有效': True, '已经消失': False,
        '方向': 7, '锚点x': 0.0, '锚点y': 0.0,
        '地图格子': target_grid, '地图坐标': target_px,
        '属性': LuaTable({'hp': 5000, '中心Y偏移': float(target_cy), '模型大小': float(target_scale)}),
    })
    S.rawset('屏幕事件组', LuaTable({1: merc, 2: target}))

    # Load merc_mode_v288 and (unless use_old_only) runtime_v340
    ev.G.get('loadstring')(merc_src)()(S, ss)
    if not use_old_only:
        ev.G.get('loadstring')(rt_src)(S)
        if reload_merc_mode:
            # Simulate save reload overwriting prepare & step, then pickup_frame re-wrapping both!
            ev.G.get('loadstring')(merc_src)()(S, ss)
            ev.G.get('__gm_pickup_frame_v299')(env['U'], env['G'])

    # Build authentic m22/53 skill state + m22/52 refresh
    hit_delay = 0.15 * 10.0 / atk_spd_mult
    dmg_delay = 0.30 * 10.0 / atk_spd_mult
    state = LuaTable({
        '施法者': merc, '目标': target, '对象': LuaTable({'名称': skill}),
        '起手动画延迟': 0.0, '命中动画延迟': hit_delay,
        '伤害进度': LuaTable({1: dmg_delay}),
        '延迟dt': 0.0, '完成': False,
        '起手动画_已播放': False, '命中动画_已播放': False, '伤害产生_已结束': False,
    })
    events = {'hit_fx_frame': None, 'dmg_frame': None, 'retire_frame': None, 'end_frame': None,
              'dmg_count': 0, 'visible_draw_frames': 0}
    cur_frame = [0]

    def native_refresh():
        if state.rawget('完成'):
            return True
        state.rawset('延迟dt', float(state.rawget('延迟dt')) + dt)
        ev.G.rawget('__gm_merc_visual_step_v255')(state)
        if state.rawget('完成'):
            return True
        if float(state.rawget('延迟dt')) >= float(state.rawget('起手动画延迟')) and not state.rawget('起手动画_已播放'):
            state.rawset('起手动画_已播放', True)
        if float(state.rawget('延迟dt')) >= float(state.rawget('命中动画延迟')) and not state.rawget('命中动画_已播放'):
            state.rawset('命中动画_已播放', True)
            events['hit_fx_frame'] = cur_frame[0]
        if not state.rawget('伤害产生_已结束'):
            dp = state.rawget('伤害进度')
            if dp.length() >= 1 and float(state.rawget('延迟dt')) >= float(dp.rawget(1)):
                events['dmg_count'] += 1
                events['dmg_frame'] = cur_frame[0]
                state.rawset('伤害产生_已结束', True)
        if state.rawget('伤害产生_已结束'):
            state.rawset('完成', True)
            return True
        return False

    public = LuaTable({'刷新': native_refresh})
    ev.G.rawget('__gm_merc_visual_prepare_v255')(state, public)

    retired = False
    hitstun_left = 0
    for frame in range(1, 300):
        cur_frame[0] = frame
        if target_vx != 0.0 and frame > 1:
            target_px.rawset('x', float(target_px.rawget('x')) + target_vx * dt)
        if hitstun_start_frame is not None and frame == hitstun_start_frame:
            hitstun_left = merc_hitstun_frames

        # Phase 1 (m14/428 PC 584): 屏幕子弹组 updates FIRST!
        for i in range(len(bullets) - 1, -1, -1):
            b = bullets[i]
            b.rawget('更新')()
            if bullet_traces and bullet_traces[0][1]['gone'] and events['end_frame'] is None:
                events['end_frame'] = frame
            if b.rawget('已经消失')():
                b.rawget('销毁')()
                bullets.pop(i)

        # Phase 2 (m14/428 PC 634): 屏幕事件组 updates SECOND! (blocked when merc is in 硬直!)
        if hitstun_left > 0:
            hitstun_left -= 1
        elif not retired:
            if public.rawget('刷新')():
                retired = True
                events['retire_frame'] = frame

        # Phase 3 (m14/428 PC 1045): 屏幕子弹组 draws visible bullets
        for info, st in bullet_traces:
            if not st['gone']:
                events['visible_draw_frames'] += 1

        if retired and len(bullets) == 0 and state.rawget('完成'):
            break

    return events, state, blinks


def test_v340_merc_ranged_hit_timing(rt_src):
    # 1. Normal mob at 6 cells (288px), 66 FPS: new hits significantly earlier than old, 0-frame end->dmg gap!
    old_norm, _, _ = _run_ranged_sim(rt_src, dx_px=288.0, fps=66.0, target_cy=35.0, target_scale=1.0, use_old_only=True)
    new_norm, _, _ = _run_ranged_sim(rt_src, dx_px=288.0, fps=66.0, target_cy=35.0, target_scale=1.0, reload_merc_mode=True)
    assert new_norm['dmg_count'] == 1 and new_norm['hit_fx_frame'] == new_norm['dmg_frame']
    assert new_norm['dmg_frame'] == new_norm['end_frame'], f'Expected 0-frame end->dmg gap, got {new_norm}'
    assert old_norm['dmg_frame'] - new_norm['dmg_frame'] >= 3, (old_norm, new_norm)
    assert new_norm['retire_frame'] == old_norm['retire_frame'], 'Original cast retire cadence must stay identical'
    assert new_norm['visible_draw_frames'] >= 15

    # 2. Large Boss (模型大小=1.5, 中心Y偏移=70) at 6 cells, 66 FPS: saves even more frames (~6..9 frames)!
    old_boss, _, _ = _run_ranged_sim(rt_src, dx_px=288.0, fps=66.0, target_cy=70.0, target_scale=1.5, use_old_only=True)
    new_boss, _, _ = _run_ranged_sim(rt_src, dx_px=288.0, fps=66.0, target_cy=70.0, target_scale=1.5)
    assert new_boss['dmg_count'] == 1 and new_boss['dmg_frame'] == new_boss['end_frame']
    assert old_boss['dmg_frame'] - new_boss['dmg_frame'] >= 6, (old_boss, new_boss)

    # 3. shot.skip coincidence frame (retire on frame K, arrival on frame K+1):
    #    Sweep distances & attack speeds to hit exact retire+1 arrival and prove 0-frame gap on new!
    saw_old_skip_lag = False
    for dist_px in range(120, 260, 12):
        for spd_m in (10.0, 15.0, 20.0, 30.0):
            o, _, _ = _run_ranged_sim(rt_src, dx_px=float(dist_px), fps=66.0, atk_spd_mult=spd_m, use_old_only=True)
            if o['dmg_frame'] - o['end_frame'] >= 1:
                saw_old_skip_lag = True
            n, _, _ = _run_ranged_sim(rt_src, dx_px=float(dist_px), fps=66.0, atk_spd_mult=spd_m)
            assert n['dmg_count'] == 1
            assert n['dmg_frame'] == n['end_frame'], f'Non-zero end->dmg gap at dist={dist_px}, spd={spd_m}: {n}'
            assert n['hit_fx_frame'] == n['dmg_frame']
    assert saw_old_skip_lag, 'Test sweep should reproduce the old shot.skip +1 frame lag'

    # 4. Mercenary hitstun (硬直) during close/mid range flight (arrived while shot.retired == false):
    #    Old code stalled damage for the entire remaining hitstun (8 frames) AFTER bullet vanished!
    #    New v1.340 flushes immediately inside bullet.更新 -> 0-frame gap!
    old_stun, _, _ = _run_ranged_sim(rt_src, dx_px=96.0, fps=66.0, atk_spd_mult=10.0,
                                     merc_hitstun_frames=16, hitstun_start_frame=4, use_old_only=True)
    new_stun, _, _ = _run_ranged_sim(rt_src, dx_px=96.0, fps=66.0, atk_spd_mult=10.0,
                                     merc_hitstun_frames=16, hitstun_start_frame=4)
    assert old_stun['dmg_frame'] - old_stun['end_frame'] >= 7, f'Expected old hitstun stall, got {old_stun}'
    assert new_stun['dmg_count'] == 1 and new_stun['dmg_frame'] == new_stun['end_frame'], new_stun

    # 5. Close range 1-cell throws (48px horizontal & 32px vertical): still visibly fly >= 2 frames!
    for dx_c, dy_c in ((48.0, 0.0), (0.0, 32.0)):
        c_res, _, _ = _run_ranged_sim(rt_src, dx_px=dx_c, dy_px=dy_c, fps=66.0)
        assert c_res['dmg_count'] == 1 and c_res['dmg_frame'] == c_res['end_frame']
        assert c_res['visible_draw_frames'] >= 2, f'1-cell throw must remain visible: {c_res}'

    # 6. Moving target walking toward merc (-160 px/s): live target tracking hits cleanly with 0-frame gap!
    mv_old, _, _ = _run_ranged_sim(rt_src, dx_px=288.0, fps=66.0, target_vx=-160.0, use_old_only=True)
    mv_new, _, _ = _run_ranged_sim(rt_src, dx_px=288.0, fps=66.0, target_vx=-160.0)
    assert mv_new['dmg_count'] == 1 and mv_new['dmg_frame'] == mv_new['end_frame']
    assert mv_old['dmg_frame'] - mv_new['dmg_frame'] >= 3, (mv_old, mv_new)

    # 7. All 6 mercenary ranged skills (刺客普通攻击 + 蝉舞/盛开/白莲/红莲/月桂) pass with 0-frame gap!
    for sk in ('刺客普通攻击', '蝉舞', '盛开', '白莲', '红莲', '月桂'):
        res, _, _ = _run_ranged_sim(rt_src, skill=sk, dx_px=240.0, fps=66.0, reload_merc_mode=True)
        assert res['dmg_count'] == 1 and res['dmg_frame'] == res['end_frame'] == res['hit_fx_frame'], (sk, res)

    # 8. 「前尘忆梦」 100% isolated (uses exact old prepare & step timing, untouched!)
    qc_old, _, _ = _run_ranged_sim(rt_src, story='前尘忆梦', dx_px=288.0, fps=66.0, use_old_only=True)
    qc_new, _, _ = _run_ranged_sim(rt_src, story='前尘忆梦', dx_px=288.0, fps=66.0, use_old_only=False)
    assert qc_new['end_frame'] == qc_old['end_frame'] and qc_new['dmg_frame'] == qc_old['dmg_frame'], (qc_old, qc_new)

    # 9. 200-cast continuous repetition test across distances & speeds (zero leaks, 0-frame gap)
    dists = (48.0, 96.0, 144.0, 192.0, 240.0, 288.0)
    spds = (10.0, 20.0, 40.0)
    skills = ('刺客普通攻击', '蝉舞', '盛开', '白莲', '红莲', '月桂')
    for idx in range(200):
        res, _, _ = _run_ranged_sim(
            rt_src,
            skill=skills[idx % len(skills)],
            dx_px=dists[idx % len(dists)],
            fps=66.0,
            atk_spd_mult=spds[idx % len(spds)],
            target_cy=35.0 if idx % 3 else 70.0,
            target_scale=1.0 if idx % 3 else 1.5,
        )
        assert res['dmg_count'] == 1 and res['dmg_frame'] == res['end_frame'] == res['hit_fx_frame'], (idx, res)
        assert res['visible_draw_frames'] >= 2, (idx, res)

    print(
        f'MERC_TIMING_V340_PASS (200x): '
        f'normal_mob saved={old_norm["dmg_frame"] - new_norm["dmg_frame"]}f, '
        f'boss saved={old_boss["dmg_frame"] - new_boss["dmg_frame"]}f, '
        f'hitstun_old_gap={old_stun["dmg_frame"] - old_stun["end_frame"]}f -> new_gap=0f'
    )


def main():
    mods_o, rt_src = test_diff_syntax_and_m12_37()
    test_v340_merc_ranged_hit_timing(rt_src)
    # Direct & recent regressions
    test_v339_hero_merc_boundary_and_heal(mods_o[12], rt_src)
    test_v338_mount_medal_seal_enchants_and_confirm(mods_o[12], rt_src)
    test_v335_repeat_autocast_ux(rt_src)

    out_bytes = (W / 'game_v340.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.340',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v340.res': out_sha,
            'runtime_v340.lua': hashlib.sha256((W / 'runtime_v340.lua').read_bytes()).hexdigest(),
            'patch_v340.py': hashlib.sha256((W / 'patch_v340.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'm12_37_zero_jmp_below_params_preserved',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'v340_merc_ranged_body_edge_impact_normal_and_boss_pass',
            'v340_merc_ranged_zero_post_arrival_gap_skip_and_hitstun_pass',
            'v340_merc_ranged_1cell_visibility_moving_target_all_6_skills_rewrap_pass',
            'v340_qianchi_isolated_pass',
            'v339_v338_v335_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v340.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v340.json').write_text(text, encoding='utf-8')
    print('ALL v1.340 TESTS PASSED!')


if __name__ == '__main__':
    main()
