"""Match crafted poison powder charges to the shop values."""
import argparse
import hashlib
import json
import struct
import subprocess
import zlib

from ljdis import OPS
from ljtool import Dump, rc4, uleb
from patch_v139 import W, encstr
from patch_v201 import set_string
from portal_routes_v213 import child_refs
from resource_tools import decode

BASE_SHA = 'cdc4b35d8e82f48c9e502dccc4656ef23230cfd2e12c6afca5763a657d2c9982'
CRAFT_ROOTS = (7868, 9261, 10400)
POWDERS = ('灰色药粉', '黄色药粉')
SIZES = {'小': 100, '中': 200}
CHARGE_FIELDS = tuple(key.encode('gbk') for key in ('最小次数', '最大次数'))
MULTIPLIER = 200
RECIPE_SLOT = 15


def recipe_prototypes(dump):
    refs = child_refs(dump)
    commands = {f'嘱托{name}_{size}'.encode('gbk'): (name, size)
                for name in POWDERS for size in SIZES}
    result = {}
    for root in CRAFT_ROOTS:
        factory = dump.protos[root]
        found = set()
        for pc, word in enumerate(factory.bc):
            if OPS[word & 255] != 'TSETS':
                continue
            expected = commands.get(factory.gc((word >> 16) & 255))
            if expected is None:
                continue
            load = factory.bc[pc - 1]
            assert OPS[load & 255] == 'FNEW'
            assert (word >> 8) & 255 == (load >> 8) & 255
            idx = refs[root, load >> 16]
            name, size = expected
            p = dump.protos[idx]
            assert p.gc(13) == name.encode('gbk')
            assert dict(p.gc(14)[2])['显示名'.encode('gbk')] == f'{name}({size})'.encode('gbk')
            assert expected not in found and idx not in result
            found.add(expected)
            result[idx] = SIZES[size]
        assert found == set(commands.values()), root
    return result


def patch_recipes(dump):
    recipes = recipe_prototypes(dump)
    for idx, old_charges in recipes.items():
        p = dump.protos[idx]
        kind, array, fields = p.gc(RECIPE_SLOT)
        assert kind == 'table' and not array and len(fields) == 3
        raw = p.kraw[-1 - RECIPE_SLOT]
        for field in CHARGE_FIELDS:
            assert dict(fields)[field] == ('int', old_charges)
            prefix = encstr(field) + uleb(3)
            old = prefix + uleb(old_charges)
            assert raw.count(old) == 1
            raw = raw.replace(old, prefix + uleb(old_charges * MULTIPLIER), 1)
        p.kraw[-1 - RECIPE_SLOT] = raw
    return recipes


def build(runtime=None, rebuild_history=False):
    path = W / 'game_v285.res'
    base = path.read_bytes() if path.is_file() else b''
    if rebuild_history or hashlib.sha256(base).hexdigest() != BASE_SHA:
        command = ['python3', str(W / 'patch_v285.py')]
        if runtime:
            command.extend(('--runtime', runtime))
        if rebuild_history:
            command.append('--rebuild-history')
        subprocess.run(command, check=True)
        base = path.read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA

    outer, modules = decode(base, [12, 14, 30])
    recipes = patch_recipes(modules[12])
    version_slots = []
    for mid, dump in modules.items():
        for p in dump.protos:
            for slot, value in enumerate(p.kgc):
                if not isinstance(value, bytes):
                    continue
                updated = value.replace(b'v1.285', b'v1.286')
                if mid == 12 and p.idx in (76, 22198):
                    updated = updated.replace(b'1.285', b'1.286')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    version_slots.append([mid, p.idx])
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encoded = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encoded if mid == 12 else encoded.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v286.res').write_bytes(data)
    report = {'version': 'v1.286', 'base_sha256': BASE_SHA, 'bytes': len(data),
              'sha256': hashlib.sha256(data).hexdigest(), 'craft_powder_charge_multiplier': MULTIPLIER,
              'recipe_prototypes': recipes, 'version_slots': version_slots}
    (W / 'build_v286.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['sha256'], report['bytes'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    parser.add_argument('--rebuild-history', action='store_true')
    args = parser.parse_args()
    build(args.runtime, args.rebuild_history)
