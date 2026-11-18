"""Filter player summons in the town guard action and damage scripts."""
import argparse
import hashlib
import json
import struct
import subprocess
import zlib

from ljdis import OPS
from ljtool import Dump, Proto, rc4
from patch_v139 import W, abc, ad, rebuild_proto
from patch_v201 import set_string
from patch_v282 import add_child, compile_helper
from patch_v289 import splice
from portal_routes_v213 import child_refs
from resource_tools import decode
from runtime import ensure_runtime

BASE_SHA = 'aaa70535d036aae8d82874e47faf92096833b6f6dfa12f76c12af31ef1f80761'
MODULES = (12, 14, 22, 30)
ACTIONS = (7688, 7708, 8056, 9139, 9294, 9493, 9606, 11221)
SCRIPT_TARGETS = tuple(sorted((*ACTIONS, *(idx - 1 for idx in ACTIONS))))


def patch_guards(modules, runtime):
    events = modules[22]
    original = events.protos[112]
    native, = compile_helper(runtime, 'guard_ignore_v292', unwrap=True)
    assert (native.params, native.nuv) == (original.params, original.nuv) == (3, 0)
    events.protos[112] = Proto(native.raw, 112)

    helper, = compile_helper(runtime, 'guard_summon_target_v292', unwrap=True)
    assert (helper.params, helper.nuv) == (1, 0)
    db = modules[12]
    refs = child_refs(db)
    for idx in ACTIONS:
        action = db.protos[idx]
        assert refs[idx, action.bc[76] >> 16] == idx - 1
        assert action.bc == db.protos[9493].bc
        assert db.protos[idx - 1].bc == db.protos[9492].bc

    for idx in reversed(SCRIPT_TARGETS):
        p = db.protos[idx]
        child = add_child(p)
        p = Proto(rebuild_proto(p), idx)
        if idx in ACTIONS:
            # R4 is the candidate proxy. R9 and R10 are free before the
            # original name-mode check. The existing FORL advances on skip.
            pc = 63
            word = p.bc[pc]
            assert OPS[word & 255] == 'TGETS' and p.gc((word >> 16) & 255) == '名称显示方式'.encode('gbk')
            fragment = [ad('FNEW', 9, child), ad('MOV', 10, 4), abc('CALL', 9, 2, 2),
                        ad('IST', 0, 9), 0, word]
            p = splice(p, {pc: fragment}, ((pc, 4, 79, 9),))
        else:
            # The attack animation can finish after ownership changes.
            # R3 is reused by the next original UGET, which reads the victim.
            pc = 3
            assert p.bc[pc] == ad('UGET', 3, 0)
            fragment = [ad('FNEW', 3, child), ad('UGET', 4, 0), abc('CALL', 3, 2, 2),
                        ad('IST', 0, 3), 0, p.bc[pc]]
            p = splice(p, {pc: fragment}, ((pc, 4, 26, 3),))
        db.protos[idx] = p
        db.protos.insert(idx, Proto(helper.raw, idx))


def build(runtime=None, rebuild_history=False):
    path = W / 'game_v291.res'
    if rebuild_history or not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != BASE_SHA:
        args = ['python3', str(W / 'patch_v291.py')]
        if runtime:
            args.extend(('--runtime', runtime))
        if rebuild_history:
            args.append('--rebuild-history')
        subprocess.run(args, check=True)
    base = path.read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    outer, modules = decode(base, MODULES)
    patch_guards(modules, runtime or str(ensure_runtime()))
    for mid, dump in modules.items():
        for p in dump.protos:
            for slot, value in enumerate(p.kgc):
                if not isinstance(value, bytes):
                    continue
                updated = value.replace(b'v1.291', b'v1.292')
                if mid == 12 and p.idx in (76, 22198):
                    updated = updated.replace(b'1.291', b'1.292')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())
    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v292.res').write_bytes(data)
    report = {'version': 'v1.292', 'base_sha256': BASE_SHA, 'bytes': len(data),
              'sha256': hashlib.sha256(data).hexdigest(), 'native_guard_prototype': 112,
              'original_script_prototypes': SCRIPT_TARGETS}
    (W / 'build_v292.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['sha256'], report['bytes'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    parser.add_argument('--rebuild-history', action='store_true')
    args = parser.parse_args()
    build(args.runtime, args.rebuild_history)
