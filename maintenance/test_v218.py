"""Focused native hero/effect integration and unchanged combat timing."""
from pathlib import Path
import argparse,json,hashlib,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from patch_v139 import ad,jump
from patch_v201 import unpack_config
from bytecode_relocate import BRANCHES
from ljdis import OPS
from runtime import ensure_runtime
from test_v192 import lua
from test_v210 import SKILLS
W=Path(__file__).resolve().parent

def main(runtime):
 (W/'validation_v218.json').unlink(missing_ok=True);work=W/'native_work/v218';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v217.res').read_bytes();b=(W/'game_v218.res').read_bytes();ao,old=decode(a,range(2,86,2));bo,new=decode(b,range(2,86,2));build=json.loads((W/'build_v218.json').read_text())
 expected={12:[76,22187],14:[632,668,684],26:[87],30:[39,87]}
 assert {int(k):v for k,v in build['changed_prototypes'].items()}=={m:expected.get(m,[])for m in [12,14,26,30]}
 assert ao.protos[0].bc==bo.protos[0].bc and a[-10:]==b[-10:]
 for mid,d in new.items():
  assert d.rebuild()==d.raw and len(d.protos)==len(old[mid].protos)
  for i,(p,q) in enumerate(zip(d.protos,old[mid].protos)):
   assert (p.raw!=q.raw)==(i in expected.get(mid,[])),(mid,i)
   assert (p.params,p.uv)==(q.params,q.uv),(mid,i)
   if (mid,i)not in [(26,0),(26,55),(26,87)]:assert p.frame==q.frame and p.bc==q.bc,(mid,i)
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,i,pc)
 _,ref=decode((W/'game_v207.res').read_bytes(),[26])
 d=ref[26];(work/'class_reference.ljbc').write_bytes(standalone(d,trees(d),87))
 (work/'tick_reference.ljbc').write_bytes(standalone(d,trees(d),3,{0:jump(0,839,3),843:ad('RET0',0,1)}))
 # Original activation text/color/duration are compared with real event constants.
 expected_notice={new[12].protos[46].gc(i)for i in [32,36,40]}
 for v in expected_notice:assert v.decode('gbk')in (W/'melee_timing_v218.lua').read_text()
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
  d=mods[26];(work/f'class_{label}.ljbc').write_bytes(standalone(d,trees(d),88))
  (work/f'tick_{label}.ljbc').write_bytes(standalone(d,trees(d),3,{0:jump(0,839,3),848:ad('RET0',0,1)}))
 for mid,i,n in [(20,8,'animation'),(20,6,'reverse'),(20,21,'reset'),(12,4091,'skill_factory'),(30,43,'rotate'),(14,386,'effect_factory'),(42,13,'effect_class')]:
  d=new[mid];(work/f'{n}.ljbc').write_bytes(standalone(d,trees(d),i))
 # Execute real rule rows, status insertion/timing, native selector and public lookup.
 for mid,i,n in [(12,46,'selector'),(14,222,'skill_info'),(40,20,'buff_class'),(14,340,'hero_api'),(12,165,'refresh_skills'),(14,221,'skill_set'),(12,126,'role_a'),(12,132,'role_b'),(12,204,'shift')]:
  d=new[mid];(work/f'{n}.ljbc').write_bytes(standalone(d,trees(d),i))
 d=new[12];(work/'shift_registration.ljbc').write_bytes(standalone(d,trees(d),292,{0:jump(0,63,0),66:jump(66,240,0),241:jump(241,301,1),304:jump(304,472,1)}))
 d=new[12];p=d.protos[142];assert OPS[p.bc[2972]&255]=='TNEW'
 (work/'rules.ljbc').write_bytes(standalone(d,trees(d),142,{0:ad('TNEW',1,0),1:jump(1,2972,4),3032:ad('RET1',1,2)}))
 d=new[26];stop=3
 (work/'reset_session.ljbc').write_bytes(standalone(d,trees(d),0,{stop:ad('RET0',0,1)}))
 d=new[26];(work/'buff_tick.ljbc').write_bytes(standalone(d,trees(d),3,{0:jump(0,87,3),141:ad('RET0',0,1)}))
 # Exact status template data; scripts are the real child factories.
 from portal_routes_v213 import child_refs
 from ljtool import Proto
 p=new[12].protos[725];refs=child_refs(new[12]);status={}
 wanted={'烈火剑法','翔空剑法','莲月剑法','烈火剑法CD','翔空剑法CD','莲月剑法CD'}
 for pc,x in enumerate(p.bc):
  if OPS[x&255]!='TDUP':continue
  t=p.gc(x>>16)
  if not isinstance(t,tuple)or t[0]!='table':continue
  fields=dict(t[2]);name=fields.get('标识'.encode('gbk'))
  if name is None or name.decode('gbk')not in wanted:continue
  fields.pop('配置项文本'.encode('gbk'),None);fields['属性'.encode('gbk')]={}
  status[name]=fields
  site=next(j for j in range(pc,pc+15)if OPS[p.bc[j]&255]=='FNEW')
  idx=refs[725,p.bc[site]>>16]
  (work/('status_'+name.hex()+'.ljbc')).write_bytes(standalone(new[12],trees(new[12]),idx))
 assert len(status)==6
 (work/'statuses.lua').write_bytes(('return '+lua(status)).encode('gbk'))
 prefix=(W/'melee_regression_v210.lua').read_text().split("local melee={'普通攻击'")[0]
 prefix=prefix.replace("skills[name]['起手动画']={};skills[name]['目标动画']={};", "if not opts.effects then skills[name]['起手动画']={};skills[name]['目标动画']={} end;")
 # Reuse actual finite-art effect scene, but the v218 tests compare 215 to 216.
 visual=(W/'effect_regression_v211.lua').read_text().split('\nfor _,name in ipairs(names)do')[0]
 (work/'effects.lua').write_bytes((prefix+visual+(W/'combat_regression_v218.lua').read_text()).encode('gbk'));runs=[]
 for mode in ['normal','hot']:
  res=subprocess.run([runtime,str(work/'effects.lua'),str(work),mode],capture_output=True,timeout=90)
  output=(res.stdout+res.stderr).decode('gbk','replace');(work/(mode+'.log')).write_bytes(res.stdout+res.stderr)
  assert res.returncode==0 and 'EFFECT_V218_PASS'in output,output[-4000:]
  print(output,flush=True);runs.append({'mode':mode,'output':output})
 names=['patch_v218.py','test_v218.py','combat_regression_v218.lua','melee_timing_v218.lua','melee_timing_v218.ljbc','effect_regression_v211.lua','package_v218.py','player_changes_v218.json','melee_regression_v210.lua']
 result={'version':'v1.218','all_passed':True,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'test_scope':'forced_shift_cadence_original_207_reference_wait_pose_native_animation_and_charge_notice_lifecycle_with_existing_reserve_regression','effect_interval_ratio':.5,'xiang_kong_playback_rate_ratio':.7,'combat_instructions_preserved':True,'full_windows_game_run':False,'full_original_assets':False,'complete_native_frame':False,'historical_suites_rerun':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v218.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--runtime');x=ap.parse_args();main(x.runtime or str(ensure_runtime()))
