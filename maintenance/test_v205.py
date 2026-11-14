"""Resolution callback / real window constructor and complete native-frame regression."""
from pathlib import Path
import argparse,hashlib,json,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from patch_v139 import jump
from runtime import ensure_runtime
from patch_v196 import number_pool
from ljdis import OPS
W=Path(__file__).resolve().parent

def main(runtime):
 (W/'validation_v205.json').unlink(missing_ok=True);work=W/'native_work/v205';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v204.res').read_bytes();b=(W/'game_v205.res').read_bytes();ao,old=decode(a,range(2,86,2));bo,new=decode(b,range(2,86,2));build=json.loads((W/'build_v205.json').read_text())
 expected={12:[76,22187],14:[632,668,684],30:[39,87],48:[7,44]}
 assert ao.protos[0].bc==bo.protos[0].bc and a[-10:]==b[-10:]
 for m,d in new.items():
  assert d.rebuild()==d.raw and len(d.protos)==len(old[m].protos)
  for i,q in enumerate(old[m].protos):
   p=d.protos[i];assert(p.raw!=q.raw)==(i in expected.get(m,[])),(m,i)
   assert p.params==q.params and p.nkn==q.nkn and p.kgc==q.kgc if m==48 else p.params==q.params
   assert number_pool(p)==number_pool(q)
   if (m,i)==(48,7):
    assert p.nuv==1 and p.uv==bytes.fromhex('02c0') and p.frame==q.frame
    assert p.bc[:3754]==q.bc[:3754] and p.bc[3759:]==q.bc[3759:]
    assert [OPS[x&255]for x in p.bc[3754:3759]]==['UGET','MOV','CALL','RET0','RET0']
   elif(m,i)==(48,44):
    assert p.frame==3 and p.nuv==0 and p.nbc==106
    assert OPS[p.bc[3]&255]=='FNEW' and p.bc[3]>>8&255==2
    assert OPS[p.bc[-2]&255]=='UCLO' and OPS[p.bc[-1]&255]=='RET0'
   else:assert p.bc==q.bc and p.frame==q.frame and p.uv==q.uv,(m,i)
 assert new[48].protos[43].raw==old[48].protos[43].raw,'reuse previously compiled helper unchanged'
 # Both old and new modules retain actual class registration, initialization and display.
 for label,mods in [('old',old),('new',new)]:
  for m,i,n in[(48,44,'class'),(14,385,'frame')]:
   d=mods[m];index=i;(work/f'{n}_{label}.ljbc').write_bytes(standalone(d,trees(d),index))
 for m,i,n in[(12,21694,'button'),(12,189,'resolution'),(14,299,'screen_setter')]:
  d=new[m];(work/f'{n}.ljbc').write_bytes(standalone(d,trees(d),i))
 (work/'resolution.lua').write_bytes((W/'resolution_regression_v205.lua').read_text().encode('gbk'))
 runs=[]
 for label,mode in [('old','cold'),('new','cold'),('new','normal'),('new','hot')]:
  r=subprocess.run([runtime,str(work/'resolution.lua'),str(work),label,mode],capture_output=True,timeout=60);output=(r.stdout+r.stderr).decode('gbk','replace');(work/f'{label}_{mode}.log').write_bytes(r.stdout+r.stderr)
  if label=='old':
   assert r.returncode!=0 and "attempt to call field '__gm_draw_merc_hp_v204' (a nil value)"in output,output
  else:assert r.returncode==0 and 'RESOLUTION_V205_PASS'in output,output[-3000:]
  print(label,mode,output[-700:],flush=True);runs.append({'resource':label,'mode':mode,'expected_failure':label=='old','returncode':r.returncode,'output':output})
 names=['patch_v205.py','test_v205.py','resolution_regression_v205.lua','package_v205.py','player_changes_v205.json','window_hp_v204.lua','window_hp_v204.ljbc']
 result={'version':'v1.205','all_passed':True,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'test_scope':'actual_resolution_button_screen_setter_window_class_constructor_display_and_full_native_frame','old_startup_nil_helper_reproduced':True,'class_descriptor_readable_methods':False,'historical_suites_rerun':False,'full_windows_game_run':False,'physical_resolution_switch_tested':False,'save_reload_tested':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v205.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');x=a.parse_args();main(str(Path(x.runtime).resolve())if x.runtime else str(ensure_runtime()))
