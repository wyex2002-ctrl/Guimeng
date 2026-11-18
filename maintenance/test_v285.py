"""Verify the information panel and all in-game powder purchase listings."""
import argparse
import hashlib
import json
import subprocess

from bytecode_relocate import BRANCHES
from ljdis import OPS
from ljtool import Proto
from native_test_utils import standalone, trees
from patch_v139 import W, ad, encstr, jump, rebuild_proto
from patch_v285 import BASE_SHA, MANA_NOTICE, PANEL_PARENT, POWDERS, SEPARATOR, SHOP_STOCK
from resource_tools import decode
from runtime import ensure_runtime
from test_v282 import export_fixtures

FILES = ('patch_v285.py', 'test_v285.py', 'information_panel_v285.lua', 'information_panel_v285.ljbc',
         'melee_timing_v285.lua', 'melee_timing_v285.ljbc', 'auto_poison_v285.lua',
         'auto_poison_v285.ljbc', 'alt_pickup_v285.lua', 'panel_shop_regression_v285.lua',
         'melee_regression_v210.lua', 'auto_poison_regression_v282.lua', 'test_v282.py',
         'combat_regression_v283.lua')


def verify(old, new):
    targets = {12: {PANEL_PARENT, *SHOP_STOCK}, 14: {427}, 26: {55, 87, *range(89, 98)}}
    listings = 0
    for mid, dump in new.items():
        trees(dump)
        assert dump.rebuild() == dump.raw
        before = old[mid].protos
        after = dump.protos
        if mid == 12:
            after = after[:PANEL_PARENT] + after[PANEL_PARENT + 1:]
        assert len(before) == len(after)
        for p, q in zip(before, after):
            if mid == 12 and p.idx in SHOP_STOCK:
                i = SHOP_STOCK[p.idx]
                _, previous, _ = p.gc(i)
                _, current, _ = q.gc(i)
                assert len(previous) == len(current)
                for a, b in zip(previous, current):
                    if isinstance(a, bytes) and a.split(SEPARATOR)[0] in POWDERS:
                        prior, now = a.split(SEPARATOR), b.split(SEPARATOR)
                        assert now[:3] == prior[:3] and now[4:] == prior[4:]
                        assert int(now[3]) == 200 * int(prior[3])
                        listings += 1
                    else:
                        assert a == b
                q.kraw[-1 - i] = p.kraw[-1 - i]
                assert rebuild_proto(q) == p.raw
            elif p.idx not in targets.get(mid, ()):
                restored = Proto(q.raw, q.idx)
                for slot, value in enumerate(restored.kgc):
                    if not isinstance(value, bytes):
                        continue
                    back = value.replace(b'v1.285', b'v1.284')
                    if mid == 12 and p.idx in (76, 22197):
                        back = back.replace(b'1.285', b'1.284')
                    if back != value:
                        restored.kgc[slot], restored.kraw[slot] = back, encstr(back)
                assert rebuild_proto(restored) == p.raw, (mid, p.idx)
        for q in dump.protos:
            for pc, word in enumerate(q.bc):
                if OPS[word & 255] in BRANCHES:
                    assert 0 <= pc + 1 + (word >> 16) - 32768 < q.nbc, (mid, q.idx, pc)
    assert listings == 50
    p, q = old[26].protos[55], new[26].protos[55]
    saved = {pc: pc if pc < 200 else pc - 13 for pc in range(p.nbc) if pc not in MANA_NOTICE}
    for pc, updated in saved.items():
        original, current = p.bc[pc], q.bc[updated]
        if OPS[original & 255] in BRANCHES:
            assert current & 65535 == original & 65535
            assert updated + 1 + (current >> 16) - 32768 == saved[pc + 1 + (original >> 16) - 32768]
        else:
            assert original == current
    assert old[14].protos[427].bc == new[14].protos[427].bc


