"""Current summon dispatch, shared controls, transformations and death bookkeeping."""
from pathlib import Path
import argparse,hashlib,json,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from bytecode_relocate import BRANCHES,numeric_and_debug
from patch_v195 import SUMMONERS
from patch_v139 import ad,jump
from ljdis import OPS
from runtime import ensure_runtime
W=Path(__file__).resolve().parent

def main(runtime):
 (W/'validation_v195.json').unlink(missing_ok=True);work=W/'native_work/v195';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v194.res').read_bytes();b=(W/'game_v195.res').read_bytes();ao,old=decode(a,range(2,86,2));bo,new=decode(b,range(2,86,2));report=json.loads((W/'build_v195.json').read_text())
 changes={int(k):v for k,v in report['changed_prototypes'].items()};assert changes=={12:SUMMONERS,14:[632,668,684],30:[39,87]}
 assert ao.protos[0].bc==bo.protos[0].bc and a[-10:]==b[-10:]
 for m,d in new.items():
  assert d.rebuild()==d.raw and len(d.protos)==len(old[m].protos)
  for i,(p,q)in enumerate(zip(d.protos,old[m].protos)):
   assert(p.raw!=q.raw)==(i in changes.get(m,[])),(m,i)
   assert numeric_and_debug(p)[0]==numeric_and_debug(q)[0]
   assert(p.params,p.frame,p.uv)==(q.params,q.frame,q.uv)
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(m,i,pc)
    if OPS[x&255]in ['GGET','KSTR','FNEW','TDUP','ISEQS','ISNES']:assert x>>16<p.nkgc
    if OPS[x&255]in ['TGETS','TSETS']:assert (x>>16&255)<p.nkgc
 for i in SUMMONERS:
  p,q=new[12].protos[i],old[12].protos[i]
  assert p.bc[:422]==q.bc[:422] and p.bc[423:q.nbc]==q.bc[423:]
  assert p.kgc[-q.nkgc:]==q.kgc
 for label,mods in [('old',old),('new',new)]:
  d=mods[12];t=trees(d)
  for i in SUMMONERS if label=='new'else[4498]:(work/f'{label}_{i}.ljbc').write_bytes(standalone(d,t,i))
 d=new[12];t=trees(d)
 for i,name in [(239,'control'),(52,'keyboard'),(425,'transform'),(17206,'death'),(17218,'destroy')]:
  (work/f'{name}.ljbc').write_bytes(standalone(d,t,i))
 d=new[14];t=trees(d)
 (work/'sandbox_install.ljbc').write_bytes(standalone(d,t,378,{0:jump(0,597,13),609:ad('RET0',0,1)}))
 (work/'summon.lua').write_bytes((W/'summon_regression_v195.lua').read_text().encode('gbk'));runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'summon.lua'),str(work),mode],capture_output=True,timeout=90);(work/(mode+'.log')).write_bytes(r.stdout+r.stderr)
  assert r.returncode==0,(r.stdout+r.stderr).decode('gbk','replace')[-3500:]
  output=r.stdout.decode('gbk');assert 'SUMMON_V195_PASS'in output;print(output,flush=True);runs.append({'mode':mode,'output':output})
 names=['patch_v195.py','test_v195.py','summon_regression_v195.lua','package_v195.py','player_changes_v195.json']
 result={'version':'v1.195','all_passed':True,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'test_scope':'current_summon_dispatch_controls_transform_and_death','historical_suites_rerun':False,'full_windows_game_run':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v195.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');x=a.parse_args();main(str(Path(x.runtime).resolve())if x.runtime else str(ensure_runtime()))
