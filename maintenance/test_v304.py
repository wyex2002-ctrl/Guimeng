"""Exhaustive verification suite for v1.304:
- Strict 类_地图物品类_.lua:696 ground-render guard: every dropped item MUST carry live 地面精灵 or 精灵
  restored from S.游戏道具组[名称] (even when parsed table from 附加.挖取 had nil/corrupted sprite fields)
- Strict 14/502 数据保护(nil) guard: 附加 and 属性 must be non-nil plain tables and template tables untouched
- Custom serialized fields (品质, 价格, rolled equipment affixes) preserved intact over template defaults
- Re-runs v1.303 ranged assassin merc blink-behind-locked-target & 3s cooldown checks
"""
import hashlib
import json
import math
from pathlib import Path

from ljtool import Dump
from lua51_eval import LuaTable, syntax_check
from native_test_utils import trees
from patch_v139 import ad
from resource_tools import decode
from test_v300 import make_env
from test_v301 import V301VM
from test_v303 import test_merc_blink_behind_locked_target_and_rewrap

W = Path(__file__).resolve().parent
BASE_SHA = 'd851e51c7709f7012d881bbc873a96beb1a39ec0833552db38135f949bc809d5'


def extract_runtime_v304(m14):
    p = m14.protos[781]
    hits = [v for v in p.kgc if isinstance(v, bytes) and v.startswith(b'-- Guimeng v1.304 runtime helper')]
    assert len(hits) == 1, f'Expected 1 runtime_v304.lua string in 14/781, found {len(hits)}'
    return hits[0].decode('gbk')


def test_diff_syntax_and_cd():
    base_bytes = (W / 'game_v303.res').read_bytes()
    out_bytes = (W / 'game_v304.res').read_bytes()
    assert hashlib.sha256(base_bytes).hexdigest() == BASE_SHA

    outer_b, mods_b = decode(base_bytes, (12, 14, 22, 30))
    outer_o, mods_o = decode(out_bytes, (12, 14, 22, 30))

    root_b, root_o = outer_b.protos[0], outer_o.protos[0]
    changed_slots = [i for i in range(root_b.nkgc) if root_b.gc(i) != root_o.gc(i)]
    assert changed_slots == [12, 14, 30], f'Expected only [12, 14, 30] changed, got {changed_slots}'
    for mid in (12, 14, 30):
        ro = mods_o[mid].rebuild()
        assert Dump(ro).rebuild() == ro
        trees(mods_o[mid])

    # Confirm 3s cooldown intact in 12/18045 & 12/18047
    assert mods_o[12].protos[18045].bc[117] == ad('KSHORT', 17, 3)
    assert mods_o[12].protos[18045].bc[118] == ad('KSHORT', 18, 3)
    assert mods_o[12].protos[18047].bc[103] == ad('KSHORT', 12, 3)
    assert mods_o[12].protos[18047].bc[104] == ad('KSHORT', 13, 3)

    rt_src = extract_runtime_v304(mods_o[14])
    syntax_check(rt_src)
    for ch in rt_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'
    return mods_o, rt_src


