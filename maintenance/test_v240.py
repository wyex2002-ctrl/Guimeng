"""Current UI, actual lotus effect chain, and divine-water inventory regressions."""
from test_v225 import *
from patch_v139 import abc
from patch_v201 import unpack_config
from portal_routes_v213 import child_refs
from test_v210 import SKILLS

def main(runtime):
 work=W/'native_work/v240';work.mkdir(parents=True,exist_ok=True)
 base=(W/'game_v239.res').read_bytes();data=(W/'game_v240.res').read_bytes()
 _,old=decode(base,range(2,86,2));_,new=decode(data,range(2,86,2));build=json.loads((W/'build_v240.json').read_text())
 expected={12:[76,1256,1259,22193,22194],14:[632,668,684],26:[87],30:[39,87]}
 assert {int(k):v for k,v in build['changed_prototypes'].items()}==expected
 for mid,d in new.items():
  trees(d);assert len(d.protos)==len(old[mid].protos)and d.rebuild()==d.raw
  for i,p in enumerate(d.protos):
   assert (p.raw!=old[mid].protos[i].raw)==(i in expected.get(mid,[])),(mid,i)
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,i,pc)
 for idx in [1256,1259]:
  p,q=old[12].protos[idx],new[12].protos[idx];mp={int(k):v for k,v in build['water_maps'][str(idx)].items()}
  assert q.bc[mp[147]]==ad('KSHORT',5,1)
  for pc,x in enumerate(p.bc):
   at=mp[pc]+(1 if pc==147 else 0);y=q.bc[at]
   if OPS[x&255]in BRANCHES:
    assert x&65535==y&65535 and mp[pc+1+(x>>16)-32768]==at+1+(y>>16)-32768
   else:assert x==y,(idx,pc)
 def export(mid,idx,name,patches=None,dumps=new):
  d=dumps[mid];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx,patches))
 # Real UI root -> warehouse helper -> native image button and sprite wrappers.
 for mid,idx,name in [(14,413,'window_lookup'),(48,26,'add_control'),(48,23,'bind_control'),(62,12,'button_register'),(16,73,'sprite_native')]:export(mid,idx,name)
 d=new[12];pc=d.protos[22194].nbc-3
 export(12,22194,'ui_root',{0:jump(0,30000,0),30000:jump(30000,pc,0)})
 ui=(W/'inventory_regression_v224.lua').read_text();ui=ui[:ui.index('local function sale')]+ui[ui.index('local skin_color'):]
 ui=ui.replace('eq(c.w,55)','eq(c.w,44)').replace('eq(c.x,169)','eq(c.x,180)').replace('INVENTORY_V219_PASS','WAREHOUSE_V240_PASS')
 (work/'ui.lua').write_bytes(ui.encode('gbk'))
 # Actual current hero/skill instance/effect factory and native effect update.
 for label,dumps in [('old',old),('new',new)]:
  export(26,89,'class_'+label,dumps=dumps);export(26,3,'tick_'+label,{0:jump(0,843,3),852:ad('RET0',0,1)},dumps)
 for mid,idx,name in [(20,8,'animation'),(20,6,'reverse'),(20,21,'reset'),(12,4091,'skill_factory'),(30,43,'rotate'),(14,386,'effect_factory'),(42,13,'effect_class')]:export(mid,idx,name)
 d=new[12];cfg={name.encode('gbk'):unpack_config(d.protos[6464].gc(i))for i,name in SKILLS.items()};(work/'configs.lua').write_bytes(('return '+lua(cfg)).encode('gbk'))
 refs=child_refs(d);callbacks={};p=d.protos[6464]
 for n,name in enumerate(SKILLS.values()):
  text=('【数据库/技能脚本/'+name+'】').encode('gbk');pc=next(i for i,x in enumerate(p.bc)if OPS[x&255]=='KSTR'and p.gc(x>>16)==text)
  idx=refs[6464,p.bc[pc-2]>>16];key='callback_'+str(n);callbacks[name.encode('gbk')]=key.encode();export(12,idx,key)
 (work/'scripts.lua').write_bytes(('return '+lua(callbacks)).encode('gbk'))
 prefix=(W/'melee_regression_v210.lua').read_text().split("local melee={'普通攻击'")[0].replace("skills[name]['起手动画']={};skills[name]['目标动画']={};","if not opts.effects then skills[name]['起手动画']={};skills[name]['目标动画']={} end;")
 visual=(W/'effect_regression_v211.lua').read_text().split('\nfor _,name in ipairs(names)do')[0]
 (work/'effects.lua').write_bytes((prefix+visual+'\n'+(W/'lotus_regression_v240.lua').read_text()).encode('gbk'))
 # Water is run through original inventory use/consume, metadata and proxy,
 # with actual native BUFF application. Unrelated pre-use UI events are finite.
 for mid,idx,name in [(14,340,'hero_api'),(14,458,'proxy'),(14,224,'slot_info'),(14,13,'public_sys'),(34,3,'inventory_use'),(34,22,'consume'),(40,20,'buff_class'),(26,64,'add'),(26,63,'clear'),(26,62,'list'),(26,61,'modify'),(12,126,'role_a'),(12,132,'role_b')]:export(mid,idx,name)
 export(12,142,'rules',{0:ad('TNEW',1,0),1:jump(1,2429,2),2444:jump(2444,2676,2),2706:ad('RET1',1,2)})
 starts=[9882,10499,11116,11733,12350,12967,14818,15435];repl={0:ad('KNIL',0,25),1:jump(1,starts[0],26)}
 for at,nxt in zip(starts,starts[1:]):
  if at+617!=nxt:repl[at+617]=jump(at+617,nxt,26)
 repl[16052]=ad('RET0',0,1);export(12,725,'statuses',repl)
 p=new[12].protos[725];cfg={}
 for at in starts:
  t=dict(p.gc(p.bc[at]>>16)[2]);s=t['配置项文本'.encode('gbk')];cfg[s]=unpack_config(s)
 (work/'water_configs.lua').write_bytes(('return '+lua(cfg)).encode('gbk'))
 p=new[12].protos[4090];templates={};flags=None
 for pc,x in enumerate(p.bc):
  op=OPS[x&255]
  if op=='KSTR'and(x>>8&255)==4:flags=p.gc(x>>16)
  if op!='TDUP':continue
  t=p.gc(x>>16)
  if not isinstance(t,tuple)or t[0]!='table':continue
  item=dict(t[2]);name=item.get('名称'.encode('gbk'),b'')
  if '神水'.encode('gbk')not in name:continue
  props={}
  for s in flags.decode('gbk').split('ぃ'):
   if s:
    k,v=s.split('ぅ');props[k.encode('gbk')]=int(v)if v.isdigit()else v.encode('gbk')
  assert '神水位置'.encode('gbk')in props
  item['附加'.encode('gbk')]=props;item['属性'.encode('gbk')]={};item['资源'.encode('gbk')]={};item['风格提示'.encode('gbk')]={'宽度'.encode('gbk'):0,'高度'.encode('gbk'):0};templates[name]=item
 assert len(templates)==24;(work/'waters.lua').write_bytes(('return '+lua(templates)).encode('gbk'))
 for idx in [1256,1259]:export(12,idx,'water'+str(idx));export(12,idx,'water_old'+str(idx),dumps=old)
 fixture=(W/'magic_shield_regression_v239.lua').read_text().split("for _,story in ipairs({'归梦','来世续缘'})do")[0]
 fixture=fixture.replace("work..'/configs.lua'","work..'/water_configs.lua'").replace("local custom={'伤害减免'","local custom={'最大破坏','最大自然','最大灵魂','伤害减免'")
 (work/'waters_test.lua').write_bytes((fixture+(W/'water_regression_v240.lua').read_text()).encode('gbk'))
 runs=[]
 for suite in ['ui','effects','waters_test']:
  for mode in ['normal','hot']:
   r=subprocess.run([runtime,str(work/(suite+'.lua')),str(work),mode],capture_output=True,timeout=90);output=(r.stdout+r.stderr).decode('gbk','replace');(work/(suite+'.'+mode+'.log')).write_text(output)
   assert r.returncode==0,(suite,mode,output[-5000:]);print(output);runs.append({'suite':suite,'mode':mode,'output':output})
 names=['patch_v240.py','test_v240.py','lotus_regression_v240.lua','water_regression_v240.lua','warehouse_button_v240.lua','warehouse_button_v240.ljbc','melee_timing_v240.lua','melee_timing_v240.ljbc','package_v240.py','player_changes_v240.json']
 result={'version':'v1.240','all_passed':True,'sha256':hashlib.sha256(data).hexdigest(),'runs':runs,'all_42_modules_checked':True,'full_windows_game_run':False,'historical_suites_rerun':False,'scope':'current native warehouse UI/button/sprite; real hero cast/skill/effect and finite art; both water scripts/all 24 original templates, native data proxy, public metadata, inventory use and consumption, native Buff attribute application; finite UI pre-use callbacks/graphics and actor foundation/final stat recomputation, no full Windows test','tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v240.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');a=p.parse_args();main(a.runtime or str(ensure_runtime()))
