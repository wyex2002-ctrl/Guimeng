"""Dynamic monster gold drop consolidation (5000 per full pile + remainder) for 「来世续缘」 (v1.297)."""
import hashlib
import json
import struct
import zlib

from ljdis import OPS
from ljtool import Dump, Proto, rc4
from patch_v139 import W, Asm, abc, ad, gcid, rebuild_proto
from patch_v201 import set_string
from patch_v289 import splice
from resource_tools import decode

BASE_SHA = '345acf85e29af000d1a87a3eb3e51fcd300a7eb6516a42968e2095dd12dd913b'
MODULES = (12, 14, 22, 30)


def patch_drop_event_12_14(m12):
    """In 12/14 (【全局事件/物品掉落】), honor pre-calculated R4.金币 when present."""
    p = Proto(m12.protos[14].raw, 14)
    # Verify anchor around PC 92..118
    assert OPS[p.bc[92] & 255] == 'TGETS' and p.gc((p.bc[92] >> 16) & 255) == '小金币'.encode('gbk')
    assert OPS[p.bc[93] & 255] == 'ISEQP' and ((p.bc[93] >> 8) & 255) == 5
    assert OPS[p.bc[94] & 255] == 'JMP'
    assert OPS[p.bc[95] & 255] == 'GGET' and p.gc((p.bc[95] >> 16) & 65535) == 'Gly独'.encode('gbk')
    assert OPS[p.bc[112] & 255] == 'TDUP' and ((p.bc[112] >> 8) & 255) == 5
    gold_k = gcid(p, '金币')
    assert gold_k == 20, gold_k

    # Insert right at PC 95:
    #   if R4.金币 ~= nil then goto PC 112 (return { 显示名 = '金币(' .. R4.金币 .. ')' }) end
    injected = [
        abc('TGETS', 5, 4, gold_k),
        ad('ISNEP', 5, 0),
        0,  # JMP A=5 -> original PC 112
        p.bc[95],
    ]
    patched = splice(p, {95: injected}, ((95, 2, 112, 5),))
    m12.protos[14] = patched
    return len(patched.bc) - p.nbc