def test_corpse_drop_live_sprites(m22, rt_src):
    """Verify 类_地图物品类_.lua:696 ground rendering + 数据保护(nil) protection for 猪肉/鸡肉/赤龙宝甲_男."""
    p97 = m22.protos[97]

    def run_death(story, monster_name, dig_items, item_db):
        env = make_env(story=story)
        ev, S = env['ev'], env['S']
        ev.G.rawset('Gly独', None)
        ev.G.rawset('文本加解密', None)
        ss = S.rawget('script_setting')

        # Populate live S.游戏道具组 (mirroring both entry.数据 and direct entry forms)
        db_tbl = S.rawget('游戏道具组')
        for name, spec in item_db.items():
            db_tbl.rawset(name, spec)

        item_store = {}
        ss.rawset('文本加解密', lambda raw, key: raw[4:] if raw.startswith('ENC:') else raw)
        ss.rawset('table', LuaTable({'loadstring': lambda plain: item_store[plain]}))

        dig_tbl = LuaTable()
        for idx, it in enumerate(dig_items, 1):
            token = f'ITEM_{idx}'
            item_store[token] = LuaTable(it)
            dig_tbl.rawset(idx, 'ENC:' + token)

        pub_obj = LuaTable({
            '属性': LuaTable({'名称': monster_name}),
            '附加': LuaTable({'挖取': dig_tbl}),
        })
        ss.rawset('Gly独', LuaTable({'事件对象': lambda aid: pub_obj if aid == 9001 else None}))

        ev.G.get('loadstring')(rt_src)(S)
        raw_actor_lua = LuaTable({'id': 9001, '属性': LuaTable({'名称': monster_name})})
        dropped = []

        def shallow_copy(o):
            if isinstance(o, dict):
                return dict(o)
            if isinstance(o, LuaTable):
                return dict(o._data)
            return o

        def sys_run(name, *args):
            if name == '数据保护':
                if args[0] is None:
                    raise RuntimeError('内存保护() 参数为nil,请检查！')
                return args[0]
            if name == '掉落物前置处理':
                return (False, args[3], args[2])
            if name == '掉落物品':
                item_obj = args[1]
                # STRICT 类_地图物品类_.lua:696 RENDER SIMULATION!
                sprite = item_obj.get('地面精灵') or item_obj.get('精灵')
                if sprite is None:
                    raise RuntimeError("类_地图物品类_.lua:696: attempt to index field '精灵' (a nil value)")
                assert isinstance(sprite, LuaTable) and callable(sprite.rawget('显示_高级'))
                dropped.append({'item': item_obj, 'count': args[2]})
                return None
            return None

        has_fn = ev.G.get('__gm_corpse_has_v301')
        drop_fn = ev.G.get('__gm_corpse_drop_v301')

        def vm_drop(actor, drops):
            drops_lua = LuaTable()
            for i in range(1, len(drops) + 1):
                if i in drops:
                    drops_lua.rawset(i, drops[i])
            added = drop_fn(raw_actor_lua, drops_lua)
            for i in range(len(drops) + 1, drops_lua.length() + 1):
                entry = drops_lua.rawget(i)
                # Keep live LuaTable sprite handles intact across boundary just like real LuaJIT!
                it_raw = entry.rawget('物品道具')
                drops[i] = {
                    '物品道具': dict(it_raw._data),
                    '掉落数量': entry.rawget('掉落数量'),
                }
            return added

        actor_vm = {
            'id': 9001,
            '宠物配置': {'掉落物品': True},
            '属性': {'名称': monster_name, '掉宝数据表': {}, '掉宝倍数': 1},
            '地图格子': {'x': 100, 'y': 100},
        }
        vm_globals = {
            '引擎': {'置随机数种子': lambda *a: None, '取随机整数': lambda s, a, b: int(a)},
            'Gly独': {'取随机数': lambda a, b: a},
            'Ux雌': {'版本选择': story},
            'Q_地图': {'取格子信息': lambda x, y, k: 0},
            'Sys': {'run': sys_run},
            'table': {'insert': lambda t, v: t.__setitem__(len(t) + 1, v), 'copy': shallow_copy, 'sort': lambda *a: None},
            'math': {'floor': math.floor, 'ceil': math.ceil, 'abs': abs},
            'tonumber': lambda x: int(x),
            'lookupHelixNumber': lambda dx, dy: dx * dx + dy * dy,
            '__gm_corpse_has_v301': lambda a: bool(has_fn(raw_actor_lua)),
            '__gm_corpse_drop_v301': vm_drop,
        }
        vm = V301VM(vm_globals, child_handlers={36: lambda drops: None, 27: lambda a, b: a[1] < b[1]})
        vm.run_proto(p97, actor_vm)
        return dropped, pub_obj.rawget('附加').rawget('挖取').length()

    live_pig_sprite = LuaTable({'显示_高级': lambda *a: 'OK_PIG'})
    live_armor_ground = LuaTable({'显示_高级': lambda *a: 'OK_ARMOR_GROUND'})
    live_armor_bag = LuaTable({'显示_高级': lambda *a: 'OK_ARMOR_BAG'})

    item_db = {
        # Wrapped in entry.数据 (real S.游戏道具组 format!) with ONLY 精灵 (no 地面精灵, just like 猪肉!)
        '猪肉': LuaTable({'数据': LuaTable({
            '名称': '猪肉', '显示名': '猪肉', '分类': '道具', '精灵': live_pig_sprite,
            '附加': LuaTable({'品质': 1}), '属性': LuaTable(),
        })}),
        # Equipment with both 地面精灵 & 精灵
        '赤龙宝甲_男': LuaTable({'数据': LuaTable({
            '名称': '赤龙宝甲_男', '显示名': '赤龙宝甲(男)', '分类': '装备', '子类': '衣服',
            '地面精灵': live_armor_ground, '精灵': live_armor_bag,
            '附加': LuaTable(), '属性': LuaTable({'防御': 5}),
        })}),
    }

    # 1. 猪 drops 猪肉 (serialized without 精灵 or 属性, carrying rolled 品质=9 & 价格=180)
    d1, rem1 = run_death('来世续缘', '猪', [
        {'名称': '猪肉', '分类': '道具', '价格': 180, '附加': LuaTable({'品质': 9})},
    ], item_db)
    assert len(d1) == 1 and rem1 == 0
    pig_it = d1[0]['item']
    assert pig_it['精灵'] is live_pig_sprite, 'Must restore live 精灵 handle from S.游戏道具组!'
    assert pig_it['附加'].rawget('品质') == 9, 'Must preserve rolled 品质 from 附加.挖取!'
    assert pig_it['价格'] == 180
    # Ensure template 品质 was NOT mutated
    assert item_db['猪肉'].rawget('数据').rawget('附加').rawget('品质') == 1

    # 2. 赤龙魔王 drops rolled 赤龙宝甲_男 (even if serialized table had garbage string in 精灵)
    d2, rem2 = run_death('来世续缘', '赤龙魔王', [
        {'名称': '赤龙宝甲_男', '分类': '装备', '精灵': 'CORRUPT', '显示名': '赤龙宝甲(男)',
         '附加': LuaTable({'条数': 5}), '属性': LuaTable({'防御': 12})},
    ], item_db)
    assert len(d2) == 1 and rem2 == 0
    arm_it = d2[0]['item']
    assert arm_it['地面精灵'] is live_armor_ground and arm_it['精灵'] is live_armor_bag
    assert arm_it['附加'].rawget('条数') == 5 and arm_it['属性'].rawget('防御') == 12

    # 3. Item missing from S.游戏道具组 (no sprite) is safely skipped instead of crashing!
    d3, rem3 = run_death('来世续缘', '未知怪', [{'名称': '不存在的物品', '分类': '道具'}], item_db)
    assert d3 == [] and rem3 == 0

    # 4. 「前尘忆梦」 untouched
    d4, rem4 = run_death('前尘忆梦', '猪', [{'名称': '猪肉', '分类': '道具'}], item_db)
    assert d4 == [] and rem4 == 1


