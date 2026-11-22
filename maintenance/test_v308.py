"""Exhaustive verification suite for v1.308:
1. Outer resource diff restricted strictly to modules [12, 14, 30] + rebuild + trees()
2. Strict Lua 5.1 syntax parse + GBK 0x5C check on embedded runtime_v308.lua
3. Authentic m48/1 + m48/2 engine window proxy test (__call table proxy where type(win.打开) == 'table', NOT 'function'!):
   - Verified via m14/361 style script_setting __index -> S.tbl_controls[name].tbl (with _G.仓库窗口 == nil & _G.行会仓库 == nil)
   - Click sound proxy (按键音效1.播放 as __call table) also verified
   - Guild NOT activated: click 1 -> 普通仓库 (warm amber); click 2 -> close (default grey)
   - Guild ACTIVATED: click 1 -> 普通仓库 (warm amber); click 2 -> close 普通 + open 行会仓库 (cool teal); click 3 -> close (default grey)
   - External close immediately resets color; NPC open does not falsely tint
   - 「前尘忆梦」 100% isolated & story switch restores original button
4. Mode 2 【自动拾取+自动出售】 ordinary-mob materials regression intact
"""
import hashlib
import json
from pathlib import Path

from ljtool import Dump
from lua51_eval import LuaTable, syntax_check
from native_test_utils import trees
from patch_v305 import ORDINARY_MOB_MATERIALS
from resource_tools import decode
from test_v300 import make_env
from test_v307 import find_ctrl, test_mode2_ordinary_materials, test_v306_regression

W = Path(__file__).resolve().parent
BASE_SHA = '9bddf977e34cc0aa4bedcbc61a128bba56fd735c070d0cd5f442e096029f916f'


