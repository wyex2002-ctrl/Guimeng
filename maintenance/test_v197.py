"""Current affix generation plus the complete live/base equipment tooltip."""
from pathlib import Path
import argparse,hashlib,json,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from bytecode_relocate import BRANCHES,numeric_and_debug
from patch_v139 import ad,jump
from ljdis import OPS
from runtime import ensure_runtime
from test_v192 import lua
W=Path(__file__).resolve().parent

def main(runtime):
 (W/'validation_v197.json').unlink(missing_ok=True);work=W/'native_work/v197';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v196.res').read_bytes();b=(W/'game_v197.res').read_bytes();ao,old=decode(a,range(2,86,2));bo,new=decode(b,range(2,86,2));report=json.loads((W/'build_v197.json').read_text())
 changes={int(k):v for k,v in report['changed_prototypes'].items()};assert changes=={12:[193,300],14:[632,668,684],30:[39,87]}
 assert ao.protos[0].bc==bo.protos[0].bc and a[-10:]==b[-10:]
 for m,d in new.items():
  assert d.rebuild()==d.raw and len(d.protos)==len(old[m].protos)
  for i,(p,q)in enumerate(zip(d.protos,old[m].protos)):
   assert(p.raw!=q.raw)==(i in changes.get(m,[])),(m,i)
   assert numeric_and_debug(p)[0]==numeric_and_debug(q)[0]
   assert(p.params,p.frame,p.uv)==(q.params,q.frame,q.uv)
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(m,i,pc)
 p,q=old[12].protos[300],new[12].protos[300]
 assert all(new[12].protos[193].bc[i]==x for i,x in enumerate(old[12].protos[193].bc)if i!=1067)
 assert new[12].protos[193].bc[1067]==jump(1067,1089,8)
 assert all(q.bc[i]==x for i,x in enumerate(p.bc)if i not in [702,2778])
 assert q.kgc[-p.nkgc:]==p.kgc
 assert old[12].protos[142].raw==new[12].protos[142].raw
 d=old[12];(work/'gen_old.ljbc').write_bytes(standalone(d,trees(d),193,{0:jump(0,681,5)}))
 d=new[12]
 (work/'config.ljbc').write_bytes(standalone(d,trees(d),142,{0:jump(0,1238),1248:ad('RET1',2,2)}))
 (work/'gen.ljbc').write_bytes(standalone(d,trees(d),193,{0:jump(0,681,5)}))
 (work/'tip.ljbc').write_bytes(standalone(d,trees(d),300));d=old[12];(work/'tip_old.ljbc').write_bytes(standalone(d,trees(d),300))
 for i,n in [(458,'proxy'),(223,'item_info')]:
  d=new[14];(work/(n+'.ljbc')).write_bytes(standalone(d,trees(d),i))
 p=new[12].protos[4090];shoes=[]
 for pc in [13670,19473,24973]:
  t=dict(p.gc(p.bc[pc]>>16)[2]);assert t['子类'.encode('gbk')]=='鞋子'.encode('gbk')
  t['风格提示'.encode('gbk')]=dict(p.gc(p.bc[pc+3]>>16)[2]);shoes.append(t)
 (work/'shoes.lua').write_bytes(('return {'+','.join(lua(t)for t in shoes)+'}').encode('gbk'))
 (work/'comfort.lua').write_bytes((W/'comfort_regression_v197.lua').read_text().encode('gbk'));runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'comfort.lua'),str(work),mode],capture_output=True,timeout=90);(work/(mode+'.log')).write_bytes(r.stdout+r.stderr)
  assert r.returncode==0,(r.stdout+r.stderr).decode('gbk','replace')[-3500:]
  output=r.stdout.decode('gbk');assert 'COMFORT_V197_PASS'in output;print(output,flush=True);runs.append({'mode':mode,'output':output})
 names=['patch_v197.py','test_v197.py','comfort_regression_v197.lua','package_v197.py','player_changes_v197.json']
 result={'version':'v1.197','all_passed':True,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'test_scope':'existing_generator_and_full_equipment_tooltip','comfort_coefficient_unchanged':True,'new_random_agility_removed':True,'other_name_and_colors_unchanged':True,'historical_suites_rerun':False,'full_windows_game_run':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v197.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');x=a.parse_args();main(str(Path(x.runtime).resolve())if x.runtime else str(ensure_runtime()))
