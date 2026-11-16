"""Current native water/UI/death plus pickup scheduling and safety boundaries."""
from test_v225 import *
from patch_v241 import water_sites,registered_consumables
from patch_v201 import unpack_config

def main(runtime):
 work=W/'native_work/v242';work.mkdir(parents=True,exist_ok=True)
 base=(W/'game_v241.res').read_bytes();data=(W/'game_v242.res').read_bytes()
 _,old=decode(base,range(2,86,2));_,new=decode(data,range(2,86,2));report=json.loads((W/'build_v242.json').read_text())
 expected={int(k):v for k,v in report['changed_original_prototypes'].items()};assert expected=={12:[76,4089,22194],14:[385,632,668,684,685,688],22:[3,64,112],26:[0],30:[39,87],40:[19]}
 for mid,d in new.items():
  trees(d);assert d.rebuild()==d.raw
  at,n=report['insertions'].get(str(mid),(len(d.protos),0));assert len(d.protos)==len(old[mid].protos)+n
  for i,p in enumerate(old[mid].protos):assert (p.raw!=d.protos[i+(n if i>=at else 0)].raw)==(i in expected.get(mid,[])),(mid,i)
  for p in d.protos:
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,p.idx,pc)
 def export(mid,idx,name,patches=None,dumps=new):
  d=dumps[mid];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx,patches))
 _,older=decode((W/'game_v240.res').read_bytes(),[12])
 sites=water_sites(new[12]);bindings=registered_consumables(new[12],sites)
 assert len(sites)==len(bindings)==49 and set(sites.values())=={148}
 assert len(bindings)==49
 assert all(new[12].protos[i].bc[147]==ad('KSHORT',5,1)for i in sites)
 def export(mid,idx,name,patches=None,dumps=new):
  d=dumps[mid];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx,patches))
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
  item=dict(t[2]);name=item.get('名称'.encode('gbk'),b'').decode('gbk')
  if name not in bindings:continue
  assert bindings[name]['template_pc']==pc
  props={}
  for s in flags.decode('gbk').split('ぃ'):
   if s:
    k,v=s.split('ぅ');props[k.encode('gbk')]=int(v)if v.isdigit()else v.encode('gbk')
  item['附加'.encode('gbk')]=props;item['属性'.encode('gbk')]={};item['资源'.encode('gbk')]={};item['风格提示'.encode('gbk')]={'宽度'.encode('gbk'):0,'高度'.encode('gbk'):0};templates[name.encode('gbk')]=item
 assert len(templates)==49 and sum('神水位置'.encode('gbk')in t['附加'.encode('gbk')]for t in templates.values())==24
 (work/'waters.lua').write_bytes(('return '+lua(templates)).encode('gbk'))
 (work/'bindings.lua').write_bytes(('return '+lua({k.encode('gbk'):{a.encode():v for a,v in b.items()}for k,b in bindings.items()})).encode('gbk'))
 for b in bindings.values():
  export(12,b['factory'],'factory'+str(b['factory']));export(12,b['factory'],'old_factory'+str(b['factory']),dumps=older)
 fixture=(W/'magic_shield_regression_v239.lua').read_text().split("for _,story in ipairs({'归梦','来世续缘'})do")[0]
 fixture=fixture.replace("work..'/configs.lua'","work..'/water_configs.lua'").replace("local custom={'伤害减免'","local custom={'最大破坏','最大自然','最大灵魂','伤害减免'")
 (work/'test.lua').write_bytes((fixture+(W/'water_regression_v242.lua').read_text()).encode('gbk'))
 runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'test.lua'),str(work),mode],capture_output=True,timeout=90);output=(r.stdout+r.stderr).decode('gbk','replace');(work/(mode+'.log')).write_text(output)
  assert r.returncode==0 and 'WATER_V242_PASS'in output,(mode,output[-5000:]);print(output);runs.append({'mode':mode,'output':output})

 for mid,idx,name in [(14,413,'window_lookup'),(48,26,'add_control'),(48,23,'bind_control'),(62,12,'button_register'),(16,73,'sprite_native'),(22,64,'death_new'),(22,3,'spawn'),(12,191,'currency_new'),(14,339,'fx_getter'),(14,416,'public_get'),(14,458,'data_protection'),(12,4089,'oil_template'),(14,685,'oil_reset'),(22,report['oil_index'],'oil_helper'),(14,report['timer_index'],'timer')]:export(mid,idx,name)
 export(22,64,'death_old',dumps=old)
 export(30,193,'table_register',{0:jump(0,33),42:jump(42,57),69:ad('RET0',0,1)})
 p=new[12].protos[report['ui_root']];start=p.nbc-5
 export(12,report['ui_root'],'ui_root',{0:jump(0,30000,0),30000:jump(30000,start,0)})
 # Execute original Alt gate including new scheduler fragment, real root-installed helper.
 p=new[14].protos[385];mp={int(k):v for k,v in report['maps']['frame'].items()}
 export(14,385,'frame_gate',{0:jump(0,mp[2956],1),mp[2975]:ad('RET1',1,2)})
 p=new[26].protos[0];end=6;export(26,0,'hero_defaults',{end:ad('RET0',0,1)})
 for n in ['range_pickup_v242','pickup_tick_v242']:(work/(n+'.lua')).write_bytes((W/(n+'.lua')).read_text().encode('gbk'))
 for label,dumps in [('old',old),('new',new)]:export(14,385,'frame_'+label,dumps=dumps)
 for suite in ['ui','pickup','oil','frame']:
  (work/(suite+'.lua')).write_bytes((W/(suite+'_regression_v242.lua')).read_text().encode('gbk'))
  for mode in ['normal','hot']:
   r=subprocess.run([runtime,str(work/(suite+'.lua')),str(work),mode],capture_output=True,timeout=90);output=(r.stdout+r.stderr).decode('gbk','replace');(work/(suite+'.'+mode+'.log')).write_text(output)
   assert r.returncode==0,(suite,mode,output[-5000:]);print(output);runs.append({'suite':suite,'mode':mode,'output':output})
 names=['patch_v242.py','test_v242.py','water_regression_v242.lua','ui_regression_v242.lua','pickup_regression_v242.lua','oil_regression_v242.lua','frame_regression_v242.lua','package_v242.py','player_changes_v242.json']+[n+s for n in ['oil_drop_v242','oil_reset_v242','pickup_options_v242','pickup_tick_v242']for s in ['.lua','.ljbc']]+['range_pickup_v242.lua']
 result={'version':'v1.242','all_passed':True,'sha256':hashlib.sha256(data).hexdigest(),'runs':runs,'all_42_modules_checked':True,'full_windows_game_run':False,'scope':'49 actual consumable factories/native inventory/Buff; native UI controls with finite graphics/font; native death/public getter/data proxy; pickup source and native gate with finite ground items/engine; no full Windows test','tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v242.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');a=p.parse_args();main(a.runtime or str(ensure_runtime()))
