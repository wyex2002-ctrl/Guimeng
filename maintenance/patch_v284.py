"""Remove the manual skill cooldown dependency from automatic poison."""
import argparse
import hashlib
import json
import struct
import subprocess
import zlib

from bytecode_relocate import BRANCHES, replace_instructions
from ljdis import OPS
from ljtool import Dump, Proto, rc4
from patch_v139 import W, abc, ad, encstr, rebuild_dump, rebuild_proto
from patch_v201 import set_string
from patch_v282 import compile_helper
from resource_tools import decode
from runtime import ensure_runtime

BASE_SHA = 'eb22fa606ba1014df913670e66ad7209f93762cdb8da6f71bd303867626f468d'


def patch_hero(dump, helper):
    assert len(dump.protos) == 101 and len(helper) == 9
    dump.protos[89:98] = helper
    root = dump.protos[-1]
    assert root.nkgc == 163 and root.kgc[:2] == [('child',), ('child',)]
    assert root.bc[161:164] == [ad('FNEW', 3, 161), ad('FNEW', 4, 162), abc('CALL', 1, 1, 4)]
    assert all(pc + 1 + (word >> 16) - 32768 not in (162, 163)
               for pc, word in enumerate(root.bc) if OPS[word & 255] in BRANCHES)
    # The installer only needs the hero class. Drop the two private wrappers
    # that previously exposed manual skill metadata and cooldown initialization.
    del root.kgc[:2]
    del root.kraw[:2]
    root.nkgc -= 2
    raw, _ = replace_instructions(root, {161: [], 162: [], 163: [abc('CALL', 1, 1, 2)]})
    dump.protos[98:] = [Proto(raw, 98)]


def build(runtime=None, rebuild_history=False):
    path = W / 'game_v283.res'
    if rebuild_history or not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != BASE_SHA:
        command = ['python3', str(W / 'patch_v283.py')]
        if runtime:
            command.extend(('--runtime', runtime))
        if rebuild_history:
            command.append('--rebuild-history')
        subprocess.run(command, check=True)
    base = path.read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    outer, modules = decode(base, [12, 14, 26, 30])
    runtime = runtime or str(ensure_runtime())
    patch_hero(modules[26], compile_helper(runtime, 'auto_poison_v284'))

    for mid, dump in modules.items():
        for index, proto in enumerate(dump.protos):
            for slot, value in enumerate(proto.kgc):
                if not isinstance(value, bytes):
                    continue
                updated = value.replace(b'v1.283', b'v1.284')
                if mid == 12 and index in (76, 22197):
                    updated = updated.replace(b'1.283', b'1.284')
                if updated != value:
                    proto.kgc[slot], proto.kraw[slot] = updated, encstr(updated)
            dump.protos[index] = Proto(rebuild_proto(proto), index)
        raw = rebuild_dump(dump, set())
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encoded = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encoded if mid == 12 else encoded.hex().upper().encode())

    data = rc4(rebuild_dump(outer, {0}), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v284.res').write_bytes(data)
    report = {'version': 'v1.284', 'base_sha256': BASE_SHA, 'bytes': len(data),
              'sha256': hashlib.sha256(data).hexdigest(), 'auto_poison_cooldown_seconds': 0,
              'manual_poison_cooldown_seconds': 1.5, 'shared_cooldown': False}
    (W / 'build_v284.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['sha256'], report['bytes'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    parser.add_argument('--rebuild-history', action='store_true')
    args = parser.parse_args()
    build(args.runtime, args.rebuild_history)
