"""Add Blessing Oil to reputation shop, add 1s lightweight auto-pickup toggle, and pre-generate mount oil batches (v1.299)."""
import hashlib
import json
import struct
import zlib

from ljdis import OPS
from ljtool import Dump, Proto, rc4
from patch_v139 import W, abc, ad, gcid, rebuild_proto
from patch_v181 import save_table
from patch_v201 import set_string
from patch_v289 import splice
from resource_tools import decode

BASE_SHA = 'fec3c995db817d5a80995230dffbf3850e73d7fb7654fce8ed8c22f7e9380005'
MODULES = (12, 14, 30)
REP_OIL_ENTRY = '祝福油附加祝福油附加2000附加0附加声望'


def patch_reputation_shop_12_143(m12):
    """Prepend Blessing Oil (2,000 reputation) to slot 1 of 「来世续缘」 reputation shop."""
    p = Proto(m12.protos[143].raw, 143)
    assert OPS[p.bc[250] & 255] == 'ISNES' and p.gc((p.bc[250] >> 16) & 65535) == '来世续缘'.encode('gbk')
    assert OPS[p.bc[286] & 255] == 'TDUP' and ((p.bc[286] >> 16) & 65535) == 160
    assert OPS[p.bc[287] & 255] == 'TSETS' and p.gc((p.bc[287] >> 16) & 255) == '声望'.encode('gbk')

    t = p.gc(160)
    assert isinstance(t, tuple) and t[0] == 'table'
    arr, hash_pairs = t[1], t[2]
    assert arr[0] is None and len(arr) == 54
    assert arr[1] == '随机传送石附加随机传送石附加15附加0附加声望'.encode('gbk')

    entry_b = REP_OIL_ENTRY.encode('gbk')
    assert entry_b not in arr
    new_arr = [None, entry_b] + list(arr[1:])
    save_table(p, 160, ('table', new_arr, hash_pairs))
    m12.protos[143] = Proto(rebuild_proto(p), 143)
    return len(arr) - 1, len(new_arr) - 1


def patch_shop_stackable_whitelist(m12):
    """Remove non-stackable 祝福油 from 12/217 & 12/220 stackable-consumable fast-buy whitelist."""
    oil_b = '祝福油'.encode('gbk')
    removed = []
    for pid in (217, 220):
        p = Proto(m12.protos[pid].raw, pid)
        t = p.gc(3)
        assert isinstance(t, tuple) and t[0] == 'table'
        assert any(k == oil_b for k, _ in t[2]), f'12/{pid} missing 祝福油 in gc(3)'
        new_hash = [(k, v) for k, v in t[2] if k != oil_b]
        save_table(p, 3, ('table', t[1], new_hash))
        m12.protos[pid] = Proto(rebuild_proto(p), pid)
        removed.append(pid)
    return removed


