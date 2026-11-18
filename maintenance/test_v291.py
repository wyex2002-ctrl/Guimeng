"""Exercise automatic poison with the game's compact control-list initialization."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from bytecode_relocate import BRANCHES
from ljdis import OPS
from ljtool import Proto
from native_test_utils import standalone, trees
from patch_v139 import W, ad, jump
from patch_v201 import set_string, unpack_config
from patch_v285 import BASE_SHA as V284_SHA
from patch_v291 import BASE_SHA, POWDER
from portal_routes_v213 import child_refs
from resource_tools import decode
from runtime import ensure_runtime
from test_v192 import lua
from test_v282 import MELEE, RANGED, OTHERS, find_config


def verify(old, new):
    for mid, dump in new.items():
        assert dump.rebuild() == dump.raw
        trees(dump)
        assert len(dump.protos) == len(old[mid].protos)
        for before, after in zip(old[mid].protos, dump.protos):
            if (mid, before.idx) == (12, POWDER):
                assert before.raw != after.raw
                globals_used = {after.gc(word >> 16) for word in after.bc
                                if OPS[word & 255] == 'GGET'}
                assert globals_used == {name.encode('gbk') for name in
                                        ('type', '分割文本', 'Gly独', 'Ux雌', 'FXru胃啪')}
                for pc, word in enumerate(after.bc):
                    if OPS[word & 255] in BRANCHES:
                        assert 0 <= pc + 1 + (word >> 16) - 32768 < after.nbc
                continue
            p = Proto(after.raw, after.idx)
            for slot, value in enumerate(p.kgc):
                if isinstance(value, bytes):
                    restored = value.replace(b'v1.291', b'v1.290')
                    if mid == 12 and p.idx in (76, 22198):
                        restored = restored.replace(b'1.291', b'1.290')
                    if restored != value:
                        set_string(p, p.nkgc - 1 - slot, restored)
            assert before.raw == p.rebuild(), (mid, p.idx)


def prepare(work, old, new, legacy):
    def export(modules, mid, idx, name, patches=None, params=None):
        d = modules[mid]
        (work / (name + '.ljbc')).write_bytes(
            standalone(d, trees(d), idx, patches, params))

    compared = [('old', old, 6468, 182), ('new', new, 6468, 182)]
    if legacy:
        compared.append(('legacy', legacy, 6467, 181))
    for label, modules, factory_id, layout_id in compared:
        export(modules, 26, len(modules[26].protos) - 1, 'class_' + label)
        export(modules, 26, 3, 'tick_' + label,
               {0: jump(0, 843, 3), 852: ad('RET0', 0, 1)})
        export(modules, 12, layout_id, 'layout_' + label,
               {0: jump(0, 456, 5), 498: ad('RET0', 0, 1)})
        db = modules[12]
        factory = db.protos[factory_id]
        refs = child_refs(db)
        for name, file, pc in [('施毒术', 'poison', 2630), ('施毒大法', 'area_poison', 3236)]:
            assert factory.gc(factory.bc[pc] >> 16) == f'【数据库/技能脚本/{name}】'.encode('gbk')
            assert OPS[factory.bc[pc - 2] & 255] == 'FNEW'
            export(modules, 12, refs[factory_id, factory.bc[pc - 2] >> 16], file + '_' + label)

    for mid, idx, name in [
        (20, 8, 'animation'), (20, 6, 'reverse'), (20, 21, 'reset'), (12, 4094, 'skill_factory'),
        (30, 43, 'rotate'), (14, 13, 'public_sys'), (14, 458, 'public_get'),
        (14, 423, 'dispatch'), (14, 301, 'gly_class'), (14, 340, 'hero_api'),
        (12, 46, 'manual_event'), (12, 254, 'powder_refill'), (12, 167, 'rank_update'),
        (22, 94, 'add_status'), (22, 91, 'list_status'), (46, 7, 'projectile'),
        (40, 20, 'buff_class'), (22, 56, 'monster_damage'),
    ]:
        export(new, mid, idx, name)
    export(new, 14, 420, 'sandbox', {
        0: ad('UGET', 11, 0), 1: ad('MOV', 12, 0), 2: jump(2, 562, 13), 571: ad('RET0', 0, 1),
    }, 1)
    export(new, 12, 143, 'ranks', {
        0: ad('TNEW', 1, 0), 1: jump(1, 2616, 2), 2631: ad('RET1', 1, 2),
    })
    export(new, 12, 728, 'poison_statuses', {
        0: ad('KNIL', 0, 25), 1: jump(1, 4329, 26), 5563: jump(5563, 30000, 26),
        30000: jump(30000, 51221, 26), 52455: ad('RET0', 0, 1),
    })
    p = new[12].protos[728]
    status_configs = {}
    for pc in (4329, 4946, 51221, 51838):
        fields = dict(p.gc(p.bc[pc] >> 16)[2])
        encoded = fields['配置项文本'.encode('gbk')]
        status_configs[encoded] = unpack_config(encoded)
    (work / 'poison_cfg.lua').write_bytes(('return ' + lua(status_configs)).encode('gbk'))
    lookup = new[12].protos[6468]
    configs = {name.encode('gbk'): find_config(lookup, name) for name in MELEE + RANGED + OTHERS}
    (work / 'configs.lua').write_bytes(('return ' + lua(configs)).encode('gbk'))
    (work / 'scripts.lua').write_text('return {}\n')


def regression_source():
    melee = (W / 'melee_regression_v210.lua').read_text().split("local melee={'普通攻击'")[0]
    melee = melee.replace("start('hotloop=1','hotexit=1')end", "start('hotloop=1','hotexit=1')else jit.off()end")
    prior = (W / 'auto_poison_regression_v282.lua').read_text()
    setup = prior.split('-- Every supported melee release')[0]
    # Reuse the native hit fixture with real slot initialization and buff logic.
    setup = setup.replace("版本选择 = '来世续缘',", "版本选择 = options.story,")
    setup = setup.replace("    local bag = {}", "    local bag, layout = {}, {}")
    setup = setup.replace("主角格子 = bag", "主角格子 = layout")
    setup = setup.replace("    owner.取包裹指定物品个数", """    local shortcut = options.story == '前尘忆梦' and 1 or 21
    for id = shortcut, shortcut + 5 do
        local name = '物品格子' .. id
        controls[#controls + 1] = {名称 = name, 类型 = 6, 格子ID = id}
        owner.tbl_controls[name] = {tbl = {道具 = nil}}
    end
    owner.取包裹指定物品个数""")
    setup = setup.replace("    eq(E.Sys, nil); eq(E.pcall, nil); eq(E._G, nil)",
                          """    eq(E.Sys, nil); eq(E.pcall, nil); eq(E._G, nil)
    load('layout_' .. version, E)()
    eq(#layout, 102, 'native compact list omits missing controls')
    eq(layout[7], bag[31], 'slot 31 is entry 7')
    eq(layout[31], bag[55], 'entry 31 is a different slot')
    eq(G.取控件对象('物品格子31'), bag[31], 'native getter preserves slot ID')
    eq(G.取控件对象('物品格子30'), nil)""")
    setup = setup.replace("        if op == 'fun' then",
                          "        if op == 'adds' then setfenv(first, E); return first() end\n        if op == 'fun' then")
    begin = setup.index('    N.类_BUFF图标类 =')
    end = setup.index('    s.skills[poison].脚本', begin)
    fixture, cases = (W / 'auto_poison_regression_v291.lua').read_text().split('-- Regression cases\n')
    setup = setup[:begin] + fixture + setup[end:]
    direct = prior.split('local function direct(s, name)')[1].split('-- Isolate native cooldown')[0]
    return melee + setup + 'local function direct(s, name)' + direct + cases


def main(runtime, v284_resource=None):
    work = W / 'native_work/v291'
    work.mkdir(parents=True, exist_ok=True)
    base, data = ((W / f'game_v{v}.res').read_bytes() for v in (290, 291))
    build = json.loads((W / 'build_v291.json').read_text())
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    assert hashlib.sha256(data).hexdigest() == build['sha256']
    before, old = decode(base, range(2, 86, 2))
    after, new = decode(data, range(2, 86, 2))
    assert before.protos[0].bc == after.protos[0].bc and base[-10:] == data[-10:]
    verify(old, new)
    legacy = None
    if v284_resource:
        history = v284_resource.read_bytes()
        assert hashlib.sha256(history).hexdigest() == V284_SHA
        _, legacy = decode(history, (12, 26))
    prepare(work, old, new, legacy)
    source = work / 'auto_poison.lua'
    source.write_bytes(regression_source().encode('gbk'))
    runs = []
    for mode in ('normal', 'hot'):
        command = [runtime, str(source), str(work), mode]
        if legacy:
            command.append('legacy')
        result = subprocess.run(command, capture_output=True, timeout=60)
        output = (result.stdout + result.stderr).decode('gbk', 'replace')
        (work / f'{mode}.log').write_text(output)
        assert result.returncode == 0 and 'AUTO_POISON_V291_PASS' in output, (mode, output)
        print(output, end='', flush=True)
        runs.append({'mode': mode, 'output': output})
    names = ('patch_v291.py', 'test_v291.py', 'auto_poison_regression_v291.lua',
             'poison_powder_v291.lua', 'poison_powder_v291.ljbc', 'melee_regression_v210.lua',
             'auto_poison_regression_v282.lua')
    report = {'version': 'v1.291', 'all_passed': True, 'sha256': build['sha256'],
              'v284_original_class_callback_and_layout_checked': bool(legacy),
              'runs': runs, 'all_42_modules_checked': True, 'full_windows_game_run': False,
              'tested_files': {name: hashlib.sha256((W / name).read_bytes()).hexdigest() for name in names}}
    (W / 'validation_v291.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    parser.add_argument('--v284-resource', type=Path)
    args = parser.parse_args()
    main(args.runtime or str(ensure_runtime()), args.v284_resource)
