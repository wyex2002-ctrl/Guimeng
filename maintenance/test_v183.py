"""Real page registration/dispatch regression; no injected game API getters."""
from pathlib import Path
import argparse,hashlib,json,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from patch_v139 import ad,jump
from bytecode_relocate import BRANCHES,numeric_and_debug
from ljdis import OPS
from runtime import ensure_runtime
W=Path(__file__).resolve().parent

def children(d):
 stack=[];result={}
 for p in d.protos:
  c={}
  for k,v in enumerate(p.kgc):
   if v==('child',):c[p.nkgc-1-k]=stack.pop()
  result[p.idx]=c;stack.append(p.idx)
 assert len(stack)==1
 return result

def audit(before,after):
 spec=json.loads((W/'check_removal_v181.json').read_text());removed=[];factories=[]
 for m,d in before.items():
  links=children(d)
  for p in d.protos:
   key=f'{m}:{p.idx}'
   spans=spec['remove_ranges'].get(key,[])
   for pc,ins in enumerate(p.bc):
    if OPS[ins&255]=='FNEW' and any(a<=pc<b for a,b in spans):
     removed.append({'module':m,'prototype':p.idx,'pc':pc,'child':links[p.idx][ins>>16]})
   if p.idx in spec['stubs'].get(str(m),[]):
    returns=[OPS[i&255] for i in p.bc if OPS[i&255] in ['RET','RET1','RETM','CALLT','CALLMT']]
    if returns:factories.append({'module':m,'prototype':p.idx,'returns':returns})
 assert {(r['module'],r['prototype'],r['pc'])for r in removed}=={(12,20,175),(12,87,78),(12,94,23),(12,179,1220),(12,254,1221)}
 assert [(r['module'],r['prototype'])for r in factories]==[(12,86),(34,7)]
 # The original getter and original table factory are byte-identical. All
 # legacy report/check methods are single RET0 instructions; no dependencies.
 assert after[12].protos[73].raw==before[12].protos[73].raw
 assert after[12].protos[86].raw==before[12].protos[86].raw
 assert after[34].protos[7].bc==before[34].protos[7].bc[-2:]
 for i in range(77,86):assert after[12].protos[i].bc==[ad('RET0',0,1)]
 return {'removed_closure_registrations_reviewed':removed,'stubbed_return_contracts_reviewed':factories,'restored_legitimate_api':'Ux雌.金轮法王','disabled_methods':list(range(77,86))}

def main(runtime):
 (W/'validation_v183.json').unlink(missing_ok=True)
 work=W/'native_work/v183';work.mkdir(parents=True,exist_ok=True)
 base=(W/'game_v182.res').read_bytes();data=(W/'game_v183.res').read_bytes()
 ao,old=decode(base,range(2,86,2));bo,new=decode(data,range(2,86,2));_,v180=decode((W/'game_v180.res').read_bytes(),range(2,86,2))
 build=json.loads((W/'build_v183.json').read_text());changes={int(k):v for k,v in build['changed_prototypes'].items()}
 assert ao.protos[0].bc==bo.protos[0].bc and base[-10:]==data[-10:]
 assert changes[12]==[86,87]
 for m,d in new.items():
  trees(d);assert d.rebuild()==d.raw and len(d.protos)==len(old[m].protos)
  assert [i for i,(p,q)in enumerate(zip(old[m].protos,d.protos))if p.raw!=q.raw]==changes.get(m,[])
  for p in d.protos:
   q=old[m].protos[p.idx];assert numeric_and_debug(p)[0]==numeric_and_debug(q)[0]
   assert (p.flags,p.params,p.frame,p.nuv,p.uv)==(q.flags,q.params,q.frame,q.nuv,q.uv)
   for pc,ins in enumerate(p.bc):
    op=OPS[ins&255]
    if op in BRANCHES:assert 0<=pc+1+(ins>>16)-32768<len(p.bc),(m,p.idx,pc)
    if op in ['KSTR','GGET','GSET','FNEW','TDUP','ISEQS','ISNES']:assert ins>>16<p.nkgc
    if op in ['TGETS','TSETS']:assert ((ins>>16)&255)<p.nkgc
 reviewed=audit(v180,new)
 def emit(d,index,name,patches=None,params=None):
  (work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),index,patches,params))
 # Use the database's ORIGINAL registration statements and complete original
 # page factories/Main functions. Skip only graphics creation before/after.
 for label,mods in [('old',old),('new',new)]:
  emit(mods[12],313,'register_'+label,{0:jump(0,115,3),248:ad('RET0',0,1)})
  emit(mods[12],22193,'database_'+label)
 emit(new[84],18,'ux_init',{0:jump(0,198),203:ad('RET1',4,2)})
 maps=json.loads((W/'build_v181.json').read_text())['relocations']
 pc=lambda n:maps['14:378'][str(n)]
 emit(new[14],378,'builtin_exports',{0:jump(0,pc(433),13),pc(451):ad('RET1',12,2)},13)
 emit(new[14],378,'sandbox_install',{0:jump(0,pc(635),6),pc(647):ad('RET0',0,1)},6)
 emit(new[14],381,'dispatch')
 emit(new[14],13,'public_sys')
 emit(new[34],7,'item_timer')
 emit(new[14],90,'rng_original')
 (work/'startup.lua').write_bytes((W/'startup_regression_v183.lua').read_text().encode('gbk'))
 runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'startup.lua'),str(work),mode],capture_output=True,timeout=120)
  (work/(mode+'.startup.log')).write_bytes(r.stdout+r.stderr)
  assert r.returncode==0,(mode,r.stdout[-2000:],r.stderr)
  assert b'V182_MISSING_API_REPRODUCED' in r.stdout and b'PAGE_STARTUP_PASS' in r.stdout
  output=r.stdout.decode('gbk');print(output,flush=True);runs.append({'mode':mode,'output':output})
 r=subprocess.run(['python3',str(W/'test_v182.py'),'--runtime',runtime],capture_output=True)
 (work/'baseline.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0,(r.stdout[-2000:],r.stderr)
 loader=work/'load.lua';loader.write_text('for i=1,#arg do assert(loadfile(arg[i]))end;print("LOAD_PASS")')
 subprocess.run([runtime,str(loader)]+[str(W/f'module_{m}_v183.ljbc')for m in changes],check=True)
 result={'version':'v1.183','all_passed':True,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'startup_runs':runs,'removal_audit':reviewed,'v182_regressions_rerun':True,'rules_changed':False,'full_windows_game_run':False}
 names=['patch_v183.py','test_v183.py','startup_regression_v183.lua','bytecode_relocate.py','player_changes_v183.json']
 result['tested_files']={n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}
 (W/'validation_v183.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');x=a.parse_args();main(str(Path(x.runtime).resolve())if x.runtime else str(ensure_runtime()))
