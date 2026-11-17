from test_v225 import *
from patch_v271 import BASE_SHA
from patch_v200 import numbers
from patch_v139 import encstr, rebuild_proto
from ljtool import Proto
def main(runtime,resume=False):
 work=W/'native_work/v271';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v270.res').read_bytes();b=(W/'game_v271.res').read_bytes();assert hashlib.sha256(a).hexdigest()==BASE_SHA
 _,old=decode(a,range(2,86,2));_,new=decode(b,range(2,86,2));build=json.loads((W/'build_v271.json').read_text());cnt=build['watch_count'];delta=cnt-20
 for mid,d in new.items():
  trees(d);assert d.rebuild()==d.raw
  before=[p for p in old[mid].protos if mid!=14 or not 729<=p.idx<749]
  after=[p for p in d.protos if mid!=14 or not 729<=p.idx<729+cnt]
  assert len(before)==len(after)
  for p,q in zip(before,after):
   restored=Proto(q.raw,q.idx)
   if mid==12 and p.idx==20:restored=numbers(restored,{25:1800})
   for j,v in enumerate(restored.kgc):
    if not isinstance(v,bytes):continue
    back=v.replace(b'v1.271',b'v1.270')
    if mid==12 and p.idx in [76,22196]:back=back.replace(b'1.271',b'1.270')
    if back!=v:restored.kgc[j]=back;restored.kraw[j]=encstr(back)
   assert rebuild_proto(restored)==p.raw,(mid,p.idx,q.idx)
  for p in d.protos:
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,p.idx,pc)
 def export(mid,idx,name,patches=None,params=None,baseline=False):
  d=(old if baseline else new)[mid];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx,patches,params))
 for mid,idx,name in [(14,728+cnt,'watch'),(14,753+delta,'exit_watch'),(14,13,'readonly'),(14,726,'legacy_diag'),(30,1,'os_exit'),(14,99,'native_quit'),(14,12,'native_error'),(12,154,'save_quit')]:export(mid,idx,name)
 export(14,754+delta,'constructor',{0:ad('MOV',0,0),1:jump(1,280,1)},1)
 for mid,idx,name in [(12,126,'role_a'),(12,132,'role_b'),(12,129,'config_a'),(12,134,'config_b'),(12,73,'mode_get'),(12,154,'quit153'),(12,190,'quit188'),(14,167,'timer_factory'),(14,725,'profile_only'),(14,13,'public_sys'),(14,427,'native_frame')]:export(mid,idx,name)
 export(12,20,'timer_new',{140:ad('RET0',0,1)});export(12,20,'timer_old',{140:ad('RET0',0,1)},baseline=True)
 export(14,754+delta,'native_exports',{0:jump(0,280)},1)
 suites={'watch':'native_watch_regression_v271.lua','exit':'exit_watch_regression_v270.lua','autosave':'autosave_regression_v271.lua'};runs=[]
 for suite,name in suites.items():
  src=work/(suite+'.lua');src.write_bytes((W/name).read_text().encode('gbk'))
  for mode in ['normal','hot']:
   receipt=work/(suite+'.'+mode+'.passed.json');identity={'resource':hashlib.sha256(b).hexdigest(),'source':hashlib.sha256(src.read_bytes()).hexdigest(),'mode':mode}
   if resume and receipt.exists():
    saved=json.loads(receipt.read_text())
    if saved['identity']==identity:runs.append(saved['run']);print('Reuse '+suite+' '+mode,flush=True);continue
   r=subprocess.run([runtime,str(src),str(work),mode],capture_output=True,timeout=120);out=(r.stdout+r.stderr).decode('gbk','replace');print(out,flush=True);(work/(suite+'.'+mode+'.log')).write_text(out);assert r.returncode==0,(suite,mode,out[-4000:])
   run={'suite':suite,'mode':mode,'output':out};runs.append(run);receipt.write_text(json.dumps({'identity':identity,'run':run},ensure_ascii=False))
 names=['patch_v271.py','test_v271.py','package_v271.py','player_changes_v271.json','native_watch_v271.lua','native_watch_v271.ljbc','native_watch_regression_v271.lua','autosave_regression_v271.lua']
 result={'version':'v1.271','all_passed':True,'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'autosave_seconds':3,'immediate_dense_logging':True,'crash_root_cause_confirmed':False,'all_42_modules_checked':True,'full_windows_game_run':False,'scope':'immediate frame/phase/actor/callback/action logging, original return/error identity and failed-file isolation; actual constructor/read-only public export, exit chain, native full frame/timer and two-story autosave region; finite engine/file/save/termination sinks, not client crash reproduction','tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v271.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');p.add_argument('--resume',action='store_true');a=p.parse_args();main(a.runtime or str(ensure_runtime()),a.resume)
