"""Real defensive dispatchers, public API, status registration and BUFF lifecycle."""
from test_v225 import *
from patch_v238 import DISPATCHERS,SPELLS
from patch_v201 import unpack_config
from ljtool import Proto
from patch_v139 import abc

def main(runtime):
 work=W/'native_work/v238';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v237.res').read_bytes();b=(W/'game_v238.res').read_bytes()
 _,old=decode(a,range(2,86,2));_,new=decode(b,range(2,86,2));report=json.loads((W/'build_v238.json').read_text())
 expected={12:[76,22194],14:[632,668,684],30:[39,87],40:[19]}
 assert {int(k):v for k,v in report['changed_prototypes'].items()}==expected
 for mid,d in new.items():
  trees(d);assert len(d.protos)==len(old[mid].protos) and d.rebuild()==d.raw
  for i,p in enumerate(d.protos):
   assert (p.raw!=old[mid].protos[i].raw)==(i in expected.get(mid,[])),(mid,i)
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,i,pc)
 # Both actor implementations and every dispatcher are byte-identical. Recast
 # semantics already exist; do not replace a working shared insertion method.
 for mid,indices in [(22,[91,92,93,94]),(26,[61,62,63,64]),(12,DISPATCHERS+[142,725])]:
  for i in indices:assert old[mid].protos[i].raw==new[mid].protos[i].raw
 # Only two constructor CATs gain a terminal literal. Preserve all other
 # instructions including branch A live slots and relocated targets.
 p,q=old[40].protos[19],new[40].protos[19]
 mp={int(k):v for k,v in report['constructor_map'].items()}
 for pc,x in enumerate(p.bc):
  if pc in [915,941]:
   assert OPS[q.bc[mp[pc]]&255]=='KSTR' and ((q.bc[mp[pc]]>>8)&255)==16
   assert q.gc(q.bc[mp[pc]]>>16)=='\n攻击元素总和越高，加成越高'.encode('gbk')
   assert q.bc[mp[pc]+1]==abc('CAT',10,10,16);continue
  y=q.bc[mp[pc]]
  if OPS[x&255]in BRANCHES:
   assert x&65535==y&65535
   assert mp[pc+1+(x>>16)-32768]==mp[pc]+1+(y>>16)-32768
  else:assert x==y,(pc,x,y)
 def export(mid,idx,name,patches=None):
  d=new[mid];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx,patches))
 export(14,340,'hero_api');export(14,220,'entity')
 for i,n in [(94,'event_add'),(93,'event_clear'),(91,'event_list'),(92,'event_modify')]:export(22,i,n)
 for mid,idx,name in [(40,20,'buff_class'),(26,64,'add'),(26,63,'clear'),(26,62,'list'),(26,61,'modify'),(12,126,'role_a'),(12,132,'role_b')]:export(mid,idx,name)
 export(12,142,'rules',{0:ad('TNEW',1,0),1:jump(1,2676,2),2706:ad('RET1',1,2)})
 export(26,66,'death_buffs',{0:jump(0,44,2),66:ad('RET0',0,1)})
 # Original parsing and script registration for BOTH complete status blocks.
 export(12,725,'statuses',{0:ad('KNIL',0,25),1:jump(1,14818,26),16052:ad('RET0',0,1)})
 cfg={}
 for pc in [14818,15435]:
  p=new[12].protos[725];t=dict(p.gc(p.bc[pc]>>16)[2]);s=t['配置项文本'.encode('gbk')];cfg[s]=unpack_config(s)
 (work/'configs.lua').write_bytes(('return '+lua(cfg)).encode('gbk'))
 for idx in DISPATCHERS:export(12,idx,'dispatch'+str(idx))
 # The unmodified native icon/timer implementation is exercised in full.
 # Original self-contained status update/destruction and serialization run.
 d=old[40];(work/'old_buff_class.ljbc').write_bytes(standalone(d,trees(d),20))
 d=old[12];(work/'old_dispatch.ljbc').write_bytes(standalone(d,trees(d),4498))
 (work/'test.lua').write_bytes((W/'shield_regression_v238.lua').read_text().encode('gbk'))
 runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'test.lua'),str(work),mode],capture_output=True,timeout=90)
  output=(r.stdout+r.stderr).decode('gbk','replace');(work/(mode+'.log')).write_text(output)
  assert r.returncode==0 and 'SHIELDS_V238_PASS'in output,output[-5500:]
  print(output);runs.append({'mode':mode,'output':output})
 names=['patch_v238.py','test_v238.py','shield_regression_v238.lua','package_v238.py','player_changes_v238.json']
 result={'version':'v1.238','all_passed':True,'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'all_42_modules_checked':True,'all_19_dispatchers_checked':True,'latest_stronger_weaker_equal_recast_checked':True,'separate_friendly_actor_native_API_checked':True,'replacement_implementation_changed':False,'full_windows_game_run':False,'scope':'actual public hero and independent friendly entity APIs / both role getters / six rule tiers / native status parsing and factories / cast dispatch / BUFF constructor, attributes, replacement, update, removal, death-buff fragment, export/reload, icon and hover; finite raw actor foundation, skill metadata lookup, INI/resource/graphics and final entity attribute recomputation; controlled field roundtrip, not full client save/reentry','historical_suites_rerun':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v238.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');a=p.parse_args();main(a.runtime or str(ensure_runtime()))
