"""Update the native target lanes, resource notices and Alt sale summary."""
import argparse
import hashlib
import json
import struct
import subprocess
import zlib

from bytecode_relocate import replace_instructions
from ljdis import OPS
from ljtool import Dump, Proto, rc4
from patch_v139 import W, ad, encstr, gcid, jump, rebuild_dump, rebuild_proto
from patch_v201 import set_string
from patch_v282 import compile_helper
from resource_tools import decode
from runtime import ensure_runtime

BASE_SHA = 'da367f929ce91f158d61c2daf3dca27745dec2eae86e76614b7bdc81443ec4ea'
ALT_SALE = '__gm_alt_sale_v283'
LOW_MANA = {778: 790, 808: 820, 838: 850, 936: 943, 954: 961}


def patch_db(dump):
    # These five exhaustion paths entered on each attack evaluation. Leave the
    # manually toggled sword skills and their feedback in their own branches.
    p = dump.protos[46]
    for pc, target in LOW_MANA.items():
        assert OPS[p.bc[pc] & 255] == 'GGET'
        assert OPS[p.bc[target] & 255] == ('JMP' if target < 900 else 'KSTR')
        p.bc[pc] = jump(pc, target, 7)
    dump.protos[46] = Proto(rebuild_proto(p), 46)

    p = dump.protos[193]
    assert p.gc(p.bc[52] >> 16) == '得到金币 '.encode('gbk')
    assert OPS[p.bc[34] & 255] == 'ISNEP'
    marker = gcid(p, ALT_SALE)
    # Honor the same large-credit bookkeeping and bypass only the per-item
    # message. The positive credit then uses the normal balance and labels.
    raw, positions = replace_instructions(p, {
        34: [ad('ISEQS', 2, marker), 0, p.bc[34]],
        49: [ad('ISEQS', 2, marker), 0, p.bc[49]],
    })
    q = Proto(raw, 193)
    for old_pc, destination in [(34, 36), (49, 74)]:
        at = positions[old_pc] + 1
        q.bc[at] = jump(at, positions[destination], 4)
    dump.protos[193] = Proto(rebuild_proto(q), 193)


def build(runtime=None, rebuild_history=False):
    path = W / 'game_v282.res'
    if rebuild_history or not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != BASE_SHA:
        command = ['python3', str(W / 'patch_v282.py')]
        if runtime:
            command.extend(('--runtime', runtime))
        if rebuild_history:
            command.append('--rebuild-history')
        subprocess.run(command, check=True)
    base = path.read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    outer, modules = decode(base, [12, 14, 26, 30])
    runtime = runtime or str(ensure_runtime())
    helper = compile_helper(runtime, 'auto_poison_v283')
    timing = compile_helper(runtime, 'melee_timing_v283', unwrap=True)
    assert len(helper) == 9 and len(timing) == 1 and timing[0].nuv == 0
    hero = modules[26]
    assert len(hero.protos) == 101 and len(hero.protos[89:98]) == len(helper)
    hero.protos[89:98] = helper
    hero.protos[87] = timing[0]

    patch_db(modules[12])
    frame = modules[14].protos[427]
    original = frame.gc(222)
    assert b'for dy=-5,5 do for dx=-5,5 do' in original
    assert "return true,'出售执行+'".encode('gbk') in original
    alt = (W / 'alt_pickup_v283.lua').read_text(encoding='utf-8').encode('gbk')
    set_string(frame, 222, alt)
    modules[14].protos[427] = Proto(rebuild_proto(frame), 427)

    for mid, dump in modules.items():
        for index, proto in enumerate(dump.protos):
            for slot, value in enumerate(proto.kgc):
                if not isinstance(value, bytes):
                    continue
                updated = value.replace(b'v1.282', b'v1.283')
                if mid == 12 and index in (76, 22197):
                    updated = updated.replace(b'1.282', b'1.283')
                if updated != value:
                    proto.kgc[slot], proto.kraw[slot] = updated, encstr(updated)
            dump.protos[index] = Proto(rebuild_proto(proto), index)
        raw = rebuild_dump(dump, set())
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encoded = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encoded if mid == 12 else encoded.hex().upper().encode())

    data = rc4(rebuild_dump(outer, {0}), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v283.res').write_bytes(data)
    report = {'version': 'v1.283', 'base_sha256': BASE_SHA, 'bytes': len(data),
              'sha256': hashlib.sha256(data).hexdigest(), 'charge_notice_seconds': 10,
              'low_mana_branches': LOW_MANA, 'alt_currency_quiet_marker': ALT_SALE}
    (W / 'build_v283.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(report['sha256'], report['bytes'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    parser.add_argument('--rebuild-history', action='store_true')
    args = parser.parse_args()
    build(args.runtime, args.rebuild_history)
