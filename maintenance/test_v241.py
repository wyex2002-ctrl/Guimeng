"""Actual item-to-factory-to-Main coverage, not a shared substituted callback."""
from test_v225 import *
from patch_v241 import water_sites,registered_consumables
from patch_v201 import unpack_config

def main(runtime):
 work=W/'native_work/v241';work.mkdir(parents=True,exist_ok=True)
 base=(W/'game_v240.res').read_bytes();data=(W/'game_v241.res').read_bytes()
 _,old=decode(base,range(2,86,2));_,new=decode(data,range(2,86,2));report=json.loads((W/'build_v241.json').read_text())
 changed=[int(i)for i in report['water_maps']];expected={12:sorted([76,22194]+changed),14:[632,668,684],30:[39,87]}
 assert {int(k):v for k,v in report['changed_prototypes'].items()}==expected
 for mid,d in new.items():
  trees(d);assert len(d.protos)==len(old[mid].protos)and d.rebuild()==d.raw
  for i,p in enumerate(d.protos):
   assert (p.raw!=old[mid].protos[i].raw)==(i in expected.get(mid,[])),(mid,i)
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,i,pc)
 for idx in changed:
  p,q=old[12].protos[idx],new[12].protos[idx];mp={int(k):v for k,v in report['water_maps'][str(idx)].items()}
  assert q.bc[mp[147]]==ad('KSHORT',5,1)
  for pc,x in enumerate(p.bc):
   at=mp[pc]+(1 if pc==147 else 0);y=q.bc[at]
   if OPS[x&255]in BRANCHES:assert x&65535==y&65535 and mp[pc+1+(x>>16)-32768]==at+1+(y>>16)-32768
   else:assert x==y,(idx,pc)
 sites=water_sites(new[12]);bindings=registered_consumables(new[12],sites)
 assert len(sites)==len(bindings)==49 and set(sites.values())=={148}
 assert bindings==report['registered_consumables']
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
  export(12,b['factory'],'factory'+str(b['factory']));export(12,b['factory'],'old_factory'+str(b['factory']),dumps=old)
 fixture=(W/'magic_shield_regression_v239.lua').read_text().split("for _,story in ipairs({'归梦','来世续缘'})do")[0]
 fixture=fixture.replace("work..'/configs.lua'","work..'/water_configs.lua'").replace("local custom={'伤害减免'","local custom={'最大破坏','最大自然','最大灵魂','伤害减免'")
 (work/'test.lua').write_bytes((fixture+(W/'water_regression_v241.lua').read_text()).encode('gbk'))
 runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'test.lua'),str(work),mode],capture_output=True,timeout=90);output=(r.stdout+r.stderr).decode('gbk','replace');(work/(mode+'.log')).write_text(output)
  assert r.returncode==0 and 'WATER_V241_PASS'in output,(mode,output[-5000:]);print(output);runs.append({'mode':mode,'output':output})
 names=['patch_v241.py','test_v241.py','water_regression_v241.lua','package_v241.py','player_changes_v241.json']
 result={'version':'v1.241','all_passed':True,'sha256':hashlib.sha256(data).hexdigest(),'registered_script_count':49,'all_template_factory_bindings_checked':True,'actual_divine_water_factories':24,'all_42_modules_checked':True,'v240_coverage_gap':'its 24 templates were assigned only Main1256/1259; actual 49 distinct template factories are now loaded and own getself/child Main verified','runs':runs,'full_windows_game_run':False,'historical_suites_rerun':False,'scope':'all 49 native factories and own Main callbacks, real 24 water variants, registered factory identity, current proxy/public metadata/inventory use/consume/native Buff; finite graphics/actor foundation/final stats/pre-use UI callbacks and healing request bridge, not Windows effect ticks','tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v241.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');a=p.parse_args();main(a.runtime or str(ensure_runtime()))