def patch_reputation_buy_rollback_12_218(m12):
    """In 12/218 (reputation shop buy confirm), validate finite integer qty and rollback reputation on grant failure."""
    p = Proto(m12.protos[218].raw, 218)
    assert OPS[p.bc[17] & 255] == 'ISGT'
    assert OPS[p.bc[18] & 255] == 'JMP'
    assert OPS[p.bc[19] & 255] == 'RET0'
    assert OPS[p.bc[20] & 255] == 'JMP'
    assert OPS[p.bc[77] & 255] == 'CALL' and ((p.bc[77] >> 8) & 255) == 1
    assert OPS[p.bc[78] & 255] == 'TSETB'
    assert OPS[p.bc[176] & 255] == 'CALL' and ((p.bc[176] >> 8) & 255) == 0
    assert OPS[p.bc[177] & 255] == 'RET0'

    k_ux = gcid(p, 'Ux雌')
    k_win = gcid(p, '窗口相关')
    k_ui = gcid(p, '界面切换')
    k_rep = gcid(p, '声望')
    assert max(k_ux, k_win, k_ui, k_rep) < 256

    # Reject non-integer / NaN / inf quantities (qty % 1 == 0 holds iff finite integer).
    # Note: original PC 20 is JMP A=5 -> 178; relocate it explicitly via extra_jumps!
    assert (20 + 1 + (p.bc[20] >> 16) - 32768) == 178
    inj_20 = [
        ad('UGET', 0, 0),
        ad('KSHORT', 1, 1),
        abc('MODVV', 1, 0, 1),
        ad('KSHORT', 2, 0),
        ad('ISEQV', 1, 2),
        0,                  # JMP A=0 -> (20, 7) (relocated orig PC 20)
        ad('RET0', 0, 1),
        0,                  # JMP A=5 -> (178, 0) (orig PC 20 jump target!)
    ]
    # If 取道具信息_名称 returned nil (R1 == nil -> ISEQP true -> jump), rollback reputation and exit safely.
    inj_78 = [
        ad('ISEQP', 1, 0),
        0,                  # JMP A=0 -> (176, 3) (reputation rollback)
        p.bc[78],
    ]
    # Capture ok = Gly独.增加物品(...); if falsy, refund +(price * qty) reputation.
    inj_176 = [
        abc('CALL', 0, 2, 4),       # 0: capture return value in R0
        ad('IST', 0, 0),            # 1: if truthy -> skip rollback
        0,                          # 2: JMP A=0 -> (177, 0) (orig RET0)
        ad('GGET', 0, k_ux),        # 3: rollback start
        abc('TGETS', 0, 0, k_win),  # 4
        abc('TGETS', 0, 0, k_ui),   # 5
        ad('UGET', 1, 1),           # 6: U1
        abc('TGETB', 1, 1, 3),      # 7: price (number)
        ad('UGET', 2, 0),           # 8: qty
        abc('MULVV', 1, 1, 2),      # 9: +total
        ad('KSTR', 2, k_rep),       # 10: '声望'
        abc('CALL', 0, 1, 3),       # 11: refund reputation
    ]
    patched = splice(
        p,
        {20: inj_20, 78: inj_78, 176: inj_176},
        (
            (20, 5, (20, 7), 0),
            (20, 7, (178, 0), 5),
            (78, 1, (176, 3), 0),
            (176, 2, (177, 0), 0),
        ),
    )
    m12.protos[218] = patched
    return len(patched.bc) - p.nbc


def patch_module14_init_781(m14, runtime_src):
    """Compile and execute runtime_v299.lua once during module 14 Sys initialization."""
    p = Proto(m14.protos[781].raw, 781)
    assert OPS[p.bc[285] & 255] == 'CALL'
    assert OPS[p.bc[286] & 255] == 'UGET' and ((p.bc[286] >> 8) & 255) == 2

    k_loadstring = gcid(p, 'loadstring')
    k_src = gcid(p, runtime_src)
    inj_286 = [
        ad('GGET', 2, k_loadstring),
        ad('KSTR', 3, k_src),
        abc('CALL', 2, 2, 2),
        ad('ISF', 0, 2),
        0,                  # JMP A=2 -> (286, 7) (orig PC 286)
        ad('MOV', 3, 0),
        abc('CALL', 2, 1, 2),
        p.bc[286],
    ]
    patched = splice(p, {286: inj_286}, ((286, 4, (286, 7), 2),))
    m14.protos[781] = patched
    return len(patched.bc) - p.nbc


def patch_frame_loop_14_428(m14):
    """Route frame Alt + 1s lightweight auto-pickup check through cached _G.__gm_pickup_frame_v299."""
    p = Proto(m14.protos[428].raw, 428)
    assert OPS[p.bc[2956] & 255] == 'GGET' and p.gc((p.bc[2956] >> 16) & 65535) == '引擎'.encode('gbk')
    assert OPS[p.bc[2973] & 255] == 'CALL' and ((p.bc[2973] >> 8) & 255) == 1
    assert OPS[p.bc[2974] & 255] == 'GGET' and p.gc((p.bc[2974] >> 16) & 65535) == 'Ae冻集'.encode('gbk')
    assert p.gc(219) == 'script_setting'.encode('gbk')
    assert p.gc(220) == 'Ux雌'.encode('gbk')
    assert p.gc(221) == 'Gly独'.encode('gbk')

    # Note: 14/428 has nkgc > 255, so use 16-bit GGET for the new global and existing <256 IDs for TGETS.
    k_frame = gcid(p, '__gm_pickup_frame_v299')
    inj_2956 = [
        ad('GGET', 1, k_frame),     # 0: _G.__gm_pickup_frame_v299
        ad('ISF', 0, 1),            # 1: fallback if nil
        0,                          # 2: JMP A=1 -> (2956, 9) (orig PC 2956)
        ad('UGET', 2, 0),           # 3: S
        abc('TGETS', 2, 2, 219),    # 4: S.script_setting
        abc('TGETS', 3, 2, 221),    # 5: Gly独
        abc('TGETS', 2, 2, 220),    # 6: Ux雌
        abc('CALL', 1, 1, 3),       # 7: pickup_frame(Ux雌, Gly独)
        0,                          # 8: JMP A=1 -> (2974, 0) (skip legacy per-press loadstring)
        p.bc[2956],                 # 9: orig PC 2956 fallback
    ]
    patched = splice(
        p,
        {2956: inj_2956},
        (
            (2956, 2, (2956, 9), 1),
            (2956, 8, (2974, 0), 1),
        ),
    )
    m14.protos[428] = patched
    return len(patched.bc) - p.nbc


