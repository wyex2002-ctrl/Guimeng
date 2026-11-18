"""Run the original hero release, damage and poison paths under LuaJIT 2.0."""
import argparse
import hashlib
import json
import subprocess

from bytecode_relocate import BRANCHES
from ljdis import OPS
from ljtool import Proto
from native_test_utils import standalone, trees
from patch_v139 import W, ad, encstr, jump, rebuild_proto
from patch_v201 import unpack_config
from patch_v282 import BASE_SHA, DB_POISON
from portal_routes_v213 import child_refs
from resource_tools import decode
from runtime import ensure_runtime
from test_v192 import lua

MELEE = ('普通攻击', '攻杀剑术', '刺杀剑术', '烈火剑法', '翔空剑法', '莲月剑法',
         '半月弯刀', '十方斩', '基本剑术', '精神力战法')
RANGED = ('火球术', '大火球', '冰月神掌', '冰月震天', '霹雳掌', '雷电术', '风掌',
          '击风', '月魂断玉', '月魂灵波', '灵魂火符', '灭魂火符')
OTHERS = ('炎天火雨', '炎天火雨_引导', '地狱火', '爆裂火焰', '施毒术',
          '施毒大法', '诱惑之光', '乾坤大挪移', '斗转星移')


def verify_original_instructions(before, after, insertions):
    starts = {}
    added = 0
    for pc in range(before.nbc):
        starts[pc] = pc + added
        added += sum(insertions.get(pc, (0, 0)))
    assert before.nbc + added == after.nbc
    for pc, word in enumerate(before.bc):
        moved = starts[pc] + insertions.get(pc, (0, 0))[0]
        if OPS[word & 255] in BRANCHES:
            target = pc + 1 + (word >> 16) - 32768
            word = (word & 65535) | ((starts[target] - moved - 1 + 32768) << 16)
        assert after.bc[moved] == word, (before.idx, pc, moved)
    for index in range(before.nkgc):
        assert before.gc(index) == after.gc(index), (before.idx, index)


def verify(old, new, build):
    # Each pair counts the instructions before and after the original
    # instruction at the site. Every original jump must enter the same block.
    changed = {12: {DB_POISON: {27: (7, 0), 155: (4, 0)}},
               26: {51: {41: (8, 0)}, 54: {5: (0, 2)}, 55: {574: (6, 0)}, 89: {158: (6, 0)}}}
    for mid, dump in new.items():
        trees(dump)
        assert dump.rebuild() == dump.raw
        before = old[mid].protos
        after = dump.protos
        if mid == 12:
            after = after[:DB_POISON] + after[DB_POISON + 1:]
        elif mid == 26:
            assert len(after) - len(before) == build['hero_helper_prototypes']
            after = after[:89] + after[-1:]
        assert len(before) == len(after)
        for p, q in zip(before, after):
            if p.idx in changed.get(mid, {}):
                verify_original_instructions(p, q, changed[mid][p.idx])
                continue
            restored = Proto(q.raw, q.idx)
            for slot, value in enumerate(restored.kgc):
                if isinstance(value, bytes):
                    back = value.replace(b'v1.282', b'v1.281')
                    if mid == 12 and p.idx in (76, 22196):
                        back = back.replace(b'1.282', b'1.281')
                    if back != value:
                        restored.kgc[slot], restored.kraw[slot] = back, encstr(back)
            assert rebuild_proto(restored) == p.raw, (mid, p.idx)
        for q in dump.protos:
            for pc, word in enumerate(q.bc):
                if OPS[word & 255] in BRANCHES:
                    assert 0 <= pc + 1 + (word >> 16) - 32768 < q.nbc, (mid, q.idx, pc)
    assert old[26].protos[54].bc[113:157] == new[26].protos[-3].bc[2:-1]


def find_config(proto, name):
    wanted = name.encode('gbk')
    for pc, word in enumerate(proto.bc[:-3]):
        if OPS[word & 255] != 'KSTR' or (word >> 8 & 255) != 4 or proto.gc(word >> 16) != wanted:
            continue
        value = proto.bc[pc + 3]
        if OPS[value & 255] == 'KSTR':
            try:
                return unpack_config(proto.gc(value >> 16))
            except (AssertionError, ValueError):
                continue
    raise ValueError(name)


