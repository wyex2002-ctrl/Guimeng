"""Exercise the actual potion resources through native inventory and DB events."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from bytecode_relocate import BRANCHES
from ljdis import OPS
from ljtool import Dump, Proto
from native_test_utils import standalone, trees
from patch_v139 import W, ad, jump
from patch_v201 import set_string
from patch_v241 import water_sites
from patch_v293 import MODULES, OTHER_STATUS_SCRIPTS
from portal_routes_v213 import child_refs
from resource_tools import decode
from runtime import ensure_runtime
from test_v192 import lua

ITEMS = (
    '金创药_小', '金创药_中', '金创药_大', '金创药_特', '金创药_特大', 'Q金创药_小',
    '魔法药_小', '魔法药_中', '魔法药_大', '魔法药_特', '魔法药_特大', 'Q魔法药_小',
    '太阳水', '强效太阳水', '万年雪霜',
    '金创药_小_包', '魔法药_小_包', '强效太阳水_包', '攻击神水_小', '回城卷',
)
FILES = ('patch_v293.py', 'test_v293.py', 'potion_regression_v293.lua', 'potions_v293.lua',
         'potion_merc_v293.lua', 'potion_ui_v293.lua', 'potion_use_bridge_v293.lua')


def gbk(value):
    return value.encode('gbk')


def prepare():
    data = (W / 'game_v293.res').read_bytes()
    base = (W / 'game_v292.res').read_bytes()
    report = json.loads((W / 'build_v293.json').read_text())
    assert hashlib.sha256(data).hexdigest() == report['sha256']
    old_outer, old = decode(base, range(2, 86, 2))
    outer, new = decode(data, range(2, 86, 2))
    assert outer.protos[0].bc == old_outer.protos[0].bc and data[-10:] == base[-10:]
    inserted = {int(mid): {int(idx): n for idx, n in changes.items()}
                for mid, changes in report['inserted_children'].items()}
    subtrees = {mid: trees(dump) for mid, dump in new.items()}

    def idx(mid, prior):
        return prior + sum(count for target, count in inserted.get(mid, {}).items() if target <= prior)

    targets = {12: {20, 37, 264, 286, 295, *OTHER_STATUS_SCRIPTS, *water_sites(old[12])},
               14: {443}, 34: {3, 22}, 40: {19}}
    for mid, dump in new.items():
        assert dump.rebuild() == dump.raw
        assert len(dump.protos) == len(old[mid].protos) + sum(inserted.get(mid, {}).values())
        if mid not in MODULES:
            assert old[mid].raw == dump.raw
        for p in old[mid].protos:
            q = dump.protos[idx(mid, p.idx)]
            if p.idx not in targets.get(mid, ()):
                restored = Proto(q.raw, q.idx)
                for i, value in enumerate(restored.kgc):
                    if not isinstance(value, bytes):
                        continue
                    previous = value.replace(b'v1.293', b'v1.292')
                    if mid == 12 and p.idx in (76, 22198):
                        previous = previous.replace(b'1.293', b'1.292')
                    if previous != value:
                        set_string(restored, restored.nkgc - 1 - i, previous)
                assert restored.rebuild() == p.raw, (mid, p.idx)
        for p in dump.protos:
            for pc, word in enumerate(p.bc):
                if OPS[word & 255] in BRANCHES:
                    assert 0 <= pc + 1 + (word >> 16) - 32768 < p.nbc, (mid, p.idx, pc)

    work = W / 'native_work/v293'
    work.mkdir(parents=True, exist_ok=True)

    def extract(mid, old_idx, name, edits=None, direct=False):
        i = old_idx if direct else idx(mid, old_idx)
        (work / (name + '.ljbc')).write_bytes(standalone(new[mid], subtrees[mid], i, edits))

    for mid, i, name in (
        (12, 37, 'item_event'), (12, 264, 'merc'), (12, 286, 'aux'), (12, 296, 'setup'),
        (14, 13, 'public_sys'), (14, 301, 'gly_factory'), (14, 423, 'dispatch'),
        (14, 439, 'use_bag'), (14, 470, 'run_item_event'),
        (34, 2, 'mouse_use'), (34, 3, 'item_use'), (34, 22, 'consume'),
    ):
        extract(mid, i, name)
    extract(12, 20, 'periodic', {0: jump(0, 1016, 10), 1048: ad('RET0', 0, 1)})
    # The status constructor is large and requires the graphics runtime. Slice
    # its actual visibility hook so both stories and adjacent statuses run.
    extract(40, 19, 'buff_visible', {0: ad('MOV', 5, 4), 1: jump(1, 708, 7), 717: ad('RET1', 5, 2)})
    extract(14, 443, 'tooltip_description',
            {0: jump(0, 83, 9), 90: ad('RET1', 9, 2)})
    db = new[12]
    refs = child_refs(db)
    root = db.protos[idx(12, 4093)]
    templates = {}
    for pc, word in enumerate(root.bc):
        if OPS[word & 255] != 'TDUP':
            continue
        value = root.gc(word >> 16)
        if not isinstance(value, tuple):
            continue
        item = dict(value[2])
        name = item.get(gbk('名称'))
        if name not in {gbk(item) for item in ITEMS}:
            continue
        flags = [root.gc(code >> 16).decode('gbk') for code in root.bc[pc - 65:pc]
                 if OPS[code & 255] == 'KSTR' and (code >> 8 & 255) == 4][-1]
        item[gbk('附加')] = {
            gbk(k): int(v) if v.isdigit() else gbk(v)
            for k, v in (pair.split('ぅ') for pair in flags.split('ぃ') if pair)
        }
        item[gbk('风格提示')] = dict(root.gc(root.bc[pc + 3] >> 16)[2])
        assert item[gbk('冷却时间')] == ('int', 0)
        factory = next(code for code in root.bc[pc:pc + 20] if OPS[code & 255] == 'FNEW')
        extract(12, refs[root.idx, factory >> 16], 'script_' + name.hex(), direct=True)
        templates[name] = item
    assert len(templates) == len(ITEMS)
    (work / 'templates.lua').write_bytes(('return ' + lua(templates) + '\n').encode('gbk'))
    (work / 'test.lua').write_bytes((W / 'potion_regression_v293.lua').read_text().encode('gbk'))
    return work, report


def main(runtime):
    work, report = prepare()
    output = {}
    for mode in ('normal', 'hot'):
        result = subprocess.run([runtime, str(work / 'test.lua'), str(work), mode],
                                capture_output=True, timeout=60)
        log = (result.stdout + result.stderr).decode('gbk', 'replace')
        (work / (mode + '.log')).write_text(log)
        assert result.returncode == 0 and 'POTIONS_V293_PASS' in log, log
        output[mode] = log.strip()
        print(log, end='')
    result = {'version': 'v1.293', 'all_passed': True, 'sha256': report['sha256'],
              'runs': output, 'windows_client_tested': False,
              'tested_files': {file: hashlib.sha256((W / file).read_bytes()).hexdigest()
                               for file in FILES}}
    (W / 'validation_v293.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    args = parser.parse_args()
    main(str(Path(args.runtime).resolve()) if args.runtime else str(ensure_runtime()))