def patch_add_item_14_456(m14):
    """After creating each non-stackable item in slot R9, pre-generate mount oil batch."""
    p = Proto(m14.protos[456].raw, 456)
    assert OPS[p.bc[404] & 255] == 'CALL' and ((p.bc[404] >> 8) & 255) == 16
    assert OPS[p.bc[405] & 255] == 'UGET' and ((p.bc[405] >> 8) & 255) == 16
    assert OPS[p.bc[406] & 255] == 'TGETS' and p.gc((p.bc[406] >> 16) & 255) == 'qs_item_box'.encode('gbk')

    k_hook = gcid(p, '__gm_on_slot_item_v299')
    k_src = gcid(p, 'add_item')
    assert max(k_hook, k_src) < 256

    inj_405 = [
        ad('UGET', 16, 0),
        abc('TGETS', 16, 16, k_hook),
        ad('ISF', 0, 16),
        0,                          # JMP A=16 -> (405, 7)
        ad('MOV', 17, 9),           # R9 = newly populated slot_id
        ad('KSTR', 18, k_src),
        abc('CALL', 16, 1, 3),
        p.bc[405],
    ]
    patched = splice(p, {405: inj_405}, ((405, 3, (405, 7), 16),))
    m14.protos[456] = patched
    return len(patched.bc) - p.nbc


def patch_reset_item_14_481(m14):
    """After resetting a slot item (outside save load), pre-generate mount oil batch."""
    p = Proto(m14.protos[481].raw, 481)
    assert OPS[p.bc[148] & 255] == 'CALL' and ((p.bc[148] >> 8) & 255) == 11
    assert OPS[p.bc[149] & 255] == 'UGET' and ((p.bc[149] >> 8) & 255) == 11
    assert OPS[p.bc[150] & 255] == 'TGETS' and p.gc((p.bc[150] >> 16) & 255) == '包裹物品组'.encode('gbk')

    k_hook = gcid(p, '__gm_on_slot_item_v299')
    k_src = gcid(p, 'reset_item')
    assert max(k_hook, k_src) < 256

    inj_149 = [
        ad('UGET', 11, 0),
        abc('TGETS', 11, 11, k_hook),
        ad('ISF', 0, 11),
        0,                          # JMP A=11 -> (149, 7)
        ad('MOV', 12, 6),           # R6 = slot_id
        ad('KSTR', 13, k_src),
        abc('CALL', 11, 1, 3),
        p.bc[149],
    ]
    patched = splice(p, {149: inj_149}, ((149, 3, (149, 7), 11),))
    m14.protos[481] = patched
    return len(patched.bc) - p.nbc


def patch_drop_item_14_446(m14):
    """At entry of 掉落物品(mode, item, ...), pre-generate mount oil batch before spawning on ground."""
    p = Proto(m14.protos[446].raw, 446)
    assert OPS[p.bc[0] & 255] == 'MOV' and ((p.bc[0] >> 8) & 255) == 7

    k_hook = gcid(p, '__gm_ensure_mount_batch_v299')
    k_src = gcid(p, 'drop_item')
    assert max(k_hook, k_src) < 256

    # R0..R6 are parameters -> R7..R9 has zero uninitialized call gap!
    inj_0 = [
        ad('UGET', 7, 0),
        abc('TGETS', 7, 7, k_hook),
        ad('ISF', 0, 7),
        0,                          # JMP A=7 -> (0, 7)
        ad('MOV', 8, 1),            # R1 = item
        ad('KSTR', 9, k_src),
        abc('CALL', 7, 1, 3),
        p.bc[0],
    ]
    patched = splice(p, {0: inj_0}, ((0, 3, (0, 7), 7),))
    m14.protos[446] = patched
    return len(patched.bc) - p.nbc


