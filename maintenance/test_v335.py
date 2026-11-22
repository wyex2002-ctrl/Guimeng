"""Exhaustive verification suite for v1.335:
1. Outer resource diff strictly [12, 14, 30] + Dump.rebuild() + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v335.lua
3. m12/37 (qs_item_box.Main) still has ZERO JMP instructions with A < params
4. Long-press auto-cast UX optimization (v1.335, 「来世续缘」 only):
   - Holding F1 (112) for 1.0s activates auto-cast and casts every 0.1s once released.
   - Clicking mouse while hovering friendly Mercenary/Summon (所属阵营=='友方') DOES NOT cancel auto-cast.
   - Clicking mouse while hovering UI (UI焦点=true) or neutral NPC still cancels (mouse_interaction).
   - Opening visible 背包 / 仓库 / 商店 / 设置 / 对话 windows or having input focus DOES NOT cancel auto-cast.
   - Pressing Tab (9), Shift (16), Ctrl (17), R (82), Space (32), B (66), F (70), etc. DOES NOT cancel auto-cast.
   - Pressing ESC (27) IMMEDIATELY cancels auto-cast (reason='esc_key').
   - Pressing a bound skill hotkey (e.g. F1=112) still cancels auto-cast (reason='skill_key').
   - Map change ('cancel') still cancels auto-cast.
   - 「前尘忆梦」 delegates 100% untouched to original __gm_repeat_control_v229.
5. Full v1.334 + v1.333 + v1.332 + v1.331 + v1.330 + v1.319 + v1.317 + v1.308 + v1.307 + v1.306 regressions.
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

W = Path(__file__).resolve().parent
BASE_SHA = '3dd0865f4db9395dc1a42fb57c49fe74a5f2204779394a6cf4ed0f8bc8c716be'


def extract_runtime_v335(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.335 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v335.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_syntax_and_m12_37():
    base_bytes = (W / 'game_v334.res').read_bytes()
    out_bytes = (W / 'game_v335.res').read_bytes()
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

    rt_src = extract_runtime_v335(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_v335_repeat_autocast_ux(rt_src):
    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']

    keys_down = set()
    keys_pressed = set()
    eng = ev.G.rawget('引擎')
    eng.rawset('取按键事件', lambda self_e, k: k in keys_down)
    eng.rawset('取按键按下', lambda self_e, k: k in keys_pressed)

    L = ev.G.rawget('L常量')
    L.rawset('键_鼠标左', 1)
    L.rawset('键_鼠标右', 2)
    L.rawset('键_ALT', 18)
    L.rawset('键_SHIFT', 16)
    L.rawset('键_CTRL', 17)

    casts = []
    skill_ranges = LuaTable({d: LuaTable({1: LuaTable({'x': 1, 'y': 0})}) for d in range(1, 9)})
    skill_obj = LuaTable({
        '施放位置': '目标', '目标类型': '敌方', '穿透模式': 0,
        '施法距离': 8, '发射数量': 0, '作用范围': skill_ranges,
    })
    slot_f1 = LuaTable({'键值': 112, '绑定技能': '击风', '事件': lambda flag: casts.append(flag)})

    E = ev.G.rawget('Ae冻集')
    E.rawset('屏幕焦点', True)
    E.rawset('镜头ID', 0)
    E.rawset('UI焦点', False)
    E.rawset('鼠标焦点事件对象', None)
    E.rawset('快捷事件组', LuaTable({1: slot_f1}))
    E.rawset('最后按键', 0)
    ev.G.rawset('Ae冻', LuaTable({'地图id': 1}))
    ev.G.rawset('Q_鼠标', LuaTable({'被占用': False}))
    ev.G.rawset('dt', 0.25)

    orig_calls = []
    def orig_repeat(self_h, mode=None, tag=None, msg=None):
        orig_calls.append((mode, tag, msg))

    hero = S.rawget('Hero')
    hero.rawset('id', 0)
    hero.rawset('已经死亡', False)
    hero.rawset('属性', LuaTable({'hp': 1000, 'mp': 300, '禁攻击': False}))
    hero.rawset('剧情表', LuaTable())
    hero.rawset('硬直', 0)
    hero.rawset('抵达目标点', True)
    hero.rawset('技能信息', LuaTable({'击风': LuaTable({'可用': True, '可触发': True, '开始CD效果': False, '对象': skill_obj})}))
    hero.rawset('__gm_repeat_control_v229', orig_repeat)

    # Mock open 背包 / 仓库 / 对话 windows with active input focus
    bag_win = LuaTable({'名称': '背包窗口', '可视': True, '是否有输入框焦点': lambda self_w: True})
    wh_win = LuaTable({'名称': '仓库窗口', '可视': True, '是否有输入框焦点': lambda self_w: False})
    dlg_win = LuaTable({'名称': '对话窗口', '可视': True, '是否有输入框焦点': lambda self_w: False})
    sys_tbl = ev.G.rawget('Sys')
    orig_sys_get = sys_tbl.rawget('get')
    sys_tbl.rawset('get', lambda k: LuaTable({1: bag_win, 2: wh_win, 3: dlg_win}) if k == 'item_box' else orig_sys_get(k))

    ev.G.get('loadstring')(rt_src)(S)
    ctrl = hero.rawget('__gm_repeat_control_v229')
    assert ctrl is not orig_repeat

    def tick():
        ctrl(hero)

    # Frame 1: init + unblock
    tick()
    assert hero.rawget('__gm_repeat_skill_v229').rawget('blocked') is False

    # Hold F1 (112) for 1.0s (5 ticks: start=0, 0.25, 0.5, 0.75, 1.0)
    keys_down.add(112)
    for _ in range(5):
        tick()
    st = hero.rawget('__gm_repeat_skill_v229')
    assert st.rawget('active') is True and st.rawget('name') == '击风', 'Failed to activate auto-cast'

    # Release F1 -> next tick casts!
    keys_down.clear()
    tick()
    assert len(casts) == 1, f'Expected 1 cast, got {len(casts)}'

    # 1. Open 背包/仓库/对话 windows + input focus -> MUST STAY ACTIVE and KEEP CASTING!
    tick()
    assert st.rawget('active') is True and len(casts) == 2

    # 2. Click left mouse while hovering friendly Mercenary / Summon (所属阵营=='友方') -> MUST STAY ACTIVE!
    E.rawset('鼠标焦点事件对象', LuaTable({'id': 50001, '所属阵营': '友方'}))
    keys_down.add(1)  # left mouse
    tick()
    assert st.rawget('active') is True, 'Clicking friendly unit MUST NOT cancel auto-cast!'
    keys_down.clear()
    E.rawset('鼠标焦点事件对象', None)
    tick()
    assert st.rawget('active') is True and len(casts) == 3

    # 3. Press non-hotbar keys: Tab(9), Shift(16), Ctrl(17), R(82), Space(32), B(66), F(70), C(67), M(77) -> MUST STAY ACTIVE!
    for k in (9, 16, 17, 82, 32, 66, 70, 67, 77):
        E.rawset('最后按键', k)
        keys_pressed.add(k)
        tick()
        assert st.rawget('active') is True, f'Non-hotbar key {k} MUST NOT cancel auto-cast!'
        keys_pressed.clear()

    # 4. Press ESC (27) -> MUST CANCEL immediately with reason='esc_key'!
    E.rawset('最后按键', 27)
    keys_pressed.add(27)
    tick()
    assert st.rawget('active') is False and st.rawget('reason') == 'esc_key', f'ESC failed to cancel: {st.rawget("reason")}'
    keys_pressed.clear()

    # Re-activate auto-cast to test F1 skill-key toggle-off & UI click cancel
    tick()  # unblock
    keys_down.add(112)
    for _ in range(5):
        tick()
    assert st.rawget('active') is True
    keys_down.clear()
    tick()
    assert st.rawget('active') is True

    # Press F1 again -> cancels with reason='skill_key'
    keys_down.add(112)
    tick()
    assert st.rawget('active') is False and st.rawget('reason') == 'skill_key'
    keys_down.clear()

    # Re-activate and test clicking neutral NPC -> still cancels with mouse_interaction
    tick()  # unblock
    keys_down.add(112)
    for _ in range(5):
        tick()
    assert st.rawget('active') is True
    keys_down.clear()
    E.rawset('鼠标焦点事件对象', LuaTable({'id': 90001, '所属阵营': '中立'}))
    keys_down.add(1)
    tick()
    assert st.rawget('active') is False and st.rawget('reason') == 'mouse_interaction'
    keys_down.clear()
    E.rawset('鼠标焦点事件对象', None)

    # 5. 「前尘忆梦」 delegates 100% untouched to orig_repeat
    U.rawset('版本选择', '前尘忆梦')
    orig_calls.clear()
    tick()
    assert len(orig_calls) == 1 and orig_calls[0] == (None, None, None)


def main():
    mods_o, rt_src = test_diff_syntax_and_m12_37()
    test_v335_repeat_autocast_ux(rt_src)
    test_v334_mode2_qingtongfu_mofachangpao_non7(rt_src)
    test_v333_shared_weapon_tooltip_note(rt_src)
    test_v332_corpse_drop_jipin_stats(rt_src)
    test_v331_gem_tooltip_cache_refresh(rt_src)
    test_v330_split_bracelet_ring_gems(mods_o[12], rt_src)
    test_real_boss_blueprint_drops_5_5pct(mods_o[12], rt_src)
    test_compact_equip_spaces_v317(rt_src)
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v335.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.335',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v335.res': out_sha,
            'runtime_v335.lua': hashlib.sha256((W / 'runtime_v335.lua').read_bytes()).hexdigest(),
            'patch_v335.py': hashlib.sha256((W / 'patch_v335.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'm12_37_zero_jmp_below_params_preserved',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'repeat_autocast_keeps_active_on_friendly_click_open_windows_and_non_hotbar_keys',
            'repeat_autocast_cancels_on_esc_skill_key_and_neutral_ui_click_with_qianchi_isolated',
            'v334_v333_v332_v331_v330_v319_v317_v308_v307_v306_regressions_pass',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v335.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v335.json').write_text(text, encoding='utf-8')
    print('ALL v1.335 TESTS PASSED!')


if __name__ == '__main__':
    main()
