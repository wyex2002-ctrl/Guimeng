"""Use native bag slot IDs to find powders for automatic poison."""
import argparse
import hashlib
import json
import struct
import subprocess
import zlib

from ljtool import Dump, Proto, rc4
from patch_v139 import W
from patch_v201 import set_string
from patch_v282 import REQUEST, compile_helper
from portal_routes_v213 import child_refs
from resource_tools import decode
from runtime import ensure_runtime

BASE_SHA = '4ace343e7f77a6520bd3776424fbc83e49f6279026f7ba2ac8a62e17cef6a832'
MODULES = (12, 14, 30)
POWDER = 4586


def patch_powder(database, runtime):
    original = database.protos[POWDER]
    callback = database.protos[POWDER + 1]
    assert child_refs(database)[POWDER + 1, 147] == POWDER
    assert callback.gc(148).decode('gbk') == REQUEST
    assert (original.params, original.nuv) == (2, 0)
    helper, = compile_helper(runtime, 'poison_powder_v291', unwrap=True)
    assert (helper.params, helper.nuv) == (2, 0)
    database.protos[POWDER] = Proto(helper.raw, POWDER)


def build(runtime=None, rebuild_history=False):
    path = W / 'game_v290.res'
    if rebuild_history or not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != BASE_SHA:
        args = ['python3', str(W / 'patch_v290.py')]
        if runtime:
            args.extend(('--runtime', runtime))
        if rebuild_history:
            args.append('--rebuild-history')
        subprocess.run(args, check=True)
    base = path.read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    outer, modules = decode(base, MODULES)
    patch_powder(modules[12], runtime or str(ensure_runtime()))
    for mid, dump in modules.items():
        for p in dump.protos:
            for slot, value in enumerate(p.kgc):
                if not isinstance(value, bytes):
                    continue
                updated = value.replace(b'v1.290', b'v1.291')
                if mid == 12 and p.idx in (76, 22198):
                    updated = updated.replace(b'1.290', b'1.291')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())
    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v291.res').write_bytes(data)
    report = {'version': 'v1.291', 'base_sha256': BASE_SHA, 'bytes': len(data),
              'sha256': hashlib.sha256(data).hexdigest(), 'automatic_powder_prototype': POWDER}
    (W / 'build_v291.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['sha256'], report['bytes'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    parser.add_argument('--rebuild-history', action='store_true')
    args = parser.parse_args()
    build(args.runtime, args.rebuild_history)
