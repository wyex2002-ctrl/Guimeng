"""Native map renderer/marker registration plus read-only destination/layout tests."""
from pathlib import Path
import argparse,json,hashlib,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from portal_routes_v213 import extract,child_refs
from patch_v139 import ad,jump
from bytecode_relocate import BRANCHES
from ljdis import OPS
from runtime import ensure_runtime
from test_v192 import lua
W=Path(__file__).resolve().parent

def main(runtime):
 (W/'validation_v214.json').unlink(missing_ok=True);work=W/'native_work/v214';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v213.res').read_bytes();b=(W/'game_v214.res').read_bytes();ao,old=decode(a,range(2,86,2));bo,new=decode(b,range(2,86,2));build=json.loads((W/'build_v214.json').read_text());count=build['helper_count']
 expected={10:[39,40,41],12:[76,22187],14:[632,668,684],30:[39,87]}
 assert ao.protos[0].bc==bo.protos[0].bc and a[-10:]==b[-10:]
 for mid,d in new.items():
  trees(d);assert d.rebuild()==d.raw and len(d.protos)==len(old[mid].protos)
  for i,q in enumerate(old[mid].protos):
   p=d.protos[i]
   assert (p.raw!=q.raw)==(i in expected.get(mid,[])),(mid,i)
   if (mid,i)not in [(10,39),(10,40),(10,41)]:assert p.bc==q.bc,(mid,i)
  for p in d.protos:
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,p.idx,pc)
 routes,evidence=extract(new[12]);assert len(routes)==99
 (work/'routes.lua').write_bytes(('return '+lua({k:v.encode('gbk')for k,v in routes.items()})).encode('gbk'))
 _,broken=decode((W/'game_v212.res').read_bytes(),[10])
 _,baseline=decode((W/'game_v211.res').read_bytes(),[10])
 for version,mods,index in [('old',baseline,39),('broken',broken,42),('black',old,42),('new',new,42)]:
  d=mods[10];(work/f'map_{version}.ljbc').write_bytes(standalone(d,trees(d),index))
 for mid,index,name in [(14,49,'event_engine_factory'),(12,6,'font_registration'),(12,6488,'transfer'),(12,574,'door_expire')]:
  d=new[mid];patches={0:jump(0,180),184:ad('RET0',0,1)}if name=='font_registration'else None
  (work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),index,patches))
 for ident,idx,callback in [(1301,17510,17513),(1329,17639,17642),(1330,17716,17719),(1331,17793,17796)]:
  d=new[12]
  for name,index in [('door_script',idx),('door_callback',callback)]:
   (work/(name+str(ident)+'.ljbc')).write_bytes(standalone(d,trees(d),index))
 # Actual EM_引擎 exports: no 画线/创建文字. Reuse its real public sprite
 # factory and rotation/scaling methods with finite low-level __Sprite only.
 d=new[16];exports={d.protos[98].gc(x>>16&255)for x in d.protos[98].bc if OPS[x&255]=='TSETS'}
 assert '画线'.encode('gbk')not in exports and '创建文字'.encode('gbk')not in exports
 for name in ['创建精灵','创建包围盒']:assert name.encode('gbk')in exports
 (work/'sprite_factory.ljbc').write_bytes(standalone(d,trees(d),73))
 # Exact original native font call, with unrelated rich-text loop locals zeroed.
 # This proves the argument contract against a shipped caller, not our own mock.
 d=new[52];p=d.protos[6];assert OPS[p.bc[1531]&255]=='KSHORT'and p.bc[1531]>>16==0
 patches={i:ad('KSHORT',reg,0)for i,reg in enumerate([13,14,37,18,15])}
 patches|={5:ad('KSHORT',35,1),6:ad('KSHORT',42,1),7:jump(7,1521,55),1538:ad('RET0',0,1)}
 (work/'native_font_call.ljbc').write_bytes(standalone(d,trees(d),6,patches))
 # Actual original installer builds script_setting, copies its restricted exports,
 # substitutes EM_引擎, then binds L插件 functions with setfenv. Only startup before
 # this independent setup stage and unrelated post-stage graphics are omitted.
 d=new[14];(work/'plugin_install.ljbc').write_bytes(standalone(d,trees(d),378,{0:jump(0,317,13),639:ad('RET0',0,1)}))
 # Actual death callback portal-spawn and map-change cleanup blocks.
 for idx,name,start,end in [(10294,'door_spawn',468,558),(58,'map_door_clear',287,298)]:
  d=new[12];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx,{0:jump(0,start,d.protos[idx].params),end:ad('RET0',0,1),**({630:ad('RET0',0,1)}if idx==10294 else {})}))
 (work/'maps.lua').write_bytes((W/'portal_regression_v214.lua').read_text().encode('gbk'));runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'maps.lua'),str(work),mode],capture_output=True,timeout=90);output=(r.stdout+r.stderr).decode('gbk','replace');(work/(mode+'.log')).write_bytes(r.stdout+r.stderr)
  assert r.returncode==0 and 'PORTALS_V214_PASS'in output,output[-4500:]
  print(output,flush=True);runs.append({'mode':mode,'output':output})
 names=['patch_v214.py','test_v214.py','package_v214.py','portal_routes_v213.py','portal_routes_v213.json','portal_labels_v214.lua','portal_labels_v214.ljbc','portal_regression_v214.lua','player_changes_v214.json']
 result={'version':'v1.214','all_passed':True,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'portal_count':len(routes),'runs':runs,'test_scope':'native_font_argument_contract_v213_negative_real_sprite_factory_connectors_and_plugin_map_otherworld_with_finite_engine_boundaries','all_42_modules_checked':True,'historical_suites_rerun':False,'full_windows_game_run':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v214.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--runtime');a=ap.parse_args();main(a.runtime or str(ensure_runtime()))