def patch_drop_filter_22_96(m22):
    """Extend 22/96 to dynamically consolidate monster gold drops in 「来世续缘」 into 5000-gold piles + remainder."""
    p = Proto(m22.protos[96].raw, 96)
    assert p.params == 1 and p.nuv == 0 and p.nbc == 35
    assert OPS[p.bc[3] & 255] == 'FORI' and (3 + 1 + (p.bc[3] >> 16) - 32768) == 34
    assert OPS[p.bc[33] & 255] == 'FORL'
    assert p.bc[34] == ad('RET0', 0, 1)

    # Replace PC 34 (RET0) with our gold consolidation routine.
    # PC 0..33 (v1.289 scroll/potion filter) remain untouched; both FORI(3 -> 34)
    # and FORL(33 fallthrough -> 34) enter directly at PC 34 with R0..R3 initialized.
    p.bc.pop()  # remove old RET0 at PC 34; Asm starts at base = 34
    a = Asm(p)

    # --- 1. Only active in 「来世续缘」 ---
    # if type(Ae冻) ~= 'table' or Ae冻.版本选择 ~= '来世续缘' then return end
    a.glob(1, 'type')
    a.glob(2, 'Ae冻')
    a.emit('CALL', 1, b=2, c=2)
    a.emit('ISNES', 1, gcid(p, 'table'))
    a.jmp('ret_exit', a=1)
    a.glob(1, 'Ae冻')
    a.get(2, 1, '版本选择')
    a.emit('ISNES', 2, gcid(p, '来世续缘'))
    a.jmp('ret_exit', a=1)

    # --- 2. Read player gold drop bonus: R1 = tonumber(Ae冻.主角金币掉落) or 0 ---
    a.glob(2, 'tonumber')
    a.get(3, 1, '主角金币掉落')
    a.emit('CALL', 2, b=2, c=2)
    a.emit('ISNEP', 2, 0)
    a.jmp('have_bonus', a=3)
    a.emit('KSHORT', 2, 0)
    a.mark('have_bonus')
    a.emit('MOV', 1, 2)       # R1 = bonus
    a.emit('KSHORT', 2, 0)    # R2 = total = 0
    a.emit('KPRI', 3, 0)      # R3 = fallback = nil

    # --- 3. Loop 1: scan drops backwards, roll & sum all gold entries, remove originals ---
    # for i = #drops, 1, -1 do   (R4=#drops, R5=1, R6=-1, R7=i)
    a.emit('LEN', 4, 0)
    a.emit('KSHORT', 5, 1)
    a.emit('KSHORT', 6, -1)
    a.jmp('after_loop1', a=4, op='FORI')

    a.mark('loop1_body')
    a.emit('TGETV', 8, b=0, c=7)      # R8 = entry = drops[i]
    a.get(9, 8, '物品道具')            # R9 = item = entry.物品道具
    a.glob(10, 'type')
    a.emit('MOV', 11, 9)
    a.emit('CALL', 10, b=2, c=2)
    a.emit('ISNES', 10, gcid(p, 'table'))
    a.jmp('next_i', a=8)

    a.get(10, 9, '附加')               # R10 = extra = item.附加
    a.glob(11, 'type')
    a.emit('MOV', 12, 10)
    a.emit('CALL', 11, b=2, c=2)
    a.emit('ISNES', 11, gcid(p, 'table'))
    a.jmp('next_i', a=8)

    a.get(11, 10, '小金币')
    a.emit('ISEQP', 11, 0)
    a.jmp('next_i', a=8)
    a.get(11, 10, '大金币')
    a.emit('ISEQP', 11, 0)
    a.jmp('next_i', a=8)

    # Matched a gold entry! Save fallback item in R3.
    a.emit('MOV', 3, 9)

    # R11 = count = tonumber(entry.掉落数量) or 1; if count < 1 then count = 1 end
    a.glob(11, 'tonumber')
    a.get(12, 8, '掉落数量')
    a.emit('CALL', 11, b=2, c=2)
    a.emit('ISNEP', 11, 0)
    a.jmp('chk_count', a=12)
    a.emit('KSHORT', 11, 1)
    a.mark('chk_count')
    a.emit('KSHORT', 12, 1)
    a.emit('ISGE', 11, 12)
    a.jmp('have_count', a=12)
    a.emit('KSHORT', 11, 1)
    a.mark('have_count')

    # Check if extra.金币 is already pre-rolled: R12 = tonumber(extra.金币)
    a.glob(12, 'tonumber')
    a.get(13, 10, '金币')
    a.emit('CALL', 12, b=2, c=2)
    a.emit('ISEQP', 12, 0)
    a.jmp('roll_gold', a=12)
    # pre ~= nil: total = total + pre * count
    a.emit('MULVV', 12, b=12, c=11)
    a.emit('ADDVV', 2, b=2, c=12)
    a.jmp('remove_entry', a=8)

    a.mark('roll_gold')
    # R12 = lo = tonumber(extra.小金币), R13 = hi = tonumber(extra.大金币)
    a.glob(12, 'tonumber')
    a.get(13, 10, '小金币')
    a.emit('CALL', 12, b=2, c=2)
    a.glob(13, 'tonumber')
    a.get(14, 10, '大金币')
    a.emit('CALL', 13, b=2, c=2)
    a.emit('ISEQP', 12, 0)
    a.jmp('remove_entry', a=8)
    a.emit('ISEQP', 13, 0)
    a.jmp('remove_entry', a=8)

    # Inner loop: for k = 1, count, 1 do  (R14=1, R15=count, R16=1, R17=k)
    a.emit('KSHORT', 14, 1)
    a.emit('MOV', 15, 11)
    a.emit('KSHORT', 16, 1)
    a.jmp('remove_entry', a=14, op='FORI')

    a.mark('inner_body')
    # R18 = g = 引擎:取随机整数(lo, hi)
    a.glob(18, '引擎')
    a.emit('MOV', 19, 18)
    a.get(18, 18, '取随机整数')
    a.emit('MOV', 20, 12)
    a.emit('MOV', 21, 13)
    a.emit('CALL', 18, b=2, c=4)

    # R19 = math.ceil((bonus / 150) * g)  -- matches 12/14 knum[2]=150 exactly
    a.glob(19, 'math')
    a.get(19, 19, 'ceil')
    a.emit('KSHORT', 20, 150)
    a.emit('DIVVV', 20, b=1, c=20)
    a.emit('MULVV', 20, b=20, c=18)
    a.emit('CALL', 19, b=2, c=2)

    # g = (g + R19) * 3; total = total + g
    a.emit('ADDVV', 18, b=18, c=19)
    a.emit('KSHORT', 19, 3)
    a.emit('MULVV', 18, b=18, c=19)
    a.emit('ADDVV', 2, b=2, c=18)
    a.jmp('inner_body', a=14, op='FORL')

    a.mark('remove_entry')
    a.glob(8, 'table')
    a.get(8, 8, 'remove')
    a.emit('MOV', 9, 0)
    a.emit('MOV', 10, 7)
    a.emit('CALL', 8, b=1, c=3)

    a.mark('next_i')
    a.jmp('loop1_body', a=4, op='FORL')

    a.mark('after_loop1')
    # if total <= 0 or fallback == nil then return end
    a.emit('KSHORT', 4, 0)
    a.emit('ISLE', 2, 4)
    a.jmp('ret_exit', a=1)
    a.emit('ISEQP', 3, 0)
    a.jmp('ret_exit', a=1)

    # --- 4. Loop 2: split total into 5000-gold full piles + final remainder pile ---
    a.mark('split_loop')
    a.emit('KSHORT', 4, 0)
    a.emit('ISLE', 2, 4)
    a.jmp('ret_exit', a=4)
    a.jmp('ret_exit', a=4, op='LOOP')

    # R4 = pile = (total > 5000) and 5000 or total; total = total - pile
    a.emit('MOV', 4, 2)
    a.emit('KSHORT', 5, 5000)
    a.emit('ISLE', 4, 5)
    a.jmp('keep_pile', a=5)
    a.emit('KSHORT', 4, 5000)
    a.mark('keep_pile')
    a.emit('SUBVV', 2, b=2, c=4)

    # Select visual coin template tier name into R5 based on pile value
    a.emit('KSHORT', 6, 60)
    a.emit('ISGT', 4, 6)
    a.jmp('chk_small', a=5)
    a.const(5, '金币_极小')
    a.jmp('got_tier', a=6)

    a.mark('chk_small')
    a.emit('KSHORT', 6, 600)
    a.emit('ISGT', 4, 6)
    a.jmp('chk_mid', a=5)
    a.const(5, '金币_小')
    a.jmp('got_tier', a=6)

    a.mark('chk_mid')
    a.emit('KSHORT', 6, 2400)
    a.emit('ISGT', 4, 6)
    a.jmp('chk_big', a=5)
    a.const(5, '金币_中')
    a.jmp('got_tier', a=6)

    a.mark('chk_big')
    a.emit('KSHORT', 6, 4500)
    a.emit('ISGT', 4, 6)
    a.jmp('tier_huge', a=5)
    a.const(5, '金币_大')
    a.jmp('got_tier', a=6)

    a.mark('tier_huge')
    a.const(5, '金币_极大')

    a.mark('got_tier')
    # R6 = tpl = Sys.get('item', tier); if type(tpl) ~= 'table' then tpl = fallback end
    a.glob(6, 'Sys')
    a.get(6, 6, 'get')
    a.const(7, 'item')
    a.emit('MOV', 8, 5)
    a.emit('CALL', 6, b=2, c=3)
    a.glob(7, 'type')
    a.emit('MOV', 8, 6)
    a.emit('CALL', 7, b=2, c=2)
    a.emit('ISEQS', 7, gcid(p, 'table'))
    a.jmp('have_tpl', a=7)
    a.emit('MOV', 6, 3)

    a.mark('have_tpl')
    # R7 = copy = table.copy(tpl)
    a.glob(7, 'table')
    a.get(7, 7, 'copy')
    a.emit('MOV', 8, 6)
    a.emit('CALL', 7, b=2, c=2)

    # R8 = extra = copy.附加; if type(extra) ~= 'table' then extra = {}; copy.附加 = extra end
    a.get(8, 7, '附加')
    a.glob(9, 'type')
    a.emit('MOV', 10, 8)
    a.emit('CALL', 9, b=2, c=2)
    a.emit('ISEQS', 9, gcid(p, 'table'))
    a.jmp('have_extra', a=9)
    a.emit('TNEW', 8, 0)
    a.set(8, 7, '附加')

    a.mark('have_extra')
    a.set(4, 8, '金币')

    # table.insert(drops, { 物品道具 = copy, 掉落数量 = 1 })
    a.glob(9, 'table')
    a.get(9, 9, 'insert')
    a.emit('MOV', 10, 0)
    a.emit('TNEW', 11, 0)
    a.set(7, 11, '物品道具')
    a.emit('KSHORT', 12, 1)
    a.set(12, 11, '掉落数量')
    a.emit('CALL', 9, b=1, c=3)
    a.jmp('split_loop', a=4)

    a.mark('ret_exit')
    a.emit('RET0', 0, 1)
    a.finish()

    p.frame = 24
    rebuilt = Proto(rebuild_proto(p), 96)
    m22.protos[96] = rebuilt
    return rebuilt.nbc


