"""Native map renderer/marker registration plus read-only destination/layout tests."""
from pathlib import Path
import argparse,json,hashlib,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from portal_routes_v212 import extract,child_refs
from patch_v139 import ad,jump
from bytecode_relocate import BRANCHES
from ljdis import OPS
from runtime import ensure_runtime
from test_v192 import lua
W=Path(__file__).resolve().parent

def main(runtime):
 (W/'validation_v212.json').unlink(missing_ok=True);work=W/'native_work/v212';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v211.res').read_bytes();b=(W/'game_v212.res').read_bytes();ao,old=decode(a,range(2,86,2));bo,new=decode(b,range(2,86,2));build=json.loads((W/'build_v212.json').read_text());count=build['helper_count']
 expected={10:[27,39],12:[76,22187],14:[632,668,684],30:[39,87]}
 assert ao.protos[0].bc==bo.protos[0].bc and a[-10:]==b[-10:]
 for mid,d in new.items():
  trees(d);assert d.rebuild()==d.raw and len(d.protos)==len(old[mid].protos)+(count if mid==10 else 0)
  for i,q in enumerate(old[mid].protos):
   p=d.protos[i+(count if mid==10 and i>=39 else 0)]
   assert (p.raw!=q.raw)==(i in expected.get(mid,[])),(mid,i)
   if (mid,i)not in [(10,27),(10,39)]:assert p.bc==q.bc,(mid,i)
  for p in d.protos:
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,p.idx,pc)
 for index,key,added in [(27,'render',{int(k):v for k,v in build['render_insertions'].items()}),(39,'constructor',{99:2})]:
  p=old[10].protos[index];q=new[10].protos[index+(count if index>=39 else 0)];mp={int(k):v for k,v in build['relocations'][key].items()}
  for pc,x in enumerate(p.bc):
   at=mp[pc]+added.get(pc,0);value=x
   if OPS[x&255]in BRANCHES:value=(x&65535)|((mp[pc+1+(x>>16)-32768]-at-1+32768)<<16)
   assert q.bc[at]==value,(index,pc)
 routes,evidence=extract(new[12]);assert len(routes)==99
 (work/'routes.lua').write_bytes(('return '+lua({k:v.encode('gbk')for k,v in routes.items()})).encode('gbk'))
 for version,mods in [('old',old),('new',new)]:
  d=mods[10];(work/f'map_{version}.ljbc').write_bytes(standalone(d,trees(d),39+(count if version=='new'else 0)))
 for mid,index,name in [(14,37,'font_factory'),(12,6,'font_registration'),(12,6488,'transfer')]:
  d=new[mid];patches={0:jump(0,180),184:ad('RET0',0,1)}if name=='font_registration'else None
  (work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),index,patches))
 (work/'maps.lua').write_bytes((W/'portal_regression_v212.lua').read_text().encode('gbk'));runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'maps.lua'),str(work),mode],capture_output=True,timeout=90);output=(r.stdout+r.stderr).decode('gbk','replace');(work/(mode+'.log')).write_bytes(r.stdout+r.stderr)
  assert r.returncode==0 and 'PORTALS_V212_PASS'in output,output[-4500:]
  print(output,flush=True);runs.append({'mode':mode,'output':output})
 names=['patch_v212.py','test_v212.py','package_v212.py','portal_routes_v212.py','portal_routes_v212.json','portal_labels_v212.lua','portal_labels_v212.ljbc','portal_regression_v212.lua','player_changes_v212.json']
 result={'version':'v1.212','all_passed':True,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'portal_count':len(routes),'runs':runs,'test_scope':'complete_native_map_constructor_renderer_marker_attachment_actual_public_font_factory_real_transfer_dispatch_with_finite_engine_graphics','all_42_modules_checked':True,'historical_suites_rerun':False,'full_windows_game_run':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v212.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--runtime');a=ap.parse_args();main(a.runtime or str(ensure_runtime()))
