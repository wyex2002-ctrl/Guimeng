"""Fix melee poison selection, visible notices and ground-name colors."""
import argparse
import hashlib
import json
import struct
import subprocess
import zlib

from bytecode_relocate import replace_instructions
from ljtool import Dump, Proto, rc4
from patch_v139 import W, abc, ad
from patch_v201 import set_string
from patch_v282 import compile_helper
from resource_tools import decode
from runtime import ensure_runtime

BASE_SHA = '8e48976cb7cc90dbe21ee55f817e41449257dd69c960cb9cd6eb9392f2c44ef6'


def patch_ground(dump, runtime):
    helper = compile_helper(runtime, 'ground_name_color_v287', unwrap=True)
    assert len(helper) == 1 and helper[0].params == 3
    dump.protos[0] = helper[0]
    p = dump.protos[1]
    call = abc('CALL', 17, 2, 3)
    assert p.bc[504] == call and p.frame > 20
    # R20 is free here. The constructor still owns the native label and outline.
    raw, relocation = replace_instructions(p, {504: [ad('MOV', 20, 0), abc('CALL', 17, 2, 4)]})
    dump.protos[1] = Proto(raw, 1)
    return relocation


def build(runtime=None, rebuild_history=False):
    path = W / 'game_v286.res'
    if rebuild_history or not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != BASE_SHA:
        command = ['python3', str(W / 'patch_v286.py')]
        if runtime:
            command.extend(('--runtime', runtime))
        if rebuild_history:
            command.append('--rebuild-history')
        subprocess.run(command, check=True)
    base = path.read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    runtime = runtime or str(ensure_runtime())
    outer, modules = decode(base, [12, 14, 26, 30, 76])

    poison = compile_helper(runtime, 'auto_poison_v287')
    timing = compile_helper(runtime, 'melee_timing_v287', unwrap=True)
    hero = modules[26]
    assert len(hero.protos) == 99 and len(poison) == 9 and len(timing) == 1
    hero.protos[89:98] = poison
    hero.protos[87] = timing[0]

    frame = modules[14].protos[427]
    assert frame.gc(222) == (W / 'alt_pickup_v285.lua').read_text(encoding='utf-8').encode('gbk')
    set_string(frame, 222, (W / 'alt_pickup_v287.lua').read_text(encoding='utf-8').encode('gbk'))
    ground = patch_ground(modules[76], runtime)

    version_slots = []
    for mid, dump in modules.items():
        for idx, p in enumerate(dump.protos):
            for slot, value in enumerate(p.kgc):
                if not isinstance(value, bytes):
                    continue
                updated = value.replace(b'v1.286', b'v1.287')
                if mid == 12 and idx in (76, 22198):
                    updated = updated.replace(b'1.286', b'1.287')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    version_slots.append([mid, idx])
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encoded = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encoded if mid == 12 else encoded.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v287.res').write_bytes(data)
    report = {'version': 'v1.287', 'base_sha256': BASE_SHA, 'bytes': len(data),
              'sha256': hashlib.sha256(data).hexdigest(), 'version_slots': version_slots,
              'low_mana_notice_ms': 1000, 'automatic_charge_notice_ms': 10000,
              'ground_override_color': '#FFFFFF', 'ground_constructor_relocation': ground}
    (W / 'build_v287.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['sha256'], report['bytes'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    parser.add_argument('--rebuild-history', action='store_true')
    args = parser.parse_args()
    build(args.runtime, args.rebuild_history)
