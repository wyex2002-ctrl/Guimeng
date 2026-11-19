"""Independent potion cooldowns and shared auto-use for the second story."""
import argparse
import hashlib
import json
import struct
import subprocess
import zlib

from bytecode_relocate import BRANCHES
from ljdis import OPS
from ljtool import Dump, Proto, rc4
from patch_v139 import W, abc, ad, gcid, rebuild_proto
from patch_v201 import set_string
from patch_v241 import water_sites
from patch_v282 import add_child, compile_helper, small_key
from patch_v289 import splice
from portal_routes_v213 import child_refs
from resource_tools import decode
from runtime import ensure_runtime

BASE_SHA = 'be391608138adefeca84958d3486cc02bdfcaaa7f2f5166e502a2751b13bd49d'
MODULES = (12, 14, 30, 34, 40)
KEY = '__gm_potions_v293'
OTHER_STATUS_SCRIPTS = (1029, 1032, 1927, 1930)


def constant(p, r, value):
    return ad('KSTR', r, gcid(p, value))


def core(p, r, action):
    return [
        ad('GGET', r, gcid(p, 'Ux雌')),
        abc('TGETS', r, r, small_key(p, '窗口相关')),
        constant(p, r + 1, KEY),
        abc('TGETV', r, r, r + 1),
        constant(p, r + 1, action),
    ]


def rebuilt(p):
    return Proto(rebuild_proto(p), p.idx)


def put(dump, p, edits, branches=()):
    dump.protos[p.idx] = splice(rebuilt(p), edits, branches)


def insert(dump, added):
    for idx, prototypes in sorted(added.items(), reverse=True):
        dump.protos[idx:idx] = [Proto(p.raw, idx) for p in prototypes]


def assert_no_entry(p, start, stop):
    for pc, word in enumerate(p.bc):
        if OPS[word & 255] in BRANCHES and not start <= pc < stop:
            assert not start < pc + 1 + (word >> 16) - 32768 < stop, (p.idx, pc)


def exact_pack_match(p, at, r, skip):
    assert OPS[p.bc[at] & 255] == 'ISEQS'
    assert p.gc(p.bc[at] >> 16) == '加血蓝'.encode('gbk')
    # Only the preceding pack-type value and R2 (requested group) are live.
    # In the second story, a red/blue request therefore leaves mixed packs for
    # the separate rescue attempt.
    p.frame = max(p.frame, r + 1)
    code = [ad('GGET', r, gcid(p, 'Ux雌')),
            abc('TGETS', r, r, small_key(p, '版本选择')),
            ad('ISEQS', r, gcid(p, '来世续缘')), 0, p.bc[at]]
    return code, (at, 3, skip, r + 1)


