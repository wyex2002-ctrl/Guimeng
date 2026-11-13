"""Diagnostic performance plus current-resource startup/gameplay regressions."""
from pathlib import Path
import argparse,hashlib,json,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from bytecode_relocate import BRANCHES,numeric_and_debug
from ljdis import OPS
from runtime import ensure_runtime
W=Path(__file__).resolve().parent

def main(runtime):
 (W/'validation_v184.json').unlink(missing_ok=True)
 work=W/'native_work/v184';work.mkdir(parents=True,exist_ok=True)
 base=(W/'game_v183.res').read_bytes();data=(W/'game_v184.res').read_bytes()
 ao,old=decode(base,range(2,86,2));bo,new=decode(data,range(2,86,2));build=json.loads((W/'build_v184.json').read_text());changes={int(k):v for k,v in build['changed_prototypes'].items()}
 assert set(changes)=={14,30};assert ao.protos[0].bc==bo.protos[0].bc and base[-10:]==data[-10:]
 for m,d in new.items():
  trees(d);assert d.rebuild()==d.raw and len(d.protos)==len(old[m].protos)
  assert [i for i,(p,q)in enumerate(zip(old[m].protos,d.protos))if p.raw!=q.raw]==changes.get(m,[])
  for p in d.protos:
   q=old[m].protos[p.idx]
   # The isolated diagnostics subtree is freshly compiled source. All native
   # and gameplay prototypes retain their numeric pools and closure layouts.
   if not(m==14 and 645<=p.idx<=668):
    assert numeric_and_debug(p)[0]==numeric_and_debug(q)[0]
    assert(p.flags,p.params,p.frame,p.nuv,p.uv)==(q.flags,q.params,q.frame,q.nuv,q.uv)
   for pc,ins in enumerate(p.bc):
    op=OPS[ins&255]
    if op in BRANCHES:assert 0<=pc+1+(ins>>16)-32768<len(p.bc),(m,p.idx,pc)
    if op in ['KSTR','GGET','GSET','FNEW','TDUP','ISEQS','ISNES']:assert ins>>16<p.nkgc
    if op in ['TGETS','TSETS']:assert((ins>>16)&255)<p.nkgc
 assert new[14].protos[668].params==1 and new[14].protos[668].nuv==0
 for label,mods in [('old',old),('new',new)]:
  d=mods[14];(work/f'installer_{label}.ljbc').write_bytes(standalone(d,trees(d),669))
 d=new[14];(work/'dispatch.ljbc').write_bytes(standalone(d,trees(d),381))
 (work/'performance.lua').write_bytes((W/'performance_regression_v184.lua').read_text().encode('gbk'))
 runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'performance.lua'),str(work),mode],capture_output=True,timeout=90)
  (work/(mode+'.performance.log')).write_bytes(r.stdout+r.stderr)
  assert r.returncode==0,(mode,r.stdout[-2000:],r.stderr)
  assert b'PERFORMANCE_PASS' in r.stdout
  out=r.stdout.decode('gbk');print(out,flush=True);runs.append({'mode':mode,'output':out})
 # Rerun all prior suites, then execute the current compiled diagnostics against
 # the existing death/public-Sys integration and startup fixtures as well.
 r=subprocess.run(['python3',str(W/'test_v183.py'),'--runtime',runtime],capture_output=True)
 (work/'baseline.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0,(r.stdout[-2000:],r.stderr)
 integration=W/'native_work/v179';d=new[14]
 (integration/'installer179.ljbc').write_bytes(standalone(d,trees(d),669))
 for filename in ['diagnostics.lua','integration.lua']:
  for mode in ['normal','hot']:
   r=subprocess.run([runtime,str(integration/filename),str(integration),mode],capture_output=True,timeout=90)
   (work/(filename+'.'+mode+'.log')).write_bytes(r.stdout+r.stderr);assert r.returncode==0,(filename,mode,r.stdout[-2000:],r.stderr)
 # Startup fixtures use unchanged gameplay prototypes; run them against actual
 # v184 extracts to ensure the current resource is the one being exercised.
 from patch_v139 import ad,jump
 d=new[12];startup=W/'native_work/v183'
 for filename,index,patch in [('register_new',313,{0:jump(0,115,3),248:ad('RET0',0,1)}),('database_new',22193,None)]:
  (startup/(filename+'.ljbc')).write_bytes(standalone(d,trees(d),index,patch))
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(startup/'startup.lua'),str(startup),mode],capture_output=True,timeout=90)
  (work/(mode+'.startup.log')).write_bytes(r.stdout+r.stderr);assert r.returncode==0,(r.stdout[-2000:],r.stderr)
 result={'version':'v1.184','all_passed':True,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'performance_runs':runs,'v183_regressions_rerun':True,'current_diagnostics_public_integration':True,'rules_changed':False,'full_windows_game_run':False}
 names=['patch_v184.py','test_v184.py','diagnostics_v184.lua','diagnostics_v184.ljbc','performance_regression_v184.lua','player_changes_v184.json']
 result['tested_files']={n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}
 (W/'validation_v184.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');x=a.parse_args();main(str(Path(x.runtime).resolve())if x.runtime else str(ensure_runtime()))
