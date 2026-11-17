"""Keep party-animation entry calls adjacent to their live parameters."""
from patch_v276 import *

BASE_SHA = '88550aa91b9e7efc85ac4a2f9300123bc1579e60d00ccb94ac8f407fe0095a78'
ENTRY_SLOTS = {89: (8, 4, 4), 97: (18, 2, 3)}


def repair_entry(p):
    old, new, length = ENTRY_SLOTS[p.idx]
    assert p.params == new and p.nuv == 0
    assert OPS[p.bc[0] & 255] == 'GGET'
    assert p.gc(p.bc[0] >> 16) == b'__gm_party_wait_v262'
    expected = [ad('GGET', old, p.bc[0] >> 16), ad('MOV', old + 1, 0)]
    if p.idx == 89:
        expected.append(ad('MOV', old + 2, 1))
    expected.append(abc('CALL', old, 1, 3 if p.idx == 89 else 2))
    assert p.bc[:length] == expected
    q = Proto(p.raw, p.idx)
    # Only the destination/call register changes. Original parameters, register
    # frame size, branch PCs, constants, debug data and the entire body remain.
    q.bc[:length] = [(ins & ~0xff00) | (((ins >> 8 & 255) - old + new) << 8)
                     for ins in expected]
    return Proto(rebuild_proto(q), p.idx)


def build(runtime=None, rebuild_history=False):
    path = W / 'game_v276.res'
    if rebuild_history or not path.exists():
        subprocess.run(['python3', str(W / 'patch_v276.py')]
                       + (['--rebuild-history'] if rebuild_history else [])
                       + (['--runtime', runtime] if runtime else []), check=True)
    base = path.read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    outer, mods = decode(base, [12, 14, 22, 30])
    for idx in ENTRY_SLOTS:
        mods[22].protos[idx] = repair_entry(mods[22].protos[idx])
    for mid, d in mods.items():
        for i, p in enumerate(d.protos):
            changed = False
            for j, v in enumerate(p.kgc):
                if not isinstance(v, bytes):
                    continue
                new = v.replace(b'v1.276', b'v1.277')
                if mid == 12 and i in [76, 22196]:
                    new = new.replace(b'1.276', b'1.277')
                if new != v:
                    p.kgc[j] = new
                    p.kraw[j] = encstr(new)
                    changed = True
            if changed:
                d.protos[i] = Proto(rebuild_proto(p), i)
        raw = rebuild_dump(d, set())
        assert Dump(raw).rebuild() == raw
        (W / f'module_{mid}_v277.ljbc').write_bytes(raw)
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        enc = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, enc if mid == 12 else enc.hex().upper().encode())
    data = rc4(rebuild_dump(outer, {0}), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v277.res').write_bytes(data)
    report = {'version': 'v1.277', 'base_sha256': BASE_SHA,
              'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
              'entry_registers': {'22/89': [8, 4], '22/97': [18, 2]},
              'changed_business_instructions': 7, 'instruction_counts_unchanged': True,
              'helper_and_animation_bodies_unchanged': True,
              'jit_globally_disabled': False, 'autosave_seconds': 5,
              'blessing_oil_high_drop_test_retained': True, 'player_note_count': 54}
    (W / 'build_v277.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    parser.add_argument('--rebuild-history', action='store_true')
    args = parser.parse_args()
    build(args.runtime, args.rebuild_history)
