"""Update Taoist treatment, the bag sale, regular monster drops and skill text."""
import argparse
import hashlib
import json
import struct
import subprocess
import zlib

from bytecode_relocate import BRANCHES, replace_instructions
from ljdis import OPS
from ljtool import Dump, Proto, rc4
from patch_v139 import W, abc, ad, gcid, jump
from patch_v201 import set_string
from patch_v282 import add_child, compile_helper, small_key
from resource_tools import decode, numbers
from runtime import ensure_runtime

BASE_SHA = '9ba234252010ed59ad89319f335f7deb0fe083f28af2fef70f7798b3463cba24'
MODULES = (12, 14, 22, 26, 30)
HEALS = (4501, 4514, 4542, 4555, 4568, 4587, 4600, 4613, 4631, 4644,
         4657, 4670, 4683, 4696, 4714, 4727, 4745, 4991, 5004)


def splice(p, edits, branches=()):
    raw, pos = replace_instructions(p, edits)
    result = Proto(raw, p.idx)
    for pc, offset, target, register in branches:
        at = pos[pc] + offset
        destination = pos[target] if isinstance(target, int) else pos[target[0]] + target[1]
        result.bc[at] = jump(at, destination, register)
    return Proto(result.rebuild(), p.idx)


def healing_formula(p):
    offset = 81 if p.idx == 4587 else 0
    assert numbers(p)[0][4] == 2 and numbers(p)[0][14] == .8
    assert p.gc(120) == '主角攻神元素'.encode('gbk')
    assert [p.gc(i).decode('gbk') for i in range(135, 142)] == [
        f'攻{e}元素' for e in '火冰雷风神暗幻']
    edits = {}
    for pc, register in ((1169, 8), (1263, 9), (1267, 9)):
        pc += offset
        assert p.bc[pc:pc + 2] == [ad('GGET', register, 0), abc('TGETS', register, register, 120)]
        attrs, next_value = register + 1, register + 2
        code = [ad('GGET', attrs, 38), abc('TGETS', attrs, attrs, 53),
                abc('TGETS', register, attrs, 135)]
        for slot in range(136, 142):
            code.extend((abc('TGETS', next_value, attrs, slot),
                         abc('ADDVV', register, register, next_value)))
        edits[pc], edits[pc + 1] = code, []
    # The level is already in R9. Keep the learned-duration and practice
    # branches, then join the original additive wellness multiplier.
    start, stop = 1292 + offset, 1309 + offset
    assert p.bc[start - 1] == abc('TGETB', 9, 9, 1)
    assert p.bc[1301 + offset] == abc('ADDVN', 8, 9, 4)
    assert not any(pc + 1 + (word >> 16) - 32768 in range(start + 1, stop)
                   for pc, word in enumerate(p.bc)
                   if not start <= pc < stop and OPS[word & 255] in BRANCHES)
    edits.update({pc: [] for pc in range(start, stop)})
    edits[start] = [abc('ADDVN', 8, 9, 4)]
    return splice(p, edits)


def call_method(p, dest, receiver, method, arguments):
    return [
        abc('TGETS', dest, receiver, small_key(p, method)),
        ad('MOV', dest + 1, receiver),
        *(ad('MOV', dest + 2 + i, arg) for i, arg in enumerate(arguments)),
        abc('CALL', dest, 2, len(arguments) + 2),
    ]


