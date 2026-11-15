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
 (W/'validation_v211.json').unlink(missing_ok=True);work=W/'native_work/v211';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v210.res').read_bytes();b=(W/'game_v211.res').read_bytes();ao,old=decode(a,range(2,86,2));bo,new=decode(b,range(2,86,2));build=json.loads((W/'build_v211.json').read_text())
 current=(W/'melee_timing_v211.lua').read_text();prior=(W/'melee_timing_v210.lua').read_text()
 assert current[:current.index("    if mode == 'effect'")]+current[current.index("    if mode == 'input'"):]==prior,'existing melee/input helper changed'
 expected={12:[76,22187],14:[632,668,684],26:[29,53,87],30:[39,87]}
 assert {int(k):v for k,v in build['changed_prototypes'].items()}=={m:expected.get(m,[])for m in [12,14,26,30]}
 assert ao.protos[0].bc==bo.protos[0].bc and a[-10:]==b[-10:]
 for mid,d in new.items():
  assert d.rebuild()==d.raw and len(d.protos)==len(old[mid].protos)
  for i,(p,q) in enumerate(zip(d.protos,old[mid].protos)):
   assert (p.raw!=q.raw)==(i in expected.get(mid,[])),(mid,i)
   assert (p.params,p.uv)==(q.params,q.uv),(mid,i)
   if (mid,i)not in [(26,29),(26,53),(26,87)]:assert p.frame==q.frame and p.bc==q.bc,(mid,i)
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,i,pc)
 for idx,info in build['effect_relocations'].items():
  idx=int(idx);mp={int(k):v for k,v in info['map'].items()};sites={v['call_pc']:v for v in info['sites']};p,q=old[26].protos[idx],new[26].protos[idx]
  for pc,ins in enumerate(p.bc):
   at=mp[pc]+(sites[pc]['inserted']if pc in sites else 0);value=ins
   if OPS[ins&255]in BRANCHES:value=(ins&65535)|((mp[pc+1+(ins>>16)-32768]-at-1+32768)<<16)
   assert q.bc[at]==value,(idx,pc)
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
  mp={int(k):v for k,v in build['relocations']['3'].items()}
  (work/f'tick_{label}.ljbc').write_bytes(standalone(d,trees(d),3,{0:jump(0,mp[839],3),mp[843]+5:ad('RET0',0,1)}))
 for mid,i,n in [(20,8,'animation'),(20,6,'reverse'),(20,21,'reset'),(12,4091,'skill_factory'),(30,43,'rotate'),(14,386,'effect_factory'),(42,13,'effect_class')]:
  d=new[mid];(work/f'{n}.ljbc').write_bytes(standalone(d,trees(d),i))
 prefix=(W/'melee_regression_v210.lua').read_text().split("local melee={'普通攻击'")[0]
 prefix=prefix.replace("skills[name]['起手动画']={};skills[name]['目标动画']={};", "if not opts.effects then skills[name]['起手动画']={};skills[name]['目标动画']={} end;")
 (work/'effects.lua').write_bytes((prefix+(W/'effect_regression_v211.lua').read_text()).encode('gbk'));runs=[]
 for mode in ['normal','hot']:
  res=subprocess.run([runtime,str(work/'effects.lua'),str(work),mode],capture_output=True,timeout=90)
  output=(res.stdout+res.stderr).decode('gbk','replace');(work/(mode+'.log')).write_bytes(res.stdout+res.stderr)
  assert res.returncode==0 and 'EFFECT_V211_PASS'in output,output[-4000:]
  print(output,flush=True);runs.append({'mode':mode,'output':output})
 names=['patch_v211.py','test_v211.py','effect_regression_v211.lua','melee_timing_v211.lua','melee_timing_v211.ljbc','package_v211.py','player_changes_v211.json','melee_regression_v210.lua']
 result={'version':'v1.211','all_passed':True,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'test_scope':'real_hero_skill_effect_dispatch_native_effect_factory_class_and_animation_with_finite_assets','effect_interval_ratio':.5,'combat_instructions_preserved':True,'full_windows_game_run':False,'full_original_assets':False,'complete_native_frame':False,'historical_suites_rerun':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v211.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--runtime');x=ap.parse_args();main(x.runtime or str(ensure_runtime()))