def export_fixtures(old, new, work):
    subtrees = {label: {m: trees(d) for m, d in data.items()}
                for label, data in [('old', old), ('new', new)]}

    def export(mid, idx, name, patches=None, params=None, label='new'):
        d = (new if label == 'new' else old)[mid]
        raw = standalone(d, subtrees[label][mid], idx, patches, params)
        (work / (name + '.ljbc')).write_bytes(raw)

    for label, data in [('old', old), ('new', new)]:
        export(26, len(data[26].protos) - 1, 'class_' + label, label=label)
        export(26, 3, 'tick_' + label, {0: jump(0, 843, 3), 852: ad('RET0', 0, 1)}, label=label)
        db = data[12]
        idx = 6466 + (label == 'new')
        proto = db.protos[idx]
        refs = child_refs(db)
        for name, file in [('施毒术', 'poison'), ('施毒大法', 'area_poison')]:
            marker = ('【数据库/技能脚本/' + name + '】').encode('gbk')
            at = next(i for i, x in enumerate(proto.bc) if OPS[x & 255] == 'KSTR' and proto.gc(x >> 16) == marker)
            assert OPS[proto.bc[at - 2] & 255] == 'FNEW'
            export(12, refs[idx, proto.bc[at - 2] >> 16], file + '_' + label, label=label)

    for mid, idx, name in [
        (20, 8, 'animation'), (20, 6, 'reverse'), (20, 21, 'reset'), (12, 4093, 'skill_factory'),
        (30, 43, 'rotate'), (14, 13, 'public_sys'), (14, 458, 'public_get'), (14, 423, 'dispatch'),
        (14, 301, 'gly_class'), (14, 340, 'hero_api'), (12, 46, 'manual_event'),
        (12, 253, 'powder_refill'), (12, 347, 'green_status'), (12, 352, 'red_status'),
        (12, 166, 'rank_update'), (22, 94, 'add_status'), (22, 91, 'list_status'),
        (46, 7, 'projectile'),
    ]:
        export(mid, idx, name)
    export(14, 420, 'sandbox', {0: ad('UGET', 11, 0), 1: ad('MOV', 12, 0),
                                2: jump(2, 562, 13), 571: ad('RET0', 0, 1)}, 1)
    export(12, 142, 'ranks', {0: ad('TNEW', 1, 0), 1: jump(1, 2616, 2), 2631: ad('RET1', 1, 2)})
    config = old[12].protos[6466]
    configs = {name.encode('gbk'): find_config(config, name) for name in MELEE + RANGED + OTHERS}
    (work / 'configs.lua').write_bytes(('return ' + lua(configs)).encode('gbk'))
    (work / 'scripts.lua').write_text('return {}\n')


def main(runtime):
    work = W / 'native_work/v282'
    work.mkdir(parents=True, exist_ok=True)
    base = (W / 'game_v281.res').read_bytes()
    data = (W / 'game_v282.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    build = json.loads((W / 'build_v282.json').read_text())
    assert hashlib.sha256(data).hexdigest() == build['sha256']
    _, old = decode(base, range(2, 86, 2))
    _, new = decode(data, range(2, 86, 2))
    verify(old, new, build)
    export_fixtures(old, new, work)
    fixture = (W / 'melee_regression_v210.lua').read_text().split("local melee={'普通攻击'")[0]
    fixture = fixture.replace("if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end",
                              "if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')else jit.off()end")
    source = work / 'combat.lua'
    source.write_bytes((fixture + (W / 'auto_poison_regression_v282.lua').read_text()).encode('gbk'))
    runs = []
    for mode in ('normal', 'hot'):
        result = subprocess.run([runtime, str(source), str(work), mode], capture_output=True, timeout=90)
        output = (result.stdout + result.stderr).decode('gbk', 'replace')
        (work / (mode + '.log')).write_text(output)
        assert result.returncode == 0 and 'AUTO_POISON_V282_PASS' in output, (mode, output)
        print(output, flush=True)
        runs.append({'mode': mode, 'output': output})
    names = ('patch_v282.py', 'test_v282.py', 'auto_poison_v282.lua', 'poison_powder_v282.lua',
             'auto_poison_v282.ljbc', 'poison_powder_v282.ljbc', 'auto_poison_regression_v282.lua',
             'melee_regression_v210.lua')
    report = {'version': 'v1.282', 'all_passed': True, 'sha256': build['sha256'], 'runs': runs,
              'all_42_modules_checked': True, 'full_windows_game_run': False,
              'runtime_version': subprocess.check_output([runtime, '-v'], stderr=subprocess.STDOUT).decode().strip(),
              'scope': 'native hero release, instance/update, hit and projectile paths; original skill callbacks, read-only Sys, database sandbox, inventory refill and status application; finite native map, graphics, final HP and bag control bridges',
              'tested_files': {name: hashlib.sha256((W / name).read_bytes()).hexdigest() for name in names}}
    (W / 'validation_v282.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    options = parser.parse_args()
    main(options.runtime or str(ensure_runtime()))
