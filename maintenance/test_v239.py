"""Magic-shield recast through native dispatch, public API and actual BUFFs."""
from test_v225 import *
from patch_v239 import MAGIC_DISPATCHERS
from patch_v201 import unpack_config

def main(runtime):
 work=W/'native_work/v239';work.mkdir(parents=True,exist_ok=True)
 base=(W/'game_v238.res').read_bytes();data=(W/'game_v239.res').read_bytes()
 _,old=decode(base,range(2,86,2));_,new=decode(data,range(2,86,2));report=json.loads((W/'build_v239.json').read_text())
 expected={12:[76,142]+MAGIC_DISPATCHERS+[22194],14:[632,668,684],30:[39,87],40:[19]}
 assert {int(k):v for k,v in report['changed_prototypes'].items()}==expected
 for mid,d in new.items():
  trees(d);assert len(d.protos)==len(old[mid].protos)and d.rebuild()==d.raw
  for i,p in enumerate(d.protos):
   assert (p.raw!=old[mid].protos[i].raw)==(i in expected.get(mid,[])),(mid,i)
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,i,pc)
 for idx in MAGIC_DISPATCHERS:
  p,q=old[12].protos[idx],new[12].protos[idx];mp={int(k):v for k,v in report['dispatch_maps'][str(idx)].items()}
  for pc,x in enumerate(p.bc):
   if pc in range(810,838)or pc==883:continue
   y=q.bc[mp[pc]]
   if OPS[x&255]in BRANCHES:
    assert x&65535==y&65535
    assert mp[pc+1+(x>>16)-32768]==mp[pc]+1+(y>>16)-32768
   else:assert x==y,(idx,pc)
 # Only the intended time constants change in rules; previous defensive
 # spell formulas, state definitions and all unrelated rows are identical.
 p,q=old[12].protos[142],new[12].protos[142];assert p.bc==q.bc
 targets={p.bc[pc]>>16 for pc in [2430,2432,2434,2436,2438,2440]}
 for k in range(p.nkgc):
  if k not in targets:assert p.gc(k)==q.gc(k),(142,k)
  else:
   a,b=dict(p.gc(k)[2]),dict(q.gc(k)[2]);assert b.pop('持续时间'.encode('gbk'))==('int',0);a.pop('持续时间'.encode('gbk'));assert a==b
 a,b=old[40].protos[19],new[40].protos[19]
 assert all(a.bc[pc]==b.bc[pc]for pc in range(a.nbc)if pc!=892)
 for mid,idx in [(40,5),(40,6),(40,7),(12,725),(26,55),(26,88)]:assert old[mid].protos[idx].raw==new[mid].protos[idx].raw
 def export(mid,idx,name,patches=None,dumps=new):
  d=dumps[mid];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx,patches))
 for mid,idx,name in [(14,340,'hero_api'),(40,20,'buff_class'),(26,64,'add'),(26,63,'clear'),(26,62,'list'),(26,61,'modify'),(12,126,'role_a'),(12,132,'role_b')]:export(mid,idx,name)
 export(12,142,'rules',{0:ad('TNEW',1,0),1:jump(1,2429,2),2444:jump(2444,2676,2),2706:ad('RET1',1,2)})
 export(26,66,'death_buffs',{0:jump(0,44,2),66:ad('RET0',0,1)})
 export(12,725,'statuses',{0:ad('KNIL',0,25),1:jump(1,13584,26),14201:jump(14201,14818,26),16052:ad('RET0',0,1)})
 cfg={};p=new[12].protos[725]
 for pc in [13584,14818,15435]:
  t=dict(p.gc(p.bc[pc]>>16)[2]);s=t['配置项文本'.encode('gbk')];cfg[s]=unpack_config(s)
 (work/'configs.lua').write_bytes(('return '+lua(cfg)).encode('gbk'))
 for idx in MAGIC_DISPATCHERS+[4498]:export(12,idx,'dispatch'+str(idx))
 export(40,20,'old_buff_class',dumps=old);export(12,4115,'old_dispatch',dumps=old)
 (work/'test.lua').write_bytes((W/'magic_shield_regression_v239.lua').read_text().encode('gbk'))
 runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'test.lua'),str(work),mode],capture_output=True,timeout=90)
  output=(r.stdout+r.stderr).decode('gbk','replace');(work/(mode+'.log')).write_text(output)
  assert r.returncode==0 and'MAGIC_SHIELD_V239_PASS'in output,output[-5000:]
  print(output);runs.append({'mode':mode,'output':output})
 names=['patch_v239.py','test_v239.py','magic_shield_regression_v239.lua','package_v239.py','player_changes_v239.json']
 result={'version':'v1.239','all_passed':True,'sha256':hashlib.sha256(data).hexdigest(),'runs':runs,'all_42_modules_checked':True,'all_34_magic_dispatchers_checked':True,'bonuses_and_unrelated_rules_preserved':True,'full_windows_game_run':False,'historical_suites_rerun':False,'scope':'both real role getters/six native rule tiers/34 complete native dispatchers/public insertion and deletion/real status registration and BUFF constructor, arithmetic, recast disposal, update, icon/hover, death-buff fragment, field export/reload; previous two shields checked; finite actor foundation, skill metadata, INI/resource/graphics/animation binding and final entity stat recomputation, not complete Windows client save/reentry','tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v239.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');a=p.parse_args();main(a.runtime or str(ensure_runtime()))
