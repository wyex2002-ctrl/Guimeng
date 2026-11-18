"""Check game-resource scope and run the original LuaJIT combat and UI paths."""
import argparse
from collections import Counter
import hashlib
import json
import subprocess

from bytecode_relocate import BRANCHES, replace_instructions
from ljdis import OPS
from native_test_utils import standalone, trees
from patch_v139 import W, abc, ad, jump
from patch_v201 import set_string
from patch_v287 import BASE_SHA
from resource_tools import decode
from runtime import ensure_runtime
from test_v192 import lua
from test_v282 import export_fixtures


def verify(old, new, build):
    assert build['base_sha256'] == BASE_SHA
    changed_helpers = {26: {87, *range(89, 98)}, 76: {0}}
    versions = []
    for mid, dump in new.items():
        assert dump.rebuild() == dump.raw
        trees(dump)
        assert len(dump.protos) == len(old[mid].protos)
        for before, after in zip(old[mid].protos, dump.protos):
            idx = before.idx
            if idx in changed_helpers.get(mid, ()):
                if (mid, idx) == (76, 0):
                    assert after.params == 3 and after.nuv == 0
                else:
                    assert before.params == after.params
                    if idx not in (91, 92):
                        assert before.uv == after.uv
                for pc, word in enumerate(after.bc):
                    if OPS[word & 255] in BRANCHES:
                        assert 0 <= pc + 1 + (word >> 16) - 32768 < after.nbc
                continue
            if (mid, idx) == (76, 1):
                raw, mp = replace_instructions(before, {504: [ad('MOV', 20, 0), abc('CALL', 17, 2, 4)]})
                assert raw == after.raw
                assert {str(pc): value for pc, value in mp.items()} == build['ground_constructor_relocation']
                continue
            if (mid, idx) == (14, 427):
                assert after.gc(222) == (W / 'alt_pickup_v287.lua').read_text().encode('gbk')
                set_string(after, 222, before.gc(222))
            for slot, value in enumerate(after.kgc):
                if not isinstance(value, bytes):
                    continue
                back = value.replace(b'v1.287', b'v1.286')
                if mid == 12 and idx in (76, 22198):
                    back = back.replace(b'1.287', b'1.286')
                if back != value:
                    set_string(after, after.nkgc - 1 - slot, back)
                    versions.append([mid, idx])
            assert after.rebuild() == before.raw, (mid, idx)
    assert versions == build['version_slots']


def ground_templates(dump):
    proto = dump.protos[4093]
    samples = {}
    counts = Counter()
    for pc, instruction in enumerate(proto.bc):
        if OPS[instruction & 255] != 'TDUP':
            continue
        value = proto.gc(instruction >> 16)
        if not isinstance(value, tuple) or value[0] != 'table':
            continue
        fields = dict(value[2])
        name = fields.get('名称'.encode('gbk'), b'').decode('gbk')
        if not name:
            continue
        properties = [proto.gc(word >> 16).decode('gbk') for word in proto.bc[max(0, pc - 65):pc]
                      if OPS[word & 255] == 'KSTR' and (word >> 8) & 255 == 4]
        extra = {}
        for entry in properties[-1].split('ぃ') if properties else ():
            if 'ぅ' in entry:
                key, data = entry.split('ぅ', 1)
                extra[key.encode('gbk')] = int(data) if data.isdigit() else data.encode('gbk')
        if name.startswith('金币_'):
            category = 'coin'
        elif name in ('太阳水', '强效太阳水', '强效太阳水_包'):
            category = 'sun'
        elif name.startswith(('金创药_', '魔法药_', 'Q金创药_', 'Q魔法药_')):
            category = 'medicine'
        elif extra.get('商店'.encode('gbk')) == '书店'.encode('gbk') and fields.get('分类'.encode('gbk')) == '道具'.encode('gbk'):
            assert fields['道具说明'.encode('gbk')].endswith('秘籍'.encode('gbk'))
            rank = extra.get('强化书'.encode('gbk'))
            category = 'high' if rank in (4, 5) else 'book'
        else:
            continue
        samples[name.encode('gbk')] = {key: fields[key] for key in (
            word.encode('gbk') for word in ('名称', '显示名', '分类', '子类', '颜色值'))}
        samples[name.encode('gbk')].update({b'category': category.encode(), '附加'.encode('gbk'): extra})
        counts[category] += 1
    assert counts == {'coin': 5, 'sun': 3, 'medicine': 22, 'book': 94, 'high': 148}, counts
    return samples


