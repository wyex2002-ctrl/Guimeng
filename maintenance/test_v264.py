from test_v225 import *
from patch_v264 import BASE_SHA

def main(runtime,resume=False):
 work=W/'native_work/v264';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v263.res').read_bytes();b=(W/'game_v264.res').read_bytes();assert hashlib.sha256(a).hexdigest()==BASE_SHA
 _,old=decode(a,range(2,86,2));_,new=decode(b,range(2,86,2));build=json.loads((W/'build_v264.json').read_text());cnt=build['luck_helper_count']
 expected={12:{20,37,76,149,180,4091,22196},14:{674,710,726,727,614},30:{39,87}}
 for mid,d in new.items():
  trees(d);assert d.rebuild()==d.raw;assert len(d.protos)==len(old[mid].protos)
  changes={i for i,(p,q)in enumerate(zip(old[mid].protos,d.protos))if p.raw!=q.raw and not(mid==14 and 378<=i<400)}
  assert changes==expected.get(mid,set()),(mid,changes)
  for p in d.protos:
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,p.idx,pc)
 assert new[34].raw==old[34].raw
 assert all(p.raw==q.raw for p,q in zip(old[14].protos[400:420],new[14].protos[400:420]))
 p,q=old[12].protos[20],new[12].protos[20];assert all(x==y for pc,(x,y)in enumerate(zip(p.bc,q.bc))if pc!=120)
 # Preserve every pre-existing event instruction and jump, including the
 # original helper dispatch appended by 245; only the oil merge guard is new.
 p,q=old[12].protos[37],new[12].protos[37];mp={int(k):v for k,v in build['event_map'].items()}
 for pc,x in enumerate(p.bc):
  at=mp[pc]+(4 if pc==707 else 0);y=q.bc[at]
  if OPS[x&255]in BRANCHES:assert x&65535==y&65535 and at+1+(y>>16)-32768==mp[pc+1+(x>>16)-32768],(pc,at)
  else:assert x==y,(pc,at)
 assert old[14].protos[614].bc==new[14].protos[614].bc
 oldlist=old[14].protos[614].gc(0);newlist=new[14].protos[614].gc(0)
 assert newlist==('table',oldlist[1],[(k,v)for k,v in oldlist[2]if k!='祝福油'.encode('gbk')])
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
 # Current actual gift/load and inventory entry points.
 for mid,idx,name in [(14,419,'merc_helper'),(14,727,'oil_reset'),(14,94,'notice'),(14,339,'fx_getter'),(14,458,'public_get'),(14,500,'data_protection'),(14,614,'stack_install'),(14,454,'add_item'),(14,451,'free_slots'),(14,87,'gly_add'),(12,126,'role_q'),(12,132,'role_main'),(12,126,'role_a'),(12,132,'role_b'),(12,129,'config_a'),(12,134,'config_b'),(12,73,'mode_get'),(12,154,'quit153'),(12,190,'quit188'),(14,167,'timer_factory'),(14,427,'native_frame'),(14,725,'profile_only')]:export(mid,idx,name)
 export(14,729,'native_exports',{0:jump(0,280)},1)
 for label,d in [('old',old[12]),('new',new[12])]:
  (work/('timer_'+label+'.ljbc')).write_bytes(standalone(d,trees(d),20,{140:ad('RET0',0,1)}))
 login_maps=json.loads((W/'build_v259.json').read_text())['login_maps']
 for oldidx,actualidx,pc,entry,exit in [(149,150,319,142,151),(179,181,613,214,228)]:
  target=int(login_maps[str(oldidx)][str(pc)])+1
  export(12,actualidx,'login_'+str(oldidx),{0:jump(0,entry,4),exit:jump(exit,target,5)})
  export(12,actualidx,'save_'+str(oldidx))
 runs=[]
 for suite in ['oil_batch','gift_stack','autosave']:
  src=work/(suite+'.lua');src.write_bytes((W/(suite+'_regression_v264.lua')).read_text().encode('gbk'))
  for mode in ['normal','hot']:
   receipt=work/(suite+'.'+mode+'.passed.json');identity={'sha256':hashlib.sha256(b).hexdigest(),'suite_source':hashlib.sha256(src.read_bytes()).hexdigest(),'mode':mode}
   if resume and receipt.exists():
    saved=json.loads(receipt.read_text())
    if saved['identity']==identity:runs.append(saved['run']);print('Reuse passed '+suite+' '+mode,flush=True);continue
   r=subprocess.run([runtime,str(src),str(work),mode],capture_output=True,timeout=90);out=(r.stdout+r.stderr).decode('gbk','replace');print(out,flush=True);(work/(suite+'.'+mode+'.log')).write_text(out);assert r.returncode==0,(suite,mode,out[-5000:]);runs.append({'suite':suite,'mode':mode,'output':out});receipt.write_text(json.dumps({'identity':identity,'run':runs[-1]},ensure_ascii=False))
 names=['patch_v264.py','test_v264.py','package_v264.py','player_changes_v264.json','luck_system_v264.lua','luck_system_v264.ljbc','luck_rules_v249.lua','oil_batch_regression_v264.lua','oil_gift_v264.lua','oil_gift_v264.ljbc','oil_reset_v264.lua','oil_reset_v264.ljbc','gift_stack_regression_v264.lua','autosave_regression_v264.lua']
 result={'version':'v1.264','all_passed':True,'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'all_42_modules_checked':True,'historical_suites_rerun':False,'full_windows_game_run':False,'full_client_save_load':False,'scope':'actual oil inventory/quickbar/batches, post-load gift and native confirmation bridge, native add/stack/sort with legacy quantities, native timer/frame/public run to bounded autosave callback; finite UI/engine/file bridges','tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v264.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');p.add_argument('--resume',action='store_true');a=p.parse_args();main(a.runtime or str(ensure_runtime()),a.resume)
