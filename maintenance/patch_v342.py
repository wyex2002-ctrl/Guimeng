"""v1.342 patch for 「来世续缘」 only (「前尘忆梦」 untouched):
Adds an aligned manual [Save] button inside the N-key settings window (系统窗口, Window 561):
1. Layout: Anchored between Quit Game (单图按钮12, 62,348,97x25) and [X] (单图按钮10, 241,345,30x30)
   at (167, 348, 66x25) with 8px symmetric spacing and identical height to Quit Game.
2. Visuals: Uses 1:1 3-slice rendering from built-in stone button -1480207602.img (80x25, gold caps)
   verified via D:\\guimeng_art\\guimeng_png_reference (-1480207602.png), with normal / hover /
   pressed / 900ms jade-gold post-save flash states and fallback to -1657209002.img 9-slice.
3. Save Action & Guards: Invokes native Ux雌.窗口相关.存档读档('存档', Ux雌.人物选择, nil, 0)
   with loading, 1000ms debounce, cursor-item, alive-HP, and valid-slot (including slot==0) guards,
   playing 按键音效1 and displaying green/red 屏幕提示 feedback.
4. Retains all v1.341..v1.299 features intact; 「前尘忆梦」 keeps the Save button hidden & disabled.
"""
import hashlib
import json
import struct
import zlib

from ljtool import Dump, Proto, rc4
from patch_v139 import W, rebuild_proto
from patch_v201 import set_string
from resource_tools import decode

BASE_SHA = 'fed99de0e6bd44f3b418e56775eb2beab6ab940971fb120718240f43da8ee55f'
MODULES = (12, 14, 30)


def patch_module14_init_781(m14, runtime_src):
    """Replace embedded runtime_v341.lua string constant in 14/781 with runtime_v342.lua."""
    p = Proto(m14.protos[781].raw, 781)
    marker = b'-- Guimeng v1.341 runtime helper'
    hits = []
    for slot, val in enumerate(p.kgc):
        if isinstance(val, bytes) and val.startswith(marker):
            hits.append(p.nkgc - 1 - slot)
    assert len(hits) == 1, f'Expected exactly 1 runtime_v341.lua constant in 14/781, found {hits}'
    set_string(p, hits[0], runtime_src.encode('gbk'))
    m14.protos[781] = Proto(rebuild_proto(p), 781)
    return hits[0]


def build():
    base = (W / 'game_v341.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v341.res SHA256 mismatch'

    runtime_src = (W / 'runtime_v342.lua').read_text(encoding='utf-8')
    runtime_gbk = runtime_src.encode('gbk')
    for ch in runtime_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'

    outer, modules = decode(base, MODULES)

    runtime_gc_idx = patch_module14_init_781(modules[14], runtime_src)

    version_updates = 0
    for mid, dump in modules.items():
        for p in dump.protos:
            for slot, value in enumerate(p.kgc):
                if not isinstance(value, bytes):
                    continue
                if mid == 14 and p.idx == 781 and (p.nkgc - 1 - slot) == runtime_gc_idx:
                    continue
                updated = value.replace(b'v1.341', b'v1.342')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.341', b'1.342')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    version_updates += 1
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v342.res').write_bytes(data)

    report = {
        'version': 'v1.342',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'runtime_v342_lua_gbk_bytes': len(runtime_gbk),
        'runtime_gc_index_14_781': runtime_gc_idx,
        'version_string_updates': version_updates,
        'changes_v342': {
            'settings_save_button_layout': 'Adds 手动存档按钮_v342 ("Save") in N-key settings window (系统窗口, id=561) aligned between 单图按钮12 (Quit Game, 62,348,97x25) and 单图按钮10 (close [X], 241,345,30x30) at (167, 348, 66x25)',
            'settings_save_button_visuals': 'Uses 1:1 3-slice rendering from built-in stone button -1480207602.img (80x25, metallic gold caps) with normal/hover/pressed/900ms jade-gold confirmation flash states and -1657209002.img 9-slice fallback',
            'settings_save_action_and_guards': 'Invokes native Ux雌.窗口相关.存档读档("存档", Ux雌.人物选择, nil, 0) with loading, 1000ms debounce, cursor-item, alive-HP, and valid-slot (incl. slot==0) guards + 屏幕提示 feedback',
            'qianchi_isolated': '前尘忆梦 keeps Save button hidden and disabled',
        },
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v342.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v342.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], 'gc_idx=', runtime_gc_idx, 'ver_updates=', version_updates)


if __name__ == '__main__':
    build()
