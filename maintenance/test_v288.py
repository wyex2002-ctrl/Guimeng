"""Exercise the changed native battle paths with controlled engine inputs."""
import argparse
import hashlib
import json
import subprocess

from bytecode_relocate import BRANCHES
from ljdis import OPS
from ljtool import Proto
from native_test_utils import standalone, trees
from patch_v139 import W, ad, jump
from patch_v201 import set_string
from patch_v288 import BASE_SHA, MANA_SLOTS
from portal_routes_v213 import child_refs
from resource_tools import decode
from runtime import ensure_runtime
from test_v192 import lua
from test_v282 import MELEE, RANGED, OTHERS, find_config


def verify(old, new):
    allowed = {12: {143, 4587}, 14: set(range(400, 420)), 22: {62}}
    for mid, dump in new.items():
        assert dump.rebuild() == dump.raw
        trees(dump)
        assert len(dump.protos) == len(old[mid].protos)
        for p, q in zip(old[mid].protos, dump.protos):
            if q.idx in allowed.get(mid, ()):
                for pc, word in enumerate(q.bc):
                    if OPS[word & 255] in BRANCHES:
                        assert 0 <= pc + 1 + (word >> 16) - 32768 < q.nbc
                continue
            restored = Proto(q.raw, q.idx)
            for slot, v in enumerate(restored.kgc):
                if isinstance(v, bytes):
                    back = v.replace(b'v1.288', b'v1.287')
                    if mid == 12 and q.idx in (76, 22198):
                        back = back.replace(b'1.288', b'1.287')
                    if back != v:
                        set_string(restored, q.nkgc - 1 - slot, back)
            assert restored.rebuild() == p.raw, (mid, q.idx)


def fixtures(old, new, work):
    subtrees = {m: trees(d) for m, d in new.items()}

    def export(mid, idx, name, patches=None, params=None):
        (work / (name + '.ljbc')).write_bytes(
            standalone(new[mid], subtrees[mid], idx, patches, params))

    export(26, 98, 'class_new')
    export(26, 3, 'tick_new', {0: jump(0, 843, 3), 852: ad('RET0', 0, 1)})
    db = new[12]
    factory = db.protos[6468]
    refs = child_refs(db)
    for name, file in [('施毒术', 'poison'), ('施毒大法', 'area_poison')]:
        marker = ('【数据库/技能脚本/' + name + '】').encode('gbk')
        at = next(i for i, x in enumerate(factory.bc) if OPS[x & 255] == 'KSTR'
                  and factory.gc(x >> 16) == marker)
        assert OPS[factory.bc[at - 2] & 255] == 'FNEW'
        export(12, refs[6468, factory.bc[at - 2] >> 16], file + '_new')
    for mid, idx, name in [
        (20, 8, 'animation'), (20, 6, 'reverse'), (20, 21, 'reset'), (12, 4094, 'skill_factory'),
        (30, 43, 'rotate'), (14, 13, 'public_sys'), (14, 458, 'public_get'),
        (14, 423, 'dispatch'), (14, 301, 'gly_class'), (14, 340, 'hero_api'),
        (12, 46, 'manual_event'), (12, 254, 'powder_refill'), (12, 348, 'green_status'),
        (12, 353, 'red_status'), (12, 167, 'rank_update'), (22, 94, 'add_status'),
        (22, 91, 'list_status'), (46, 7, 'projectile'),
        (14, 419, 'merc_install'), (24, 31, 'map_cell'), (14, 176, 'teleport'),
        (22, 53, 'merc_skill'), (12, 18013, 'chant'),
        (22, 64, 'death_new'), (22, 3, 'spawn'), (12, 194, 'currency_new'),
        (14, 339, 'fx_getter'), (14, 500, 'data_protection'),
    ]:
        export(mid, idx, name)
    (work / 'death_old.ljbc').write_bytes(standalone(old[22], trees(old[22]), 64))
    export(14, 420, 'sandbox', {0: ad('UGET', 11, 0), 1: ad('MOV', 12, 0),
                                2: jump(2, 562, 13), 571: ad('RET0', 0, 1)}, 1)
    export(12, 143, 'ranks', {0: ad('TNEW', 1, 0), 1: jump(1, 2616, 2),
                              2631: ad('RET1', 1, 2)})
    configs = {name.encode('gbk'): find_config(factory, name) for name in MELEE + RANGED + OTHERS}
    (work / 'configs.lua').write_bytes(('return ' + lua(configs)).encode('gbk'))
    (work / 'scripts.lua').write_text('return {}\n')

    cfg = db.protos[143]
    key = '法力转换'.encode('gbk')
    expected = [3, 5, 6, 8, 8, 8, 8, 9, 11, 12, 12, 12,
                12, 14, 15, 17, 17, 17, 17, 18, 20, 23, 23, 23]
    import struct
    for slot, percent in zip(MANA_SLOTS, expected, strict=True):
        old_cfg = old[12].protos[143]
        old_fields, fields = dict(old_cfg.gc(slot)[2]), dict(cfg.gc(slot)[2])
        del old_fields[key]
        _, low, high = fields.pop(key)
        assert old_fields == fields
        assert struct.unpack('<d', struct.pack('<II', low, high))[0] == percent / 100
    assert cfg.bc == old_cfg.bc
    export(12, 143, 'mana_rank', {0: ad('TDUP', 0, 1533), 1: ad('RET1', 0, 2)})
    export(12, 18012, 'mana_damage', {
        0: ad('KNIL', 7, 14), 1: ad('KSHORT', 15, 0),
        2: jump(2, 444, 16), 457: ad('RET1', 15, 2),
    }, 7)


