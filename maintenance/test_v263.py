from test_v225 import *
from patch_v263 import BASE_SHA

def main(runtime):
 work=W/'native_work/v263';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v262.res').read_bytes();b=(W/'game_v263.res').read_bytes();assert hashlib.sha256(a).hexdigest()==BASE_SHA
 _,old=decode(a,range(2,86,2));_,new=decode(b,range(2,86,2));build=json.loads((W/'build_v263.json').read_text());cnt=build['luck_helper_count']
 expected={12:{76,22196},14:{652,688,704},30:{39,87},34:{22}}
 # Normalize the one helper insertion; all unrelated gameplay remains exact.
 for mid,d in new.items():
  trees(d);assert d.rebuild()==d.raw
  pre=[p for p in old[mid].protos if mid!=14 or not 378<=p.idx<399];post=[p for p in d.protos if mid!=14 or not 378<=p.idx<378+cnt]
  assert len(pre)==len(post)
  changes={i for i,(p,q)in enumerate(zip(pre,post))if p.raw!=q.raw};assert changes==expected.get(mid,set()),(mid,changes)
  for p in d.protos:
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,p.idx,pc)
 p,q=old[34].protos[22],new[34].protos[22];mp={int(k):v for k,v in build['consume_map'].items()}
 for pc,x in enumerate(p.bc):
  if pc==41:continue
  at=mp[pc];y=q.bc[at]
  if OPS[x&255]in BRANCHES:assert x&65535==y&65535 and at+1+(y>>16)-32768==mp[pc+1+(x>>16)-32768]
  else:assert x==y
 def export(mid,idx,name,patches=None,params=None):
  d=new[mid];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx,patches,params))
 for mid,idx,name in [(12,37,'item_event'),(34,1,'inventory_init'),(34,31,'inventory_class'),(48,25,'add_control'),(48,23,'bind_control'),(14,439,'use_by_name'),(14,450,'quantity'),(12,100,'chat_message'),(12,306,'screen_message'),(14,500,'proxy'),(14,13,'public_sys'),(14,224,'metadata'),(14,223,'template_info'),(14,340,'hero_api'),(12,4091,'oil_template'),(34,3,'inventory_use'),(34,22,'consume'),(34,11,'swap'),(34,16,'take'),(34,18,'place'),(14,479,'reset_item')]:export(mid,idx,name)
 export(30,193,'table_register',{0:jump(0,33),42:jump(42,48),69:ad('RET0',0,1)})
 # Execute the real native installer around the lucky helper registration.
 report=json.loads((W/'build_v244.json').read_text());mp={int(k):v for k,v in report['install_map'].items()}
 export(14,420,'install',{0:ad('UGET',11,0),1:ad('MOV',12,0),2:jump(2,mp[562],13),571:ad('RET0',0,1)},1)
 # Native save's complete inventory-field capture block; unchanged serialization
 # and readback functions are executed separately, encryption/file IO excluded.
 export(14,253,'save_item',{0:ad('MOV',9,0),1:ad('TNEW',3,0),2:ad('KSHORT',12,1),3:jump(3,82,23),132:ad('RET1',24,2)},1)
 # Full original table.tostring/loadstring registration above is authoritative.
 src=work/'test.lua';src.write_bytes((W/'oil_batch_regression_v263.lua').read_text().encode('gbk'));runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(src),str(work),mode],capture_output=True,timeout=90);out=(r.stdout+r.stderr).decode('gbk','replace');print(out,flush=True);(work/(mode+'.log')).write_text(out);assert r.returncode==0,(mode,out[-5000:]);runs.append({'mode':mode,'output':out})
 names=['patch_v263.py','test_v263.py','package_v263.py','player_changes_v263.json','luck_system_v263.lua','luck_system_v263.ljbc','luck_rules_v249.lua','oil_batch_regression_v263.lua']
 result={'version':'v1.263','all_passed':True,'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'all_42_modules_checked':True,'historical_suites_rerun':False,'full_windows_game_run':False,'full_client_save_load':False,'scope':'native installer/data proxy/table copy/tostring/loadstring, actual oil Main/inventory use/consume, native save item capture and reset/transfer; finite Sys and UI/engine bridges; mount batches and repeated controlled save/reload, not Windows full-client IO','tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v263.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');a=p.parse_args();main(a.runtime or str(ensure_runtime()))
