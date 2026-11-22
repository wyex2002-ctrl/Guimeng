"""Verify v1.295 window title and in-game version label replacement ('魔改版' -> '不烧心版')."""
import hashlib
import json

from bytecode_relocate import BRANCHES
from ljdis import OPS
from ljtool import Proto
from native_test_utils import trees
from patch_v139 import W
from patch_v201 import set_string
from patch_v295 import BASE_SHA, NEW_LABEL, OLD_LABEL
from resource_tools import decode

FILES = ('patch_v295.py', 'test_v295.py')


def verify(base, updated):
    outer_old, before = decode(base, range(2, 86, 2))
    outer_new, after = decode(updated, range(2, 86, 2))
    assert outer_new.protos[0].bc == outer_old.protos[0].bc and updated[-10:] == base[-10:]

    remaining_old_label = []
    new_label_hits = []

    for mid, dump in after.items():
        assert dump.rebuild() == dump.raw
        assert len(dump.protos) == len(before[mid].protos)
        trees(dump)
        for p in dump.protos:
            for value in p.kgc:
                if isinstance(value, bytes):
                    if OLD_LABEL in value:
                        remaining_old_label.append((mid, p.idx, value.decode('gbk', errors='replace')))
                    if NEW_LABEL in value:
                        new_label_hits.append((mid, p.idx, value.decode('gbk', errors='replace')))
        if mid not in (12, 14, 30):
            assert dump.raw == before[mid].raw
            continue
        for p in before[mid].protos:
            now = dump.protos[p.idx]
            restored = Proto(now.raw, now.idx)
            for slot, value in enumerate(restored.kgc):
                if not isinstance(value, bytes):
                    continue
                previous = value.replace(b'v1.295', b'v1.294')
                if mid == 12 and p.idx == 76:
                    previous = previous.replace(NEW_LABEL, OLD_LABEL).replace(b'1.295', b'1.294')
                elif mid == 12 and p.idx == 22232 and NEW_LABEL in previous:
                    previous = previous.replace(NEW_LABEL, OLD_LABEL).replace(b'1.295', b'1.292')
                if previous != value:
                    set_string(restored, restored.nkgc - 1 - slot, previous)
            assert restored.rebuild() == p.raw, (mid, p.idx)
        for p in dump.protos:
            for pc, word in enumerate(p.bc):
                if OPS[word & 255] in BRANCHES:
                    assert 0 <= pc + 1 + (word >> 16) - 32768 < p.nbc, (mid, p.idx, pc)

    assert not remaining_old_label, f'Remaining old label: {remaining_old_label}'
    expected_hits = [
        (12, 76, '不烧心版 1.295'),
        (12, 76, '] 不烧心版 '),
        (12, 22232, '不烧心版 1.295'),
    ]
    assert new_label_hits == expected_hits, new_label_hits
    return {
        'remaining_old_label': remaining_old_label,
        'new_label_hits': new_label_hits,
    }


def main():
    base = (W / 'game_v294.res').read_bytes()
    updated = (W / 'game_v295.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    checks = verify(base, updated)
    tested_files = {name: hashlib.sha256((W / name).read_bytes()).hexdigest() for name in FILES}
    report = {
        'version': 'v1.295',
        'base_sha256': BASE_SHA,
        'sha256': hashlib.sha256(updated).hexdigest(),
        'bytes': len(updated),
        'tested_files': tested_files,
        'checks': checks,
        'all_passed': True,
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'validation_v295.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'validation_v295.json').write_text(report_text, encoding='utf-8')
    print('ALL PASSED:', report['sha256'], checks['new_label_hits'])


if __name__ == '__main__':
    main()
