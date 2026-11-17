from test_v225 import *
from patch_v265 import BASE_SHA
from patch_v201 import unpack_config
from test_v192 import lua
from bytecode_relocate import numeric_and_debug

def main(runtime):
 work=W/'native_work/v265';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v264.res').read_bytes();b=(W/'game_v265.res').read_bytes();assert hashlib.sha256(a).hexdigest()==BASE_SHA
 _,old=decode(a,range(2,86,2));_,new=decode(b,range(2,86,2));expected={12:{76,22196},14:{674,710,726},26:{88},30:{39,87}}
 for mid,d in new.items():
  trees(d);assert d.rebuild()==d.raw and len(d.protos)==len(old[mid].protos)
  assert {i for i,(p,q)in enumerate(zip(old[mid].protos,d.protos))if p.raw!=q.raw}==expected.get(mid,set()),mid
  for p in d.protos:
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,p.idx,pc)
 # The compiled control-flow skeleton is preserved. Constant remapping is
 # compiler-managed when the only changed literal reuses the existing 1 slot.
 before=(W/'repeat_skill_v236.lua').read_text();after=(W/'repeat_skill_v265.lua').read_text();assert before.replace('state.started + 1e-9 >= 1.5','state.started + 1e-9 >= 1')==after
 assert new[36].raw==old[36].raw and new[16].raw==old[16].raw
 def export(mid,idx,name,patches=None):
  d=new[mid];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx,patches))
 for mid,idx,name in [(26,89,'class_new'),(20,8,'animation'),(20,6,'reverse'),(20,21,'reset'),(12,4093,'skill_factory'),(30,43,'rotate'),(36,13,'slot_class'),(16,39,'cd_factory'),(16,73,'sprite_factory'),(14,458,'getter'),(14,13,'readonly'),(12,46,'selector')]:export(mid,idx,name)
 export(26,3,'repeat_head',{4:ad('RET0',0,1)})
 export(26,0,'repeat_reset',{3:ad('RET0',0,1)})
 export(26,3,'tick_new',{0:ad('RET0',0,1)}) # fixture never steps unrelated native combat
 d=old[26];(work/'control_old.ljbc').write_bytes(standalone(d,trees(d),88))
 cfg={};p=new[12].protos[6466];name=None
 wanted={'月魂灵波','雷电术','普通攻击','召唤神兽'}
 for x in p.bc:
  if OPS[x&255]=='KSTR':
   reg=(x>>8)&255;v=p.gc(x>>16)
   if reg==4:name=v
   if reg==7 and name and name.decode('gbk','replace')in wanted and isinstance(v,bytes)and v.endswith(b'*'):cfg[name]=unpack_config(v)
 assert len(cfg)==4
 (work/'configs.lua').write_bytes(('return '+lua(cfg)).encode('gbk'));(work/'scripts.lua').write_bytes(b'return {}')
 prefix=(W/'melee_regression_v210.lua').read_text().split("local melee={'普通攻击'")[0]
 src=work/'test.lua';src.write_bytes((prefix+(W/'repeat_hold_regression_v265.lua').read_text()).encode('gbk'));runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(src),str(work),mode],capture_output=True,timeout=90);out=(r.stdout+r.stderr).decode('gbk','replace');print(out,flush=True);(work/(mode+'.log')).write_text(out);assert r.returncode==0,(mode,out[-5000:]);runs.append({'mode':mode,'output':out})
 notes=json.loads((W/'player_changes_v265.json').read_text());assert len(notes)==54
 import re
 basis=(W.parent/'docs/玩家版说明_基础版.txt').read_text();rows=re.findall(r'^(\d+)\. (.+)$',basis,re.M)
 assert [int(n)for n,_ in rows]==list(range(1,55)) and [s for _,s in rows]==notes
 assert '快捷键1秒'in notes[49] and not any('1.5秒'in s for s in notes)
 assert not any('佣兵进入游戏时默认处于锁定状态'in s or '修复使用灵魂神水等六种神水时可能闪退'in s for s in notes)
 names=['patch_v265.py','test_v265.py','package_v265.py','player_changes_v265.json','repeat_skill_v265.lua','repeat_skill_v265.ljbc','repeat_hold_regression_v265.lua']
 result={'version':'v1.265','all_passed':True,'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'all_42_modules_checked':True,'full_windows_game_run':False,'historical_suites_rerun':False,'scope':'actual hero class registration/update entry, skill factory, hotkey slot callback and repeat scheduler; finite physical-input/graphics/dispatch bridges; one-second boundaries and unchanged exit gates; player copy deletion/renumbering consistency','tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v265.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');a=p.parse_args();main(a.runtime or str(ensure_runtime()))
