"""Apply v1.288 to the hash-pinned v1.287 resource."""
import argparse
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import struct
import subprocess
import zlib

from bytecode_relocate import replace_instructions
from ljtool import Dump, Proto, rc4, uleb
from patch_v139 import W, abc, ad
from patch_v201 import set_string
from patch_v282 import compile_helper
from resource_tools import decode, numbers
from runtime import ensure_runtime

BASE_SHA = '4c2611ddc715ac049fd64675c7b97532b17ed33664481f95db8f9b88c6bbaf3c'
MODULES = (12, 14, 22, 30)
MANA_SLOTS = (*range(1509, 1515), *range(1516, 1522),
              *range(1530, 1536), *range(1537, 1543))
GREEN = (119, 175)
RED = (136, 146, 192, 202)


def poison(p):
    assert numbers(p)[0][5:7] == [0.07, 0.05]
    # This is the same seven-element expression used by the shield event.
    elements = p.bc[964:979]
    assert p.gc(38).decode('gbk') == 'FXru胃啪'
    assert [p.gc(i).decode('gbk') for i in range(135, 142)] == [
        f'攻{element}元素' for element in '火冰雷风神暗幻']
    replacements = {}
    for start in (*GREEN, *RED):
        call = (p.bc[start] >> 8) & 255
        assert p.bc[start + 5] == abc('CALL', call, 2, 2)
        # Reuse the existing register window, two slots past the former
        # single-element argument. All three slots are below the frame limit.
        assert call + 3 < p.frame
        attrs, total, term = call + 1, call + 2, call + 3
        sum_code = [ad('GGET', attrs, 38), abc('TGETS', attrs, attrs, 53),
                    abc('TGETS', total, attrs, 135)]
        for slot in range(136, 142):
            sum_code += [abc('TGETS', term, attrs, slot),
                         abc('ADDVV', total, total, term)]
        assert len(sum_code) == len(elements)
        if start in GREEN:
            # 2 * total / 5 avoids rounding an exact integer up because
            # the binary representation of 0.4 lies above the decimal value.
            fragment = sum_code + [
                abc('MULVN', attrs, total, 4), ad('KSHORT', total, 5),
                abc('DIVVV', attrs, attrs, total),
                ad('GGET', call, 7), abc('TGETS', call, call, 8),
                abc('CALL', call, 2, 2)]
        else:
            fragment = sum_code + [ad('MOV', call, total)]
        replacements[start] = fragment
        for pc in range(start + 1, start + 6):
            replacements[pc] = []
    raw, _ = replace_instructions(p, replacements)
    return Proto(raw, p.idx)


def mana_conversion(p):
    key = '法力转换'.encode('gbk')
    slots = tuple(i for i in range(p.nkgc)
                  if isinstance(p.gc(i), tuple) and p.gc(i)[0] == 'table'
                  and key in dict(p.gc(i)[2]))
    assert slots == MANA_SLOTS
    changes = []
    for i in slots:
        _, low, high = dict(p.gc(i)[2])[key]
        old = struct.unpack('<d', struct.pack('<II', low, high))[0]
        percent = (Decimal(str(old)) * 150).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        new = float(percent / 100)
        new_low, new_high = struct.unpack('<II', struct.pack('<d', new))
        prefix = uleb(len(key) + 5) + key + uleb(4)
        original = prefix + uleb(low) + uleb(high)
        raw = p.kraw[-1-i]
        assert raw.count(original) == 1
        p.kraw[-1-i] = raw.replace(original, prefix + uleb(new_low) + uleb(new_high), 1)
        changes.append([i, old, new])
    return changes


def reputation(p):
    for pc, register in ((654, 23), (694, 28)):
        assert p.bc[pc] == ad('KSHORT', register, 4)
        p.bc[pc] = ad('KSHORT', register, 3)


def bump_version(mid, p):
    for slot, value in enumerate(p.kgc):
        if not isinstance(value, bytes):
            continue
        updated = value.replace(b'v1.287', b'v1.288')
        if mid == 12 and p.idx in (76, 22198):
            updated = updated.replace(b'1.287', b'1.288')
        if updated != value:
            set_string(p, p.nkgc - 1 - slot, updated)


def build(runtime=None, rebuild_history=False):
    path = W / 'game_v287.res'
    if rebuild_history or not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != BASE_SHA:
        command = ['python3', str(W / 'patch_v287.py')]
        if runtime:
            command.extend(('--runtime', runtime))
        if rebuild_history:
            command.append('--rebuild-history')
        subprocess.run(command, check=True)
    base = path.read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    outer, modules = decode(base, MODULES)
    skills = modules[12].protos
    skills[4587] = poison(skills[4587])
    changes = mana_conversion(skills[143])
    reputation(modules[22].protos[62])
    helper = compile_helper(runtime or str(ensure_runtime()), 'merc_mode_v288', unwrap=True)
    original = modules[14].protos[400:420]
    assert len(helper) == len(original)
    assert [p.params for p in helper] == [p.params for p in original]
    assert [i for i, (p, q) in enumerate(zip(helper, original), 400) if p.nuv != q.nuv] == [413]
    modules[14].protos[400:420] = [Proto(p.raw, idx) for idx, p in enumerate(helper, 400)]

    for mid, dump in modules.items():
        for p in dump.protos:
            bump_version(mid, p)
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encoded = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encoded if mid == 12 else encoded.hex().upper().encode())
    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v288.res').write_bytes(data)
    report = {'version': 'v1.288', 'base_sha256': BASE_SHA, 'bytes': len(data),
              'sha256': hashlib.sha256(data).hexdigest(), 'mana_conversion': changes,
              'ordinary_reputation_percent': 3}
    (W / 'build_v288.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['sha256'], report['bytes'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    parser.add_argument('--rebuild-history', action='store_true')
    args = parser.parse_args()
    build(args.runtime, args.rebuild_history)
