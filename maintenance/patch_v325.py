"""Fix m12/37 (qs_item_box.Main) LuaJIT BC_JMP A=0 snapshot-truncation crash on save load + skip redundant save-load tooltip refresh (v1.325)."""
import hashlib
import json
import struct
import zlib

from ljdis import OPS
from ljtool import Dump, Proto, rc4
from patch_v139 import W, rebuild_proto
from patch_v201 import set_string
from resource_tools import decode

BASE_SHA = '27568ce22e989e95f33fcc0d442241f30b8257cddc52427c8f8146a9ddd41ca0'
MODULES = (12, 14, 30)

# Exact 9 hand-patched JMP instructions in m12/37 (params=5, frame=22) that had A=0,
# causing LuaJIT lj_record.c (`if (ra < J->maxslot) J->maxslot = ra; lj_snap_shrink(J)`)
# to drop live slots (including param r1=a2 and r5=Ux雌) when wrapped_box -> orig_box
# JIT-compiled and side-exited into 数据库.lua:3260 (`ISGT 5 0 1`).
# Format: pc -> (expected_target_pc, new_A_live_slots)
M12_37_JMP_FIXES = {
    4398: (4450, 5),   # ISNEN 0, 2 -> target 4450 (r0..r4 params live)
    4401: (4405, 5),   # ISEQV 1, 12 -> target 4405 (r0..r4 params live)
    4404: (4450, 5),   # ISNEV 1, 408 -> target 4450 (r0..r4 params live)
    4411: (4450, 5),   # ISF 8 -> target 4450 (r0..r4 params live)
    4418: (4450, 5),   # ISEQP 8, nil -> target 4450 (r0..r4 params live)
    4421: (4450, 5),   # ISNES 9, '聚灵符咒_灵' -> target 4450 (r0..r4 params live)
    4427: (4441, 11),  # ISLE 10, 11 -> target 4441 (r0..r10 live)
    4440: (4442, 13),  # JMP -> target 4442 (r0..r12 live; r12 holds screen tip text!)
    4451: (15, 6),     # JMP -> target 15 (r0..r4 params + r5=Ux雌 live, read at pc=15!)
}


def patch_m12_37_jmp_maxslot(m12):
    """Fix A=0 -> exact live slot count on the 9 hand-patched JMPs in m12/37."""
    p = Proto(m12.protos[37].raw, 37)
    assert p.params == 5 and p.frame >= 13 and p.nbc == 4493, (p.params, p.frame, p.nbc)

    fixed = {}
    for pc, (exp_target, new_a) in M12_37_JMP_FIXES.items():
        ins = p.bc[pc]
        op = ins & 0xFF
        old_a = (ins >> 8) & 0xFF
        d = ins >> 16
        target = pc + 1 + d - 0x8000
        assert OPS[op] == 'JMP', f'm12/37 pc={pc} expected JMP, got {OPS[op]}'
        assert old_a == 0, f'm12/37 pc={pc} expected old A=0, got {old_a}'
        assert target == exp_target, f'm12/37 pc={pc} expected target {exp_target}, got {target}'
        assert p.params <= new_a <= p.frame, f'invalid new_a={new_a}'
        p.bc[pc] = (ins & 0xFFFF00FF) | (new_a << 8)
        fixed[pc] = {'target': target, 'old_a': old_a, 'new_a': new_a}

    # Verify ZERO JMP instructions in m12/37 now have A < p.params
    for pc, ins in enumerate(p.bc):
        if OPS[ins & 0xFF] == 'JMP':
            a = (ins >> 8) & 0xFF
            assert a >= p.params, f'm12/37 pc={pc} still has JMP A={a} < params={p.params}'

    new_raw = p.rebuild()
    assert len(new_raw) == len(m12.protos[37].raw), 'm12/37 byte length must remain identical'
    m12.protos[37] = Proto(new_raw, 37)
    return fixed


def patch_module14_init_781(m14, runtime_src):
    """Replace embedded runtime_v324.lua string constant in 14/781 with runtime_v325.lua."""
    p = Proto(m14.protos[781].raw, 781)
    marker = b'-- Guimeng v1.324 runtime helper'
    hits = []
    for slot, val in enumerate(p.kgc):
        if isinstance(val, bytes) and val.startswith(marker):
            hits.append(p.nkgc - 1 - slot)
    assert len(hits) == 1, f'Expected exactly 1 runtime_v324.lua constant in 14/781, found {hits}'
    set_string(p, hits[0], runtime_src.encode('gbk'))
    m14.protos[781] = Proto(rebuild_proto(p), 781)
    return hits[0]


def build():
    base = (W / 'game_v324.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v324.res SHA256 mismatch'

    runtime_src = (W / 'runtime_v325.lua').read_text(encoding='utf-8')
    runtime_gbk = runtime_src.encode('gbk')
    for ch in runtime_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'

    outer, modules = decode(base, MODULES)

    jmp_fixes = patch_m12_37_jmp_maxslot(modules[12])
    runtime_gc_idx = patch_module14_init_781(modules[14], runtime_src)

    version_updates = 0
    for mid, dump in modules.items():
        for p in dump.protos:
            for slot, value in enumerate(p.kgc):
                if not isinstance(value, bytes):
                    continue
                if mid == 14 and p.idx == 781 and (p.nkgc - 1 - slot) == runtime_gc_idx:
                    continue
                updated = value.replace(b'v1.324', b'v1.325')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.324', b'1.325')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    version_updates += 1
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v325.res').write_bytes(data)

    report = {
        'version': 'v1.325',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': '来世续缘 only for gameplay/UI; m12/37 BC_JMP A-slot fix restores LuaJIT bytecode validity without changing 前尘忆梦 behavior',
        'runtime_v325_lua_gbk_bytes': len(runtime_gbk),
        'runtime_gc_index_14_781': runtime_gc_idx,
        'version_string_updates': version_updates,
        'm12_37_jmp_fixes': {str(k): v for k, v in jmp_fixes.items()},
        'save_load_tooltip_refresh_deferred': True,
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v325.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v325.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], 'gc_idx=', runtime_gc_idx, 'ver_updates=', version_updates, 'jmp_fixes=', len(jmp_fixes))


if __name__ == '__main__':
    build()
