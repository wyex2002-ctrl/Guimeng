"""Allow 【一键出售】 button in 「来世续缘」 to sell ordinary-monster corpse-dig materials (v1.305)."""
import hashlib
import json
import struct
import zlib

from ljtool import Dump, Proto, rc4
from patch_v139 import W, rebuild_proto
from patch_v201 import set_string
from resource_tools import decode

BASE_SHA = '3cea4fe6937d0fe9071d55ecb599d7155a2d4251cda56e50793fb6438d54b033'
MODULES = (12, 14, 30)

# All 36 ordinary-monster corpse-dig materials from 12/143 岗位上的().
# Strictly excludes Boss / rare / quest / seal items:
# 商会物资, 沃玛号角, 精灵骸骨, 火影晶体, 震天魔印, 飞龙剑碎片, and all 30 *_印记.
ORDINARY_MOB_MATERIALS = (
    '僵尸骨头', '兔肉', '号角', '夜明珠', '宝玉', '思念珍珠', '指甲',
    '毒蛇胆汁', '毒蜘蛛牙齿', '潘夜之泪', '牙齿', '牛肉', '狼肉',
    '猪肉', '皮', '神灵雕像', '羊毛', '羊肉', '羊角', '蚂蚁卵', '蛆卵',
    '蜘蛛线', '蝎子的尾巴', '褐色栗子', '跳蚤皮', '遗物', '金色栗子',
    '铜色栗子', '银色栗子', '食人花果实', '食人花树叶', '骷髅骨',
    '鸡肉', '鸡血', '鹿肉', '鹿茸',
)