def build():
    base = (W / 'game_v296.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v296.res SHA256 mismatch'

    outer, modules = decode(base, MODULES)
    added_12_14 = patch_drop_event_12_14(modules[12])
    nbc_22_96 = patch_drop_filter_22_96(modules[22])

    version_updates = 0
    for mid, dump in modules.items():
        if mid in (12, 14, 30):
            for p in dump.protos:
                for slot, value in enumerate(p.kgc):
                    if not isinstance(value, bytes):
                        continue
                    updated = value.replace(b'v1.296', b'v1.297')
                    if mid == 12 and p.idx in (76, 22232):
                        updated = updated.replace(b'1.296', b'1.297')
                    if updated != value:
                        set_string(p, p.nkgc - 1 - slot, updated)
                        version_updates += 1
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v297.res').write_bytes(data)
    report = {
        'version': 'v1.297',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'gold_pile_cap': 5000,
        'split_mode': 'dynamic_5000_plus_remainder',
        'scope': '来世续缘 only',
        'proto_12_14_added_instructions': added_12_14,
        'proto_22_96_total_instructions': nbc_22_96,
        'version_string_updates': version_updates,
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v297.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v297.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], f'12/14 +{added_12_14}, 22/96={nbc_22_96} insns')


if __name__ == '__main__':
    build()
