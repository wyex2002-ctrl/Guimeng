"""Actual native drop/ground initialization and removed UI/timer regressions."""
from test_v225 import *

def main(runtime):
 work=W/'native_work/v243';work.mkdir(parents=True,exist_ok=True)
 base=(W/'game_v242.res').read_bytes();data=(W/'game_v243.res').read_bytes()
 _,old=decode(base,range(2,86,2));_,new=decode(data,range(2,86,2));_,prior=decode((W/'game_v241.res').read_bytes(),[12,14,26])
 expected={12:[76,22203],14:[385,632,668,684,689],22:[112],26:[0],30:[39,87]}
 removed={12:set(range(22194,22203)),14:{688}}
 for mid,d in new.items():
  trees(d);assert d.rebuild()==d.raw
  keep=[p for p in old[mid].protos if p.idx not in removed.get(mid,set())];assert len(keep)==len(d.protos)
  changes=[p.idx for p,q in zip(keep,d.protos)if p.raw!=q.raw];assert changes==expected.get(mid,[]),(mid,changes)
  for p in d.protos:
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc
 assert new[26].protos[0].raw==prior[26].protos[0].raw
 p,q=new[14].protos[385],prior[14].protos[385];assert p.bc==q.bc and p.frame==q.frame and p.uv==q.uv
 assert p.gc(222)==q.gc(222).replace(b'for dy=-4,4 do for dx=-4,4 do',b'for dy=-5,5 do for dx=-5,5 do')
 assert new[40].raw==old[40].raw
 for p in new[12].protos:assert b'__gm_auto_pickup_v242'not in p.strings()
 def export(mid,idx,name,patches=None,dumps=new):
  d=dumps[mid];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx,patches))
 for mid,idx,name in [(14,413,'window_lookup'),(48,26,'add_control'),(48,23,'bind_control'),(62,12,'button_register'),(16,73,'sprite_native'),(22,64,'death_new'),(22,3,'spawn'),(12,191,'currency_new'),(14,339,'fx_getter'),(14,416,'public_get'),(14,13,'public_sys'),(14,458,'data_protection'),(12,4089,'oil_template'),(14,685,'oil_reset'),(22,112,'oil_helper'),(14,402,'native_drop'),(76,0,'ground_init')]:export(mid,idx,name)
 export(22,112,'old_oil_helper',dumps=old);export(22,64,'death_old',dumps=old)
 export(30,193,'table_register',{0:jump(0,33),42:jump(42,57),69:ad('RET0',0,1)})
 p=new[12].protos[22194];pc=p.nbc-3;export(12,22194,'ui_root',{0:jump(0,30000,0),30000:jump(30000,pc,0)})
 for label,dumps in [('old',old),('new',new)]:export(14,385,'frame_'+label,dumps=dumps)
 (work/'range_pickup.lua').write_bytes(new[14].protos[385].gc(222))
 runs=[]
 for suite in ['ui','pickup','oil','frame']:
  (work/(suite+'.lua')).write_bytes((W/(suite+'_regression_v243.lua')).read_text().encode('gbk'))
  for mode in ['normal','hot']:
   r=subprocess.run([runtime,str(work/(suite+'.lua')),str(work),mode],capture_output=True,timeout=90);output=(r.stdout+r.stderr).decode('gbk','replace');(work/(suite+'.'+mode+'.log')).write_text(output)
   assert r.returncode==0,(suite,mode,output[-5000:]);print(output,flush=True);runs.append({'suite':suite,'mode':mode,'output':output})
 names=['patch_v243.py','test_v243.py','package_v243.py','player_changes_v243.json','oil_drop_v243.lua','oil_drop_v243.ljbc']+[s+'_regression_v243.lua'for s in ['ui','pickup','oil','frame']]
 result={'version':'v1.243','all_passed':True,'sha256':hashlib.sha256(data).hexdigest(),'all_42_modules_checked':True,'runs':runs,'old_oil_error_reproduced':True,'real_native_drop_402_and_full_ground_constructor_76_0':True,'full_windows_game_run':False,'scope':'native death/public Sys/data proxy/template/native drop/complete ground init with finite engine graphics/map/class allocation and public operation bridge; actual UI; complete zero-input frame; pickup finite ground objects; water/other modules unchanged','tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v243.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');a=p.parse_args();main(a.runtime or str(ensure_runtime()))
