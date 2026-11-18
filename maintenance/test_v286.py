"""Verify the crafted powder capacities through all three NPC factories."""
import argparse
import hashlib
import json
import subprocess

from native_test_utils import standalone, trees
from patch_v139 import W, ad, jump
from patch_v201 import set_string
from patch_v286 import BASE_SHA, CHARGE_FIELDS, CRAFT_ROOTS, MULTIPLIER, RECIPE_SLOT, recipe_prototypes
from resource_tools import decode
from runtime import ensure_runtime


def verify(old, new):
    recipes = recipe_prototypes(old[12])
    assert recipes == recipe_prototypes(new[12]) and len(recipes) == 12
    for mid, dump in new.items():
        original = old[mid]
        trees(dump)
        assert dump.rebuild() == dump.raw
        assert len(dump.protos) == len(original.protos)
        for p, q in zip(original.protos, dump.protos):
            if mid == 12 and p.idx in recipes:
                kind, array, fields = p.gc(RECIPE_SLOT)
                transformed = [(key, ('int', recipes[p.idx] * MULTIPLIER) if key in CHARGE_FIELDS else value)
                               for key, value in fields]
                assert q.gc(RECIPE_SLOT) == (kind, array, transformed)
                q.kraw[-1 - RECIPE_SLOT] = p.kraw[-1 - RECIPE_SLOT]
            for slot, value in enumerate(q.kgc):
                if not isinstance(value, bytes):
                    continue
                back = value.replace(b'v1.286', b'v1.285')
                if mid == 12 and q.idx in (76, 22198):
                    back = back.replace(b'1.286', b'1.285')
                if back != value:
                    set_string(q, q.nkgc - 1 - slot, back)
            assert q.rebuild() == p.raw, (mid, p.idx)


def fixtures(work, old, new):
    for label, dump in (('old', old[12]), ('new', new[12])):
        tree = trees(dump)
        for root in CRAFT_ROOTS:
            (work / f'npc_{root}_{label}.ljbc').write_bytes(standalone(dump, tree, root))
    dump = new[14]
    tree = trees(dump)
    for idx, label in [(83, 'gly_count'), (84, 'gly_remove'), (87, 'gly_add'),
                       (440, 'remove_item'), (450, 'count_item'), (451, 'free_slots'),
                       (454, 'add_item'), (500, 'data_protection'), (614, 'stack_install')]:
        (work / f'{label}.ljbc').write_bytes(standalone(dump, tree, idx))
    dump = new[30]
    patches = {0: jump(0, 33), 42: jump(42, 48), 69: ad('RET0', 0, 1)}
    (work / 'table_register.ljbc').write_bytes(standalone(dump, trees(dump), 193, patches))


def main(runtime):
    work = W / 'native_work/v286'
    work.mkdir(parents=True, exist_ok=True)
    base, data = ((W / f'game_v{version}.res').read_bytes() for version in (285, 286))
    build = json.loads((W / 'build_v286.json').read_text())
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    assert hashlib.sha256(data).hexdigest() == build['sha256']
    _, old = decode(base, range(2, 86, 2))
    _, new = decode(data, range(2, 86, 2))
    fixtures(work, old, new)
    verify(old, new)
    lua = 'powder_craft_regression_v286.lua'
    source = work / 'powder_craft.lua'
    source.write_bytes((W / lua).read_text().encode('gbk'))
    runs = []
    for mode in ('normal', 'hot'):
        result = subprocess.run([runtime, str(source), str(work), mode], capture_output=True, timeout=90)
        output = (result.stdout + result.stderr).decode('gbk', 'replace')
        (work / f'{mode}.log').write_text(output)
        assert result.returncode == 0 and 'POWDER_CRAFT_V286_PASS' in output, (mode, output)
        print(output, flush=True)
        runs.append({'mode': mode, 'output': output})
    files = ('patch_v286.py', 'test_v286.py', lua)
    report = {'version': 'v1.286', 'all_passed': True, 'sha256': build['sha256'], 'runs': runs,
              'all_42_modules_checked': True, 'full_windows_game_run': False,
              'scope': 'three real NPC factories and their recipe actions, native inventory count, deduction, addition and stack processing, with finite UI and engine bridges',
              'tested_files': {name: hashlib.sha256((W / name).read_bytes()).hexdigest() for name in files}}
    (W / 'validation_v286.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    args = parser.parse_args()
    main(args.runtime or str(ensure_runtime()))