def patch_load_save_14_256(m14):
    """Mark save-loading scope in 14/256 and run one-time idempotent mount migration at load.return."""
    p = Proto(m14.protos[256].raw, 256)
    assert OPS[p.bc[108] & 255] == 'KPRI' and ((p.bc[108] >> 8) & 255) == 10
    assert OPS[p.bc[110] & 255] == 'RET1'
    assert OPS[p.bc[198] & 255] == 'KPRI' and ((p.bc[198] >> 8) & 255) == 10
    assert OPS[p.bc[200] & 255] == 'RET1'
    assert OPS[p.bc[1062] & 255] == 'RET1' and ((p.bc[1062] >> 8) & 255) == 4
    assert OPS[p.bc[1063] & 255] == 'UGET' and ((p.bc[1063] >> 8) & 255) == 32
    assert OPS[p.bc[1136] & 255] == 'UGET' and ((p.bc[1136] >> 8) & 255) == 35

    k_hook = gcid(p, '__gm_load_state_v299')
    assert k_hook < 256

    def make_call(pc, reg, loading_pri, migrate_pri):
        return [
            ad('UGET', reg, 0),
            abc('TGETS', reg, reg, k_hook),
            ad('ISF', 0, reg),
            0,                              # JMP A=reg -> (pc, 7)
            ad('KPRI', reg + 1, loading_pri),
            ad('KPRI', reg + 2, migrate_pri),
            abc('CALL', reg, 1, 3),
            p.bc[pc],
        ]

    repl = {
        108: make_call(108, 11, 1, 1),    # fail return 1 -> loading=false, migrate=false (R0..R10 live)
        198: make_call(198, 11, 1, 1),    # fail return 2 -> loading=false, migrate=false (R0..R10 live)
        1062: make_call(1062, 5, 1, 1),   # fail return 3 -> loading=false, migrate=false (R0..R4 live)
        1063: make_call(1063, 3, 2, 1),   # load.begin -> loading=true, migrate=false (R0..R2 params; zero gap!)
        1136: make_call(1136, 24, 1, 2),  # load.return -> loading=false, migrate=true (R0..R23 live; zero gap!)
    }
    jumps = (
        (108, 3, (108, 7), 11),
        (198, 3, (198, 7), 11),
        (1062, 3, (1062, 7), 5),
        (1063, 3, (1063, 7), 3),
        (1136, 3, (1136, 7), 24),
    )
    patched = splice(p, repl, jumps)
    m14.protos[256] = patched
    return len(patched.bc) - p.nbc


def build():
    base = (W / 'game_v298.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v298.res SHA256 mismatch'
    runtime_src = (W / 'runtime_v299.lua').read_text(encoding='utf-8')
    # Ensure GBK-encodable and free of GBK 0x5C backslash hazards.
    runtime_gbk = runtime_src.encode('gbk')
    for ch in runtime_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'

    outer, modules = decode(base, MODULES)

    old_rep_cnt, new_rep_cnt = patch_reputation_shop_12_143(modules[12])
    wl_removed = patch_shop_stackable_whitelist(modules[12])
    add_12_218 = patch_reputation_buy_rollback_12_218(modules[12])
    add_14_781 = patch_module14_init_781(modules[14], runtime_src)
    add_14_428 = patch_frame_loop_14_428(modules[14])
    add_14_456 = patch_add_item_14_456(modules[14])
    add_14_481 = patch_reset_item_14_481(modules[14])
    add_14_446 = patch_drop_item_14_446(modules[14])
    add_14_256 = patch_load_save_14_256(modules[14])

    version_updates = 0
    for mid, dump in modules.items():
        for p in dump.protos:
            for slot, value in enumerate(p.kgc):
                if not isinstance(value, bytes):
                    continue
                updated = value.replace(b'v1.298', b'v1.299')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.298', b'1.299')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    version_updates += 1
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v299.res').write_bytes(data)
    report = {
        'version': 'v1.299',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'reputation_shop': {
            'proto': '12/143',
            'slot1_entry': REP_OIL_ENTRY,
            'old_count': old_rep_cnt,
            'new_count': new_rep_cnt,
            'whitelist_removed_oil': wl_removed,
            'rollback_proto': '12/218',
        },
        'runtime_v299_lua_gbk_bytes': len(runtime_gbk),
        'added_instructions': {
            '12/218': add_12_218,
            '14/781': add_14_781,
            '14/428': add_14_428,
            '14/456': add_14_456,
            '14/481': add_14_481,
            '14/446': add_14_446,
            '14/256': add_14_256,
        },
        'version_string_updates': version_updates,
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v299.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v299.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], report['added_instructions'])


if __name__ == '__main__':
    build()
