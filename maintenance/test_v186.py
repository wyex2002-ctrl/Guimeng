"""Exercise actual skill checkpoint traffic and bounded native frame metrics."""
from pathlib import Path
import argparse,hashlib,json,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from bytecode_relocate import BRANCHES,numeric_and_debug
from ljdis import OPS
from runtime import ensure_runtime
W=Path(__file__).resolve().parent

def main(runtime):
 (W/'validation_v186.json').unlink(missing_ok=True)
 work=W/'native_work/v186';work.mkdir(parents=True,exist_ok=True)
 base=(W/'game_v185.res').read_bytes();data=(W/'game_v186.res').read_bytes()
 ao,old=decode(base,range(2,86,2));bo,new=decode(data,range(2,86,2));build=json.loads((W/'build_v186.json').read_text());n=build['profile_delta'];changes={int(k):v for k,v in build['changed_original_prototypes'].items()}
 assert set(changes)=={14,30};assert ao.protos[0].bc==bo.protos[0].bc and base[-10:]==data[-10:]
 for m,d in new.items():
  trees(d);assert d.rebuild()==d.raw and len(d.protos)==len(old[m].protos)+(n if m==14 else 0)
  found=[]
  for i,q in enumerate(old[m].protos):
   p=d.protos[i+n if m==14 and i>=678 else i]
   if m==14 and 669<=i<678:continue
   if p.raw!=q.raw:found.append(i)
   assert numeric_and_debug(p)[0]==numeric_and_debug(q)[0],(m,i)
   assert(p.flags,p.params,p.frame,p.nuv,p.uv)==(q.flags,q.params,30 if m==14 and i==385 else q.frame,q.nuv,q.uv),(m,i)
  assert found==changes.get(m,[]),(m,found)
  for p in d.protos:
   for pc,ins in enumerate(p.bc):
    op=OPS[ins&255]
    if op in BRANCHES:assert 0<=pc+1+(ins>>16)-32768<len(p.bc),(m,p.idx,pc)
    if op in ['KSTR','GGET','GSET','FNEW','TDUP','ISEQS','ISNES']:assert ins>>16<p.nkgc
    if op in ['TGETS','TSETS']:assert((ins>>16)&255)<p.nkgc
 # Prove every original instruction survives, with the exact original branch
 # destination after insertion, including JMP inside a replaced fragment.
 from patch_v186 import PHASES
 p,q=old[14].protos[385],new[14].protos[385]
 mp={int(k):v for k,v in build['frame_relocations'].items()}
 for pc,ins in enumerate(p.bc):
  at=mp[pc]+(9 if pc in PHASES else 0);expected=ins
  if OPS[ins&255] in BRANCHES:
   target=mp[pc+1+(ins>>16)-32768]
   expected=(ins&65535)|((target-at-1+32768)<<16)
  assert q.bc[at]==expected,('original frame instruction changed',pc,at)
 for pc in PHASES:assert not OPS[p.bc[pc-1]&255].startswith('IS'),('conditional skip boundary',pc)
 _,io_old=decode((W/'game_v184.res').read_bytes(),[14])
 for label,mods,idx in [('old',io_old,669),('new',new,678+n)]:
  d=mods[14];(work/f'installer_{label}.ljbc').write_bytes(standalone(d,trees(d),idx))
 for m,index,name in [(14,381,'dispatch'),(14,13,'public_sys'),(14,416,'public_get'),(26,55,'hero_skill'),(36,9,'skill_slot'),(14,677+n,'profile_only')]:
  d=new[m];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),index))
 from patch_v139 import jump
 d=new[14];(work/'native_exports.ljbc').write_bytes(standalone(d,trees(d),681+n,{0:jump(0,280)},1))
 (work/'frame.lua').write_bytes((W/'frame_regression_v185.lua').read_text().encode('gbk'))
 for label,mods in [('old',old),('new',new)]:
  d=mods[14];(work/f'frame_{label}.ljbc').write_bytes(standalone(d,trees(d),385))
 (work/'native_frame.lua').write_bytes((W/'native_frame_regression_v186.lua').read_text().encode('gbk'))
 runs=[]
 for mode in ['normal','hot']:
  q=subprocess.run([runtime,str(work/'native_frame.lua'),str(work),mode],capture_output=True,timeout=90)
  (work/(mode+'.native_frame.log')).write_bytes(q.stdout+q.stderr);assert q.returncode==0,(mode,q.stdout,q.stderr);print(q.stdout.decode('gbk'),flush=True)
  r=subprocess.run([runtime,str(work/'frame.lua'),str(work),mode],capture_output=True,timeout=90)
  (work/(mode+'.frame.log')).write_bytes(r.stdout+r.stderr);assert r.returncode==0,(mode,r.stdout[-2000:],r.stderr)
  assert b'FRAME_AND_SKILL_PASS' in r.stdout;out=r.stdout.decode('gbk');print(out,flush=True);runs.append({'mode':mode,'output':out})
 r=subprocess.run(['python3',str(W/'test_v185.py'),'--runtime',runtime],capture_output=True)
 (work/'baseline.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0,(r.stdout[-2000:],r.stderr)
 integration=W/'native_work/v179';d=new[14]
 (integration/'installer179.ljbc').write_bytes(standalone(d,trees(d),678+n))
 for filename in ['diagnostics.lua','integration.lua']:
  for mode in ['normal','hot']:
   r=subprocess.run([runtime,str(integration/filename),str(integration),mode],capture_output=True,timeout=90)
   (work/(filename+'.'+mode+'.log')).write_bytes(r.stdout+r.stderr);assert r.returncode==0,(filename,mode,r.stdout[-1500:],r.stderr)
 result={'version':'v1.186','all_passed':True,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'frame_and_skill_runs':runs,'v185_regressions_rerun':True,'current_diagnostics_public_integration':True,'complete_native_frame_and_phase_attribution':True,'rules_changed':False,'full_windows_game_run':False}
 names=['patch_v186.py','test_v186.py','profiling_v186.lua','profiling_v186.ljbc','frame_regression_v185.lua','native_frame_regression_v186.lua','player_changes_v186.json']
 result['tested_files']={name:hashlib.sha256((W/name).read_bytes()).hexdigest()for name in names}
 (W/'validation_v186.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');x=a.parse_args();main(str(Path(x.runtime).resolve())if x.runtime else str(ensure_runtime()))
