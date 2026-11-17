from test_v225 import *
from patch_v273 import BASE_SHA
from patch_v200 import numbers
from patch_v139 import encstr, rebuild_proto
from ljtool import Proto

def main(runtime):
 work=W/'native_work/v273';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v272.res').read_bytes();b=(W/'game_v273.res').read_bytes();assert hashlib.sha256(a).hexdigest()==BASE_SHA
 _,old=decode(a,range(2,86,2));_,new=decode(b,range(2,86,2));changes={}
 for mid,d in new.items():
  trees(d);assert d.rebuild()==d.raw and len(d.protos)==len(old[mid].protos)
  for p,q in zip(old[mid].protos,d.protos):
   if p.raw!=q.raw:changes.setdefault(mid,[]).append(p.idx)
   restored=Proto(q.raw,q.idx)
   if mid==12 and p.idx==20:restored=numbers(restored,{25:200})
   for j,v in enumerate(restored.kgc):
    if not isinstance(v,bytes):continue
    back=v.replace(b'v1.273',b'v1.272')
    if mid==12 and p.idx in [76,22196]:back=back.replace(b'1.273',b'1.272')
    if back!=v:restored.kgc[j]=back;restored.kraw[j]=encstr(back)
   assert rebuild_proto(restored)==p.raw,(mid,p.idx)
   for pc,x in enumerate(q.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<q.nbc,(mid,q.idx,pc)
 def export(mid,idx,name,patches=None,params=None,baseline=False):
  d=(old if baseline else new)[mid];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx,patches,params))
 for mid,idx,name in [(12,126,'role_a'),(12,132,'role_b'),(12,129,'config_a'),(12,134,'config_b'),(12,73,'mode_get'),(12,154,'quit153'),(12,190,'quit188'),(14,167,'timer_factory'),(14,725,'profile_only'),(14,13,'public_sys'),(14,427,'native_frame')]:export(mid,idx,name)
 export(12,20,'timer_new',{140:ad('RET0',0,1)});export(12,20,'timer_old',{140:ad('RET0',0,1)},baseline=True)
 export(14,755,'native_exports',{0:jump(0,280)},1)
 src=work/'autosave.lua';src.write_bytes((W/'autosave_regression_v273.lua').read_text().encode('gbk'));runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(src),str(work),mode],capture_output=True,timeout=90);out=(r.stdout+r.stderr).decode('gbk','replace');print(out,flush=True);(work/(mode+'.log')).write_text(out);assert r.returncode==0,(mode,out[-4000:]);runs.append({'mode':mode,'output':out})
 names=['patch_v273.py','test_v273.py','package_v273.py','player_changes_v273.json','autosave_regression_v273.lua']
 result={'version':'v1.273','all_passed':True,'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'changed_prototypes':changes,'autosave_seconds':5,'all_42_modules_checked':True,'full_windows_game_run':False,'scope':'sole autosave constant and version strings; actual two-story autosave region, native timer/full frame and current constructor/read-only public.run, unchanged diagnostic policy; finite engine/file/save sinks, not full client save IO','tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v273.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');a=p.parse_args();main(a.runtime or str(ensure_runtime()))