def main():
    mods_o, rt_src = test_diff_syntax_and_cd()
    test_corpse_drop_live_sprites(mods_o[22], rt_src)
    test_merc_blink_behind_locked_target_and_rewrap(rt_src)

    out_sha = hashlib.sha256((W / 'game_v304.res').read_bytes()).hexdigest()
    tested_files = {
        fname: hashlib.sha256((W / fname).read_bytes()).hexdigest()
        for fname in ('game_v304.res', 'runtime_v304.lua', 'patch_v304.py', 'test_v304.py')
    }
    report = {
        'version': 'v1.304',
        'all_passed': True,
        'status': 'PASS',
        'sha256': out_sha,
        'tested_files': tested_files,
        'checks': [
            'Outer resource diff restricted strictly to modules [12, 14, 30] + rebuild + trees()',
            'Strict Lua 5.1 syntax parse + GBK 0x5C scan on embedded runtime_v304.lua',
            'Strict 类_地图物品类_.lua:696 ground-sprite render test + 14/502 内存保护(nil) guard: 猪肉 & 赤龙宝甲_男 restore live 地面精灵/精灵 handles from S.游戏道具组 while keeping rolled 品质/affixes; missing-sprite items safely skipped; 前尘忆梦 isolated',
            'Ranged assassin merc blink behind locked target + auto-rewrap + 3s cooldown regression passed',
        ],
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v304.json').write_text(text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v304.json').write_text(text, encoding='utf-8')
    print('ALL v1.304 CHECKS PASSED!')


if __name__ == '__main__':
    main()
