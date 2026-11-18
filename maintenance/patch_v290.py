"""Correct the town guard's summon-ownership and damage gates."""
import argparse
import hashlib
import json
import struct
import subprocess
import zlib

from ljtool import Dump, Proto, rc4
from patch_v139 import W, abc, ad
from patch_v201 import set_string
from patch_v282 import compile_helper, small_key
from patch_v289 import splice
from resource_tools import decode
from runtime import ensure_runtime

BASE_SHA = '65bb9a4174c0c09517392d51a074b5e382301301edd6e2abf7990086f5ec71ea'
GUARD_KEY = '__gm_guard_ignore_v224'
MODULES = (12, 14, 22, 30)
TARGETS = (44, 45, 50, 112)


def patch_guard(dump, runtime):
    original = dump.protos[112]
    assert (original.params, original.nuv) == (2, 0)
    helper, = compile_helper(runtime, 'guard_ignore_v290', unwrap=True)
    assert (helper.params, helper.nuv) == (3, 0)
    dump.protos[112] = Proto(helper.raw, 112)

    for idx, target, scratch in ((44, 1, 8), (45, 2, 4)):
        p = dump.protos[idx]
        assert p.params == scratch and p.frame >= scratch + 3
        method = small_key(p, GUARD_KEY)
        # Both original entries already return false on rejection.
        fragment = [
            abc('TGETS', scratch, 0, method), ad('MOV', scratch + 1, 0),
            ad('MOV', scratch + 2, target), abc('CALL', scratch, 2, 3),
            ad('ISF', 0, scratch), 0, ad('KPRI', scratch, 1),
            ad('RET1', scratch, 2), p.bc[0],
        ]
        dump.protos[idx] = splice(p, {0: fragment}, ((0, 5, (0, 8), scratch),))

    p = dump.protos[50]
    assert p.bc[1] == ad('UGET', 1, 0)
    assert p.gc(3).decode('gbk') == '命中目标组' and p.gc(6).decode('gbk') == '施法者'
    method = small_key(p, GUARD_KEY)
    # R0 already holds the result array. Remove protected targets from the
    # shared list before both native damage and the subsequent hit script.
    fragment = [
        ad('UGET', 4, 0), abc('TGETS', 2, 4, 6),
        abc('TGETS', 1, 2, method), ad('KPRI', 3, 0),
        abc('TGETS', 4, 4, 3), abc('CALL', 1, 1, 4), p.bc[1],
    ]
    dump.protos[50] = splice(p, {1: fragment})


def build(runtime=None, rebuild_history=False):
    path = W / 'game_v289.res'
    if rebuild_history or not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != BASE_SHA:
        args = ['python3', str(W / 'patch_v289.py')]
        if runtime:
            args.extend(('--runtime', runtime))
        if rebuild_history:
            args.append('--rebuild-history')
        subprocess.run(args, check=True)
    base = path.read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    outer, modules = decode(base, MODULES)
    patch_guard(modules[22], runtime or str(ensure_runtime()))
    for mid, dump in modules.items():
        for p in dump.protos:
            for slot, value in enumerate(p.kgc):
                if not isinstance(value, bytes):
                    continue
                updated = value.replace(b'v1.289', b'v1.290')
                if mid == 12 and p.idx in (76, 22198):
                    updated = updated.replace(b'1.289', b'1.290')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())
    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v290.res').write_bytes(data)
    report = {'version': 'v1.290', 'base_sha256': BASE_SHA, 'bytes': len(data),
              'sha256': hashlib.sha256(data).hexdigest(), 'guard_prototypes': TARGETS}
    (W / 'build_v290.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['sha256'], report['bytes'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    parser.add_argument('--rebuild-history', action='store_true')
    args = parser.parse_args()
    build(args.runtime, args.rebuild_history)
