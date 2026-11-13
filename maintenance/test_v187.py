"""Reproduce timer autosave spam and verify its original bounded cadence."""
from pathlib import Path
import argparse,hashlib,json,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from bytecode_relocate import BRANCHES,numeric_and_debug
from ljdis import OPS
from patch_v139 import ad,jump
from runtime import ensure_runtime
W=Path(__file__).resolve().parent

def main(runtime):
 (W/'validation_v187.json').unlink(missing_ok=True)
 work=W/'native_work/v187';work.mkdir(parents=True,exist_ok=True)
 base=(W/'game_v186.res').read_bytes();data=(W/'game_v187.res').read_bytes()
 ao,old=decode(base,range(2,86,2));bo,new=decode(data,range(2,86,2));build=json.loads((W/'build_v187.json').read_text())
 assert ao.protos[0].bc==bo.protos[0].bc and base[-10:]==data[-10:]
 changes={int(k):v for k,v in build['changed_prototypes'].items()};assert changes=={12:[20],14:[632,668,681],30:[39,87]},changes
 for m,d in new.items():
  trees(d);assert d.rebuild()==d.raw and len(d.protos)==len(old[m].protos)
  found=[]
  for i,(p,q) in enumerate(zip(d.protos,old[m].protos)):
   if p.raw!=q.raw:found.append(i)
   assert numeric_and_debug(p)[0]==numeric_and_debug(q)[0],(m,i)
   assert(p.flags,p.params,p.frame,p.nuv,p.uv)==(q.flags,q.params,q.frame,q.nuv,q.uv),(m,i)
   for pc,ins in enumerate(p.bc):
    op=OPS[ins&255]
    if op in BRANCHES:assert 0<=pc+1+(ins>>16)-32768<len(p.bc),(m,i,pc)
  assert found==changes.get(m,[]),(m,found)
 p,q=old[12].protos[20],new[12].protos[20];mp={int(k):v for k,v in build['timer_relocations'].items()}
 for pc,ins in enumerate(p.bc):
  at=mp[pc]+(8 if pc==119 else 0);expected=ins
  if OPS[ins&255]in BRANCHES:
   target=mp[pc+1+(ins>>16)-32768];expected=(ins&65535)|((target-at-1+32768)<<16)
  assert q.bc[at]==expected,('original timer instruction changed',pc)
 assert p.kraw==q.kraw
 _,historical=decode((W/'game_v180.res').read_bytes(),[12]);historical=historical[12].protos[20]
 for offset in range(8):
  expected=historical.bc[662+offset]
  if offset in [3,7]:expected=jump(119+offset,140,1)
  assert q.bc[119+offset]==expected
 for label,d,stop in [('old',old[12],132),('new',new[12],140)]:
  (work/f'timer_{label}.ljbc').write_bytes(standalone(d,trees(d),20,{stop:ad('RET0',0,1)}))
 d=new[12]
 for index,name in [(126,'role_a'),(132,'role_b'),(129,'config_a'),(134,'config_b'),(73,'mode_get'),(153,'quit153'),(188,'quit188')]:
  (work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),index))
 d=new[14]
 for index,name in [(167,'timer_factory'),(385,'native_frame'),(680,'profile_only'),(13,'public_sys')]:
  (work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),index))
 (work/'native_exports.ljbc').write_bytes(standalone(d,trees(d),684,{0:jump(0,280)},1))
 (work/'autosave.lua').write_bytes((W/'autosave_regression_v187.lua').read_text().encode('gbk'))
 runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'autosave.lua'),str(work),mode],capture_output=True,timeout=90)
  (work/(mode+'.autosave.log')).write_bytes(r.stdout+r.stderr);assert r.returncode==0,(mode,r.stdout[-3000:],r.stderr)
  out=r.stdout.decode('gbk');assert 'AUTOSAVE_REGRESSION_PASS'in out;print(out,flush=True);runs.append({'mode':mode,'output':out})
 r=subprocess.run(['python3',str(W/'test_v186.py'),'--runtime',runtime],capture_output=True)
 (work/'baseline.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0,(r.stdout[-2000:],r.stderr)
 # Re-execute the current installer through real public Sys integration.
 integration=W/'native_work/v179';d=new[14]
 (integration/'installer179.ljbc').write_bytes(standalone(d,trees(d),681))
 for name in ['diagnostics.lua','integration.lua']:
  for mode in ['normal','hot']:
   r=subprocess.run([runtime,str(integration/name),str(integration),mode],capture_output=True,timeout=90)
   (work/(name+'.'+mode+'.log')).write_bytes(r.stdout+r.stderr);assert r.returncode==0,(name,mode,r.stdout[-1500:],r.stderr)
 names=['patch_v187.py','test_v187.py','autosave_regression_v187.lua','player_changes_v187.json']
 result={'version':'v1.187','all_passed':True,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'autosave_runs':runs,'v186_and_prior_regressions_rerun':True,'current_public_sys_integration':True,'all_42_modules_and_non_target_prototypes_verified':True,'rules_changed':False,'full_windows_game_run':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v187.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');x=a.parse_args();main(str(Path(x.runtime).resolve())if x.runtime else str(ensure_runtime()))
