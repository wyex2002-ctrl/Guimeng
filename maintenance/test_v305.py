"""Exhaustive verification suite for v1.305:
- Outer resource diff restricted strictly to modules [12, 14, 30] + rebuild + trees()
- Strict Lua 5.1 syntax parse + GBK 0x5C hazard check on updated 14/428 gc 230 (【一键出售】)
- End-to-end execution of 【一键出售】 script extracted from game_v305.res:
  * In 「来世续缘」: sells all 36 ordinary-mob corpse-dig materials (including stacked quantities),
    equipment, and skill books; displays accurate breakdown prompt; pays exact half-price * quantity
  * Strictly keeps Boss / rare / quest / seal items (沃玛号角/精灵骸骨/飞龙剑碎片/火影晶体/震天魔印/商会物资/火之印记),
    potions, Blessing Oil, and any item with 禁止出售=true
  * In 「前尘忆梦」: does NOT sell ordinary-mob materials (100% untouched)
"""
import hashlib
import json
from pathlib import Path

from ljtool import Dump
from lua51_eval import LuaEvaluator, LuaTable, syntax_check
from native_test_utils import trees
from patch_v305 import ORDINARY_MOB_MATERIALS
from resource_tools import decode

W = Path(__file__).resolve().parent
BASE_SHA = '3cea4fe6937d0fe9071d55ecb599d7155a2d4251cda56e50793fb6438d54b033'


def run_bulk_sale_scenario(src, story, bag_items):
    """Execute the real 14/428 gc 230 【一键出售】 script end-to-end in LuaEvaluator."""
    ev = LuaEvaluator()

    notices = []
    payments = []
    prompt_captured = []

    def make_label(w, h, *rest):
        lbl = LuaTable()
        lbl.rawset('置标题', lambda *a: 14)
        lbl.rawset('置背景色', lambda *a: None)
        lbl.rawset('显示', lambda *a: None)
        lbl.rawset('销毁', lambda *a: None)
        return lbl

    close_ctrl = LuaTable({'名称': '单图按钮1', '类型': 10, 'x': 200, 'y': 200, 'w': 20, 'h': 20})
    sort_ctrl = LuaTable({'名称': '按钮16', '类型': 10, 'x': 120, 'y': 200, 'w': 40, 'h': 20})
    bag_win = LuaTable({
        '名称': '背包窗口', '可视': True, '窗口宽度': 280,
        '坐标': LuaTable({'x': 100, 'y': 100}),
        '控件组': LuaTable([close_ctrl, sort_ctrl]),
    })

    # Build bag slots & models
    models = LuaTable()
    boxes = {}
    hero_slots = LuaTable()
    for idx, spec in enumerate(bag_items, 1):
        slot_id = 100 + idx
        it = LuaTable(spec)
        model = LuaTable({'道具': it})
        models.rawset(slot_id, model)

        def make_reset(m):
            def reset_fn(val):
                m.rawset('道具', val)
            return reset_fn

        boxes[slot_id] = LuaTable({'重置道具': make_reset(model)})
        hero_slots.rawset(idx, LuaTable({1: slot_id, 2: idx, 3: True}))

    hero = LuaTable({'背包格子': hero_slots})

    dialog = LuaTable({'可视': False})

    def show_confirm(prompt, confirm_cb, cancel_cb):
        prompt_captured.append(prompt)
        dialog.rawset('可视', True)
        dialog.rawset('确定_回调方法', confirm_cb)

    U = LuaTable({
        '版本选择': story,
        '托管显示': LuaTable({'屏幕提示': lambda text, *a: notices.append(text)}),
        '窗口相关': LuaTable({'界面切换': lambda val, *a: payments.append(val)}),
    })
    G = LuaTable({
        '取控件对象': lambda name: bag_win if name == '背包窗口' else None,
        '从ID取格子': lambda sid: boxes.get(sid),
        '询问': show_confirm,
    })

    S = LuaTable({
        'get': lambda k: (
            LuaTable([bag_win]) if k == 'item_box' else
            make_label if k == 'win_tex' else
            hero if k == 'hero' else
            models if k == 'item_arr' else None
        ),
    })

    mouse_down = [False]
    mouse_up = [False]
    ev.G.rawset('Sys', S)
    ev.G.rawset('Ae冻集', LuaTable({'屏幕焦点': True, '游戏暂停': False, '逻辑暂停': 0, '鼠标_屏幕坐标': LuaTable({'x': 275, 'y': 310})}))
    ev.G.rawset('Q_提示框', dialog)
    ev.G.rawset('Q_鼠标', LuaTable({'被占用': False}))
    ev.G.rawset('Q_文字', LuaTable({'取宽度': lambda *a: 24, '取高度': lambda *a: 12}))
    ev.G.rawset('ARGB', lambda a, r, g, b: (a << 24) | (r << 16) | (g << 8) | b)
    ev.G.rawset('取鼠标左键按下', lambda: mouse_down[0])
    ev.G.rawset('取鼠标左键弹起', lambda: mouse_up[0])

    dispatch = ev.G.get('loadstring')(src)()
    # Frame 1: install button
    dispatch(U, G, False)
    btn_ctrl = bag_win.rawget('__gm_inventory_sell_button_v150')
    assert isinstance(btn_ctrl, LuaTable), 'Button was not installed'
    btn_obj = btn_ctrl.rawget('对象')

    # Click button (mouse down then up inside button bounds)
    bx = 100 + btn_ctrl.rawget('x') + 5
    by = 100 + btn_ctrl.rawget('y') + 5
    mouse_down[0] = True
    mouse_up[0] = False
    btn_obj.rawget('更新')(bx, by)
    mouse_down[0] = False
    mouse_up[0] = True
    btn_obj.rawget('更新')(bx, by)

    # Confirm if dialog opened
    if dialog.rawget('可视') and callable(dialog.rawget('确定_回调方法')):
        dialog.rawget('确定_回调方法')()

    remaining = []
    for idx in range(1, len(bag_items) + 1):
        slot_id = 100 + idx
        it = models.rawget(slot_id).rawget('道具')
        if it is not None:
            remaining.append(it.rawget('名称'))
    return remaining, payments, prompt_captured, notices


