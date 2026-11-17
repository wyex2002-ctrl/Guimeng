"""Targeted entry ABI, native animation and protected-owner regressions."""
from test_v225 import *
from patch_v277 import BASE_SHA, ENTRY_SLOTS, repair_entry
from patch_v139 import encstr, rebuild_proto
from bytecode_relocate import numeric_and_debug
from ljtool import Proto


def main(runtime):
    work = W / 'native_work/v277'
    work.mkdir(parents=True, exist_ok=True)
    a, b = (W / 'game_v276.res').read_bytes(), (W / 'game_v277.res').read_bytes()
    assert hashlib.sha256(a).hexdigest() == BASE_SHA
    _, old = decode(a, range(2, 86, 2))
    _, new = decode(b, range(2, 86, 2))
    differences = []
    for mid, d in new.items():
        trees(d)
        assert d.rebuild() == d.raw and len(d.protos) == len(old[mid].protos)
        for p, q in zip(old[mid].protos, d.protos):
            restored = Proto(q.raw, q.idx)
            for j, value in enumerate(restored.kgc):
                if not isinstance(value, bytes):
                    continue
                back = value.replace(b'v1.277', b'v1.276')
                if mid == 12 and p.idx in [76, 22196]:
                    back = back.replace(b'1.277', b'1.276')
                if back != value:
                    restored.kgc[j], restored.kraw[j] = back, encstr(back)
            if (mid, p.idx) in [(22, 89), (22, 97)]:
                assert restored.raw == q.raw
                assert repair_entry(p).raw == q.raw
                length = ENTRY_SLOTS[p.idx][2]
                assert p.bc[length:] == q.bc[length:]
                assert (p.params, p.frame, p.uv, p.kgc, numeric_and_debug(p)) == (
                    q.params, q.frame, q.uv, q.kgc, numeric_and_debug(q))
                assert (p.bc[0] >> 8 & 255) > p.params
                assert (q.bc[0] >> 8 & 255) == q.params
                for pc, (x, y) in enumerate(zip(p.bc, q.bc)):
                    if x != y:
                        differences.append((mid, p.idx, pc))
                        assert (x & ~0xff00) == (y & ~0xff00)
            else:
                assert rebuild_proto(restored) == p.raw, (mid, p.idx)
            for pc, ins in enumerate(q.bc):
                if OPS[ins & 255] in BRANCHES:
                    assert 0 <= pc + 1 + (ins >> 16) - 32768 < q.nbc
    assert len(differences) == 7
    # These cover current diagnostic hooks, timing, oil, skill and rendering
    # code without rerunning unrelated historical suites.
    assert old[22].protos[112].raw == new[22].protos[112].raw

    def export(mid, idx, name, patches=None, baseline=False):
        d = (old if baseline else new)[mid]
        (work / (name + '.ljbc')).write_bytes(standalone(d, trees(d), idx, patches))

    for version in ['old', 'new']:
        export(22, 121, 'class_' + version, baseline=version == 'old')
        export(22, 35, 'finish_' + version,
               {0: ad('KSHORT', 1, 0), 1: jump(1, 672, 2),
                748: ad('RET0', 0, 1), 884: ad('RET0', 0, 1)},
               baseline=version == 'old')
    for mid, idx, name in [(14, 419, 'mode'), (14, 500, 'data_protection'),
                           (14, 220, 'public_actor'), (20, 8, 'anim_update'),
                           (20, 6, 'anim_reverse'), (20, 21, 'anim_reset')]:
        export(mid, idx, name)
    export(30, 193, 'table_register',
           {0: jump(0, 33), 42: jump(42, 48), 69: ad('RET0', 0, 1)})
    # Only the original-body entry is replaced for these isolated ABI probes.
    # Full native class/animation execution is tested separately below.
    for idx in ENTRY_SLOTS:
        p = new[22].protos[idx]
        export(22, idx, 'abi_' + str(idx),
               {ENTRY_SLOTS[idx][2]: ad('RET', 0, p.params + 1)})
    runs = []
    for suite in ['party_wait', 'entry_abi']:
        source = W / (suite + '_regression_v277.lua')
        script = work / (suite + '.lua')
        script.write_bytes(source.read_text().encode('gbk'))
        for mode in ['normal', 'hot']:
            result = subprocess.run([runtime, str(script), str(work), mode],
                                    capture_output=True, timeout=90)
            output = (result.stdout + result.stderr).decode('gbk', 'replace')
            print(output, flush=True)
            (work / (suite + '.' + mode + '.log')).write_text(output)
            assert result.returncode == 0, (suite, mode, result.returncode, output[-5000:])
            runs.append({'suite': suite, 'mode': mode, 'output': output})
    names = ['patch_v277.py', 'test_v277.py', 'package_v277.py',
             'player_changes_v277.json', 'party_wait_regression_v277.lua',
             'entry_abi_regression_v277.lua', 'crash_analysis_v277.json']
    report = {'version': 'v1.277', 'all_passed': True,
              'sha256': hashlib.sha256(b).hexdigest(), 'runs': runs,
              'changed_instructions': differences, 'all_42_modules_checked': True,
              'runtime_version': subprocess.check_output([runtime, '-v'], stderr=subprocess.STDOUT).decode().strip(),
              'full_windows_game_run': False, 'client_crash_reproduced': False,
              'autosave_seconds': 5, 'high_drop_test_retained': True,
              'scope': 'actual native event class, motion/reset/animation and protected attribute/public owner proxies; contiguous entry ABI, parameter preservation and original errors; finite graphics/actions/engine boundaries, not Windows x86 LuaJIT 2.0.4 validation',
              'tested_files': {n: hashlib.sha256((W / n).read_bytes()).hexdigest() for n in names}}
    (W / 'validation_v277.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    args = parser.parse_args()
    main(args.runtime or str(ensure_runtime()))
