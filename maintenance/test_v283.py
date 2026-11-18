"""Verify v1.283 against the shipped resource and exercised native routes."""
import argparse
import hashlib
import json
import subprocess

from bytecode_relocate import BRANCHES
from ljdis import OPS
from ljtool import Proto
from native_test_utils import standalone, trees
from patch_v139 import W, encstr, jump, rebuild_proto
from patch_v283 import BASE_SHA, LOW_MANA
from resource_tools import decode
from runtime import ensure_runtime
from test_v282 import export_fixtures, verify_original_instructions


def main(runtime):
    work = W / 'native_work/v283'
    work.mkdir(parents=True, exist_ok=True)
    base = (W / 'game_v282.res').read_bytes()
    data = (W / 'game_v283.res').read_bytes()
    build = json.loads((W / 'build_v283.json').read_text())
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    assert hashlib.sha256(data).hexdigest() == build['sha256']
    _, prior = decode((W / 'game_v281.res').read_bytes(), range(2, 86, 2))
    _, old = decode(base, range(2, 86, 2))
    _, new = decode(data, range(2, 86, 2))
    changed = {12: {46, 193}, 14: {427}, 26: {87, *range(89, 98)}}
    for mid, dump in new.items():
        trees(dump)
        assert dump.rebuild() == dump.raw and len(dump.protos) == len(old[mid].protos)
        for p, q in zip(old[mid].protos, dump.protos):
            for pc, op in enumerate(q.bc):
                if OPS[op & 255] in BRANCHES:
                    assert 0 <= pc + 1 + (op >> 16) - 32768 < q.nbc
            if p.idx in changed.get(mid, ()):
                continue
            q = Proto(q.raw, q.idx)
            for slot, value in enumerate(q.kgc):
                if isinstance(value, bytes):
                    back = value.replace(b'v1.283', b'v1.282')
                    if mid == 12 and q.idx in (76, 22197):
                        back = back.replace(b'1.283', b'1.282')
                    q.kgc[slot], q.kraw[slot] = back, encstr(back)
            assert rebuild_proto(q) == p.raw, (mid, q.idx)
    a, b = old[12].protos[46], new[12].protos[46]
    assert a.kgc == b.kgc and len(a.bc) == len(b.bc)
    for i, op in enumerate(a.bc):
        assert b.bc[i] == (jump(i, LOW_MANA[i], 7) if i in LOW_MANA else op)
    verify_original_instructions(old[12].protos[193], new[12].protos[193], {34: (2, 0), 49: (2, 0)})
    assert old[14].protos[427].bc == new[14].protos[427].bc

    export_fixtures(prior, new, work)
    for versions, index, name in [(old, 46, 'selector_previous'), (new, 193, 'currency'),
                                   (old, 193, 'currency_previous'), (new, 156, 'currency_first_story'),
                                   (new, 6481, 'pickup_callback')]:
        d = versions[12]
        (work / (name + '.ljbc')).write_bytes(standalone(d, trees(d), index))
    d = old[26]
    (work / 'class_previous.ljbc').write_bytes(standalone(d, trees(d), 100))
    (work / 'tick_previous.ljbc').write_bytes((work / 'tick_new.ljbc').read_bytes())
    for name in ('poison', 'area_poison'):
        (work / (name + '_previous.ljbc')).write_bytes((work / (name + '_new.ljbc')).read_bytes())
    (work / 'range_pickup.lua').write_bytes(new[14].protos[427].gc(222))

    melee = (W / 'melee_regression_v210.lua').read_text().split("local melee={'普通攻击'")[0]
    melee = melee.replace("if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end",
                          "if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')else jit.off()end")
    poison = (W / 'auto_poison_regression_v282.lua').read_text()
    poison = poison.replace("        if op == 'qs_skill_drop' and (first[4] == poison",
                            """        if op == 'qs_skill_drop' and first[1] == 5 and options.nativeSelect then
            return run('fun', manual, first)
        end
        if op == 'qs_skill_drop' and (first[4] == poison""", 1)
    source = work / 'combat.lua'
    source.write_bytes((melee + poison + (W / 'combat_regression_v283.lua').read_text()).encode('gbk'))
    runs = []
    for mode in ('normal', 'hot'):
        result = subprocess.run([runtime, str(source), str(work), mode], capture_output=True, timeout=90)
        output = (result.stdout + result.stderr).decode('gbk', 'replace')
        (work / (mode + '.log')).write_text(output)
        assert result.returncode == 0 and 'COMBAT_PICKUP_V283_PASS' in output, (mode, output)
        print(output, flush=True)
        runs.append({'mode': mode, 'output': output})
    names = ('patch_v283.py', 'test_v283.py', 'auto_poison_v283.lua', 'auto_poison_v283.ljbc',
             'melee_timing_v283.lua', 'melee_timing_v283.ljbc', 'alt_pickup_v283.lua',
             'combat_regression_v283.lua', 'auto_poison_regression_v282.lua', 'test_v282.py',
             'melee_regression_v210.lua')
    report = {'version': 'v1.283', 'all_passed': True, 'sha256': build['sha256'], 'runs': runs,
              'all_42_modules_checked': True, 'full_windows_game_run': False,
              'scope': 'real hero release, poison and projectile paths, low mana selector and clock boundaries, embedded Alt pickup through original currency and pickup callbacks, with finite map, graphics, HP and UI controls',
              'tested_files': {name: hashlib.sha256((W / name).read_bytes()).hexdigest() for name in names}}
    (W / 'validation_v283.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    args = parser.parse_args()
    main(args.runtime or str(ensure_runtime()))
