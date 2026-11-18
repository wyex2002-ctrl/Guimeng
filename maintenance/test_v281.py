"""Compare the two new lock gates against the current native combat path."""
import argparse
import hashlib
import json
import subprocess

from bytecode_relocate import BRANCHES
from ljdis import OPS
from ljtool import Proto
from native_test_utils import standalone, trees
from patch_v139 import W, ad, encstr, jump, rebuild_proto
from test_v192 import lua
from patch_v201 import unpack_config
from patch_v281 import BASE_SHA, SKILLS
from portal_routes_v213 import child_refs
from resource_tools import decode
from runtime import ensure_runtime
from test_v210 import SKILLS as CONFIGS


def verify(old, new, relocations):
    for module, dump in new.items():
        trees(dump)
        assert dump.rebuild() == dump.raw
        assert len(dump.protos) == len(old[module].protos)
        for p, q in zip(old[module].protos, dump.protos):
            for pc, x in enumerate(q.bc):
                if OPS[x & 255] in BRANCHES:
                    assert 0 <= pc + 1 + (x >> 16) - 32768 < q.nbc, (module, q.idx, pc)
            if module == 26 and p.idx in (54, 87):
                info = relocations[str(p.idx)]
                pos = {int(k): v for k, v in info['positions'].items()}
                site, added = info['site'], info['added']
                assert (p.params,p.frame,p.uv) == (q.params,q.frame,q.uv)
                for slot in range(p.nkgc):
                    assert p.gc(slot) == q.gc(slot)
                for pc, instruction in enumerate(p.bc):
                    at = pos[pc] + (added if pc == site else 0)
                    if OPS[instruction & 255] in BRANCHES:
                        target = pc + 1 + (instruction >> 16) - 32768
                        instruction = (instruction & 65535) | ((pos[target] - at - 1 + 32768) << 16)
                    assert q.bc[at] == instruction, (p.idx, pc)
                for i, name in enumerate(SKILLS):
                    at = pos[site] + 2*i
                    op, branch = q.bc[at:at+2]
                    assert op == ad('ISEQS',info['register'],op>>16)
                    assert q.gc(op>>16) == name.encode('gbk')
                    assert branch == jump(at+1,pos[info['accepted']],info['register'])
                continue
            restored = Proto(q.raw, q.idx)
            for slot, value in enumerate(restored.kgc):
                if not isinstance(value, bytes):
                    continue
                back = value.replace(b'v1.281', b'v1.280')
                if module == 12 and p.idx in (76,22196):
                    back = back.replace(b'1.281', b'1.280')
                if back != value:
                    restored.kgc[slot], restored.kraw[slot] = back, encstr(back)
            assert rebuild_proto(restored) == p.raw, (module, p.idx)


def main(runtime):
    work = W / 'native_work/v281'
    work.mkdir(parents=True, exist_ok=True)
    base = (W/'game_v280.res').read_bytes()
    resource = (W/'game_v281.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA
    _, old = decode(base, range(2,86,2))
    _, new = decode(resource, range(2,86,2))
    build = json.loads((W/'build_v281.json').read_text())
    verify(old,new,build['relocations'])
    subtrees = {mid:trees(d) for mid,d in new.items()}

    def export(mid, idx, name, patches=None):
        (work/(name+'.ljbc')).write_bytes(standalone(new[mid],subtrees[mid],idx,patches))

    for label, modules in [('old',old),('new',new)]:
        d = modules[26]
        (work/f'class_{label}.ljbc').write_bytes(standalone(d,trees(d),89))
        assert old[26].protos[3].bc == d.protos[3].bc
        (work/f'tick_{label}.ljbc').write_bytes(standalone(d,trees(d),3,{0:jump(0,843,3),852:ad('RET0',0,1)}))
    for mid,idx,name in [(20,8,'animation'),(20,6,'reverse'),(20,21,'reset'),(12,4093,'skill_factory'),(30,43,'rotate')]:
        export(mid,idx,name)
    db = new[12]
    cfg = db.protos[6466]
    configs = {name.encode('gbk'):unpack_config(cfg.gc(i)) for i,name in CONFIGS.items()}
    (work/'configs.lua').write_bytes(('return '+lua(configs)).encode('gbk'))
    refs = child_refs(db)
    callbacks = {}
    for i,name in enumerate(CONFIGS.values()):
        marker = ('【数据库/技能脚本/'+name+'】').encode('gbk')
        pc = next(j for j,x in enumerate(cfg.bc) if OPS[x&255]=='KSTR' and cfg.gc(x>>16)==marker)
        closure = cfg.bc[pc-2]
        assert OPS[closure&255]=='FNEW'
        key = 'callback_'+str(i)
        callbacks[name.encode('gbk')] = key.encode()
        export(12,refs[6466,closure>>16],key)
    (work/'scripts.lua').write_bytes(('return '+lua(callbacks)).encode('gbk'))
    prefix = (W/'melee_regression_v210.lua').read_text().split("local melee={'普通攻击'")[0]
    prefix = prefix.replace("if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end",
                            "if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')else jit.off()end")
    script = work/'combat.lua'
    script.write_bytes((prefix+(W/'locked_melee_regression_v281.lua').read_text()).encode('gbk'))
    runs = []
    for mode in ('normal','hot'):
        result = subprocess.run([runtime,str(script),str(work),mode],capture_output=True,timeout=90)
        output = (result.stdout+result.stderr).decode('gbk','replace')
        (work/(mode+'.log')).write_text(output)
        assert result.returncode==0 and 'LOCKED_MELEE_V281_PASS' in output,(mode,output)
        print(output,flush=True)
        runs.append({'mode':mode,'output':output})

    names = ['patch_v281.py','test_v281.py','package_v281.py','locked_melee_regression_v281.lua',
             'melee_regression_v210.lua','player_changes_v281.json']
    report = {'version':'v1.281','all_passed':True,'sha256':hashlib.sha256(resource).hexdigest(),
              'runs':runs,'all_42_modules_checked':True,'full_windows_game_run':False,
              'runtime_version':subprocess.check_output([runtime,'-v'],stderr=subprocess.STDOUT).decode().strip(),
              'scope':'native hero automatic attack, skill configuration and scripts, instance and grid collection to damage dispatch with finite selection, map, graphics and final damage bridges',
              'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest() for n in names}}
    (W/'validation_v281.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime')
    args = parser.parse_args()
    main(args.runtime or str(ensure_runtime()))
