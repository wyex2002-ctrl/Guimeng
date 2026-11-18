"""Verify town guards through the current event class and native hit path."""
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
from patch_v290 import BASE_SHA, TARGETS
from resource_tools import decode
from runtime import ensure_runtime


def verify(old, new):
    for mid, dump in new.items():
        assert dump.rebuild() == dump.raw
        trees(dump)
        assert len(dump.protos) == len(old[mid].protos)
        for before, after in zip(old[mid].protos, dump.protos):
            if mid == 22 and before.idx in TARGETS:
                assert before.raw != after.raw
            else:
                p = Proto(after.raw, after.idx)
                for slot, value in enumerate(p.kgc):
                    if not isinstance(value, bytes):
                        continue
                    restored = value.replace(b'v1.290', b'v1.289')
                    if mid == 12 and p.idx in (76, 22198):
                        restored = restored.replace(b'1.290', b'1.289')
                    if restored != value:
                        set_string(p, p.nkgc - 1 - slot, restored)
                assert before.raw == p.rebuild(), (mid, p.idx)
        for p in dump.protos:
            for pc, word in enumerate(p.bc):
                if OPS[word & 255] in BRANCHES:
                    assert 0 <= pc + 1 + (word >> 16) - 32768 < p.nbc


def fixtures(old, new, work):
    def export(dump, idx, name, patches=None):
        (work / (name + '.ljbc')).write_bytes(
            standalone(dump, trees(dump), idx, patches))

    for version, modules in (('old', old), ('new', new)):
        d = modules[22]
        export(d, len(d.protos) - 1, 'event_' + version)
        export(d, 50, 'hit_' + version)
    # Execute the full original Hero assignment block in 22/0. Its
    # surrounding resource, rendering and animation setup is unnecessary.
    export(new[22], 0, 'assign_hero', {0: jump(0, 118, 9), 123: ad('RET0', 0, 1)})
    for i, name in [(13, 'public_sys'), (458, 'public_get'), (219, 'entity_api')]:
        export(new[14], i, name)


def main(runtime):
    work = W / 'native_work/v290'
    work.mkdir(parents=True, exist_ok=True)
    baseline, data = [(W / f'game_v{v}.res').read_bytes() for v in (289, 290)]
    build = json.loads((W / 'build_v290.json').read_text())
    assert hashlib.sha256(baseline).hexdigest() == BASE_SHA
    assert hashlib.sha256(data).hexdigest() == build['sha256']
    before, old = decode(baseline, range(2, 86, 2))
    after, new = decode(data, range(2, 86, 2))
    assert before.protos[0].bc == after.protos[0].bc and baseline[-10:] == data[-10:]
    verify(old, new)
    fixtures(old, new, work)

    regression = 'guard_regression_v290.lua'
    source = work / regression
    source.write_bytes((W / regression).read_text().encode('gbk'))
    runs = []
    for mode in ('normal', 'hot'):
        run = subprocess.run([runtime, str(source), str(work), mode], capture_output=True, timeout=60)
        output = (run.stdout + run.stderr).decode('gbk', 'replace')
        (work / f'{mode}.log').write_text(output)
        assert run.returncode == 0 and 'TOWN_GUARD_V290_PASS' in output, (mode, output)
        print(output, end='', flush=True)
        runs.append({'mode': mode, 'output': output})
    names = ('patch_v290.py', 'test_v290.py', 'guard_ignore_v290.lua',
             'guard_ignore_v290.ljbc', regression)
    report = {'version': 'v1.290', 'all_passed': True, 'sha256': build['sha256'],
              'runs': runs, 'all_42_modules_checked': True, 'full_windows_game_run': False,
              'tested_files': {n: hashlib.sha256((W / n).read_bytes()).hexdigest() for n in names}}
    (W / 'validation_v290.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    args = parser.parse_args()
    main(args.runtime or str(ensure_runtime()))