def fixtures(work, old, new, original):
    export_fixtures(original, old, work)
    tree = {m: trees(d) for m, d in new.items()}

    def export(mid, idx, name, patches=None):
        d = new[mid]
        if mid == 12 and idx >= PANEL_PARENT:
            idx += 1
        (work / (name + '.ljbc')).write_bytes(standalone(d, tree[mid], idx, patches))

    for m, idx, name in [
        (26, 98, 'class_new'), (36, 9, 'skill_slot'), (12, 123, 'chat_init'),
        (12, 221, 'shop'), (12, 193, 'currency'), (12, 156, 'currency_first_story'),
        (12, 6481, 'pickup_callback'), (14, 392, 'oil_notice'), (14, 500, 'data_protection'),
        (14, 223, 'template_info'), (14, 614, 'stack_install'), (14, 454, 'add_item'),
        (14, 451, 'free_slots'), (14, 87, 'gly_add'), (14, 419, 'merc_helper'),
    ]:
        export(m, idx, name)
    export(30, 193, 'table_register', {0: jump(0, 33), 42: jump(42, 48), 69: ad('RET0', 0, 1)})
    for idx in SHOP_STOCK:
        patches = {0: jump(0, 281), 289: ad('RET0', 0, 1)} if idx == 142 else None
        export(12, idx, 'stock_' + str(idx), patches)
    (work / 'stock_old.ljbc').write_bytes(standalone(old[12], trees(old[12]), 7783))
    (work / 'range_pickup.lua').write_bytes(new[14].protos[427].gc(222))


def main(runtime):
    work = W / 'native_work/v285'
    work.mkdir(parents=True, exist_ok=True)
    base, data = ((W / f'game_v{version}.res').read_bytes() for version in (284, 285))
    build = json.loads((W / 'build_v285.json').read_text())
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    assert hashlib.sha256(data).hexdigest() == build['sha256']
    _, old = decode(base, range(2, 86, 2))
    _, new = decode(data, range(2, 86, 2))
    verify(old, new)
    _, original = decode((W / 'game_v281.res').read_bytes(), [12, 26])
    fixtures(work, old, new, original)
    melee = (W / 'melee_regression_v210.lua').read_text().split("local melee={'普通攻击'")[0]
    melee = melee.replace("if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end",
                          "if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')else jit.off()end")
    poison = (W / 'auto_poison_regression_v282.lua').read_text().split('-- Isolate native cooldown initialization')[0]
    poison = poison.replace("        if op == 'qs_skill_drop' and (first[4] == poison",
                            """        if op == 'qs_skill_drop' and first[1] == 5 and options.nativeSelect then
            return run('fun', manual, first)
        end
        if op == 'qs_skill_drop' and (first[4] == poison""", 1)
    alt = (W / 'combat_regression_v283.lua').read_text()
    alt = alt[alt.index('local function altRun'):alt.index("print('COMBAT_PICKUP_V283_PASS'")]
    alt = alt.replace('local notices, items, balance = {}, {},', 'local floating, messages, items, balance = {}, {}, {},')
    alt = alt.replace('notices[#notices+1] = t', 'floating[#floating+1] = t')
    alt = alt.replace("    local hero = {回调脚本", "    panel(E, U, messages, story)\n    local hero = {回调脚本")
    alt = alt.replace('#notices, 1', '#messages, 1').replace(
        "notices[1], '自动出售了白色装备，获得金币【103】'", "messages[1], '#c(-256)自动出售了白色装备，获得金币【103】#W'")
    alt = alt.replace("notices[2], '得到金币 3'", "floating[1], '得到金币 3'")
    alt = alt.replace('    if story ==', "    eq(#floating, 0, 'summary uses the information panel only')\n    if story ==")
    source = work / 'panel_shop.lua'
    tail = (W / 'panel_shop_regression_v285.lua').read_text()
    source.write_bytes((melee + poison + tail + alt + "\nprint('PANEL_SHOP_V285_PASS', mode, checks)\n").encode('gbk'))

    runs = []
    for mode in ('normal', 'hot'):
        result = subprocess.run([runtime, str(source), str(work), mode], capture_output=True, timeout=90)
        output = (result.stdout + result.stderr).decode('gbk', 'replace')
        (work / (mode + '.log')).write_text(output)
        assert result.returncode == 0 and 'PANEL_SHOP_V285_PASS' in output, (mode, output)
        print(output, flush=True)
        runs.append({'mode': mode, 'output': output})
    report = {'version': 'v1.285', 'all_passed': True, 'sha256': build['sha256'], 'runs': runs,
              'all_42_modules_checked': True, 'full_windows_game_run': False,
              'scope': 'both story panel providers, real skill-slot and hero release, native poison, currency, shop callbacks and inventory insertion with finite UI and engine bridges',
              'tested_files': {name: hashlib.sha256((W / name).read_bytes()).hexdigest() for name in FILES}}
    (W / 'validation_v285.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    args = parser.parse_args()
    main(args.runtime or str(ensure_runtime()))
