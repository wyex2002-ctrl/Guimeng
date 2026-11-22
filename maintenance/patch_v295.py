"""Replace window title and in-game version text '魔改版' with '不烧心版' for v1.295."""
import hashlib
import json
import struct
import zlib

from ljtool import Dump, rc4
from patch_v139 import W
from patch_v201 import set_string
from resource_tools import decode

BASE_SHA = '8be49f773196b969d2fcad33a183ecf422e60edb7875dd4d6c0e3f9dcbc38c50'
MODULES = (12, 14, 30)
OLD_LABEL = '魔改版'.encode('gbk')
NEW_LABEL = '不烧心版'.encode('gbk')


def build():
    base_path = W / 'game_v294.res'
    if not base_path.exists():
        lib_res = W.parent / 'Lib' / 'game.res'
        if lib_res.exists() and hashlib.sha256(lib_res.read_bytes()).hexdigest() == BASE_SHA:
            base_path.write_bytes(lib_res.read_bytes())
    base = base_path.read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v294.res SHA256 mismatch'

    outer, modules = decode(base, MODULES)
    replacements = []

    for mid, dump in modules.items():
        for p in dump.protos:
            for slot, value in enumerate(p.kgc):
                if not isinstance(value, bytes):
                    continue
                updated = value.replace(b'v1.294', b'v1.295')
                if mid == 12 and p.idx == 76:
                    updated = updated.replace(OLD_LABEL, NEW_LABEL).replace(b'1.294', b'1.295')
                elif mid == 12 and p.idx == 22232 and OLD_LABEL in updated:
                    updated = updated.replace(OLD_LABEL, NEW_LABEL).replace(b'1.292', b'1.295')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    replacements.append({
                        'module': mid,
                        'proto': p.idx,
                        'slot': p.nkgc - 1 - slot,
                        'before': value.decode('gbk', errors='replace'),
                        'after': updated.decode('gbk', errors='replace'),
                    })
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v295.res').write_bytes(data)
    report = {
        'version': 'v1.295',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'replacements': replacements,
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v295.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v295.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], f'replacements={len(replacements)}')


if __name__ == '__main__':
    build()
