"""Real defensive dispatchers, public API, status registration and BUFF lifecycle."""
from test_v225 import *
from patch_v237 import DISPATCHERS,SPELLS
from patch_v201 import unpack_config
from ljtool import Proto
from patch_v139 import abc

def main(runtime):
 work=W/'native_work/v237';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v236.res').read_bytes();b=(W/'game_v237.res').read_bytes()
 _,old=decode(a,range(2,86,2));_,new=decode(b,range(2,86,2));report=json.loads((W/'build_v237.json').read_text())
 expected={12:[76,142,725]+DISPATCHERS+[22194],14:[632,668,684],30:[39,87],40:[19]}
 assert {int(k):v for k,v in report['changed_prototypes'].items()}==expected
 for mid,d in new.items():
  trees(d);assert len(d.protos)==len(old[mid].protos) and d.rebuild()==d.raw
  for i,p in enumerate(d.protos):
   assert (p.raw!=old[mid].protos[i].raw)==(i in expected.get(mid,[])),(mid,i)
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,i,pc)
 # Every original dispatcher instruction outside the two formula spans is
 # preserved, including branch A live-slot boundaries and relocated targets.
 for idx in DISPATCHERS:
  p,q=old[12].protos[idx],new[12].protos[idx];mp={int(k):v for k,v in report['dispatch_maps'][str(idx)].items()}
  for pc,x in enumerate(p.bc):
   if pc in range(950,968)or pc in range(973,991):continue
   y=q.bc[mp[pc]]
   if OPS[x&255]in BRANCHES:
    assert x&65535==y&65535
    assert mp[pc+1+(x>>16)-32768]==mp[pc]+1+(y>>16)-32768
   else:assert x==y,(idx,pc)
 def export(mid,idx,name,patches=None):
  d=new[mid];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx,patches))
 export(14,340,'hero_api')
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
 (work/'test.lua').write_bytes((W/'shield_regression_v237.lua').read_text().encode('gbk'))
 runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'test.lua'),str(work),mode],capture_output=True,timeout=90)
  output=(r.stdout+r.stderr).decode('gbk','replace');(work/(mode+'.log')).write_text(output)
  assert r.returncode==0 and 'SHIELDS_V237_PASS'in output,output[-5500:]
  print(output);runs.append({'mode':mode,'output':output})
 names=['patch_v237.py','test_v237.py','shield_regression_v237.lua','package_v237.py','player_changes_v237.json']
 result={'version':'v1.237','all_passed':True,'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'all_42_modules_checked':True,'all_19_dispatchers_checked':True,'full_windows_game_run':False,'scope':'actual public actor API / both role getters / six rule tiers / native status parsing and factories / cast dispatch / BUFF constructor, attributes, replacement, update, removal, death-buff fragment, export/reload, icon and hover; finite raw actor foundation, skill metadata lookup, INI/resource/graphics and final entity attribute recomputation; controlled field roundtrip, not full client save/reentry','historical_suites_rerun':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v237.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');a=p.parse_args();main(a.runtime or str(ensure_runtime()))