def patch_bulk_sale_14_428(m14):
    """Update 14/428 gc 230 (【一键出售】 Lua script) to also sell ordinary-mob materials in 「来世续缘」."""
    p = Proto(m14.protos[428].raw, 428)
    orig = p.gc(230).decode('gbk')
    assert orig.startswith('local BOOKS={\n')

    mat_lines = ['local MATERIALS={'] + [f'["{nm}"] = true,' for nm in ORDINARY_MOB_MATERIALS] + ['}']
    mat_block = '\n'.join(mat_lines) + '\n\n'

    # 1. Insert MATERIALS table right after BOOKS table
    target_pending = '\nlocal pending\n'
    assert orig.count(target_pending) == 1
    src = orig.replace(target_pending, '\n' + mat_block + 'local pending\n', 1)

    # 2. Update quote(it, U) to accept MATERIALS in 「来世续缘」
    old_quote = (
        "local function quote(it)\n"
        " if not it or it['禁止出售'] then return end\n"
        " local kind\n"
        " if it['分类']=='装备' then kind='装备'\n"
        " elseif it['分类']=='道具' and BOOKS[it['名称']] then kind='技能书'\n"
        " else return end"
    )
    new_quote = (
        "local function quote(it,U)\n"
        " if not it or it['禁止出售'] then return end\n"
        " local kind\n"
        " if it['分类']=='装备' then kind='装备'\n"
        " elseif it['分类']=='道具' and BOOKS[it['名称']] then kind='技能书'\n"
        " elseif U and U['版本选择']=='来世续缘' and MATERIALS[it['名称']] then kind='材料'\n"
        " else return end"
    )
    assert src.count(old_quote) == 1
    src = src.replace(old_quote, new_quote, 1)

    # 3. Update button tooltip text
    old_tip = "['脚本信息']='出售背包内全部装备（含极品）和技能书'"
    new_tip = "['脚本信息']='出售背包内全部装备（含极品）、技能书和普通怪材料'"
    assert src.count(old_tip) == 1
    src = src.replace(old_tip, new_tip, 1)

    # 4. Track materials count & pass U into quote()
    old_scan = (
        " local equipment,books,total,unavailable=0,0,0,0\n"
        " for _,slot in ipairs(hero['背包格子'] or {}) do\n"
        "  local id=slot[1]\n"
        "  if slot[3] and not seen[id] then\n"
        "   seen[id]=true\n"
        "   phase='读取格子'..tostring(id)\n"
        "   local box=slotControl(U,G,id)\n"
        "   -- UI 道具 is a fresh display copy on every access. Quote/snapshot the\n"
        "   -- persistent item instead, so confirmation can verify the real object.\n"
        "   local it=models[id] and models[id]['道具']\n"
        "   local value,kind,quantity=quote(it)\n"
        "   if value and box and callableMethod(box['重置道具']) then\n"
        "    entries[#entries+1]={id=id,box=box,item=it,value=value,quantity=quantity,name=it['名称'],price=it['价格']}\n"
        "    total=total+value\n"
        "    if kind=='装备' then equipment=equipment+quantity else books=books+quantity end\n"
        "   elseif quote(models[id] and models[id]['道具']) then\n"
        "    unavailable=unavailable+1\n"
        "   end\n"
        "  end\n"
        " end\n"
        " if #entries==0 then\n"
        "  if unavailable>0 then notice(U,'暂时无法读取背包，请重新打开背包后再试')\n"
        "  else notice(U,'背包内没有可出售的装备或技能书') end"
    )
    new_scan = (
        " local equipment,books,materials,total,unavailable=0,0,0,0,0\n"
        " for _,slot in ipairs(hero['背包格子'] or {}) do\n"
        "  local id=slot[1]\n"
        "  if slot[3] and not seen[id] then\n"
        "   seen[id]=true\n"
        "   phase='读取格子'..tostring(id)\n"
        "   local box=slotControl(U,G,id)\n"
        "   -- UI 道具 is a fresh display copy on every access. Quote/snapshot the\n"
        "   -- persistent item instead, so confirmation can verify the real object.\n"
        "   local it=models[id] and models[id]['道具']\n"
        "   local value,kind,quantity=quote(it,U)\n"
        "   if value and box and callableMethod(box['重置道具']) then\n"
        "    entries[#entries+1]={id=id,box=box,item=it,value=value,quantity=quantity,name=it['名称'],price=it['价格']}\n"
        "    total=total+value\n"
        "    if kind=='装备' then equipment=equipment+quantity\n"
        "    elseif kind=='技能书' then books=books+quantity\n"
        "    else materials=materials+quantity end\n"
        "   elseif quote(models[id] and models[id]['道具'],U) then\n"
        "    unavailable=unavailable+1\n"
        "   end\n"
        "  end\n"
        " end\n"
        " if #entries==0 then\n"
        "  if unavailable>0 then notice(U,'暂时无法读取背包，请重新打开背包后再试')\n"
        "  else notice(U,'背包内没有可出售的装备、技能书或普通怪材料') end"
    )
    assert src.count(old_scan) == 1
    src = src.replace(old_scan, new_scan, 1)

    # 5. Pass U into quote(it, U) inside sell() confirmation loop
    old_confirm_q = "   local value,kind,quantity=quote(it)\n"
    new_confirm_q = "   local value,kind,quantity=quote(it,U)\n"
    assert src.count(old_confirm_q) == 1
    src = src.replace(old_confirm_q, new_confirm_q, 1)

    # 6. Update confirmation prompt to include 普通怪材料 count
    old_prompt = (
        " local prompt='出售所有装备（含极品）和技能书吗？\\n"
        "背包内装备：'..tostring(equipment)..'件\\n"
        "技能书：'..tostring(books)..'本\\n"
        "合计获得：'..tostring(total)..'金币'"
    )
    new_prompt = (
        " local prompt='出售所有装备（含极品）、技能书和普通怪材料吗？\\n"
        "背包内装备：'..tostring(equipment)..'件\\n"
        "技能书：'..tostring(books)..'本\\n"
        "普通怪材料：'..tostring(materials)..'个\\n"
        "合计获得：'..tostring(total)..'金币'"
    )
    assert src.count(old_prompt) == 1
    src = src.replace(old_prompt, new_prompt, 1)

    # Check GBK 0x5C hazard on every character of the updated Lua script!
    for ch in src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard in 14/428 gc 230: {ch!r}'

    set_string(p, 230, src.encode('gbk'))
    m14.protos[428] = Proto(rebuild_proto(p), 428)
    return len(src.encode('gbk'))


def build():
    base = (W / 'game_v304.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v304.res SHA256 mismatch'

    outer, modules = decode(base, MODULES)
    bulk_sale_bytes = patch_bulk_sale_14_428(modules[14])

    version_updates = 0
    for mid, dump in modules.items():
        for p in dump.protos:
            for slot, value in enumerate(p.kgc):
                if not isinstance(value, bytes):
                    continue
                if mid == 14 and p.idx == 428 and (p.nkgc - 1 - slot) == 230:
                    continue
                updated = value.replace(b'v1.304', b'v1.305')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.304', b'1.305')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    version_updates += 1
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v305.res').write_bytes(data)

    report = {
        'version': 'v1.305',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'bulk_sale_14_428_gc230_gbk_bytes': bulk_sale_bytes,
        'ordinary_mob_materials_count': len(ORDINARY_MOB_MATERIALS),
        'ordinary_mob_materials': list(ORDINARY_MOB_MATERIALS),
        'excluded_rare_boss_quest_materials': [
            '商会物资', '沃玛号角', '精灵骸骨', '火影晶体', '震天魔印', '飞龙剑碎片', '全部30种印记',
        ],
        'version_string_updates': version_updates,
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v305.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v305.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], 'bulk_bytes=', bulk_sale_bytes, 'ver_updates=', version_updates)


if __name__ == '__main__':
    build()
