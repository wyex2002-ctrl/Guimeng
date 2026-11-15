"""Focused stack sale, return scroll and native UI integration regression."""
from pathlib import Path
import argparse,json,hashlib,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from patch_v139 import ad,jump
from runtime import ensure_runtime
from bytecode_relocate import BRANCHES
from ljdis import OPS
from test_v192 import lua
W=Path(__file__).resolve().parent

def main(runtime):
 (W/'validation_v219.json').unlink(missing_ok=True)
 work=W/'native_work/v219';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v218.res').read_bytes();b=(W/'game_v219.res').read_bytes()
 ao,old=decode(a,range(2,86,2));bo,new=decode(b,range(2,86,2));build=json.loads((W/'build_v219.json').read_text());n=build['helper_count']
 changed={int(k):v for k,v in build['changed_prototypes'].items()}
 expected={12:sorted(set(build['whitelist_changes']['12']+[37,76,4090,22187])),14:[572,632,668,684],30:[39,87],34:[10]}
 assert changed==expected
 for mid,d in new.items():
  assert d.rebuild()==d.raw
  assert len(d.protos)==len(old[mid].protos)+(n if mid==12 else 0)
  for i,q in enumerate(old[mid].protos):
   p=d.protos[i+(n if mid==12 and i>=22187 else 0)]
   assert (p.raw!=q.raw)==(i in expected.get(mid,[])),(mid,i)
   if (mid,i) not in [(12,37),(12,22187)]:assert p.bc==q.bc or (mid,i)==(12,4090),(mid,i)
  for p in d.protos:
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,p.idx,pc)
 # Verify relocation of every retained event instruction/branch, not just targets.
 mp={int(k):v for k,v in build['sale_map'].items()};p=old[12].protos[37];q=new[12].protos[37]
 for pc,x in enumerate(p.bc):
  if pc in [265,266,267]:continue
  at=mp[pc]+(3 if pc in [285,1362]else 0)
  if OPS[x&255]in BRANCHES:x=(x&65535)|((mp[pc+1+(x>>16)-32768]-at-1+32768)<<16)
  assert q.bc[at]==x,(pc,at)
 for mid,ids in build['whitelist_changes'].items():
  mid=int(mid)
  for i in ids:
   p=old[mid].protos[i];q=new[mid].protos[i];assert p.bc==q.bc
   for v,w in zip(p.kgc,q.kgc):
    if v!=w:assert w==('table',v[1],v[2]+[('回城卷'.encode('gbk'),True)])
 # Export original and updated event, validators, item metadata, UI factories.
 exports=[(14,458,'proxy'),(14,443,'update_item'),(14,437,'reset_item'),(34,22,'consume_native'),(14,413,'window_lookup'),(48,26,'add_control'),(48,23,'bind_control'),(62,12,'button_register'),(14,223,'item_info'),(14,224,'slot_info'),(14,572,'stack_install'),(34,10,'consume'),(34,9,'stack_limit')]
 for mid,i,name in exports:
  d=new[mid];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),i))
 for label,mods in [('old',old),('new',new)]:
  d=mods[12]
  for i,name in [(37,'event'),(33,'validator')]: (work/(name+'_'+label+'.ljbc')).write_bytes(standalone(d,trees(d),i))
 d=new[30];(work/'table_register.ljbc').write_bytes(standalone(d,trees(d),193,{0:jump(0,33),42:jump(42,57),69:ad('RET0',0,1)}))
 # The real UI root executes the inserted helper, using its actual child slots.
 d=new[12];idx=22187+n;pc=build['ui_map'][str(old[12].protos[22187].nbc-1)]
 (work/'ui_root.ljbc').write_bytes(standalone(d,trees(d),idx,{0:jump(0,30000,0),30000:jump(30000,pc,0)}))
 p=new[12].protos[4090];cfg=dict(p.gc(p.bc[9670]>>16)[2]);assert cfg['叠加'.encode('gbk')]==('int',1)
 cfg['属性'.encode('gbk')]={};cfg['附加'.encode('gbk')]={'叠加上限'.encode('gbk'):999}
 cfg['资源'.encode('gbk')]={};cfg['风格提示'.encode('gbk')]={}
 (work/'scroll.lua').write_bytes(('return '+lua(cfg)).encode('gbk'))
 (work/'regression.lua').write_bytes((W/'inventory_regression_v219.lua').read_text().encode('gbk'));runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'regression.lua'),str(work),mode],capture_output=True,timeout=90)
  output=(r.stdout+r.stderr).decode('gbk','replace');(work/(mode+'.log')).write_bytes(r.stdout+r.stderr)
  assert r.returncode==0,output[-4500:]
  assert 'INVENTORY_V219_PASS'in output;print(output);runs.append({'mode':mode,'output':output})
 names=['patch_v219.py','test_v219.py','inventory_regression_v219.lua','warehouse_button_v219.lua','warehouse_button_v219.ljbc','package_v219.py','player_changes_v219.json']
 result={'version':'v1.219','all_passed':True,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'runs':runs,'full_windows_game_run':False,'full_client_save_load':False,'historical_suites_rerun':False,'test_scope':'native sale events and callbacks; bounded scroll stack validators; native metadata and stack installer; native UI root/helper/control factory/imagebutton with finite graphics primitives','tested_files':{name:hashlib.sha256((W/name).read_bytes()).hexdigest()for name in names}}
 (W/'validation_v219.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--runtime');x=ap.parse_args();main(x.runtime or str(ensure_runtime()))
