from test_v225 import *
from patch_v270 import BASE_SHA
from patch_v139 import encstr, rebuild_proto
from ljtool import Proto

def main(runtime,resume=False):
 work=W/'native_work/v270';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v269.res').read_bytes();b=(W/'game_v270.res').read_bytes();assert hashlib.sha256(a).hexdigest()==BASE_SHA
 _,old=decode(a,range(2,86,2));_,new=decode(b,range(2,86,2));build=json.loads((W/'build_v270.json').read_text());cnt=build['exit_watch_count']
 expected={12:{76,22196},14:{674,710,726,733,749},30:{39,87}}
 for mid,d in new.items():
  trees(d);assert d.rebuild()==d.raw
  after=[p for p in d.protos if mid!=14 or not 749<=p.idx<749+cnt]
  assert len(after)==len(old[mid].protos)
  assert {i for i,(p,q)in enumerate(zip(old[mid].protos,after))if p.raw!=q.raw}==expected.get(mid,set()),mid
  for p in d.protos:
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,p.idx,pc)
  for idx in expected.get(mid,set())-({749}if mid==14 else set()):
   p=Proto(d.protos[idx].raw,idx)
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    back=v.replace(b'v1.270',b'v1.269')
    if mid==12 and idx in [76,22196]:back=back.replace(b'1.270',b'1.269')
    if back!=v:p.kgc[j]=back;p.kraw[j]=encstr(back)
   assert rebuild_proto(p)==old[mid].protos[idx].raw,(mid,idx)
 # Preserve every original constructor instruction and branch active-register A.
 mp={int(k):v for k,v in build['install_map'].items()};p=old[14].protos[749];q=new[14].protos[749+cnt]
 for pc,x in enumerate(p.bc):
  at=mp[pc]+(3 if pc==283 else 0);y=q.bc[at]
  if OPS[x&255]in BRANCHES:assert x&65535==y&65535 and at+1+(y>>16)-32768==mp[pc+1+(x>>16)-32768]
  else:assert x==y,(pc,at)
 def export(mid,idx,name,patches=None,params=None):
  d=new[mid];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx,patches,params))
 for mid,idx,name in [(14,748+cnt,'exit_watch'),(14,13,'readonly'),(30,1,'os_exit'),(14,99,'native_quit'),(14,12,'native_error'),(12,154,'save_quit'),(14,726,'legacy_diag')]:export(mid,idx,name)
 export(14,749+cnt,'constructor',{0:ad('MOV',0,0),1:jump(1,280,1)},1)
 for mid,idx,name in [(12,126,'role_a'),(12,132,'role_b'),(12,129,'config_a'),(12,134,'config_b'),(12,73,'mode_get'),(12,154,'quit153'),(12,190,'quit188'),(14,167,'timer_factory'),(14,725,'profile_only'),(14,13,'public_sys'),(14,427,'native_frame')]:export(mid,idx,name)
 export(12,20,'timer_new',{140:ad('RET0',0,1)})
 # Old-interval control differs solely in the dedicated autosave divisor.
 from patch_v200 import numbers
 from ljtool import Dump
 d=Dump((work/'timer_new.ljbc').read_bytes());d.protos[-1]=numbers(d.protos[-1],{25:200});(work/'timer_old.ljbc').write_bytes(d.rebuild())
 export(14,749+cnt,'native_exports',{0:jump(0,280)},1)
 auto=(W/'autosave_regression_v269.lua').read_text()
 auto=auto.replace('env.os={date=os.date,clock=', 'env.os={exit=function()end,date=os.date,clock=')
 auto=auto.replace("assert(type(S.__gm_native_watch_v268)=='table','actual constructor retains diagnostic installation')", "assert(type(S.__gm_native_watch_v268)=='table');assert(type(S.__gm_exit_watch_v270)=='table','actual constructor installs exit watch before public.run')")
 auto=auto.replace("assert(watch_writes<2700,'sampled writes remain bounded')", "assert(watch_writes<2700,'sampled writes remain bounded');assert(watch_files['Log/guimeng_exit_latest.txt']:find('stage=installed',1,true));eq(S.__gm_exit_watch_v270.requests,0)")
 sources={'exit':(W/'exit_watch_regression_v270.lua').read_text(),'autosave':auto};runs=[]
 for suite,code in sources.items():
  src=work/(suite+'.lua');src.write_bytes(code.encode('gbk'))
  for mode in ['normal','hot']:
   receipt=work/((mode if suite=='exit'else suite+'.'+mode)+'.passed.json');identity={'resource':hashlib.sha256(b).hexdigest(),'source':hashlib.sha256(src.read_bytes()).hexdigest(),'mode':mode}
   if resume and receipt.exists():
    saved=json.loads(receipt.read_text())
    if saved['identity']==identity:runs.append(dict(saved['run'],suite=suite));print('Reuse passed '+suite+' '+mode,flush=True);continue
   r=subprocess.run([runtime,str(src),str(work),mode],capture_output=True,timeout=90)
   out=(r.stdout+r.stderr).decode('gbk','replace');print(out,flush=True);(work/(suite+'.'+mode+'.log')).write_text(out);assert r.returncode==0,(suite,mode,out[-4000:])
   run={'suite':suite,'mode':mode,'output':out};runs.append(run);receipt.write_text(json.dumps({'identity':identity,'run':run},ensure_ascii=False))
 names=['patch_v270.py','test_v270.py','package_v270.py','player_changes_v270.json','exit_watch_v270.lua','exit_watch_v270.ljbc','exit_watch_regression_v270.lua']
 result={'version':'v1.270','all_passed':True,'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'diagnostic_only':True,'crash_root_cause_confirmed':False,'all_42_modules_checked':True,'full_windows_game_run':False,'scope':'actual native constructor/public export and full native frame/timer/autosave region, original os.exit wrapper, original Gly quit/default error and save-and-quit callbacks; unchanged full legacy diagnostic installer compared for allocations/writes; finite file and termination sinks, not a reproduction of uploaded hard exit','tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v270.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');p.add_argument('--resume',action='store_true');a=p.parse_args();main(a.runtime or str(ensure_runtime()),a.resume)