def lock_healing(mod, runtime):
    p = mod.protos[55]
    assert p.bc[232] == ad('KPRI', 17, 0)
    skill = gcid(p, '治愈术')
    pending = small_key(p, '__gm_heal_pending_v289')
    # R3 carries only this cast's selection, including a replay of the
    # existing native pending slot. Heal bypasses the hostile lock helpers.
    enter = [ad('ISNES', 1, skill), 0,
             *call_method(p, 12, 0, '__gm_heal_capture_v289', [3, 4]),
             ad('MOV', 3, 12), 0]
    original_enter = 37 + 1 + (p.bc[37] >> 16) - 32768
    route = [ad('ISEQS', 1, skill), 0, p.bc[1031]]
    release = [ad('ISNES', 1, skill), 0,
               *call_method(p, 18, 0, '__gm_heal_target_v289', [3]),
               ad('MOV', 17, 18),
               ad('ISEQP', 17, 0), 0, ad('ISF', 0, 17), 0, 0, p.bc[232]]
    edits = {37: enter, 1031: route, 232: release}
    branches = [
        (37, 1, original_enter, (p.bc[37] >> 8) & 255),
        (37, len(enter) - 1, original_enter, 12), (1031, 1, 1111, 12),
        (232, 1, (232, len(release) - 1), 17),
        (232, len(release) - 5, 360, 18),
        (232, len(release) - 3, 343, 18),
        (232, len(release) - 2, 541, 18),
    ]
    for pc in (102, 118):
        assert p.bc[pc] == abc('TSETS', 1, 0, 11)
        edits[pc] = [p.bc[pc], ad('ISNES', 1, skill), 0, abc('TSETS', 3, 0, pending)]
        branches.append((pc, 2, pc + 1, 15))
    for pc, register in ((52, 12), (122, 15)):
        assert p.bc[pc] == abc('TSETS', register, 0, 11)
        edits[pc] = [p.bc[pc], abc('TSETS', register, 0, pending)]
    mod.protos[55] = splice(p, edits, branches)
    p = mod.protos[54]
    assert p.bc[451] == abc('TGETS', 24, 7, 37)
    init = [*call_method(p, 24, 1, '__gm_heal_init_v289', [7]),
            ad('IST', 0, 24), 0, p.bc[451]]
    mod.protos[54] = splice(p, {451: init}, ((451, len(init) - 2, 554, 24),))

    p = mod.protos[53]
    key = small_key(p, '__gm_heal_lock_v289')
    def phase(base, method, original):
        return [ad('UGET', base, 0), abc('TGETS', base + 1, base, key),
                ad('ISF', 0, base + 1), 0, abc('TGETS', base + 1, base, 4),
                *call_method(p, base + 2, base + 1, method, [base]),
                ad('IST', 0, base + 2), 0, original]
    guard = phase(0, '__gm_heal_invalid_v289', p.bc[0])
    select = phase(2, '__gm_heal_hits_v289', p.bc[1029])
    mod.protos[53] = splice(p, {0: guard, 1029: select}, (
        (0, 3, (0, len(guard) - 1), 0), (0, len(guard) - 2, 4, 0),
        (1029, 3, (1029, len(select) - 1), 2),
        (1029, len(select) - 2, 1295, 2),
    ))
    root = mod.protos[-1]
    assert root.idx == 98 and root.bc[162] == ad('GGET', 1, gcid(root, 'Sys'))
    child = add_child(root)
    mod.protos[-1] = splice(root, {162: [ad('FNEW', 1, child), ad('MOV', 2, 0),
                                       abc('CALL', 1, 1, 2), root.bc[162]]})
    mod.protos[-1:-1] = compile_helper(runtime, 'healing_lock_v289', unwrap=True)


def filter_drops(mod, runtime):
    p = mod.protos[96]
    assert p.bc[116] == ad('KSHORT', 5, 0)
    child = add_child(p)
    mod.protos[96] = splice(p, {116: [ad('FNEW', 5, child), ad('MOV', 6, 2),
                                    abc('CALL', 5, 1, 2), p.bc[116]]})
    mod.protos[96:96] = compile_helper(runtime, 'monster_drop_filter_v289', unwrap=True)


def descriptions(p):
    for slot, previous, distance in (
        (1266, '白莲', 2), (1277, '红莲', 2), (1295, '月桂', 3),
        (1306, None, 3), (1352, None, 4),
    ):
        old = p.gc(slot).decode('gbk').splitlines()
        assert len(old) >= 7 and old[0].startswith('#md属性')
        description = ['#md根据最大魔法值获得伤害加成。'] if slot != 1352 else old[5:]
        if previous:
            description.append(f'#md使用【{previous}】后，造成额外伤害。')
        description += ['#md装备远程武器且被怪物近身时，',
                        f'#md瞬移到怪物背后{distance}格处。']
        set_string(p, slot, '\n'.join(old[:5] + description).encode('gbk'))


def build(runtime=None, rebuild_history=False):
    path = W / 'game_v288.res'
    if rebuild_history or not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != BASE_SHA:
        args = ['python3', str(W / 'patch_v288.py')]
        if runtime:
            args.extend(('--runtime', runtime))
        if rebuild_history:
            args.append('--rebuild-history')
        subprocess.run(args, check=True)
    base = path.read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    runtime = runtime or str(ensure_runtime())
    outer, mods = decode(base, MODULES)
    db = mods[12].protos
    for idx in HEALS:
        db[idx] = healing_formula(db[idx])
    event = db[46]
    assert event.bc[969] == ad('GGET', 7, 0)
    event.bc[969] = jump(969, 1023, 7)
    descriptions(db[6468])
    ui = mods[14].protos[427]
    sale = ui.gc(230)
    before = b'     pay(value)\n'
    assert sale.count(before) == 1
    set_string(ui, 230, sale.replace(before, b"     pay(value,nil,'__gm_alt_sale_v283')\n"))
    lock_healing(mods[26], runtime)
    filter_drops(mods[22], runtime)

    for mid, dump in mods.items():
        for idx, p in enumerate(dump.protos):
            for slot, v in enumerate(p.kgc):
                if not isinstance(v, bytes):
                    continue
                updated = v.replace(b'v1.288', b'v1.289')
                if mid == 12 and idx in (76, 22198):
                    updated = updated.replace(b'1.288', b'1.289')
                if updated != v:
                    set_string(p, p.nkgc - 1 - slot, updated)
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encoded = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encoded if mid == 12 else encoded.hex().upper().encode())
    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v289.res').write_bytes(data)
    result = {'version': 'v1.289', 'base_sha256': BASE_SHA, 'bytes': len(data),
              'sha256': hashlib.sha256(data).hexdigest(), 'treatment_dispatchers': HEALS}
    (W / 'build_v289.json').write_text(json.dumps(result, indent=2) + '\n')
    print(result['sha256'], result['bytes'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    parser.add_argument('--rebuild-history', action='store_true')
    args = parser.parse_args()
    build(args.runtime, args.rebuild_history)