def patch_database(d, runtime):
    assert child_refs(d)[264, 194] == 262
    installer = compile_helper(runtime, 'potions_v293', unwrap=True)
    merc_helper = compile_helper(runtime, 'potion_merc_v293', unwrap=True)
    added = {295: installer, 264: merc_helper}

    p = d.protos[295]
    assert p.bc[473] == ad('RET1', 0, 2) and p.frame == 2
    p.frame = 3
    install = add_child(p)
    put(d, p, {473: [ad('FNEW', 1, install), ad('MOV', 2, 0),
                    abc('CALL', 1, 1, 2), p.bc[473]]})

    p = d.protos[20]
    assert_no_entry(p, 1016, 1040)
    fragment = [*core(p, 1, 'tick'), abc('CALL', 1, 2, 2),
                ad('IST', 0, 1), 0, p.bc[1016]]
    put(d, p, {1016: fragment}, [(1016, len(fragment) - 2, 1040, 1)])

    p = d.protos[37]
    assert p.params == 5
    # Native item use passes the same item name and slot as ordinary qs_item_box.
    # The private operations receive the actual display name before stack changes.
    key = small_key(p, '名称')
    evt = [ad('KSHORT', 5, -293 & 65535), ad('ISNEV', 0, 5), 0,
           *core(p, 5, 'gate'), ad('MOV', 6, 3), ad('TNEW', 7, 0),
           abc('TSETS', 2, 7, key), abc('TSETS', 4, 7, small_key(p, '显示名')),
           abc('CALL', 5, 2, 3), ad('RET1', 5, 2), 0]
    # Quick references can unpack a box when empty. Check cooldown before either
    # the recursive item use or that unpack path, after the original UI guards.
    quick = [*core(p, 6, 'gate'), abc('TGETS', 8, 5, small_key(p, '道具')),
             abc('CALL', 6, 2, 3), ad('KSHORT', 7, 65535), ad('ISNEV', 6, 7), 0,
             ad('KPRI', 6, 2), ad('RET1', 6, 2), p.bc[788]]
    put(d, p, {0: evt, 788: quick}, [
        (0, 2, (0, len(evt) - 1), 5),
        (0, len(evt) - 1, 4459, 5),
        (788, 9, (788, len(quick) - 1), 6),
    ])

    p = d.protos[264]
    handler = add_child(p)
    merc = [ad('ISNES', 0, gcid(p, '补丁扣除药品')), 0,
            ad('GGET', 3, gcid(p, 'Ux雌')), abc('TGETS', 3, 3, small_key(p, '版本选择')),
            ad('ISNES', 3, gcid(p, '来世续缘')), 0,
            ad('FNEW', 3, handler), ad('MOV', 4, 1), ad('MOV', 5, 2),
            ad('FNEW', 6, 194), abc('CALL', 3, 2, 4), ad('RET1', 3, 2), p.bc[0]]
    pack, branch = exact_pack_match(p, 95, 8, 97)
    put(d, p, {0: merc, 95: pack}, [(0, 1, (0, len(merc) - 1), 3),
                                   (0, 5, (0, len(merc) - 1), 3), branch])
    p = d.protos[286]
    # The hero's comparison is followed by the same ordinary type check.
    pack, branch = exact_pack_match(p, 42, 8, 44)
    put(d, p, {42: pack}, [branch])

    shared = water_sites(d)
    for idx in shared:
        p = d.protos[idx]
        assert p.uv == bytes.fromhex('01c0') and p.nbc == 375, (idx, p.nbc)
        assert p.gc((p.bc[26] >> 16) & 255) == '道具CD'.encode('gbk')
        assert_no_entry(p, 26, 31)
        frag = [*core(p, 4, 'script'), ad('MOV', 6, 1), ad('MOV', 7, 2),
                abc('CALL', 4, 2, 4), ad('ISF', 0, 4), 0, ad('KSHORT', 5, 1),
                ad('ISEQV', 4, 5), 0, ad('KPRI', 4, 1), ad('RET1', 4, 2)]
        put(d, p, {26: frag, **{pc: [] for pc in range(27, 31)}},
            [(26, 9, 31, 4), (26, 12, 37, 4)])

    # These are the four scroll/stone copies that use the original state.
    # The old refusal also covers unrelated safety conditions. Only an actual
    # active cooldown produces the new message.
    for idx in OTHER_STATUS_SCRIPTS:
        p = d.protos[idx]
        cd = next(pc for pc, word in enumerate(p.bc) if OPS[word & 255] == 'TGETS'
                  and p.gc((word >> 16) & 255) == '道具CD'.encode('gbk'))
        assert p.bc[cd] >> 8 & 255 == 1
        p.frame = max(p.frame, 6)
        at = cd + 1
        frag = [ad('ISEQP', 1, 0), 0, *core(p, 2, 'notice'),
                ad('GGET', 4, gcid(p, 'Gly独')),
                abc('TGETS', 4, 4, small_key(p, '取道具信息_格子')),
                ad('MOV', 5, 0), abc('CALL', 4, 2, 2), abc('CALL', 2, 1, 3),
                p.bc[at]]
        put(d, p, {at: frag}, [(at, 1, (at, len(frag) - 1), 2)])
    insert(d, added)
    return {idx: len(items) for idx, items in added.items()}


