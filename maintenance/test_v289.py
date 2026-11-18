"""Check resource scope and exercise affected LuaJIT gameplay entry points."""
import argparse
import hashlib
import json
import subprocess

from bytecode_relocate import BRANCHES
from ljdis import OPS
from ljtool import Proto
from native_test_utils import standalone, trees
from patch_v139 import W, ad, jump
from patch_v201 import set_string
from patch_v289 import BASE_SHA, HEALS
from resource_tools import decode
from runtime import ensure_runtime
from test_v192 import lua
from test_v282 import MELEE, RANGED, OTHERS, find_config


def verify(old, new):
    allowed = {12: {46, *HEALS, 6468}, 14: {427}, 22: {96}, 26: {53, 54, 55, 98}}
    helpers = {22: (96, 1), 26: (98, 10)}
    for mid, dump in new.items():
        assert dump.rebuild() == dump.raw
        trees(dump)
        start, count = helpers.get(mid, (0, 0))
        aligned = dump.protos[:start] + dump.protos[start + count:]
        assert len(aligned) == len(old[mid].protos)
        for p, q in zip(old[mid].protos, aligned):
            if p.idx in allowed.get(mid, ()):
                assert p.raw != q.raw
                continue
            restored = Proto(q.raw, p.idx)
            for slot, v in enumerate(restored.kgc):
                if isinstance(v, bytes):
                    back = v.replace(b'v1.289', b'v1.288')
                    if mid == 12 and p.idx in (76, 22198):
                        back = back.replace(b'1.289', b'1.288')
                    if back != v:
                        set_string(restored, p.nkgc - 1 - slot, back)
            assert restored.rebuild() == p.raw, (mid, p.idx)
        for q in dump.protos:
            for pc, word in enumerate(q.bc):
                if OPS[word & 255] in BRANCHES:
                    assert 0 <= pc + 1 + (word >> 16) - 32768 < q.nbc, (mid, q.idx, pc)


def fixtures(old, new, work):
    subtrees = {m: trees(d) for m, d in new.items()}

    def export(mid, idx, name, patches=None, params=None):
        (work / (name + '.ljbc')).write_bytes(
            standalone(new[mid], subtrees[mid], idx, patches, params))

    export(26, len(new[26].protos) - 1, 'class_new')
    export(26, 3, 'tick_new', {0: jump(0, 843, 3), 852: ad('RET0', 0, 1)})
    for mid, idx, name in [
        (20, 8, 'animation'), (20, 6, 'reverse'), (20, 21, 'reset'),
        (12, 4094, 'skill_factory'), (12, 46, 'manual_event'),
        (12, 4504, 'heal_single'), (12, 4517, 'heal_group'), (12, 370, 'heal_status'),
        (12, 4590, 'poison_new'), (12, 4603, 'area_poison_new'),
        (12, 254, 'powder_refill'), (12, 348, 'green_status'), (12, 353, 'red_status'),
        (12, 167, 'rank_update'), (12, 157, 'currency_early'), (12, 194, 'currency_late'),
        (14, 13, 'public_sys'), (14, 458, 'public_get'), (14, 423, 'dispatch'),
        (14, 301, 'gly_class'), (14, 340, 'hero_api'), (14, 500, 'data_protection'),
        (26, 64, 'hero_add_status'), (22, 94, 'add_status'), (22, 91, 'list_status'),
        (30, 43, 'rotate'), (30, 81, 'native_range'), (30, 97, 'helix'), (36, 9, 'skill_slot'), (46, 7, 'projectile'),
        (22, 97, 'monster_drop'),
    ]:
        export(mid, idx, name)
    export(14, 420, 'sandbox', {0: ad('UGET', 11, 0), 1: ad('MOV', 12, 0),
                                2: jump(2, 562, 13), 571: ad('RET0', 0, 1)}, 1)
    export(12, 143, 'ranks', {0: ad('TNEW', 1, 0), 1: jump(1, 2489, 2),
                              2631: ad('RET1', 1, 2)})
    for idx, label in ((4504, 'single'), (4517, 'group')):
        (work / f'heal_{label}_old.ljbc').write_bytes(
            standalone(old[12], trees(old[12]), idx))
    for mid in (12, 14, 22, 26, 30):
        (work / f'module_{mid}.ljbc').write_bytes(new[mid].raw)
    db = new[12].protos[6468]
    configs = {name.encode('gbk'): find_config(db, name)
               for name in MELEE + RANGED + OTHERS + ('治愈术', '群体治愈术')}
    (work / 'configs.lua').write_bytes(('return ' + lua(configs)).encode('gbk'))
    (work / 'scripts.lua').write_text('return {}\n')
    for slot, extra in ((1266, '白莲'), (1277, '红莲'), (1295, '月桂'), (1306, None), (1352, None)):
        before, after = (d[12].protos[6468].gc(slot).decode('gbk')
                         for d in (old, new))
        assert before.splitlines()[:5] == after.splitlines()[:5]
        assert '瞬移到怪物背后' in after
        if extra:
            assert f'使用【{extra}】后，造成额外伤害。' in after
        assert ('根据最大魔法值' in after) == (slot != 1352)
        assert ('连招' in before) == ('连招' in after)
        assert db.gc(slot + 1) == old[12].protos[6468].gc(slot + 1)
    (work / 'bag_sale.lua').write_bytes(new[14].protos[427].gc(230))


