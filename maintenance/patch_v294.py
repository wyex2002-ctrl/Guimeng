"""Supply the v1.293 potion scheduler with unrounded engine milliseconds."""
import argparse
import hashlib
import json
import struct
import subprocess
import zlib

from ljdis import OPS
from ljtool import Dump, rc4
from patch_v139 import W, abc, ad
from patch_v201 import set_string
from patch_v282 import add_child, compile_helper, small_key
from patch_v293 import insert, put
from resource_tools import decode
from runtime import ensure_runtime

BASE_SHA = 'fbbbd3efb356c25eb6f14cea0ffe8e7b2e090cec195e0191fc721763b6c04df3'
MODULES = (12, 14, 30)
FACTORY = 301
OLD_CLOCK = '取运行时间'.encode('gbk')
CLOCK_KEY = '__gm_potion_ms_v294'
POTION_CLOCK_CALLS = {297: 1, 303: 1, 308: 1, 310: 1, 311: 2}


def patch_clock(db, native, runtime):
    users = {p.idx for p in db.protos if OLD_CLOCK in p.kgc}
    assert users == POTION_CLOCK_CALLS.keys()
    for idx, count in POTION_CLOCK_CALLS.items():
        p = db.protos[idx]
        slot = p.nkgc - 1 - p.kgc.index(OLD_CLOCK)
        callers = [word for word in p.bc if OPS[word & 255] == 'TGETS' and (word >> 16) & 255 == slot]
        assert len(callers) == count, (idx, count)
        set_string(p, slot, CLOCK_KEY.encode())

    helper, = compile_helper(runtime, 'potion_clock_v294', unwrap=True)
    assert (helper.params, helper.nuv) == (0, 0)
    factory = native.protos[FACTORY]
    assert factory.bc[108] == abc('TSETS', 18, 90, small_key(factory, '取运行时间'))
    # R90 is the table exported as Gly独. R91 is free before the existing
    # metatable is built. Leave the rounded legacy getter as-is.
    word = factory.bc[180]
    assert OPS[word & 255] == 'TDUP' and word >> 8 & 255 == 91
    clock = add_child(factory)
    key = small_key(factory, CLOCK_KEY)
    put(native, factory, {180: [ad('FNEW', 91, clock), abc('TSETS', 91, 90, key), word]})
    insert(native, {FACTORY: (helper,)})


def build(runtime=None, rebuild_history=False):
    path = W / 'game_v293.res'
    if rebuild_history or not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != BASE_SHA:
        args = ['python3', str(W / 'patch_v293.py')]
        if runtime:
            args.extend(('--runtime', runtime))
        if rebuild_history:
            args.append('--rebuild-history')
        subprocess.run(args, check=True)
    base = path.read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    outer, modules = decode(base, MODULES)
    patch_clock(modules[12], modules[14], runtime or str(ensure_runtime()))

    for mid, dump in modules.items():
        for p in dump.protos:
            for slot, value in enumerate(p.kgc):
                if not isinstance(value, bytes):
                    continue
                updated = value.replace(b'v1.293', b'v1.294')
                if mid == 12 and p.idx == 76:
                    updated = updated.replace(b'1.293', b'1.294')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v294.res').write_bytes(data)
    report = {'version': 'v1.294', 'base_sha256': BASE_SHA, 'bytes': len(data),
              'sha256': hashlib.sha256(data).hexdigest(), 'potion_clock_calls': POTION_CLOCK_CALLS,
              'original_gly_factory': FACTORY, 'native_clock_helper': FACTORY,
              'patched_gly_factory': FACTORY + 1}
    (W / 'build_v294.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['sha256'], report['bytes'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    parser.add_argument('--rebuild-history', action='store_true')
    args = parser.parse_args()
    build(args.runtime, args.rebuild_history)