def main():
    base_bytes = (W / 'game_v304.res').read_bytes()
    out_bytes = (W / 'game_v305.res').read_bytes()
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

    src = mods_o[14].protos[428].gc(230).decode('gbk')
    syntax_check(src)
    for ch in src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'

    # Test 1: 「来世续缘」 sells all 36 ordinary-mob materials + equip + skill book,
    # while keeping Boss/rare/quest/seal items, potions, oil, and 禁止出售 items!
    bag = [
        {'名称': '裁决之杖', '分类': '装备', '价格': 1000, '数量': 1},
        {'名称': '火球术', '分类': '道具', '价格': 400, '数量': 1},
        {'名称': '猪肉', '分类': '道具', '价格': 120, '数量': 5},
        {'名称': '毒蜘蛛牙齿', '分类': '材料', '价格': 60, '数量': 10},
        {'名称': '僵尸骨头', '分类': '道具', '价格': 80, '数量': 2},
        {'名称': '鹿茸', '分类': '道具', '价格': 200, '数量': 1},
        # Protected / must keep:
        {'名称': '鸡肉', '分类': '道具', '价格': 100, '数量': 1, '禁止出售': True},
        {'名称': '沃玛号角', '分类': '道具', '价格': 500, '数量': 1},
        {'名称': '精灵骸骨', '分类': '道具', '价格': 500, '数量': 1},
        {'名称': '飞龙剑碎片', '分类': '道具', '价格': 500, '数量': 1},
        {'名称': '火影晶体', '分类': '道具', '价格': 500, '数量': 1},
        {'名称': '震天魔印', '分类': '道具', '价格': 500, '数量': 1},
        {'名称': '商会物资', '分类': '道具', '价格': 500, '数量': 1},
        {'名称': '火之印记', '分类': '道具', '价格': 500, '数量': 1},
        {'名称': '祝福油', '分类': '道具', '价格': 2000, '数量': 1},
        {'名称': '金创药(大)', '分类': '道具', '价格': 100, '数量': 20},
    ]
    rem, pays, prompts, notices = run_bulk_sale_scenario(src, '来世续缘', bag)
    assert rem == [
        '鸡肉', '沃玛号角', '精灵骸骨', '飞龙剑碎片', '火影晶体',
        '震天魔印', '商会物资', '火之印记', '祝福油', '金创药(大)',
    ], f'Unexpected remaining items: {rem}'
    # Expected gold: 500 + 200 + 60*5 + 30*10 + 40*2 + 100 = 1480
    assert sum(pays) == 1480, f'Expected 1480 gold, got {sum(pays)} ({pays})'
    assert '背包内装备：1件' in prompts[0]
    assert '技能书：1本' in prompts[0]
    assert '普通怪材料：18个' in prompts[0]
    assert '合计获得：1480金币' in prompts[0]

    # Test 2: Verify EVERY ONE of the 36 ordinary mob materials is sellable in 「来世续缘」
    all_mat_bag = [{'名称': nm, '分类': '道具', '价格': 100, '数量': 1} for nm in ORDINARY_MOB_MATERIALS]
    rem_all, pays_all, prompts_all, _ = run_bulk_sale_scenario(src, '来世续缘', all_mat_bag)
    assert rem_all == [], f'Some ordinary mob materials were not sold: {rem_all}'
    assert sum(pays_all) == 50 * len(ORDINARY_MOB_MATERIALS)
    assert f'普通怪材料：{len(ORDINARY_MOB_MATERIALS)}个' in prompts_all[0]

    # Test 3: 「前尘忆梦」 isolation — MUST NOT sell ordinary mob materials!
    old_bag = [
        {'名称': '猪肉', '分类': '道具', '价格': 120, '数量': 5},
        {'名称': '毒蜘蛛牙齿', '分类': '道具', '价格': 60, '数量': 10},
    ]
    rem_old, pays_old, prompts_old, notices_old = run_bulk_sale_scenario(src, '前尘忆梦', old_bag)
    assert rem_old == ['猪肉', '毒蜘蛛牙齿'] and pays_old == [] and prompts_old == []

    out_sha = hashlib.sha256(out_bytes).hexdigest()
    tested_files = {
        fname: hashlib.sha256((W / fname).read_bytes()).hexdigest()
        for fname in ('game_v305.res', 'patch_v305.py', 'test_v305.py')
    }
    report = {
        'version': 'v1.305',
        'all_passed': True,
        'status': 'PASS',
        'sha256': out_sha,
        'tested_files': tested_files,
        'checks': [
            'Outer resource diff restricted strictly to modules [12, 14, 30] + rebuild + trees()',
            'Strict Lua 5.1 syntax parse + GBK 0x5C scan on updated 14/428 gc 230 (【一键出售】)',
            'End-to-end 【一键出售】 test in 「来世续缘」: all 36 ordinary-mob corpse-dig materials sold (incl. stacked quantities) with exact half-price calculation & breakdown prompt',
            'Boss/rare/quest/seal items (沃玛号角/精灵骸骨/飞龙剑碎片/火影晶体/震天魔印/商会物资/印记), potions, Blessing Oil, and 禁止出售 items strictly kept',
            '「前尘忆梦」 100% isolated (ordinary-mob materials not sold)',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v305.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v305.json').write_text(text, encoding='utf-8')
    print('ALL v1.305 CHECKS PASSED!')


if __name__ == '__main__':
    main()
