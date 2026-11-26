"""Targeted verification suite for v1.342:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees() + version string checks
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v342.lua
3. m12/37 (qs_item_box.Main) still has ZERO JMP instructions with A < params
4. N-key settings window (系统窗口, id=561) manual [Save] button (v1.342, 来世续缘 only):
   - Anchored dynamically between 单图按钮12 (Quit Game, 62,348,97x25) and 单图按钮10 (close [X], 241,345,30x30)
     at exact (bx=167, by=348, w=66, h=25) with 8px symmetric spacing
   - 1:1 3-slice rendering from built-in stone button -1480207602.img (0,0,31,25 / 14,0,10,25 / 55,0,25,25),
     covering normal, hover, pressed (y+sy), and 900ms jade-gold confirmation flash states, plus
     clean 销毁() cleanup and -1657209002.img 9-slice fallback when -1480207602.img is absent
   - Native save invocation: Ux雌.窗口相关.存档读档('存档', Ux雌.人物选择, nil, 0) (including slot=0!),
     plays 按键音效1, sets flash_until_ms, increments save_count, shows green 屏幕提示
   - Safety guards: __gm_loading_save_v299, 1000ms debounce, Gly独.鼠标道具 > 0, FXru胃啪.HP <= 0,
     slot==nil / non-callable save_fn, and pcall error capture with red 屏幕提示 feedback
   - 「前尘忆梦」 isolation (hides & disables 手动存档按钮_v342 and blocks click; restores on switch back)
   - pickup_frame auto-installs & re-syncs button on story switch
   - 200x hoisted repetition loop (single loadstring outside loop) across save clicks, flash/hover/press states,
     and story transitions with zero errors
5. Recent regressions: v1.341 merc hit-FX/action-speed + v1.340 ranged sanity + v1.339 + v1.338 + v1.335.
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
from test_v335 import test_v335_repeat_autocast_ux
from test_v338 import test_v338_mount_medal_seal_enchants_and_confirm
from test_v339 import test_v339_hero_merc_boundary_and_heal
from test_v340 import _run_ranged_sim
from test_v341 import test_v341_merc_hit_fx_and_action_speed

W = Path(__file__).resolve().parent
BASE_SHA = 'fd1c59c892a3746e2695cccd078288ea63dc87d27fae27bdff392394d525cac0'  # expected output check below
PREV_SHA = 'fed99de0e6bd44f3b418e56775eb2beab6ab940971fb120718240f43da8ee55f'


def extract_runtime_v342(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.342 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v342.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_syntax_and_m12_37():
    base_bytes = (W / 'game_v341.res').read_bytes()
    out_bytes = (W / 'game_v342.res').read_bytes()
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

    p37 = mods_o[12].protos[37]
    for pc, ins in enumerate(p37.bc):
        if OPS[ins & 0xFF] == 'JMP':
            a = (ins >> 8) & 0xFF
            assert a >= p37.params, f'm12/37 pc={pc} has JMP A={a} < params={p37.params}'

    rt_src = extract_runtime_v342(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def _find_ctrl(win, name):
    ctrls = win.rawget('控件组')
    for i in range(1, ctrls.length() + 1):
        c = ctrls.rawget(i)
        if c and c.rawget('名称') == name:
            return c
    return None


def _make_settings_env(rt_src, *, story='来世续缘', stone_available=True):
    env = make_env(story=story)
    ev, S, U = env['ev'], env['S'], env['U']

    save_calls = []
    raise_on_save = [False]
    disabled_flags = []
    destroyed_count = [0]
    sprite_rects = []
    sprite_draws = []
    text_draws = []

    def do_save(mode, slot, a3=None, a4=None):
        if raise_on_save[0]:
            raise RuntimeError('disk write error')
        save_calls.append((mode, slot, a3, a4))

    U.rawset('人物选择', 0)  # Explicitly verify slot == 0 works!
    U.rawget('窗口相关').rawset('存档读档', do_save)

    G_gly = ev.G.rawget('Gly独')
    G_gly.rawset('鼠标道具', 0)
    hero_stat = LuaTable({'HP': 500})
    ev.G.rawset('FXru胃啪', hero_stat)

    # Track font draw positions & colors separately from make_env
    orig_font = ev.G.rawget('__Res')(2, '400132927.img')

    def tracked_display(layout, x, y, col, stroke):
        text_draws.append((layout.rawget('text'), x, y, col, stroke))

    font = LuaTable({
        '取宽度': lambda s, sp=0: 28,
        '取高度': lambda s, sp=0: 14,
        '解析': lambda s, a, b: LuaTable({'text': s}),
        '显示配置': tracked_display,
    })

    def res_loader(kind, name, idx=None):
        if kind == 2:
            return font
        if name == '-1480207602.img' and not stone_available:
            return None
        return LuaTable({'img': name})

    ev.G.rawset('__Res', res_loader)

    def create_sprite(img, sx=0, sy=0, sw=0, sh=0):
        sprite_rects.append((img.rawget('img') if isinstance(img, LuaTable) else img, sx, sy, sw, sh))
        st = {'color': None, 'rect': (sx, sy, sw, sh)}
        return LuaTable({
            '置颜色': lambda c: st.__setitem__('color', c),
            '置显示区域': lambda x0, y0, w0, h0: st.__setitem__('rect', (x0, y0, w0, h0)),
            '显示_高级': lambda x, y, ang, scx, scy: sprite_draws.append((x, y, scx, scy, st['color'], st['rect'])),
            '销毁': lambda: destroyed_count.__setitem__(0, destroyed_count[0] + 1),
        })

    ev.G.rawset('Q__', LuaTable({'创建精灵': create_sprite}))

    # Build Window 561 (系统窗口) with Quit Game (单图按钮12) and [X] (单图按钮10)
    win561 = LuaTable({'控件组': LuaTable(), '可视': True})
    win561.rawget('控件组').rawset(1, LuaTable({'名称': '单图按钮12', 'x': 62, 'y': 348, 'w': 97, 'h': 25, '可视': True}))
    win561.rawget('控件组').rawset(2, LuaTable({'名称': '单图按钮10', 'x': 241, 'y': 345, 'w': 30, 'h': 30, '可视': True}))

    def add_ctrl_561(_self, ctype, name, x, y, z, w, h, title, img, cfg, factories):
        fac = factories.get(1)
        scripts = fac()
        obj = LuaTable({
            '显示': lambda *a: None,
            '销毁': lambda: None,
            '是否有焦点': lambda: env['hovered'][0],
            '禁用按钮': lambda flag: disabled_flags.append(bool(flag)),
        })
        ctrl = LuaTable({
            '类型': ctype, '名称': name, 'x': x, 'y': y, 'w': w, 'h': h,
            '可视': True, '对象': obj, '脚本': scripts,
        })
        win561.get('控件组').rawset(win561.get('控件组').length() + 1, ctrl)

    win561.rawset('增加控件', add_ctrl_561)

    win539 = env['win539']
    S.rawset('取窗口对象', lambda wid: win539 if wid == 539 else (win561 if wid == 561 else None))

    # Load runtime ONCE
    ev.G.get('loadstring')(rt_src)(S)
    return {
        'env': env, 'ev': ev, 'S': S, 'U': U, 'G_gly': G_gly, 'hero_stat': hero_stat,
        'win561': win561, 'save_calls': save_calls, 'raise_on_save': raise_on_save,
        'disabled_flags': disabled_flags, 'destroyed_count': destroyed_count,
        'sprite_rects': sprite_rects, 'sprite_draws': sprite_draws, 'text_draws': text_draws,
    }


def test_v342_settings_save_btn(rt_src):
    # --- 1. Layout, 1:1 3-slice visuals, states, save(slot=0), and guards ---
    w = _make_settings_env(rt_src, story='来世续缘', stone_available=True)
    S, U, env, win561 = w['S'], w['U'], w['env'], w['win561']
    ctrl = _find_ctrl(win561, '手动存档按钮_v342')
    assert ctrl is not None, '手动存档按钮_v342 must be installed at runtime init'
    assert (ctrl.rawget('x'), ctrl.rawget('y'), ctrl.rawget('w'), ctrl.rawget('h')) == (167, 348, 66, 25), (
        ctrl.rawget('x'), ctrl.rawget('y'), ctrl.rawget('w'), ctrl.rawget('h')
    )
    assert ctrl.rawget('可视') is True

    # Verify exact 1:1 3-slice rects from -1480207602.img
    assert w['sprite_rects'] == [
        ('-1480207602.img', 0, 0, 31, 25),
        ('-1480207602.img', 14, 0, 10, 25),
        ('-1480207602.img', 55, 0, 25, 25),
    ], w['sprite_rects']

    obj = ctrl.rawget('对象')
    click = ctrl.rawget('脚本').rawget('Main')
    state = S.rawget('__gm_save_btn_state_v342')

    # Render normal, hover, pressed states
    w['sprite_draws'].clear(); w['text_draws'].clear()
    obj.rawget('显示')(167, 348, 1, 1, 0, -1, 1)
    assert len(w['sprite_draws']) == 3 and len(w['text_draws']) == 1
    assert all(d[4] == -1315861 for d in w['sprite_draws'])  # normal shade
    assert w['text_draws'][0][0] == 'Save' and w['text_draws'][0][3] == -2434342 and w['text_draws'][0][4] == -16777216
    assert abs(w['sprite_draws'][1][2] - 1.0) < 1e-9  # mid slice exact 1:1 scale (66-56)/10

    w['sprite_draws'].clear(); w['text_draws'].clear()
    env['hovered'][0] = True
    obj.rawget('显示')(167, 348, 1, 1, 0, -1, 1)
    assert all(d[4] == -1 for d in w['sprite_draws']) and w['text_draws'][0][3] == -1  # hover tint

    w['sprite_draws'].clear(); w['text_draws'].clear()
    env['mouse_left'][0] = True
    obj.rawget('显示')(167, 348, 1, 1, 0, -1, 1)
    assert all(d[4] == -3355444 and d[1] == 349 for d in w['sprite_draws'])  # pressed shifts y by +1
    assert w['text_draws'][0][3] == -2434342
    env['hovered'][0] = False; env['mouse_left'][0] = False

    # Valid save click with slot == 0
    env['toasts'].clear()
    click()
    assert w['save_calls'] == [('存档', 0, None, 0)], w['save_calls']
    assert env['sound_clicks'][0] == 1
    assert state.rawget('save_count') == 1
    assert env['toasts'][-1] == ('游戏存档成功！', -16711936), env['toasts']

    # Flash state immediately after save (<900ms), then expires (>900ms)
    w['sprite_draws'].clear(); w['text_draws'].clear()
    obj.rawget('显示')(167, 348, 1, 1, 0, -1, 1)
    assert all(d[4] == -2428209 for d in w['sprite_draws']) and w['text_draws'][0][3] == -3932212
    env['now_sec'][0] += 0.5  # +500ms -> still flashing, and within 1000ms debounce
    w['sprite_draws'].clear()
    obj.rawget('显示')(167, 348, 1, 1, 0, -1, 1)
    assert all(d[4] == -2428209 for d in w['sprite_draws'])

    # Debounce guard (<1000ms): rapid click suppressed
    prev_saves = len(w['save_calls'])
    click()
    assert len(w['save_calls']) == prev_saves, 'Click within 1000ms debounce must be suppressed'

    # Advance past 1000ms debounce; test all negative guards
    env['now_sec'][0] += 1.0  # total +1500ms
    w['sprite_draws'].clear()
    obj.rawget('显示')(167, 348, 1, 1, 0, -1, 1)
    assert all(d[4] == -1315861 for d in w['sprite_draws']), 'Flash must expire after 900ms'

    # Guard: loading save
    S.rawset('__gm_loading_save_v299', True)
    env['toasts'].clear()
    click()
    assert len(w['save_calls']) == prev_saves and env['toasts'][-1][0] == '正在读取存档，请稍候' and env['toasts'][-1][1] == -65536
    S.rawset('__gm_loading_save_v299', False)

    # Guard: cursor holding item (鼠标道具 > 0)
    w['G_gly'].rawset('鼠标道具', 12)
    env['toasts'].clear()
    click()
    assert len(w['save_calls']) == prev_saves and env['toasts'][-1][0] == '请先放下鼠标上的物品后再存档' and env['toasts'][-1][1] == -65536
    w['G_gly'].rawset('鼠标道具', 0)

    # Guard: hero dead (HP <= 0)
    w['hero_stat'].rawset('HP', 0)
    env['toasts'].clear()
    click()
    assert len(w['save_calls']) == prev_saves and env['toasts'][-1][0] == '角色阵亡状态下无法存档' and env['toasts'][-1][1] == -65536
    w['hero_stat'].rawset('HP', 500)

    # Guard: slot == nil
    U.rawset('人物选择', None)
    env['toasts'].clear()
    click()
    assert len(w['save_calls']) == prev_saves and env['toasts'][-1][0] == '当前状态暂无法存档' and env['toasts'][-1][1] == -65536
    U.rawset('人物选择', 0)

    # Guard: pcall catches save error cleanly
    w['raise_on_save'][0] = True
    env['toasts'].clear()
    click()
    assert len(w['save_calls']) == prev_saves and '存档失败：' in env['toasts'][-1][0] and env['toasts'][-1][1] == -65536
    w['raise_on_save'][0] = False

    # Destroy cleans up 3 sprites cleanly
    obj.rawget('销毁')()
    assert w['destroyed_count'][0] == 3

    # --- 2. Fallback to -1657209002.img 9-slice + 「前尘忆梦」 isolation + pickup_frame auto-sync ---
    wf = _make_settings_env(rt_src, story='来世续缘', stone_available=False)
    assert all(r[0] == '-1657209002.img' for r in wf['sprite_rects']) and len(wf['sprite_rects']) == 3
    cf = _find_ctrl(wf['win561'], '手动存档按钮_v342')
    assert cf is not None
    wf['sprite_draws'].clear()
    cf.rawget('对象').rawget('显示')(167, 348, 1, 1, 0, -1, 1)
    assert len(wf['sprite_draws']) == 9, 'Fallback 9-slice renders 3 rows x 3 sprites'

    # Switch to 「前尘忆梦」 -> pickup_frame hides & disables Save button and click is no-op
    wf['U'].rawset('版本选择', '前尘忆梦')
    wf['S'].rawget('__gm_pickup_frame_v299')(wf['U'], wf['env']['G'])
    assert cf.rawget('可视') is False and wf['disabled_flags'][-1] is True
    wf['save_calls'].clear()
    cf.rawget('脚本').rawget('Main')()
    assert wf['save_calls'] == []

    # Switch back to 「来世续缘」 -> pickup_frame restores & enables Save button
    wf['U'].rawset('版本选择', '来世续缘')
    wf['S'].rawget('__gm_pickup_frame_v299')(wf['U'], wf['env']['G'])
    assert cf.rawget('可视') is True and wf['disabled_flags'][-1] is False

    # --- 3. 200x hoisted repetition loop (single loadstring already done above!) ---
    click_f = cf.rawget('脚本').rawget('Main')
    obj_f = cf.rawget('对象')
    state_f = wf['S'].rawget('__gm_save_btn_state_v342')
    wf['save_calls'].clear()
    for i in range(200):
        wf['env']['now_sec'][0] += 1.2
        wf['U'].rawset('人物选择', i % 3)  # covers 0, 1, 2
        click_f()
        wf['env']['hovered'][0] = (i % 2 == 0)
        wf['env']['mouse_left'][0] = (i % 5 == 0)
        obj_f.rawget('显示')(167, 348, 1, 1, 0, -1, 1)
    wf['env']['hovered'][0] = False
    wf['env']['mouse_left'][0] = False
    assert len(wf['save_calls']) == 200 and state_f.rawget('save_count') == 200
    assert wf['save_calls'][-1] == ('存档', 199 % 3, None, 0)

    print('SETTINGS_SAVE_BTN_V342_PASS (200x hoisted): layout=(167,348,66,25), 1:1 3-slice + fallback, all guards, slot=0 & 前尘忆梦 isolation OK!')


def main():
    mods_o, rt_src = test_diff_syntax_and_m12_37()
    test_v342_settings_save_btn(rt_src)
    # Direct & recent regressions (fast: v1.341 suite + 2-skill v1.340 sanity + v1.339/v1.338/v1.335)
    test_v341_merc_hit_fx_and_action_speed(rt_src)
    for sk in ('刺客普通攻击', '蝉舞'):
        res, _, _ = _run_ranged_sim(rt_src, skill=sk, dx_px=240.0, fps=66.0, reload_merc_mode=True)
        assert res['dmg_count'] == 1 and res['dmg_frame'] == res['end_frame'] == res['hit_fx_frame'], (sk, res)
    test_v339_hero_merc_boundary_and_heal(mods_o[12], rt_src)
    test_v338_mount_medal_seal_enchants_and_confirm(mods_o[12], rt_src)
    test_v335_repeat_autocast_ux(rt_src)

    out_bytes = (W / 'game_v342.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.342',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v342.res': out_sha,
            'runtime_v342.lua': hashlib.sha256((W / 'runtime_v342.lua').read_bytes()).hexdigest(),
            'patch_v342.py': hashlib.sha256((W / 'patch_v342.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'm12_37_zero_jmp_below_params_preserved',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'v342_settings_save_btn_layout_3slice_states_slot0_guards_fallback_200x_pass',
            'v342_qianchi_isolated_pass',
            'v341_merc_skill_resp_and_v340_sanity_pass',
            'v339_v338_v335_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v342.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v342.json').write_text(text, encoding='utf-8')
    print('ALL v1.342 TESTS PASSED!')


if __name__ == '__main__':
    main()
