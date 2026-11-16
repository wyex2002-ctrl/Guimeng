from test_v225 import *
from patch_v245 import span
from patch_v201 import unpack_config

def main(runtime):
 work=W/'native_work/v245';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v244.res').read_bytes();b=(W/'game_v245.res').read_bytes();_,old=decode(a,range(2,86,2));_,new=decode(b,range(2,86,2));current=json.loads((W/'build_v245.json').read_text());report=json.loads((W/'build_v244.json').read_text());count=current['helper_count']
 expected={12:{37,76,4087,4089,18008,22194},14:{649,685,701,702},30:{39,87}}
 for mid,d in new.items():
  trees(d);assert d.rebuild()==d.raw
  if mid==14:
   before=[p for p in old[mid].protos if not 378<=p.idx<395];after=[p for p in d.protos if not 378<=p.idx<378+count]
  else:before=old[mid].protos;after=d.protos
  assert len(before)==len(after);changes={p.idx for p,q in zip(before,after)if p.raw!=q.raw};assert changes==expected.get(mid,set()),(mid,changes)
  for p in d.protos:
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,p.idx,pc)
 p,q=old[12].protos[37],new[12].protos[37];assert q.bc[1:p.nbc]==p.bc[1:] and(p.params,p.frame,p.uv)==(q.params,q.frame,q.uv)
 for i in range(p.nkgc):assert p.gc(i)==q.gc(i)
 for mid in [22,26,34,36,40,52]:assert new[mid].raw==old[mid].raw
 def export(mid,idx,name,patches=None,params=None):
  d=new[mid];actual=idx+(count if mid==14 and idx>=378 else 1 if mid==52 and idx>=3 else 0)
  (work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),actual,patches,params))
 for mid,idx,name in [(14,458,'proxy'),(14,13,'public_sys'),(14,224,'metadata'),(14,223,'template_info'),(14,340,'hero_api'),(12,4089,'oil_template'),(34,3,'inventory_use'),(34,22,'consume'),(14,377,'stat'),(52,3,'font')]:export(mid,idx,name)
 export(14,408,'quantity');export(14,220,'actor_api');export(14,397,'use_by_name');export(14,340,'hero_api')
 export(12,37,'item_event');export(34,1,'inventory_init');export(34,31,'inventory_class');export(48,25,'add_control');export(48,23,'bind_control');export(14,416,'public_get')
 export(14,685,'oil_reset')
 export(22,37,'merc_gear_sum',{0:ad('MOV',4,1),1:ad('MOV',5,2),2:jump(2,385,6),551:ad('RET1',4,2)},3)
 # Original mercenary merged attack span, preserving real own skill config.
 mp={int(k):v for k,v in current['merc_map'].items()}
 export(12,18008,'merc_luck',{0:ad('MOV',8,0),1:ad('MOV',9,1),2:ad('MOV',6,2),3:ad('KSHORT',11,2),4:ad('KSHORT',12,4),5:jump(5,mp[417],21),mp[437]:ad('MOV',0,15),mp[437]+1:ad('MOV',1,13),mp[437]+2:ad('RET',0,3)},3)
 export(30,193,'table_register',{0:jump(0,33),42:jump(42,57),69:ad('RET0',0,1)})
 # Original gear aggregation loop, with a supplied initialized stat accumulator.
 export(26,38,'gear_sum',{0:ad('MOV',3,1),1:jump(1,371,4),537:ad('RET1',3,2)})
 # Exact installer insertion, retaining native S.script_setting assignment.
 mp={int(k):v for k,v in report['install_map'].items()};entry=mp[562]
 export(14,378,'install',{0:ad('UGET',11,0),1:ad('MOV',12,0),2:jump(2,entry,13),mp[563]:ad('RET0',0,1)},1)
 # Hero complete merged luck span with actual configured bounds/skill locals.
 mp={int(k):v for k,v in report['maps']['hero_attack'].items()}
 export(12,278,'hero_luck',{0:ad('MOV',8,0),1:ad('MOV',9,1),2:ad('MOV',6,2),3:ad('MOV',4,3),4:ad('KSHORT',11,2),5:ad('KSHORT',12,4),6:jump(6,mp[300],22),mp[347]:ad('MOV',0,15),mp[347]+1:ad('MOV',1,13),mp[347]+2:ad('RET',0,3)},4)
 (work/'callbacks.lua').write_text('return {'+','.join(map(str,report['generic_callbacks']))+'}')
 for idx in report['generic_callbacks']:export(12,idx,'creature'+str(idx))
 _,original=decode((W/'game_v243.res').read_bytes(),[12]);d=original[12];(work/'creature_old.ljbc').write_bytes(standalone(d,trees(d),10298))
 # Compact tooltip and detailed tooltip both call the real helper.
 export(12,296,'compact_tip',{0:ad('KSTR',3,0),1:ad('MOV',4,1),2:jump(2,203,5),231:ad('RET1',3,2)},2)
 mp={int(k):v for k,v in report['maps']['tooltip'].items()};pc=mp[742]
 export(12,300,'detail_tip',{0:ad('KSTR',3,0),1:ad('MOV',4,1),2:jump(2,pc,5),pc+8:ad('RET1',3,2)},2)
 # Existing real skill configuration; no luck values edited in the DB.
 cfg=unpack_config(new[12].protos[6464].gc(3));(work/'skill_config.txt').write_bytes(cfg)
 runs=[]
 for mode in ['normal','hot']:
  src=work/'test.lua';src.write_bytes((W/'luck_regression_v245.lua').read_text().encode('gbk'))
  r=subprocess.run([runtime,str(src),str(work),mode],capture_output=True,timeout=90);out=(r.stdout+r.stderr).decode('gbk','replace');(work/(mode+'.log')).write_text(out)
  assert r.returncode==0,(mode,out[-6000:]);print(out,flush=True);runs.append({'mode':mode,'output':out})
 names=['patch_v245.py','test_v245.py','package_v245.py','player_changes_v245.json','luck_system_v245.lua','luck_system_v245.ljbc','luck_rules_v245.lua','oil_use_v245.ljbc','oil_reset_v245.lua','oil_reset_v245.ljbc','luck_regression_v245.lua']
 result={'version':'v1.245','all_passed':True,'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'all_42_modules_checked':True,'creature_callbacks':247,'full_windows_game_run':False,'scope':'actual source-aware oil Main/native inventory consume, native hero/merc gear loops and public actor attributes; own-luck ownership, complete creature callbacks, actual merc attack span; native quickslot event->use by name->inventory chain with finite graphics/pre-use engine bridge; field roundtrip only','tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v245.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');a=p.parse_args();main(a.runtime or str(ensure_runtime()))
