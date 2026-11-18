"""Verify the v1.284 resource and independent automatic and manual poison."""
import argparse
import hashlib
import json
import subprocess

from bytecode_relocate import BRANCHES
from ljdis import OPS
from ljtool import Proto
from native_test_utils import trees
from patch_v139 import W, abc, encstr, rebuild_proto
from patch_v284 import BASE_SHA
from resource_tools import decode
from runtime import ensure_runtime
from test_v282 import export_fixtures


def verify(old, new):
    for mid, dump in new.items():
        trees(dump)
        assert dump.rebuild() == dump.raw
        previous = old[mid].protos
        current = dump.protos
        if mid == 26:
            assert len(previous) == 101 and len(current) == 99
            p, q = previous[-1], current[-1]
            assert q.bc == p.bc[:161] + [abc('CALL', 1, 1, 2)] + p.bc[164:]
            assert q.kraw == p.kraw[2:]
            previous, current = previous[:89], current[:89]
        assert len(previous) == len(current)
        for p, q in zip(previous, current):
            restored = Proto(q.raw, q.idx)
            for slot, value in enumerate(restored.kgc):
                if not isinstance(value, bytes):
                    continue
                back = value.replace(b'v1.284', b'v1.283')
                if mid == 12 and q.idx in (76, 22197):
                    back = back.replace(b'1.284', b'1.283')
                if back != value:
                    restored.kgc[slot], restored.kraw[slot] = back, encstr(back)
            assert rebuild_proto(restored) == p.raw, (mid, q.idx)
        for q in dump.protos:
            for pc, word in enumerate(q.bc):
                if OPS[word & 255] in BRANCHES:
                    assert 0 <= pc + 1 + (word >> 16) - 32768 < q.nbc, (mid, q.idx, pc)


def main(runtime):
    work = W / 'native_work/v284'
    work.mkdir(parents=True, exist_ok=True)
    base = (W / 'game_v283.res').read_bytes()
    data = (W / 'game_v284.res').read_bytes()
    build = json.loads((W / 'build_v284.json').read_text())
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    assert hashlib.sha256(data).hexdigest() == build['sha256']
    _, base_modules = decode(base, range(2, 86, 2))
    _, modules = decode(data, range(2, 86, 2))
    verify(base_modules, modules)
    _, original = decode((W / 'game_v281.res').read_bytes(), [12, 26])
    export_fixtures(original, modules, work)

    melee = (W / 'melee_regression_v210.lua').read_text().split("local melee={'普通攻击'")[0]
    melee = melee.replace("if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end",
                          "if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')else jit.off()end")
    poison = (W / 'auto_poison_regression_v282.lua').read_text()
    common, tail = poison.split('-- Isolate native cooldown initialization', 1)
    tail = tail[tail.rfind("do\n    local s = setup('new')", 0, tail.index('    local spell = s.skills.火球术')):]
    tail = tail[:tail.index("print('AUTO_POISON_V282_PASS'")]
    tail = tail.replace('        if i == 2 then s.hero.技能信息[poison].开始CD效果 = false end\n', '')
    tail = tail.replace('    s.hero.技能信息[poison].开始CD效果 = false\n', '')
    source = work / 'combat.lua'
    source.write_bytes((melee + common + tail + (W / 'auto_poison_regression_v284.lua').read_text()).encode('gbk'))

    runs = []
    for mode in ('normal', 'hot'):
        result = subprocess.run([runtime, str(source), str(work), mode], capture_output=True, timeout=90)
        output = (result.stdout + result.stderr).decode('gbk', 'replace')
        (work / (mode + '.log')).write_text(output)
        assert result.returncode == 0 and 'AUTO_POISON_V284_PASS' in output, (mode, output)
        print(output, flush=True)
        runs.append({'mode': mode, 'output': output})
    names = ('patch_v284.py', 'test_v284.py', 'auto_poison_v284.lua', 'auto_poison_v284.ljbc',
             'auto_poison_regression_v284.lua', 'auto_poison_regression_v282.lua', 'test_v282.py',
             'melee_regression_v210.lua')
    report = {'version': 'v1.284', 'all_passed': True, 'sha256': build['sha256'], 'runs': runs,
              'all_42_modules_checked': True, 'full_windows_game_run': False,
              'scope': 'real hero release, single-target projectile, poison, powder, and manual cooldown paths with controlled map, graphics, HP, and inventory bridges',
              'tested_files': {name: hashlib.sha256((W / name).read_bytes()).hexdigest() for name in names}}
    (W / 'validation_v284.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    args = parser.parse_args()
    main(args.runtime or str(ensure_runtime()))