def main(runtime):
    work = W / 'native_work/v289'
    work.mkdir(parents=True, exist_ok=True)
    base, data = ((W / f'game_v{v}.res').read_bytes() for v in (288, 289))
    build = json.loads((W / 'build_v289.json').read_text())
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    assert hashlib.sha256(data).hexdigest() == build['sha256']
    before, old = decode(base, range(2, 86, 2))
    after, new = decode(data, range(2, 86, 2))
    assert before.protos[0].bc == after.protos[0].bc and base[-10:] == data[-10:]
    verify(old, new)
    fixtures(old, new, work)

    melee = (W / 'melee_regression_v210.lua').read_text().split("local melee={'普通攻击'")[0]
    melee = melee.replace("if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end",
                          "if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')else jit.off()end")
    common = (W / 'auto_poison_regression_v282.lua').read_text().split('-- Every supported melee release')[0]
    common = common.replace("if op == 'qs_skill_drop' and (first[4] == poison or first[4] == '施毒大法') and first[1] == 0 then",
                            "if op == 'qs_skill_drop' and first[1] == 0 then")
    regression = 'treatment_loot_regression_v289.lua'
    source = work / 'treatment_loot.lua'
    source.write_bytes((melee + common + (W / regression).read_text()).encode('gbk'))
    runs = []
    for mode in ('normal', 'hot'):
        result = subprocess.run([runtime, str(source), str(work), mode],
                                capture_output=True, timeout=90)
        output = (result.stdout + result.stderr).decode('gbk', 'replace')
        (work / f'{mode}.log').write_text(output)
        assert result.returncode == 0 and 'TREATMENT_LOOT_V289_PASS' in output, (mode, output)
        print(output, end='', flush=True)
        runs.append({'mode': mode, 'output': output})
    names = ('patch_v289.py', 'test_v289.py', regression, 'healing_lock_v289.lua',
             'healing_lock_v289.ljbc', 'monster_drop_filter_v289.lua',
             'monster_drop_filter_v289.ljbc', 'melee_regression_v210.lua',
             'auto_poison_regression_v282.lua')
    report = {'version': 'v1.289', 'all_passed': True, 'sha256': build['sha256'],
              'runs': runs, 'all_42_modules_checked': True,
              'full_windows_game_run': False,
              'tested_files': {n: hashlib.sha256((W / n).read_bytes()).hexdigest() for n in names}}
    (W / 'validation_v289.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    args = parser.parse_args()
    main(args.runtime or str(ensure_runtime()))