def main(runtime):
    work = W / 'native_work/v288'
    work.mkdir(parents=True, exist_ok=True)
    base, data = ((W / f'game_v{v}.res').read_bytes() for v in (287, 288))
    build = json.loads((W / 'build_v288.json').read_text())
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    assert hashlib.sha256(data).hexdigest() == build['sha256']
    old_outer, old = decode(base, range(2, 86, 2))
    new_outer, new = decode(data, range(2, 86, 2))
    assert old_outer.protos[0].bc == new_outer.protos[0].bc and base[-10:] == data[-10:]
    verify(old, new)
    fixtures(old, new, work)

    melee = (W / 'melee_regression_v210.lua').read_text().split("local melee={'普通攻击'")[0]
    melee = melee.replace("if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end",
                          "if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')else jit.off()end")
    common = (W / 'auto_poison_regression_v282.lua').read_text().split(
        '-- Every supported melee release')[0]
    combat = 'battle_regression_v288.lua'
    files = {'battle.lua': melee + common + (W / combat).read_text(),
             'reputation.lua': (W / 'reputation_regression_v288.lua').read_text()}
    runs = []
    for name, code in files.items():
        source = work / name
        source.write_bytes(code.encode('gbk'))
        for mode in ('normal', 'hot'):
            result = subprocess.run([runtime, str(source), str(work), mode],
                                    capture_output=True, timeout=90)
            output = (result.stdout + result.stderr).decode('gbk', 'replace')
            (work / f'{source.stem}-{mode}.log').write_text(output)
            assert result.returncode == 0 and '_V288_PASS' in output, (mode, output)
            print(output, end='', flush=True)
            runs.append({'suite': source.stem, 'mode': mode, 'output': output})
    names = ('patch_v288.py', 'test_v288.py', 'merc_mode_v288.lua', 'merc_mode_v288.ljbc',
             combat, 'reputation_regression_v288.lua', 'melee_regression_v210.lua',
             'auto_poison_regression_v282.lua')
    report = {'version': 'v1.288', 'all_passed': True, 'sha256': build['sha256'], 'runs': runs,
              'all_42_modules_checked': True, 'full_windows_game_run': False,
              'tested_files': {name: hashlib.sha256((W / name).read_bytes()).hexdigest() for name in names}}
    (W / 'validation_v288.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    args = parser.parse_args()
    main(args.runtime or str(ensure_runtime()))
