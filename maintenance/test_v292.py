"""Verify the actual Pan Ye village guard scripts and native protection."""
import argparse
import hashlib
import json
import subprocess

from bytecode_relocate import BRANCHES
from ljdis import OPS
from ljtool import Dump, Proto
from native_test_utils import standalone, trees
from patch_v139 import W, ad, jump
from patch_v201 import set_string, unpack_config
from patch_v292 import ACTIONS, BASE_SHA, SCRIPT_TARGETS
from portal_routes_v213 import child_refs
from resource_tools import decode
from runtime import ensure_runtime
from test_v192 import lua


def new_index(index):
    return index + sum(target <= index for target in SCRIPT_TARGETS)


def verify(old, new):
    helper, = Dump((W / 'guard_summon_target_v292.ljbc').read_bytes()).protos
    for mid, dump in new.items():
        assert dump.rebuild() == dump.raw
        trees(dump)
        assert len(dump.protos) == len(old[mid].protos) + (len(SCRIPT_TARGETS) if mid == 12 else 0)
        for before in old[mid].protos:
            i = before.idx
            after = dump.protos[new_index(i) if mid == 12 else i]
            if mid == 12 and i in SCRIPT_TARGETS:
                assert dump.protos[after.idx - 1].raw == helper.raw
                assert (after.params, after.uv, after.frame) == (before.params, before.uv, before.frame)
                assert after.kgc[1:] == before.kgc and after.kgc[0] == ('child',)
                at = 63 if i in ACTIONS else 3
                for pc, word in enumerate(before.bc):
                    position = pc + (5 if pc >= at else 0)
                    if OPS[word & 255] in BRANCHES:
                        dest = pc + 1 + (word >> 16) - 32768
                        target = dest + (5 if dest > at else 0)
                        word = (word & 65535) | ((target - position - 1 + 32768) << 16)
                    assert after.bc[position] == word, (mid, i, pc)
            elif (mid, i) != (22, 112):
                restored = Proto(after.raw, after.idx)
                for slot, value in enumerate(restored.kgc):
                    if isinstance(value, bytes):
                        original = value.replace(b'v1.292', b'v1.291')
                        if mid == 12 and i in (76, 22198):
                            original = original.replace(b'1.292', b'1.291')
                        if original != value:
                            set_string(restored, restored.nkgc - 1 - slot, original)
                assert before.raw == restored.rebuild(), (mid, i)
            for pc, word in enumerate(after.bc):
                if OPS[word & 255] in BRANCHES:
                    assert 0 <= pc + 1 + (word >> 16) - 32768 < after.nbc


def guard_configs(db):
    factory = db.protos[18524]
    refs = child_refs(db)
    needle = bytes(value ^ 16 for value in '回调脚本名=卫士'.encode('gbk')).hex().upper().encode()
    configs = {}
    for pc, word in enumerate(factory.bc):
        if OPS[word & 255] != 'KSTR':
            continue
        config = factory.gc(word >> 16)
        if not isinstance(config, bytes) or not config.endswith(b'*') or needle not in config:
            continue
        contents = unpack_config(config)
        fields = dict(line.split(b'=', 1) for line in contents.splitlines() if b'=' in line)
        assert fields['回调脚本名'.encode('gbk')] == '卫士'.encode('gbk')
        assert fields['绑定属性'.encode('gbk')] == b'NPC'
        assert fields['名称样式'.encode('gbk')] == '卫士'.encode('gbk')
        assert OPS[factory.bc[pc + 2] & 255] == 'FNEW'
        callback = db.protos[refs[factory.idx, factory.bc[pc + 2] >> 16]]
        at = next(i for i, word in enumerate(callback.bc)
                  if OPS[word & 255] == 'TSETS'
                  and callback.gc((word >> 16) & 255) == '动作监视'.encode('gbk'))
        action = refs[callback.idx, callback.bc[at - 1] >> 16]
        configs[action] = (callback.idx, contents)
    assert tuple(sorted(configs)) == ACTIONS
    return configs


def fixtures(old, new, work):
    def export(modules, mid, i, name, edits=None, params=None):
        d = modules[mid]
        (work / (name + '.ljbc')).write_bytes(standalone(d, trees(d), i, edits, params))

    configs = guard_configs(old[12])
    for name, modules in [('old', old), ('new', new)]:
        export(modules, 22, len(modules[22].protos) - 1, 'event_' + name)
        for action, (callback, _) in configs.items():
            export(modules, 12, new_index(callback) if name == 'new' else callback,
                   f'guard_{name}_{action}')
    map_data = {action: contents for action, (_, contents) in configs.items()}
    factory = old[12].protos[18524]
    for slot, event_id in ((1817, 1109), (1821, 1110)):
        config = unpack_config(factory.gc(slot))
        assert ('事件标识='.encode('gbk') + str(event_id).encode()) in config
        map_data[event_id] = config
    (work / 'configs.lua').write_bytes(('return ' + lua(map_data)).encode('gbk'))
    for m, i, label in [(14, 13, 'public_sys'), (14, 458, 'public_get'), (14, 301, 'gly'),
                        (14, 423, 'dispatch'), (30, 71, 'read_event_config')]:
        export(new, m, i, label)
    export(new, 14, 420, 'sandbox', {
        0: ad('UGET', 11, 0), 1: ad('MOV', 12, 0), 2: jump(2, 562, 13), 571: ad('RET0', 0, 1),
    }, 1)
    export(new, 22, 0, 'init_fields', {
        0: jump(0, 118, 9), 123: jump(123, 179, 19),
        255: jump(255, 1247, 22), 1259: jump(1259, 1562, 24), 1565: ad('RET0', 0, 1),
    })
    export(new, 12, 4727, 'summon', {0: jump(0, 459, 8), 528: ad('RET1', 7, 2)})


def main(runtime):
    work = W / 'native_work/v292'
    work.mkdir(parents=True, exist_ok=True)
    base, data = ((W / f'game_v{v}.res').read_bytes() for v in (291, 292))
    build = json.loads((W / 'build_v292.json').read_text())
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    assert hashlib.sha256(data).hexdigest() == build['sha256']
    before, old = decode(base, range(2, 86, 2))
    after, new = decode(data, range(2, 86, 2))
    assert before.protos[0].bc == after.protos[0].bc and base[-10:] == data[-10:]
    verify(old, new)
    fixtures(old, new, work)

    regression = 'guard_regression_v292.lua'
    source = work / regression
    source.write_bytes((W / regression).read_text().encode('gbk'))
    runs = []
    for mode in ('normal', 'hot'):
        result = subprocess.run([runtime, str(source), str(work), mode], capture_output=True, timeout=60)
        output = (result.stdout + result.stderr).decode('gbk', 'replace')
        (work / f'{mode}.log').write_text(output)
        assert result.returncode == 0 and 'TOWN_GUARD_V292_PASS' in output, (mode, output)
        print(output, end='', flush=True)
        runs.append({'mode': mode, 'output': output})
    names = ('patch_v292.py', 'test_v292.py', 'guard_ignore_v292.lua', 'guard_ignore_v292.ljbc',
             'guard_summon_target_v292.lua', 'guard_summon_target_v292.ljbc', regression)
    report = {'version': 'v1.292', 'all_passed': True, 'sha256': build['sha256'], 'runs': runs,
              'all_42_modules_checked': True, 'full_windows_game_run': False,
              'tested_files': {name: hashlib.sha256((W / name).read_bytes()).hexdigest() for name in names}}
    (W / 'validation_v292.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    args = parser.parse_args()
    main(args.runtime or str(ensure_runtime()))