def fixtures(work, old, new, original, previous_fixtures):
    export_fixtures(original, previous_fixtures, work)
    def export(dump, idx, name, instructions=None):
        (work / (name + '.ljbc')).write_bytes(standalone(dump, trees(dump), idx, instructions))

    export(old[26], 98, 'class_previous')
    export(new[26], 98, 'class_new')
    (work / 'tick_previous.ljbc').write_bytes((work / 'tick_new.ljbc').read_bytes())
    for name in ('poison', 'area_poison'):
        (work / f'{name}_previous.ljbc').write_bytes((work / f'{name}_new.ljbc').read_bytes())
    export(new[12], 46, 'manual_event')
    for m, idx, name in [
        (36, 9, 'skill_slot'), (12, 307, 'screen_notice'), (12, 124, 'chat_init'),
        (12, 194, 'currency'), (12, 157, 'currency_first_story'), (12, 6482, 'pickup_callback'),
        (14, 337, 'draw_notice'), (14, 392, 'oil_notice'),
    ]:
        export(new[m], idx, name)
    export(new[14], 427, 'render_notices', {0: jump(0, 2198), 2332: ad('RET0', 0, 1)})
    for label, modules in [('previous', old), ('new', new)]:
        export(modules[76], 1, 'ground_' + label)
        export(modules[14], 427, 'alt_' + label, {0: jump(0, 2956), 2974: ad('RET0', 0, 1)})
    (work / 'ground_templates.lua').write_bytes(('return ' + lua(ground_templates(new[12]))).encode('gbk'))


def main(runtime):
    work = W / 'native_work/v287'
    work.mkdir(parents=True, exist_ok=True)
    base, data = ((W / f'game_v{v}.res').read_bytes() for v in (286, 287))
    build = json.loads((W / 'build_v287.json').read_text())
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    assert hashlib.sha256(data).hexdigest() == build['sha256']
    _, old = decode(base, range(2, 86, 2))
    _, new = decode(data, range(2, 86, 2))
    _, original = decode((W / 'game_v281.res').read_bytes(), [12, 26])
    _, previous_fixtures = decode((W / 'game_v284.res').read_bytes(), [12, 14, 20, 22, 26, 30, 46])
    fixtures(work, old, new, original, previous_fixtures)
    verify(old, new, build)
    melee = (W / 'melee_regression_v210.lua').read_text().split("local melee={'普通攻击'")[0]
    melee = melee.replace("if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end",
                          "if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')else jit.off()end")
    poison = (W / 'auto_poison_regression_v282.lua').read_text().split('-- Isolate native cooldown initialization')[0]
    poison = poison.replace("        if op == 'qs_skill_drop' and (first[4] == poison",
                            """        if op == 'qs_skill_drop' and first[1] == 5 and options.nativeSelect then
            return run('fun', manual, first)
        end
        if op == 'qs_skill_drop' and (first[4] == poison""", 1)
    source = work / 'combat_ui_ground.lua'
    regression = 'combat_ui_ground_regression_v287.lua'
    source.write_bytes((melee + poison + (W / regression).read_text()).encode('gbk'))
    runs = []
    for mode in ('normal', 'hot'):
        result = subprocess.run([runtime, str(source), str(work), mode], capture_output=True, timeout=90)
        output = (result.stdout + result.stderr).decode('gbk', 'replace')
        (work / (mode + '.log')).write_text(output)
        assert result.returncode == 0 and 'COMBAT_UI_GROUND_V287_PASS' in output, (mode, output)
        print(output, flush=True)
        runs.append({'mode': mode, 'output': output})
    files = tuple(f'{name}_v287.{ext}' for name in ('auto_poison', 'melee_timing', 'ground_name_color')
                  for ext in ('lua', 'ljbc'))
    files += ('alt_pickup_v287.lua', 'patch_v287.py', 'test_v287.py', regression)
    report = {'version': 'v1.287', 'all_passed': True, 'sha256': build['sha256'], 'runs': runs,
              'all_42_modules_checked': True, 'full_windows_game_run': False,
              'scope': 'native skill and damage dispatch, both story currency providers, Alt input branch, blessing-oil visible label, and ground texture constructor with finite engine and graphics bridges',
              'tested_files': {name: hashlib.sha256((W / name).read_bytes()).hexdigest() for name in files}}
    (W / 'validation_v287.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    args = parser.parse_args()
    main(args.runtime or str(ensure_runtime()))