def patch_inventory(d, runtime):
    p = d.protos[3]
    helper = compile_helper(runtime, 'potion_use_bridge_v293', unwrap=True)
    child = add_child(p)

    def bridge(base, operation):
        return [ad('FNEW', base, child), constant(p, base + 1, operation),
                ad('MOV', base + 2, 0), ad('MOV', base + 3, 3),
                abc('CALL', base, 2, 4)]

    assert p.gc((p.bc[126] >> 16) & 255) == '分类'.encode('gbk')
    assert p.bc[415] == abc('CALL', 8, 1, 2)
    # Ignore any old name cooldown only for grouped drugs. Handle the legacy
    # cooldown's existing rejection at its original location for other items.
    gate = [*bridge(4, 'gate'), ad('KSHORT', 5, 1), ad('ISEQV', 4, 5), 0,
            ad('KSHORT', 5, 65535), ad('ISEQV', 4, 5), 0, p.bc[126]]
    notice = [*bridge(5, 'notice'), ad('IST', 0, 5), 0, p.bc[139]]
    put(d, p, {126: gate, 139: notice, 415: [p.bc[415], *bridge(8, 'used')]},
        [(126, 7, 163, 4), (126, 10, 161, 4), (139, 6, 161, 5)])
    p = d.protos[22]
    child = add_child(p)
    assert p.bc[24] == abc('DIVVN', 2, 2, 0)
    # R1/R2/R3 carry the name, old duration and task info. Check only on
    # the native path where an old per-item cooldown would actually start.
    skip_old = [
        ad('FNEW', 4, child), constant(p, 5, 'group'), ad('MOV', 6, 0),
        abc('TGETS', 7, 0, small_key(p, '格子组')),
        abc('TGETS', 8, 0, small_key(p, '标识')), abc('TGETV', 7, 7, 8),
        abc('TGETS', 7, 7, small_key(p, '道具')), abc('CALL', 4, 2, 4),
        ad('IST', 0, 4), 0, p.bc[24],
    ]
    put(d, p, {24: skip_old}, [(24, 9, 31, 4)])
    added = {3: helper, 22: helper}
    insert(d, added)
    return {idx: len(items) for idx, items in added.items()}


def patch_ui(d, buffs, runtime):
    helper = compile_helper(runtime, 'potion_ui_v293', unwrap=True)
    p = buffs.protos[19]
    child = add_child(p)
    assert p.bc[708] == abc('TSETS', 7, 5, small_key(p, '精灵'))
    hide = [p.bc[708], ad('FNEW', 7, child), ad('KSHORT', 8, 1), ad('MOV', 9, 0),
            abc('CALL', 7, 2, 3), ad('ISF', 0, 7), 0, ad('KPRI', 7, 1),
            abc('TSETS', 7, 5, small_key(p, '可视'))]
    put(buffs, p, {708: hide}, [(708, 6, 709, 7)])
    insert(buffs, {19: helper})

    p = d.protos[443]
    child = add_child(p)
    edits, branches = {}, []
    for pc, r in ((83, 9), (597, 9), (602, 11), (604, 9)):
        assert p.bc[pc] == abc('TGETS', r, 0, small_key(p, '道具说明'))
        edits[pc] = [ad('FNEW', r, child), ad('KSHORT', r + 1, 2), ad('MOV', r + 2, 0),
                     abc('CALL', r, 2, 3), ad('IST', 0, r), 0, p.bc[pc]]
        branches.append((pc, 5, pc + 1, r))
    put(d, p, edits, branches)
    insert(d, {443: helper})
    return {14: {443: len(helper)}, 40: {19: len(helper)}}


def build(runtime=None, rebuild_history=False):
    path = W / 'game_v292.res'
    if rebuild_history or not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != BASE_SHA:
        args = ['python3', str(W / 'patch_v292.py')]
        if runtime: args.extend(('--runtime', runtime))
        if rebuild_history: args.append('--rebuild-history')
        subprocess.run(args, check=True)
    base = path.read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    outer, modules = decode(base, MODULES)
    runtime = runtime or str(ensure_runtime())
    inserted = {12: patch_database(modules[12], runtime),
                34: patch_inventory(modules[34], runtime),
                **patch_ui(modules[14], modules[40], runtime)}
    for mid, dump in modules.items():
        for p in dump.protos:
            for slot, value in enumerate(p.kgc):
                if not isinstance(value, bytes): continue
                updated = value.replace(b'v1.292', b'v1.293')
                if mid == 12 and p.idx in (76, 22198 + sum(inserted[12].values())):
                    updated = updated.replace(b'1.292', b'1.293')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())
    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v293.res').write_bytes(data)
    report = {'version': 'v1.293', 'base_sha256': BASE_SHA, 'bytes': len(data),
              'sha256': hashlib.sha256(data).hexdigest(), 'inserted_children': inserted}
    (W / 'build_v293.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['sha256'], report['bytes'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    parser.add_argument('--rebuild-history', action='store_true')
    args = parser.parse_args()
    build(args.runtime, args.rebuild_history)
