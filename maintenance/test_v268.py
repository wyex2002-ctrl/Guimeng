from test_v225 import *
from patch_v268 import BASE_SHA

def main(runtime,resume=False):
 work=W/'native_work/v268';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v267.res').read_bytes();b=(W/'game_v268.res').read_bytes();assert hashlib.sha256(a).hexdigest()==BASE_SHA
 _,old=decode(a,range(2,86,2));_,new=decode(b,range(2,86,2));build=json.loads((W/'build_v268.json').read_text());cnt=build['watch_count']
 expected={12:{76,22196},14:{674,710,726,729},30:{39,87}}
 for mid,d in new.items():
  trees(d);assert d.rebuild()==d.raw
  before=old[mid].protos;after=[p for p in d.protos if mid!=14 or not 729<=p.idx<729+cnt]
  assert len(before)==len(after)
  assert {i for i,(p,q)in enumerate(zip(before,after))if p.raw!=q.raw}==expected.get(mid,set()),mid
  for p in d.protos:
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,p.idx,pc)
 p,q=old[14].protos[729],new[14].protos[729+cnt];mp={int(k):v for k,v in build['install_map'].items()}
 for pc,x in enumerate(p.bc):
  at=mp[pc]+(3 if pc==280 else 0);y=q.bc[at]
  if OPS[x&255]in BRANCHES:assert x&65535==y&65535 and at+1+(y>>16)-32768==mp[pc+1+(x>>16)-32768]
  else:assert x==y,(pc,at)
 def export(mid,idx,name,patches=None,params=None):
  d=new[mid];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx,patches,params))
 export(14,729+cnt,'constructor',{0:ad('MOV',0,0),1:jump(1,mp[280],1)},1)
 export(14,13,'readonly');export(14,728+cnt,'watch');export(14,726,'legacy_diag')
 # Export every fixture from the tested resource, never a prior native_work cache.
 for mid,idx,name in [(12,126,'role_a'),(12,132,'role_b'),(12,129,'config_a'),(12,134,'config_b'),(12,73,'mode_get'),(12,154,'quit153'),(12,190,'quit188'),(14,167,'timer_factory'),(14,725,'profile_only'),(14,13,'public_sys')]:export(mid,idx,name)
 export(12,20,'timer_new',{140:ad('RET0',0,1)})
 export(12,20,'timer_old',{120:__import__('patch_v139').abc('MODVN',1,1,8),140:ad('RET0',0,1)})
 export(14,427,'native_frame')
 export(14,729+cnt,'native_exports',{0:jump(0,mp[280])},1)
 sources={'watch':(W/'native_watch_regression_v268.lua').read_text()}
 auto=(W/'autosave_regression_v264.lua').read_text()
 auto=auto.replace("local env={['Ae冻']={}","local watch_files,watch_writes={},0\nlocal env={['Ae冻']={}")
 auto=auto.replace("['核心']={http_url_get=function()return {['总数']=0}end}","['核心']={写到文件=function(path,data)watch_files[path]=data;watch_writes=watch_writes+1 end,读入文件=function(path)return watch_files[path]end,http_url_get=function()return {['总数']=0}end}")
 auto=auto.replace("env.os={clock=function()return tick end,time=function()return math.floor(elapsed)end}","env.os={date=os.date,clock=function()return tick end,time=function()return math.floor(elapsed)end}")
 auto=auto.replace("local public=exporter(S);eq(public.run,S.run)","local public=exporter(S);eq(public.run,S.run);assert(type(S.__gm_native_watch_v268)=='table','actual constructor installs watch before public.run')")
 auto=auto.replace("costs[version]={saves=n,modeled_seconds=modeled}","costs[version]={saves=n,modeled_seconds=modeled};assert(watch_files['Log/guimeng_native_watch_latest.txt']:find('phase=',1,true));assert(watch_writes<350,'bounded native-frame writes')")
 sources['autosave']=auto
 runs=[]
 for suite,code in sources.items():
  src=work/(suite+'.lua');src.write_bytes(code.encode('gbk'))
  for mode in ['normal','hot']:
   receipt=work/(suite+'.'+mode+'.passed.json');identity={'resource':hashlib.sha256(b).hexdigest(),'source':hashlib.sha256(src.read_bytes()).hexdigest(),'mode':mode}
   if resume and receipt.exists():
    saved=json.loads(receipt.read_text())
    if saved['identity']==identity:runs.append(saved['run']);print('Reuse passed '+suite+' '+mode,flush=True);continue
   r=subprocess.run([runtime,str(src),str(work),mode],capture_output=True,timeout=90);out=(r.stdout+r.stderr).decode('gbk','replace');print(out,flush=True);(work/(suite+'.'+mode+'.log')).write_text(out);assert r.returncode==0,(suite,mode,out[-5000:]);runs.append({'suite':suite,'mode':mode,'output':out});receipt.write_text(json.dumps({'identity':identity,'run':runs[-1]},ensure_ascii=False))
 names=['patch_v268.py','test_v268.py','package_v268.py','player_changes_v268.json','native_watch_v268.lua','native_watch_v268.ljbc','native_watch_regression_v268.lua']
 result={'version':'v1.268','all_passed':True,'sha256':hashlib.sha256(b).hexdigest(),'diagnostic_only':True,'crash_root_cause_confirmed':False,'runs':runs,'all_42_modules_checked':True,'full_windows_game_run':False,'scope':'actual constructor child registration/read-only public run export, diagnostic return/error identity and bounded writes, native full frame/autosave gate; finite engine/file sinks; uploaded v266 abrupt termination not reproduced','tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v268.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');p.add_argument('--resume',action='store_true');a=p.parse_args();main(a.runtime or str(ensure_runtime()),a.resume)
