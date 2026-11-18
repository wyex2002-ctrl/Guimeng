"""Link the hero hit hook and reuse the database poison callback."""
import argparse
import hashlib
import json
import struct
import subprocess
import zlib

from bytecode_relocate import numeric_and_debug, replace_instructions
from ljdis import OPS
from ljtool import Dump, Proto, rc4, uleb
from patch_v139 import W, abc, ad, encstr, gcid, jump, rebuild_dump, rebuild_proto
from patch_v201 import set_string
from resource_tools import decode, numbers
from runtime import ensure_runtime

BASE_SHA = '7d6232fef42264b4982324165535761d31eac20d088571b0ed5c85bcf6fa5840'
TOKEN = '__gm_poison_token_v282'
PREPARE = '__gm_poison_prepare_v282'
DAMAGE = '__gm_poison_damage_v282'
REQUEST = '__gm_poison_request_v282'
GREEN = '__gm_poison_green_v282'
RED = '__gm_poison_red_v282'
DB_POISON = 4585


def compile_helper(runtime, name, unwrap=False):
    work = W / 'compile_work'
    work.mkdir(exist_ok=True)
    compiler = work / 'compile282.lua'
    compiler.write_text(
        'local s = assert(io.open(arg[1], "rb"))\n'
        'local f = assert(loadstring(s:read("*a"), "@" .. arg[3] .. ".lua"))\n'
        's:close()\n'
        'if arg[4] then f = f() end\n'
        'local o = assert(io.open(arg[2], "wb"))\n'
        'o:write(string.dump(f))\n'
        'o:close()\n'
    )
    source = work / (name + '_gbk.lua')
    source.write_bytes((W / (name + '.lua')).read_text(encoding='utf-8').encode('gbk'))
    output = W / (name + '.ljbc')
    command = [runtime, str(compiler), str(source), str(output), name]
    if unwrap:
        command.append('unwrap')
    subprocess.run(command, check=True)
    dump = Dump(output.read_bytes())
    assert dump.protos[-1].nuv == 0 and dump.rebuild() == dump.raw
    return dump.protos


def add_child(proto):
    logical = proto.nkgc
    proto.kgc.insert(0, ('child',))
    proto.kraw.insert(0, uleb(0))
    proto.nkgc += 1
    proto.flags |= 1
    return logical


def small_key(proto, key):
    logical = gcid(proto, key)
    assert logical < 256
    return logical


def piece(params, frame, code, strings=(), numeric=()):
    """Build an upvalue-free function from pinned existing instructions."""
    raw = bytes([0, params, frame, 0])
    raw += uleb(len(strings)) + uleb(len(numeric)) + uleb(len(code)) + b'\0'
    raw += struct.pack('<' + 'I' * len(code), *code)
    return Proto(raw + b''.join(reversed(strings)) + b''.join(numeric), -1)


def cooldown_and_info(module):
    instance = module.protos[54]
    release = module.protos[55]
    assert instance.gc(0) == '技能信息'.encode('gbk')
    assert instance.bc[118] == jump(118, 157, 8)
    assert instance.bc[147] == jump(147, 151, 8)
    assert instance.bc[156] == abc('TSETS', 9, 8, 49)
    # Reuse the constructor's complete cooldown block. All of its branches
    # stay within the block or go to the following RET0.
    cooldown = [ad('TNEW', 7, 0), abc('TSETS', 0, 7, 0)]
    cooldown.extend(instance.bc[113:157])
    cooldown.append(ad('RET0', 0, 1))
    constants = []
    for i in range(50):
        value = instance.gc(i)
        assert isinstance(value, bytes)
        constants.append(encstr(value))
    cd = piece(1, 11, cooldown, constants, numbers(instance)[1])

    assert release.bc[66] == ad('TDUP', 13, 18)
    assert release.bc[72] == abc('TSETS', 14, 13, 19)
    template = release.kraw[-1 - 18]
    obj = release.kraw[-1 - 19]
    info = piece(1, 2, [ad('TDUP', 1, 0), abc('TSETS', 0, 1, 1), ad('RET1', 1, 2)],
                 [template, obj])
    return cd, info


