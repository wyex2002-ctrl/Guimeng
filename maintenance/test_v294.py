"""Reproduce the v1.293 unit mismatch, then run through the new native clock."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from bytecode_relocate import BRANCHES
from ljdis import OPS
from ljtool import Dump, Proto
from native_test_utils import standalone, trees
from patch_v139 import W
from patch_v201 import set_string
from patch_v294 import BASE_SHA, CLOCK_KEY, FACTORY, OLD_CLOCK, POTION_CLOCK_CALLS
from portal_routes_v213 import child_refs
from resource_tools import decode
from runtime import ensure_runtime
from test_v293 import prepare as prepare_potions_v293

FILES = ('patch_v294.py', 'test_v294.py', 'potion_clock_v294.lua', 'potion_clock_v294.ljbc',
         'potion_clock_regression_v294.lua', 'test_v293.py', 'potion_regression_v293.lua')


def verify(base, updated):
    outer_old, before = decode(base, range(2, 86, 2))
    outer_new, after = decode(updated, range(2, 86, 2))
    assert outer_new.protos[0].bc == outer_old.protos[0].bc and updated[-10:] == base[-10:]
    for mid, dump in after.items():
        assert dump.rebuild() == dump.raw
        assert len(dump.protos) == len(before[mid].protos) + (mid == 14)
        trees(dump)
        if mid not in (12, 14, 30):
            assert dump.raw == before[mid].raw
            continue
        for p in before[mid].protos:
            now = dump.protos[p.idx + (mid == 14 and p.idx >= FACTORY)]
            if mid == 14 and p.idx == FACTORY:
                continue
            restored = Proto(now.raw, now.idx)
            for slot, value in enumerate(restored.kgc):
                if not isinstance(value, bytes):
                    continue
                previous = value.replace(b'v1.294', b'v1.293')
                if mid == 12 and p.idx == 76:
                    previous = previous.replace(b'1.294', b'1.293')
                if mid == 12 and p.idx in POTION_CLOCK_CALLS and value == CLOCK_KEY.encode():
                    previous = OLD_CLOCK
                if previous != value:
                    set_string(restored, restored.nkgc - 1 - slot, previous)
            assert restored.rebuild() == p.raw, (mid, p.idx)
        for p in dump.protos:
            for pc, word in enumerate(p.bc):
                if OPS[word & 255] in BRANCHES:
                    assert 0 <= pc + 1 + (word >> 16) - 32768 < p.nbc, (mid, p.idx, pc)

    old_factory = before[14].protos[FACTORY]
    factory = after[14].protos[FACTORY + 1]
    assert (factory.frame, factory.params, factory.uv) == (old_factory.frame, old_factory.params, old_factory.uv)
    assert factory.kgc[2:] == old_factory.kgc
    assert factory.bc[:180] == old_factory.bc[:180] and factory.bc[182:] == old_factory.bc[180:]
    assert OPS[factory.bc[180] & 255] == 'FNEW' and OPS[factory.bc[181] & 255] == 'TSETS'
    assert factory.gc((factory.bc[181] >> 16) & 255) == CLOCK_KEY.encode()
    assert child_refs(after[14])[FACTORY + 1, factory.bc[180] >> 16] == FACTORY
    helper, = Dump((W / 'potion_clock_v294.ljbc').read_bytes()).protos
    assert after[14].protos[FACTORY].raw == helper.raw
    assert after[14].protos[92].raw == before[14].protos[92].raw
    return after


def fixture_source():
    # Reuse the v1.293 inventory fixture and all scenarios, but exercise the
    # real Gly getters with a fractional-seconds primitive at the engine edge.
    source = (W / 'potion_regression_v293.lua').read_text()
    for old, new in (
        ('local function fixture()', 'local function fixture(start_time)'),
        ('= 100, 0, 0', '= start_time or 100, 0, 0'),
        ('取运行时间 = function() return now end, ', ''),
        ('        Ae冻 = U,', '        引擎 = {取运行时间 = function() return now / 1000 end},\n        Ae冻 = U,'),
        ('    G.使用物品 = exported.使用物品', '''    G.使用物品 = exported.使用物品
    G.取运行时间 = exported.取运行时间
    if arg[3] ~= 'v293' then G.__gm_potion_ms_v294 = exported.__gm_potion_ms_v294 end'''),
        ('POTIONS_V293_PASS', 'POTIONS_V294_PASS'),
    ):
        assert source.count(old) == 1, old
        source = source.replace(old, new)
    marker = '\ndo\n    local f = fixture()\n    f.put(31, red, 3).冷却时间'
    assert source.count(marker) == 1
    position = source.index(marker)
    coverage = (W / 'potion_clock_regression_v294.lua').read_text()
    return source[:position] + '\n' + coverage + source[position:]


def run(runtime, work, mode, version):
    result = subprocess.run([runtime, str(work / 'test.lua'), str(work), mode, version],
                            capture_output=True, timeout=60)
    log = (result.stdout + result.stderr).decode('gbk', 'replace')
    (work / (mode + '.log')).write_text(log)
    marker = 'V293_CLOCK_BUG_REPRODUCED' if version == 'v293' else 'POTIONS_V294_PASS'
    assert result.returncode == 0 and marker in log, log
    print(log, end='')
    return log.strip()


def main(runtime):
    base = (W / 'game_v293.res').read_bytes()
    updated = (W / 'game_v294.res').read_bytes()
    report = json.loads((W / 'build_v294.json').read_text())
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    assert hashlib.sha256(updated).hexdigest() == report['sha256']
    after = verify(base, updated)
    original_work, _ = prepare_potions_v293()
    work = W / 'native_work/v294'
    baseline = work / 'baseline'
    baseline.mkdir(parents=True, exist_ok=True)
    for file in (*original_work.glob('*.ljbc'), original_work / 'templates.lua'):
        shutil.copyfile(file, work / file.name)
        shutil.copyfile(file, baseline / file.name)

    for mid, idx, name in ((12, 314, 'setup'), (14, FACTORY + 1, 'gly_factory')):
        d = after[mid]
        (work / (name + '.ljbc')).write_bytes(standalone(d, trees(d), idx))
    fixture = fixture_source().encode('gbk')
    for directory in (work, baseline):
        (directory / 'test.lua').write_bytes(fixture)

    baseline_result = run(runtime, baseline, 'normal', 'v293')
    runs = {mode: run(runtime, work, mode, 'v294') for mode in ('normal', 'hot')}
    result = {'version': 'v1.294', 'all_passed': True, 'sha256': report['sha256'],
              'baseline': baseline_result, 'runs': runs, 'windows_client_tested': False,
              'tested_files': {file: hashlib.sha256((W / file).read_bytes()).hexdigest()
                               for file in FILES}}
    (W / 'validation_v294.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    args = parser.parse_args()
    main(str(Path(args.runtime).resolve()) if args.runtime else str(ensure_runtime()))
