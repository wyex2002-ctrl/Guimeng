from test_v225 import *
from patch_v244 import span
from patch_v201 import unpack_config

def main(runtime):
 work=W/'native_work/v244';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v243.res').read_bytes();b=(W/'game_v244.res').read_bytes();_,old=decode(a,range(2,86,2));_,new=decode(b,range(2,86,2));report=json.loads((W/'build_v244.json').read_text());count=report['helper_count']
 expected={12:set([76,278,296,300,4087,4089,22194]+report['generic_callbacks']),14:{378,632,668,684},30:{39,87},52:{3}}
 for mid,d in new.items():
  trees(d);assert d.rebuild()==d.raw
  at,n=(378,count)if mid==14 else(3,1)if mid==52 else(len(d.protos),0)
  assert len(d.protos)==len(old[mid].protos)+n
  changes={p.idx for p in old[mid].protos if p.raw!=d.protos[p.idx+(n if p.idx>=at else 0)].raw};assert changes==expected.get(mid,set()),(mid,changes)
  for p in d.protos:
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,p.idx,pc)
 assert new[22].raw==old[22].raw and new[26].raw==old[26].raw and new[40].raw==old[40].raw
 def export(mid,idx,name,patches=None,params=None):
  d=new[mid];actual=idx+(count if mid==14 and idx>=378 else 1 if mid==52 and idx>=3 else 0)
  (work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),actual,patches,params))
 for mid,idx,name in [(14,458,'proxy'),(14,13,'public_sys'),(14,224,'metadata'),(14,223,'template_info'),(14,340,'hero_api'),(12,4089,'oil_template'),(34,3,'inventory_use'),(34,22,'consume'),(14,377,'stat'),(52,3,'font')]:export(mid,idx,name)
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
 d=old[12];(work/'creature_old.ljbc').write_bytes(standalone(d,trees(d),10298))
 # Compact tooltip and detailed tooltip both call the real helper.
 export(12,296,'compact_tip',{0:ad('KSTR',3,0),1:ad('MOV',4,1),2:jump(2,203,5),231:ad('RET1',3,2)},2)
 mp={int(k):v for k,v in report['maps']['tooltip'].items()};pc=mp[742]
 export(12,300,'detail_tip',{0:ad('KSTR',3,0),1:ad('MOV',4,1),2:jump(2,pc,5),pc+8:ad('RET1',3,2)},2)
 # Existing real skill configuration; no luck values edited in the DB.
 cfg=unpack_config(new[12].protos[6464].gc(3));(work/'skill_config.txt').write_bytes(cfg)
 runs=[]
 for mode in ['normal','hot']:
  src=work/'test.lua';src.write_bytes((W/'luck_regression_v244.lua').read_text().encode('gbk'))
  r=subprocess.run([runtime,str(src),str(work),mode],capture_output=True,timeout=90);out=(r.stdout+r.stderr).decode('gbk','replace');(work/(mode+'.log')).write_text(out)
  assert r.returncode==0,(mode,out[-6000:]);print(out,flush=True);runs.append({'mode':mode,'output':out})
 names=['patch_v244.py','test_v244.py','package_v244.py','player_changes_v244.json','luck_system_v244.lua','luck_system_v244.ljbc','luck_rules_v244.lua','oil_use_v244.ljbc','luck_regression_v244.lua']
 result={'version':'v1.244','all_passed':True,'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'all_42_modules_checked':True,'creature_callbacks':247,'full_windows_game_run':False,'scope':'real sandbox installer insertion, data proxy/copy/metadata/native inventory use/consumption/gear aggregation loop; actual hero lucky span/all creature callbacks/tooltip/font outline; finite surrounding engine and raw actor base stats, field save roundtrip only','tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v244.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');a=p.parse_args();main(a.runtime or str(ensure_runtime()))
