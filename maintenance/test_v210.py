"""Actual hero class/skill/state/animation integration; focused normal/hot timing."""
from pathlib import Path
import argparse,json,hashlib,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from patch_v139 import ad,jump
from patch_v201 import unpack_config
from bytecode_relocate import BRANCHES,numeric_and_debug
from ljdis import OPS
from runtime import ensure_runtime
from test_v192 import lua
W=Path(__file__).resolve().parent
SKILLS={3:'普通攻击',701:'基本剑术',711:'攻杀剑术',722:'刺杀剑术',733:'半月弯刀',744:'翔空剑法',755:'烈火剑法',766:'十方斩',777:'莲月剑法',796:'快刀斩麻',32:'火球术'}
def main(runtime):
 (W/'validation_v210.json').unlink(missing_ok=True);work=W/'native_work/v210';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v207.res').read_bytes();b=(W/'game_v210.res').read_bytes();ao,old=decode(a,range(2,86,2));bo,new=decode(b,range(2,86,2));build=json.loads((W/'build_v210.json').read_text())
 _,previous=decode((W/'game_v209.res').read_bytes(),range(2,86,2))
 expected={12:[20,76,22187],14:[632,668,684],26:[26,87],30:[39,87]}
 assert {int(k):v for k,v in build['changed_prototypes'].items()}=={m:expected.get(m,[])for m in [12,14,26,30]}
 assert ao.protos[0].bc==bo.protos[0].bc and a[-10:]==b[-10:]
 for mid,d in new.items():
  assert d.rebuild()==d.raw and len(d.protos)==len(previous[mid].protos)
  for i,(p,q) in enumerate(zip(d.protos,previous[mid].protos)):
   assert (p.raw!=q.raw)==(i in expected.get(mid,[])),(mid,i)
   assert (p.params,p.uv)==(q.params,q.uv),(mid,i)
   if (mid,i)!=(26,87):assert p.frame==q.frame,(mid,i)
   if (mid,i)not in [(26,26),(26,87),(12,20)]:assert p.bc==q.bc,(mid,i)
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,i,pc)
 # Verify every surviving input/timer instruction and its relocated target;
 # other periodic jobs, 100ms timer factory and actual Shift callback unchanged.
 for mid,idx,key,deleted in [(26,26,'input210',set()),(12,20,'timer210',set(range(1307,1312)))]:
  p,q=previous[mid].protos[idx],new[mid].protos[idx]
  mp={int(k):v for k,v in build['relocations'][key].items()}
  for pc,ins in enumerate(p.bc):
   if pc in deleted:continue
   at=mp[pc]+(4 if mid==26 and pc==43 else 0);expected_ins=ins
   if OPS[ins&255]in BRANCHES:expected_ins=(ins&65535)|((mp[pc+1+(ins>>16)-32768]-at-1+32768)<<16)
   assert q.bc[at]==expected_ins,(mid,idx,pc)
 # Keep the original v207 scheduling reference, rather than treating v209's
 # faster feedback as the original combat cadence.
 # The entire shared skill configuration, callbacks, damage, hit, creature and
 # animation modules are covered by the unchanged-prototype comparison above.
 cfg={name.encode('gbk'):unpack_config(new[12].protos[6464].gc(i))for i,name in SKILLS.items()}
 (work/'configs.lua').write_bytes(('return '+lua(cfg)).encode('gbk'))
 d=new[12];stack=[];refs={}
 for q in d.protos:
  for j,v in enumerate(q.kgc):
   if v==('child',):refs[q.idx,q.nkgc-1-j]=stack.pop()
  stack.append(q.idx)
 callbacks={};p=d.protos[6464]
 for n,name in enumerate(SKILLS.values()):
  text=('【数据库/技能脚本/'+name+'】').encode('gbk')
  pc=next(i for i,x in enumerate(p.bc)if OPS[x&255]=='KSTR'and p.gc(x>>16)==text)
  assert OPS[p.bc[pc-2]&255]=='FNEW'
  i=refs[6464,p.bc[pc-2]>>16];key='callback_'+str(n);callbacks[name.encode('gbk')]=key.encode()
  (work/(key+'.ljbc')).write_bytes(standalone(d,trees(d),i))
 (work/'scripts.lua').write_bytes(('return '+lua(callbacks)).encode('gbk'))

 for label,mods in [('old',old),('new',new)]:
  d=mods[26];(work/f'class_{label}.ljbc').write_bytes(standalone(d,trees(d),88 if label=='new'else 87))
  mp={int(k):v for k,v in build['relocations']['3'].items()}if label=='new'else{j:j for j in range(d.protos[3].nbc+1)}
  (work/f'tick_{label}.ljbc').write_bytes(standalone(d,trees(d),3,{0:jump(0,mp[839],3),mp[843]:ad('RET0',0,1)} if label=='old'else {0:jump(0,mp[839],3),mp[843]+5:ad('RET0',0,1)}))
 d=previous[26];(work/'class_previous.ljbc').write_bytes(standalone(d,trees(d),88));(work/'tick_previous.ljbc').write_bytes((work/'tick_new.ljbc').read_bytes())
 for mid,i,n in [(20,8,'animation'),(20,6,'reverse'),(20,21,'reset'),(12,4091,'skill_factory'),(30,43,'rotate')]:
  d=new[mid];(work/f'{n}.ljbc').write_bytes(standalone(d,trees(d),i))
 for mid,i,n in [(12,204,'shift'),(14,340,'hero_api'),(14,167,'timer_factory')]:
  d=new[mid];(work/f'{n}.ljbc').write_bytes(standalone(d,trees(d),i))
 d=new[12];(work/'shift_registration.ljbc').write_bytes(standalone(d,trees(d),292,{0:jump(0,63,0),66:jump(66,240,0),241:jump(241,301,1),304:jump(304,472,1)}))
 d=new[14];(work/'timer_loop.ljbc').write_bytes(standalone(d,trees(d),385,{0:jump(0,2582,2),2662:ad('RET0',0,1)}))
 (work/'input.lua').write_bytes(((W/'melee_regression_v210.lua').read_text().split("local melee={'普通攻击'")[0]+(W/'input_regression_v210.lua').read_text()).encode('gbk'))
 (work/'timing.lua').write_bytes((W/'melee_regression_v210.lua').read_text().encode('gbk'));runs=[]
 for mode in ['normal','hot']:
  res=subprocess.run([runtime,str(work/'timing.lua'),str(work),mode],capture_output=True,timeout=90)
  output=(res.stdout+res.stderr).decode('gbk','replace');(work/(mode+'.log')).write_bytes(res.stdout+res.stderr)
  assert res.returncode==0 and 'MELEE_V210_PASS'in output,output[-4500:]
  print(output,flush=True);runs.append({'mode':mode,'output':output})
 for mode in ['normal','hot']:
  res=subprocess.run([runtime,str(work/'input.lua'),str(work),mode],capture_output=True,timeout=90)
  output=(res.stdout+res.stderr).decode('gbk','replace');(work/(mode+'.input.log')).write_bytes(res.stdout+res.stderr)
  assert res.returncode==0 and 'INPUT_PASS'in output,output[-4500:]
  print(output,flush=True);runs.append({'mode':mode,'scope':'native_input_and_original_timer_factory_loop_and_public_api','output':output})
 names=['input_regression_v210.lua','patch_v210.py' ,'test_v210.py','melee_timing_v210.lua','melee_timing_v210.ljbc','melee_regression_v210.lua','package_v210.py','player_changes_v210.json']
 result={'version':'v1.210','all_passed':True,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'skills':list(SKILLS.values())[:-1],'test_scope':'actual_hero_registration_release_instance_refresh_state_and_original_Lua_animation_with_finite_assets','full_windows_game_run':False,'full_original_assets':False,'complete_native_frame':False,'historical_suites_rerun':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v210.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--runtime');x=ap.parse_args();main(x.runtime or str(ensure_runtime()))
