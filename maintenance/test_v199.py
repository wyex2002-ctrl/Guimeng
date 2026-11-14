"""Current reputation death/currency/public-interface regression only."""
from pathlib import Path
import argparse,hashlib,json,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from bytecode_relocate import BRANCHES,numeric_and_debug
from patch_v139 import ad,abc
from patch_v196 import number_pool
from ljdis import OPS
from runtime import ensure_runtime
W=Path(__file__).resolve().parent

def main(runtime):
 (W/'validation_v199.json').unlink(missing_ok=True);work=W/'native_work/v199';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v198.res').read_bytes();b=(W/'game_v199.res').read_bytes();ao,old=decode(a,range(2,86,2));bo,new=decode(b,range(2,86,2));report=json.loads((W/'build_v199.json').read_text())
 changes={int(k):v for k,v in report['changed_prototypes'].items()};assert changes=={14:[632,668,684],22:[62],30:[39,87]}
 assert ao.protos[0].bc==bo.protos[0].bc and a[-10:]==b[-10:]
 for m,d in new.items():
  assert d.rebuild()==d.raw and len(d.protos)==len(old[m].protos)
  for i,(p,q)in enumerate(zip(d.protos,old[m].protos)):
   assert(p.raw!=q.raw)==(i in changes.get(m,[])),(m,i)
   assert(p.params,p.frame,p.uv,p.nbc)==(q.params,q.frame,q.uv,q.nbc)
   if(m,i)==(22,62):
    assert p.kgc==q.kgc and number_pool(p)==number_pool(q)+[5]
    assert numeric_and_debug(p)[0].startswith(numeric_and_debug(q)[0])
    expected={466:abc('DIVVN',20,4,6),654:ad('KSHORT',23,4),694:ad('KSHORT',28,4)}
    assert all(x==expected.get(pc,q.bc[pc])for pc,x in enumerate(p.bc))
   else:assert numeric_and_debug(p)[0]==numeric_and_debug(q)[0]
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc
 for m,i,n in[(22,64,'death_new'),(22,3,'spawn'),(12,191,'currency_new'),(14,339,'fx_getter'),(14,13,'public_sys'),(14,416,'public_get'),(14,458,'data_protection')]:
  d=new[m];(work/(n+'.ljbc')).write_bytes(standalone(d,trees(d),i))
 d=old[22];(work/'death_old.ljbc').write_bytes(standalone(d,trees(d),64))
 (work/'reputation.lua').write_bytes((W/'reputation_regression_v199.lua').read_text().encode('gbk'));runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'reputation.lua'),str(work),mode],capture_output=True,timeout=90);(work/(mode+'.log')).write_bytes(r.stdout+r.stderr)
  assert r.returncode==0,(r.stdout+r.stderr).decode('gbk','replace')[-3000:]
  output=r.stdout.decode('gbk');assert 'REPUTATION_V199_PASS'in output;print(output,flush=True);runs.append({'mode':mode,'output':output})
 names=['patch_v199.py','test_v199.py','reputation_regression_v199.lua','package_v199.py','player_changes_v199.json']
 result={'version':'v1.199','all_passed':True,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'test_scope':'current_reputation_death_currency_public_interface','historical_suites_rerun':False,'full_windows_game_run':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v199.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');x=a.parse_args();main(str(Path(x.runtime).resolve())if x.runtime else str(ensure_runtime()))
