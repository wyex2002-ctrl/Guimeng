"""Autosave interval boundaries and actual native frame/public export."""
from test_v225 import *
from patch_v269 import BASE_SHA
from patch_v200 import numbers
from patch_v139 import encstr, rebuild_proto
from ljtool import Proto

def main(runtime, resume=False):
 work=W/'native_work/v269';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v268.res').read_bytes();b=(W/'game_v269.res').read_bytes()
 assert hashlib.sha256(a).hexdigest()==BASE_SHA
 _,old=decode(a,range(2,86,2));_,new=decode(b,range(2,86,2))
 expected={12:{20,76,22196},14:{674,710,726,733},30:{39,87}}
 for mid,d in new.items():
  trees(d);assert d.rebuild()==d.raw and len(d.protos)==len(old[mid].protos)
  assert {i for i,(p,q)in enumerate(zip(old[mid].protos,d.protos))if p.raw!=q.raw}==expected.get(mid,set()),mid
  for p in d.protos:
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,p.idx,pc)
  # Reverse only the documented constant and version strings. The result must
  # equal every original prototype byte-for-byte, including the diagnostics.
  for idx in expected.get(mid,set()):
   p=Proto(d.protos[idx].raw,idx)
   if mid==12 and idx==20:p=numbers(p,{25:200})
   else:
    for j,v in enumerate(p.kgc):
     if not isinstance(v,bytes):continue
     back=v.replace(b'v1.269',b'v1.268')
     if mid==12 and idx in [76,22196]:back=back.replace(b'1.269',b'1.268')
     if back!=v:p.kgc[j]=back;p.kraw[j]=encstr(back)
    p=Proto(rebuild_proto(p),idx)
   assert p.raw==old[mid].protos[idx].raw,(mid,idx,'unexpected behavior change')
 def export(mid,idx,name,patches=None,params=None,baseline=False):
  d=(old if baseline else new)[mid]
  (work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx,patches,params))
 for mid,idx,name in [(12,126,'role_a'),(12,132,'role_b'),(12,129,'config_a'),(12,134,'config_b'),(12,73,'mode_get'),(12,154,'quit153'),(12,190,'quit188'),(14,167,'timer_factory'),(14,725,'profile_only'),(14,13,'public_sys'),(14,427,'native_frame')]:export(mid,idx,name)
 # Bound the event after its complete original autosave region. Native frame,
 # timer factory, role getters and constructor/public export execute directly.
 export(12,20,'timer_new',{140:ad('RET0',0,1)})
 export(12,20,'timer_old',{140:ad('RET0',0,1)},baseline=True)
 mp=json.loads((W/'build_v268.json').read_text())['install_map']
 export(14,749,'native_exports',{0:jump(0,mp['280'])},1)
 src=work/'autosave.lua';src.write_bytes((W/'autosave_regression_v269.lua').read_text().encode('gbk'))
 runs=[]
 for mode in ['normal','hot']:
  receipt=work/(mode+'.passed.json');identity={'resource':hashlib.sha256(b).hexdigest(),'source':hashlib.sha256(src.read_bytes()).hexdigest(),'mode':mode}
  if resume and receipt.exists():
   saved=json.loads(receipt.read_text())
   if saved['identity']==identity:runs.append(saved['run']);print('Reuse passed '+mode,flush=True);continue
  result=subprocess.run([runtime,str(src),str(work),mode],capture_output=True,timeout=90)
  out=(result.stdout+result.stderr).decode('gbk','replace');print(out,flush=True)
  (work/(mode+'.log')).write_text(out);assert result.returncode==0,(mode,out[-5000:])
  run={'mode':mode,'output':out};runs.append(run);receipt.write_text(json.dumps({'identity':identity,'run':run},ensure_ascii=False))
 names=['patch_v269.py','test_v269.py','package_v269.py','player_changes_v269.json','autosave_regression_v269.lua']
 result={'version':'v1.269','all_passed':True,'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'autosave_seconds':180,'crash_root_cause_confirmed':False,'all_42_modules_checked':True,'historical_suites_rerun':False,'full_windows_game_run':False,'scope':'actual two-story role/config getters, original autosave region, native timer factory/full frame and constructor/read-only public export with v268 diagnostic installation; finite engine/file/save sinks, no Windows crash reproduction','tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v269.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');p.add_argument('--resume',action='store_true');a=p.parse_args();main(a.runtime or str(ensure_runtime()),a.resume)