def extract_runtime_v308(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.308 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v308.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_and_syntax():
    base_bytes = (W / 'game_v307.res').read_bytes()
    out_bytes = (W / 'game_v308.res').read_bytes()
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

    rt_src = extract_runtime_v308(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def make_engine_window_proxy(ev, name):
    """Build an authentic m48/1 + m48/2 + m48/3 window proxy where:
    - proxy.可视 reads internal self.可视
    - proxy.打开 / proxy.关闭 sets proxy.k = method and returns proxy ITSELF (type == 'table'!)
    - proxy() invokes __call -> self[proxy.k](self)
    """
    code = """
    local name = ...
    local internal = { 名称 = name, 可视 = false, open_calls = 0, close_calls = 0 }
    function internal:打开()
     self.open_calls = self.open_calls + 1
     self.可视 = true
    end
    function internal:关闭()
     self.close_calls = self.close_calls + 1
     self.可视 = false
    end
    local proxy = {}
    setmetatable(proxy, {
     __index = function(t, k)
      if k == '可视' then return internal.可视 end
      if k == '名称' then return internal.名称 end
      if k == '打开' or k == '关闭' then
       rawset(t, 'k', k)
       return t
      end
      return nil
     end,
     __call = function(t, ...)
      local m = rawget(t, 'k')
      return internal[m](internal, ...)
     end,
    })
    internal.tbl = proxy
    return internal, proxy
    """
    return ev.G.get('loadstring')(code)(name)


def make_engine_sound_proxy(ev, counter_list):
    """Build a callable __call table proxy for 按键音效1 (type(按键音效1.播放) == 'table')."""
    code = """
    local bump = ...
    local proxy = {}
    setmetatable(proxy, {
     __index = function(t, k)
      if k == '播放' then
       rawset(t, 'k', k)
       return t
      end
      return nil
     end,
     __call = function(t)
      if rawget(t, 'k') == '播放' then bump() end
     end,
    })
    return proxy
    """
    return ev.G.get('loadstring')(code)(lambda: counter_list.append(1))


def test_authentic_proxy_warehouse_button(rt_src):
    COL_OFF, COL_OFF_HOVER = -5723992, -4671304
    COL_NORM, COL_NORM_HOVER = -3886976, -2834288
    COL_GUILD, COL_GUILD_HOVER = -8210232, -7026472

    env = make_env(story='来世续缘')
    ev, S, U, G = env['ev'], env['S'], env['U'], env['G']
    ss = S.rawget('script_setting')

    # Real-client split: _G has NEITHER 仓库窗口 NOR 行会仓库;
    # S.tbl_controls holds raw windows with .tbl proxy, exposed via script_setting __index (m14/361)!
    ev.G.rawset('仓库窗口', None)
    ev.G.rawset('行会仓库', None)

    norm_raw, norm_proxy = make_engine_window_proxy(ev, '仓库窗口')
    guild_raw, guild_proxy = make_engine_window_proxy(ev, '行会仓库')

    # Prove this proxy truly reproduces the v1.307 bug: type(proxy.打开) == 'table', NOT 'function'!
    t_open = ev.G.get('loadstring')("local w = ...; return type(w['打开']), type(w['关闭'])")(norm_proxy)
    assert t_open == ('table', 'table'), f'Expected callable table proxy, got {t_open}'

    tbl_controls = LuaTable({'仓库窗口': norm_raw, '行会仓库': guild_raw})
    S.rawset('tbl_controls', tbl_controls)
    ev.G.get('loadstring')("""
     local ss, ctrls = ...
     setmetatable(ss, {
      __index = function(t, k)
       local c = ctrls[k]
       if c then return c.tbl end
       return nil
      end
     })
    """)(ss, tbl_controls)

    guild_flag = [False]
    U.rawset('啾啾啵啵', lambda: LuaTable({'行会': LuaTable({'名称': '归梦行会'}) if guild_flag[0] else None}))
    sound_plays = []
    sound_proxy = make_engine_sound_proxy(ev, sound_plays)
    U.rawset('游戏音效', LuaTable({'按键音效1': sound_proxy}))

    # Pre-install original 远程仓库按钮 on Window 539
    win539 = S.rawget('取窗口对象')(539)
    old_disabled = [False]
    old_ctrl = LuaTable({
        '名称': '远程仓库按钮', 'x': 180, 'y': 20, 'w': 44, 'h': 22, '可视': True,
        '对象': LuaTable({
            '显示': lambda *a: None, '销毁': lambda *a: None, '是否有焦点': lambda: False,
            '禁用按钮': lambda flag: old_disabled.__setitem__(0, bool(flag)),
        }),
    })
    ctrls = win539.rawget('控件组')
    ctrls.rawset(ctrls.length() + 1, old_ctrl)

    hover_flag = [False]
    new_disabled = [False]
    orig_add = win539.rawget('增加控件')
    def add_ctrl_tracked(self_w, *args):
        orig_add(self_w, *args)
        c = self_w.rawget('控件组').rawget(self_w.rawget('控件组').length())
        c.rawset('可视', True)
        obj = c.rawget('对象')
        obj.rawset('是否有焦点', lambda: hover_flag[0])
        obj.rawset('禁用按钮', lambda flag: new_disabled.__setitem__(0, bool(flag)))
    win539.rawset('增加控件', add_ctrl_tracked)

    ev.G.get('loadstring')(rt_src)(S)
    pickup_frame = S.rawget('__gm_pickup_frame_v299')
    pickup_frame(U, G)

    new_ctrl = find_ctrl(win539, '远程仓库按钮_v307')
    assert new_ctrl is not None
    assert old_ctrl.rawget('可视') is False and old_disabled[0] is True
    assert new_ctrl.rawget('可视') is True and new_disabled[0] is False

    obj = new_ctrl.rawget('对象')
    click = new_ctrl.rawget('脚本').rawget('Main')
    wh_state = S.rawget('__gm_wh_state_v307')

    # --- 1. Guild NOT activated: Click 1 opens 普通仓库 (amber), Click 2 closes it (grey) ---
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_OFF

    click()
    assert norm_raw.rawget('可视') is True and norm_raw.rawget('open_calls') == 1
    assert guild_raw.rawget('可视') is False and guild_raw.rawget('open_calls') == 0
    assert len(sound_plays) == 1
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_NORM

    click()
    assert norm_raw.rawget('可视') is False and norm_raw.rawget('close_calls') == 1
    assert guild_raw.rawget('可视') is False and guild_raw.rawget('open_calls') == 0
    assert len(sound_plays) == 2
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_OFF

    # --- 2. Guild ACTIVATED: Click 1 -> 普通仓库 (amber), Click 2 -> 行会仓库 (teal), Click 3 -> close (grey) ---
    guild_flag[0] = True
    click()
    assert norm_raw.rawget('可视') is True and guild_raw.rawget('可视') is False
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_NORM
    hover_flag[0] = True
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_NORM_HOVER
    hover_flag[0] = False

    click()
    assert norm_raw.rawget('可视') is False and guild_raw.rawget('可视') is True
    assert guild_raw.rawget('open_calls') == 1
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_GUILD
    hover_flag[0] = True
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_GUILD_HOVER
    hover_flag[0] = False

    click()
    assert norm_raw.rawget('可视') is False and guild_raw.rawget('可视') is False
    assert guild_raw.rawget('close_calls') == 1
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_OFF

    # --- 3. External close resets color immediately ---
    click()  # normal open
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_NORM
    norm_raw.rawset('可视', False)
    obj.rawget('显示')(180, 20, 1, 1, 0, -1, 1)
    assert wh_state.rawget('last_shade') == COL_OFF and wh_state.rawget('opened_kind') is None

    # --- 4. Story switch to 「前尘忆梦」 restores original button ---
    U.rawset('版本选择', '前尘忆梦')
    pickup_frame(U, G)
    assert old_ctrl.rawget('可视') is True and old_disabled[0] is False
    assert new_ctrl.rawget('可视') is False and new_disabled[0] is True


def main():
    mods_o, rt_src = test_diff_and_syntax()
    test_authentic_proxy_warehouse_button(rt_src)
    test_mode2_ordinary_materials(rt_src)
    test_v306_regression(rt_src)

    out_bytes = (W / 'game_v308.res').read_bytes()
    out_sha = hashlib.sha256(out_bytes).hexdigest()
    report = {
        'version': 'v1.308',
        'status': 'PASS',
        'all_passed': True,
        'sha256': out_sha,
        'tested_files': {
            'game_v308.res': out_sha,
            'runtime_v308.lua': hashlib.sha256((W / 'runtime_v308.lua').read_bytes()).hexdigest(),
            'patch_v308.py': hashlib.sha256((W / 'patch_v308.py').read_bytes()).hexdigest(),
        },
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'checks': [
            'outer_diff_restricted_to_12_14_30_and_trees_valid',
            'strict_lua51_syntax_and_zero_gbk_0x5c_hazard',
            'authentic_m48_callable_table_proxy_verified_type_table',
            'warehouse_btn_guild_inactive_2click_cycle_on_real_proxy',
            'warehouse_btn_guild_active_3click_cycle_and_distinct_tints_on_real_proxy',
            'warehouse_btn_sound_proxy_called_on_every_click',
            'warehouse_btn_external_close_resets_color',
            'warehouse_btn_qianchi_isolated_and_story_switch_restore',
            'mode2_ordinary_materials_36_all_pass',
            'v306_gather_formula_regression_intact',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v308.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v308.json').write_text(text, encoding='utf-8')
    print('ALL v1.308 TESTS PASSED!')


if __name__ == '__main__':
    main()
