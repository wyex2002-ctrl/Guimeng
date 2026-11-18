"""Extend the existing locked melee judgement to Half Moon and Ten Directions."""
import argparse
import hashlib
import json
import struct
import subprocess
import zlib

from bytecode_relocate import replace_instructions
from ljtool import Dump, Proto, rc4
from patch_v139 import W, ad, encstr, gcid, jump, rebuild_dump, rebuild_proto
from patch_v201 import set_string
from resource_tools import decode

BASE_SHA = '30e776cc8de4a8642416462576bbf389562d33505aa0615f169e7f6cb7d7eed7'
SKILLS = ('半月弯刀', '十方斩')


def extend_lock(dump):
    # Add a short-circuit name check to both existing gates. R8 and R7,
    # respectively, already hold the skill name at these sites.
    sites = {54: (586, 590, 8, '刺杀剑术'), 87: (7, 10, 7, '翔空剑法')}
    relocations = {}
    for index, (site, accepted, register, first_name) in sites.items():
        original = dump.protos[index]
        assert original.bc[site] == ad('ISEQS', register, gcid(original, first_name))
        original_branch = original.bc[site + 1]
        assert original_branch == jump(site + 1, accepted, register)
        checks = []
        for name in SKILLS:
            checks.extend((ad('ISEQS', register, gcid(original, name)), 0))
        raw, positions = replace_instructions(original, {site: [*checks, original.bc[site]]})
        proto = Proto(raw, index)
        for offset in range(1, len(checks), 2):
            pc = positions[site] + offset
            proto.bc[pc] = jump(pc, positions[accepted], register)
        dump.protos[index] = Proto(rebuild_proto(proto), index)
        relocations[str(index)] = {'positions': positions, 'site': site, 'added': len(checks),
                                   'accepted': accepted, 'register': register}
    return relocations


def build(runtime=None, rebuild_history=False):
    path = W / 'game_v280.res'
    if rebuild_history or not path.exists():
        command = ['python3', str(W / 'patch_v280.py')]
        if rebuild_history:
            command.append('--rebuild-history')
        if runtime:
            command.extend(('--runtime', runtime))
        subprocess.run(command, check=True)
    base = path.read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    outer, modules = decode(base, [12, 14, 26, 30])
    relocations = extend_lock(modules[26])

    for module, dump in modules.items():
        for index, proto in enumerate(dump.protos):
            changed = False
            for slot, value in enumerate(proto.kgc):
                if not isinstance(value, bytes):
                    continue
                updated = value.replace(b'v1.280', b'v1.281')
                if module == 12 and index in (76, 22196):
                    updated = updated.replace(b'1.280', b'1.281')
                if updated != value:
                    proto.kgc[slot] = updated
                    proto.kraw[slot] = encstr(updated)
                    changed = True
            if changed:
                dump.protos[index] = Proto(rebuild_proto(proto), index)
        raw = rebuild_dump(dump, set())
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encoded = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], module, encoded if module == 12 else encoded.hex().upper().encode())

    data = rc4(rebuild_dump(outer, {0}), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v281.res').write_bytes(data)
    report = {'version': 'v1.281', 'base_sha256': BASE_SHA, 'bytes': len(data),
              'sha256': hashlib.sha256(data).hexdigest(), 'skills': SKILLS,
              'relocations': relocations, 'autosave_seconds': 300}
    (W / 'build_v281.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(report['sha256'], report['bytes'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    parser.add_argument('--rebuild-history', action='store_true')
    args = parser.parse_args()
    build(args.runtime, args.rebuild_history)
