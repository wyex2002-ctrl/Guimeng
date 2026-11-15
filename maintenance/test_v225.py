"""Native-size portal labels, original font renderer and unchanged unrelated behavior."""
from pathlib import Path
import argparse,json,hashlib,subprocess,zipfile
from resource_tools import decode
from native_test_utils import trees,standalone
from portal_routes_v213 import extract
from patch_v139 import ad,jump
from bytecode_relocate import BRANCHES
from ljdis import OPS
from runtime import ensure_runtime
from test_v192 import lua
W=Path(__file__).resolve().parent

def main(runtime):
 (W/'validation_v225.json').unlink(missing_ok=True);work=W/'native_work/v225';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v224.res').read_bytes();b=(W/'game_v225.res').read_bytes();ao,old=decode(a,range(2,86,2));bo,new=decode(b,range(2,86,2))
 expected={10:[39,40,41],12:[76,22194],14:[632,668,684],30:[39,87],56:[7]}
 build=json.loads((W/'build_v225.json').read_text());assert {int(k):v for k,v in build['changed_prototypes'].items()}==expected
 for mid,d in new.items():
  trees(d);assert d.rebuild()==d.raw and len(d.protos)==len(old[mid].protos)
  for idx,p in enumerate(d.protos):
   assert (p.raw!=old[mid].protos[idx].raw)==(idx in expected.get(mid,[])),(mid,idx)
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,idx,pc)
 _,font=decode(zipfile.ZipFile(W/'base_v176.zip').read('Lib/game.res'),[56])
 assert new[56].raw==font[56].raw,'entire native font module restored byte-for-byte'
 assert old[22].raw==new[22].raw,'guard rules unchanged'
 for idx in range(22187,22194):assert old[12].protos[idx].raw==new[12].protos[idx].raw,'warehouse unchanged'
 routes,_=extract(new[12]);assert len(routes)==99
 (work/'routes.lua').write_bytes(('return '+lua({k:v.encode('gbk')for k,v in routes.items()})).encode('gbk'))
 exports=[(10,42,'map_new',None),(56,7,'font_layout_native',None),(14,49,'event_engine_factory',None),(12,6,'font_registration',{0:jump(0,180),184:ad('RET0',0,1)}),(14,378,'plugin_install',{0:jump(0,317,13),639:ad('RET0',0,1)}),(16,73,'sprite_factory',None)]
 for mid,idx,name,patches in exports:
  d=new[mid];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx,patches))
 (work/'maps.lua').write_bytes((W/'portal_regression_v225.lua').read_text().encode('gbk'));runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'maps.lua'),str(work),mode],capture_output=True,timeout=90)
  output=(r.stdout+r.stderr).decode('gbk','replace');(work/(mode+'.log')).write_bytes(r.stdout+r.stderr)
  assert r.returncode==0 and 'PORTALS_V225_PASS'in output,output[-4500:]
  print(output);runs.append({'mode':mode,'output':output})
 names=['patch_v225.py','test_v225.py','portal_labels_v225.lua','portal_labels_v225.ljbc','portal_regression_v225.lua','package_v225.py','player_changes_v225.json']
 result={'version':'v1.225','all_passed':True,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'native_font_module_restored':True,'portal_scale':1,'test_scope':'original native font renderer, full native map/actual restricted plugin installer, native dimensions and layout, 99 IDs, optional outline, hidden map and caching; finite glyph/graphics boundaries','all_42_modules_checked':True,'historical_suites_rerun':False,'full_windows_game_run':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v225.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');a=p.parse_args();main(a.runtime or str(ensure_runtime()))