def patch_hero(module, helper):
    cd, info = cooldown_and_info(module)
    p = module.protos[55]
    assert OPS[p.bc[574] & 255] == 'FNEW' and p.bc[574] >> 8 & 255 == 18
    # R14 is dead on this successful release path. Its upvalue survives as
    # one token even when the release constructs several skill instances.
    prefix = [abc('TGETS', 18, 0, small_key(p, PREPARE)), ad('MOV', 19, 0),
              ad('MOV', 20, 13), ad('MOV', 21, 17), abc('CALL', 18, 2, 4),
              ad('MOV', 14, 18)]
    module.protos[55] = Proto(replace_instructions(p, {574: prefix + [p.bc[574]]})[0], 55)

    p = module.protos[54]
    assert p.nuv == 6 and p.gc(p.bc[5] >> 16 & 255) == '目标'.encode('gbk')
    q = Proto(replace_instructions(p, {5: [
        p.bc[5], ad('UGET', 8, 6), abc('TSETS', 8, 7, small_key(p, TOKEN)),
    ]})[0], 54)
    numeric, debug = numeric_and_debug(q)
    if debug:
        width = 1 if q.lines < 256 else 2 if q.lines < 65536 else 4
        cursor = q.nbc * width
        for _ in range(q.nuv):
            cursor = debug.index(b'\0', cursor) + 1
        debug = debug[:cursor] + b'poison_release\0' + debug[cursor:]
        q.raw = q.raw[:q.kend] + numeric + debug
        q.ndbg = len(debug)
    q.uv += struct.pack('<H', 0x8000 | 14)
    q.nuv += 1
    module.protos[54] = Proto(rebuild_proto(q), 54)

    p = module.protos[51]
    assert p.bc[41:43] == [abc('CALL', 5, 2, 6), ad('GGET', 6, gcid(p, 'type'))]
    # R5..R10 already contain the original damage method and arguments.
    # Preserve the fast original call when there is no eligible release.
    fragment = [ad('UGET', 11, 0), abc('TGETS', 11, 11, small_key(p, TOKEN)),
                ad('ISF', 0, 11), 0, ad('MOV', 12, 5),
                abc('TGETS', 5, 6, small_key(p, DAMAGE)), abc('CALL', 5, 2, 8),
                0, p.bc[41]]
    raw, positions = replace_instructions(p, {41: fragment})
    q = Proto(raw, 51)
    start = positions[41]
    q.bc[start + 3] = jump(start + 3, start + 8, 12)
    q.bc[start + 7] = jump(start + 7, positions[42], 6)
    module.protos[51] = Proto(rebuild_proto(q), 51)

    root = module.protos[-1]
    assert root.idx == 89 and root.bc[158] == ad('GGET', 1, gcid(root, 'Sys'))
    installer_id, cooldown_id, info_id = (add_child(root) for _ in range(3))
    root.frame = 5
    install = [ad('FNEW', 1, installer_id), abc('CALL', 1, 2, 1), ad('MOV', 2, 0),
               ad('FNEW', 3, cooldown_id), ad('FNEW', 4, info_id), abc('CALL', 1, 1, 4)]
    module.protos[-1] = Proto(replace_instructions(root, {158: install + [root.bc[158]]})[0], 89)
    module.protos[89:89] = [*helper, cd, info]


def patch_poison(module, powder):
    p = module.protos[DB_POISON]
    assert len(powder) == 1 and p.uv == bytes.fromhex('01c0')
    assert p.bc[27] == ad('GGET', 7, gcid(p, 'math'))
    assert p.bc[155] == abc('TGETS', 9, 6, small_key(p, '位置'))
    assert numbers(p)[0][4] == 2 and p.bc[157] == jump(157, 175, 9)
    powder_id = add_child(p)
    # The original guard has already checked the learned rank and live target
    # on entry here. Stop before the duration RNG when only paying for powder.
    payment = [ad('ISNES', 4, gcid(p, REQUEST)), 0, ad('FNEW', 7, powder_id),
               ad('MOV', 8, 6), ad('MOV', 9, 2), abc('CALL', 7, 2, 3),
               ad('RET1', 7, 2), p.bc[27]]
    colors = [ad('ISEQS', 4, gcid(p, GREEN)), 0, ad('ISEQS', 4, gcid(p, RED)), 0, p.bc[155]]
    raw, positions = replace_instructions(p, {27: payment, 155: colors})
    q = Proto(raw, DB_POISON)
    pc = positions[27]
    q.bc[pc + 1] = jump(pc + 1, pc + len(payment) - 1, 7)
    pc = positions[155]
    q.bc[pc + 1] = jump(pc + 1, positions[158], 9)
    q.bc[pc + 3] = jump(pc + 3, positions[175], 9)
    module.protos[DB_POISON] = Proto(rebuild_proto(q), DB_POISON)
    module.protos[DB_POISON:DB_POISON] = powder


def build(runtime=None, rebuild_history=False):
    path = W / 'game_v281.res'
    if rebuild_history or not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != BASE_SHA:
        command = ['python3', str(W / 'patch_v281.py')]
        if rebuild_history:
            command.append('--rebuild-history')
        if runtime:
            command.extend(('--runtime', runtime))
        subprocess.run(command, check=True)
    base = path.read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    outer, modules = decode(base, [12, 14, 26, 30])
    runtime = runtime or str(ensure_runtime())
    helper = compile_helper(runtime, 'auto_poison_v282')
    powder = compile_helper(runtime, 'poison_powder_v282', unwrap=True)

    for mid, dump in modules.items():
        for index, proto in enumerate(dump.protos):
            for slot, value in enumerate(proto.kgc):
                if isinstance(value, bytes):
                    updated = value.replace(b'v1.281', b'v1.282')
                    if mid == 12 and index in (76, 22196):
                        updated = updated.replace(b'1.281', b'1.282')
                    if updated != value:
                        proto.kgc[slot] = updated
                        proto.kraw[slot] = encstr(updated)
            dump.protos[index] = Proto(rebuild_proto(proto), index)
    patch_hero(modules[26], helper)
    patch_poison(modules[12], powder)

    for mid, dump in modules.items():
        raw = rebuild_dump(dump, set())
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encoded = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encoded if mid == 12 else encoded.hex().upper().encode())

    data = rc4(rebuild_dump(outer, {0}), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v282.res').write_bytes(data)
    report = {'version': 'v1.282', 'base_sha256': BASE_SHA, 'bytes': len(data),
              'sha256': hashlib.sha256(data).hexdigest(), 'database_poison': DB_POISON + 1,
              'hero_root': len(modules[26].protos) - 1, 'hero_helper_prototypes': len(helper) + 2,
              'shared_base_cooldown_seconds': 1.5, 'powder_notice_seconds': 10}
    (W / 'build_v282.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(report['sha256'], report['bytes'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    parser.add_argument('--rebuild-history', action='store_true')
    args = parser.parse_args()
    build(args.runtime, args.rebuild_history)
