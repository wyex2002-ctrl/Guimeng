from test_v225 import *
from patch_v266 import BASE_SHA
from test_v192 import lua

def main(runtime):
 work=W/'native_work/v266';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v265.res').read_bytes();b=(W/'game_v266.res').read_bytes();assert hashlib.sha256(a).hexdigest()==BASE_SHA
 _,old=decode(a,range(2,86,2));_,new=decode(b,range(2,86,2));expected={12:{76,22196},14:{674,710,726},22:{112},30:{39,87}}
 for mid,d in new.items():
  trees(d);assert d.rebuild()==d.raw and len(d.protos)==len(old[mid].protos)
  assert {i for i,(p,q)in enumerate(zip(old[mid].protos,d.protos))if p.raw!=q.raw}==expected.get(mid,set()),mid
  for p in d.protos:
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,p.idx,pc)
 def export(mid,idx,name,patches=None):
  d=new[mid];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx,patches))
 for mid,idx,name in [(14,13,'public_sys'),(14,458,'public_get'),(14,339,'fx_getter'),(14,500,'data_protection'),(14,419,'merc_helper'),(12,4091,'oil_template'),(22,112,'oil_helper'),(22,64,'death_new'),(22,3,'spawn'),(12,193,'currency_new'),(14,444,'native_drop'),(76,1,'ground_init')]:export(mid,idx,name)
 export(30,193,'table_register',{0:jump(0,33),42:jump(42,48),69:ad('RET0',0,1)})
 p=new[12].protos[4092]
 def cv(v):
  if isinstance(v,tuple)and v[0]=='int':return v[1]
  return v
 for x in p.bc:
  if OPS[x&255]!='TDUP':continue
  t=p.gc(x>>16)
  if isinstance(t,tuple)and t[0]=='table':
   fields={k:cv(v)for k,v in t[2]}
   if fields.get('名称'.encode('gbk'))=='自然神水_小'.encode('gbk'):
    (work/'water_base.lua').write_bytes(('return '+lua(fields)).encode('gbk'));break
 else:raise AssertionError('water template absent')
 src=work/'test.lua';src.write_bytes((W/'oil_drop_regression_v266.lua').read_text().encode('gbk'));runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(src),str(work),mode],capture_output=True,timeout=90);out=(r.stdout+r.stderr).decode('gbk','replace');print(out,flush=True);(work/(mode+'.log')).write_text(out);assert r.returncode==0,(mode,out[-5000:]);runs.append({'mode':mode,'output':out})
 names=['patch_v266.py','test_v266.py','package_v266.py','player_changes_v266.json','oil_drop_v266.lua','oil_drop_v266.ljbc','oil_drop_regression_v266.lua']
 result={'version':'v1.266','all_passed':True,'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'all_42_modules_checked':True,'historical_suites_rerun':False,'full_windows_game_run':False,'scope':'actual native death/spawn, read-only Sys and live hero getter, oil helper -> native item protection/drop -> full ground constructor; exact integer-roll/level thresholds and per-life guard; finite engine/map/graphics bridge, not Windows full combat','tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v266.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');a=p.parse_args();main(a.runtime or str(ensure_runtime()))
