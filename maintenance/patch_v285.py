"""Route combat notices to the information panel and increase shop powder charges."""
import argparse
import hashlib
import json
import struct
import subprocess
import zlib

from bytecode_relocate import BRANCHES, replace_instructions
from ljdis import OPS
from ljtool import Dump, Proto, rc4
from patch_v139 import W, abc, ad, encstr, gcid, rebuild_dump, rebuild_proto
from patch_v201 import set_string
from patch_v282 import add_child, compile_helper, small_key
from resource_tools import decode
from runtime import ensure_runtime

BASE_SHA = '960952814fa9dff8e3a5114b8e986653d2f395deeed51f05edb9aad7cece5448'


POWDERS = {name.encode('gbk') for name in ('灰色药粉', '黄色药粉')}
SEPARATOR = '附加'.encode('gbk')
SHOP_STOCK = {142: 160, 7783: 7, 8395: 7, 8780: 7, 9149: 7, 10031: 7,
              10635: 7, 11161: 7, 18485: 7}
PANEL_PARENT = 122
MANA_NOTICE = range(200, 217)


def patch_stock(dump):
    count = 0
    for idx, key in SHOP_STOCK.items():
        proto = dump.protos[idx]
        kind, products, fields = proto.gc(key)
        assert kind == 'table' and not fields
        raw = proto.kraw[-1 - key]
        for product in products:
            if not isinstance(product, bytes):
                continue
            row = product.split(SEPARATOR)
            if row[0] not in POWDERS:
                continue
            name, label, price, charges, *currency = row
            assert label.startswith(name + b'(') and int(charges) > 0
            assert not currency if idx != 142 else currency == ['声望'.encode('gbk')]
            updated = SEPARATOR.join([name, label, price, str(int(charges) * 200).encode(), *currency])
            assert raw.count(encstr(product)) == 1
            raw = raw.replace(encstr(product), encstr(updated), 1)
            count += 1
        proto.kraw[-1 - key] = raw
        dump.protos[idx] = Proto(rebuild_proto(proto), idx)
    assert count == 50
    return count


def patch_panel(dump, helper):
    assert len(helper) == 1 and helper[0].nuv == 0
    proto = dump.protos[PANEL_PARENT]
    assert proto.nbc == 36 and proto.bc[34] == ad('UCLO', 0, 32768)
    assert proto.gc(6) == '立体车库'.encode('gbk')
    key = small_key(proto, '孔爱琴泥')
    child = add_child(proto)
    code = [ad('FNEW', 1, child), abc('TSETS', 1, 0, key), proto.bc[34]]
    raw, _ = replace_instructions(proto, {34: code})
    dump.protos[PANEL_PARENT:PANEL_PARENT + 1] = [helper[0], Proto(raw, PANEL_PARENT + 1)]


def patch_hero(dump, runtime):
    poison = compile_helper(runtime, 'auto_poison_v285')
    timing = compile_helper(runtime, 'melee_timing_v285', unwrap=True)
    assert len(dump.protos) == 99 and len(poison) == 9 and len(timing) == 1
    dump.protos[89:98] = poison
    dump.protos[87] = timing[0]

    proto = dump.protos[55]
    assert proto.gc(49) == '法力值不足！无法使用技能！'.encode('gbk')
    assert proto.bc[200] == ad('KSTR', 17, 49) and proto.bc[217] == ad('KPRI', 20, 1)
    assert all(pc in MANA_NOTICE or pc + 1 + (word >> 16) - 32768 not in MANA_NOTICE
               for pc, word in enumerate(proto.bc) if OPS[word & 255] in BRANCHES)
    # The original rejection and all eligibility/cost checks stay in place.
    code = [abc('TGETS', 17, 0, 146), ad('MOV', 18, 0),
            ad('KSTR', 19, gcid(proto, 'low_mana')), abc('CALL', 17, 1, 3)]
    edits = {pc: [] for pc in MANA_NOTICE}
    edits[200] = code
    raw, _ = replace_instructions(proto, edits)
    dump.protos[55] = Proto(raw, 55)


def build(runtime=None, rebuild_history=False):
    path = W / 'game_v284.res'
    if rebuild_history or not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != BASE_SHA:
        command = ['python3', str(W / 'patch_v284.py')]
        if runtime:
            command.extend(('--runtime', runtime))
        if rebuild_history:
            command.append('--rebuild-history')
        subprocess.run(command, check=True)
    base = path.read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    outer, modules = decode(base, [12, 14, 26, 30])
    runtime = runtime or str(ensure_runtime())
    stock_count = patch_stock(modules[12])
    patch_panel(modules[12], compile_helper(runtime, 'information_panel_v285', unwrap=True))
    patch_hero(modules[26], runtime)
    frame = modules[14].protos[427]
    assert '自动出售了白色装备'.encode('gbk') in frame.gc(222)
    source = (W / 'alt_pickup_v285.lua').read_text(encoding='utf-8').encode('gbk')
    set_string(frame, 222, source)

    for mid, dump in modules.items():
        for index, proto in enumerate(dump.protos):
            for slot, value in enumerate(proto.kgc):
                if not isinstance(value, bytes):
                    continue
                updated = value.replace(b'v1.284', b'v1.285')
                if mid == 12 and index in (76, 22198):
                    updated = updated.replace(b'1.284', b'1.285')
                if updated != value:
                    proto.kgc[slot], proto.kraw[slot] = updated, encstr(updated)
            dump.protos[index] = Proto(rebuild_proto(proto), index)
        raw = rebuild_dump(dump, set())
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encoded = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encoded if mid == 12 else encoded.hex().upper().encode())

    data = rc4(rebuild_dump(outer, {0}), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v285.res').write_bytes(data)
    report = {'version': 'v1.285', 'base_sha256': BASE_SHA, 'bytes': len(data),
              'sha256': hashlib.sha256(data).hexdigest(), 'shop_powder_charge_multiplier': 200,
              'shop_powder_listings': stock_count, 'low_mana_notice_ms': 1000,
              'automatic_charge_notice_ms': 10000}
    (W / 'build_v285.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['sha256'], report['bytes'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    parser.add_argument('--rebuild-history', action='store_true')
    args = parser.parse_args()
    build(args.runtime, args.rebuild_history)
