"""Targeted display-name/configuration and real item restoration regression."""
from pathlib import Path
import argparse,hashlib,json,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from bytecode_relocate import BRANCHES,numeric_and_debug
from patch_v139 import ad,jump
from ljdis import OPS
from runtime import ensure_runtime
from test_v192 import lua
W=Path(__file__).resolve().parent

def main(runtime):
 (W/'validation_v193.json').unlink(missing_ok=True);work=W/'native_work/v193';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v192.res').read_bytes();b=(W/'game_v193.res').read_bytes();ao,old=decode(a,range(2,86,2));bo,new=decode(b,range(2,86,2))
 report=json.loads((W/'build_v193.json').read_text());changes={int(k):v for k,v in report['changed_prototypes'].items()};assert changes=={12:[4090],14:[437,632,668,684],30:[39,87]}
 assert ao.protos[0].bc==bo.protos[0].bc and a[-10:]==b[-10:]
 for m,d in new.items():
  assert d.rebuild()==d.raw and len(d.protos)==len(old[m].protos)
  for i,(p,q)in enumerate(zip(d.protos,old[m].protos)):
   assert(p.raw!=q.raw)==(i in changes.get(m,[])),(m,i)
   assert numeric_and_debug(p)[0]==numeric_and_debug(q)[0]
   assert(p.params,p.frame,p.uv)==(q.params,q.frame,q.uv)
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc
 p,q=old[12].protos[4090],new[12].protos[4090];assert p.bc==q.bc
 altered=[]
 for i,(v,n)in enumerate(zip(p.kgc,q.kgc)):
  if v==n:continue
  assert v[0]==n[0]=='table'and v[1]==n[1];left=dict(v[2]);right=dict(n[2]);name=left['名称'.encode('gbk')]
  assert name.decode('gbk')in report['renamed_books'];assert right['显示名'.encode('gbk')]==name+'(秘籍)'.encode('gbk')
  assert {k:x for k,x in left.items()if k!='显示名'.encode('gbk')}=={k:x for k,x in right.items()if k!='显示名'.encode('gbk')};altered.append(name)
 assert len(altered)==148
 p,q=old[14].protos[437],new[14].protos[437];mp={int(k):v for k,v in report['reset_relocations'].items()}
 for pc,x in enumerate(p.bc):
  at=mp[pc]+(17 if pc==124 else 0);expected=x
  if OPS[x&255]in BRANCHES:expected=(x&65535)|((mp[pc+1+(x>>16)-32768]-at-1+32768)<<16)
  assert q.bc[at]==expected,(pc,at)
 configs={};p=new[12].protos[4090]
 for pc,x in enumerate(p.bc):
  if OPS[x&255]!='TDUP':continue
  v=p.gc(x>>16)
  if not(isinstance(v,tuple)and v[0]=='table'):continue
  t=dict(v[2]);name=t.get('名称'.encode('gbk'))
  if name not in altered and name not in ['雷电术'.encode('gbk'),'魔法药_小'.encode('gbk')]:continue
  flags=[p.gc(z>>16).decode('gbk')for z in p.bc[pc-65:pc]if OPS[z&255]=='KSTR'and z>>8&255==4][-1];props={}
  for field in flags.split('ぃ'):
   if field:
    k,v=field.split('ぅ');props[k.encode('gbk')]=int(v)if v.isdigit()else v.encode('gbk')
  t['附加'.encode('gbk')]=props;t['属性'.encode('gbk')]={};t['风格提示'.encode('gbk')]=dict(p.gc(p.bc[pc+3]>>16)[2]);configs[name]=t
 assert len(configs)==150
 (work/'configs.lua').write_bytes(('return '+lua(configs)).encode('gbk'))
 for m,i,n in [(14,437,'reset'),(14,443,'update'),(14,458,'proxy'),(14,223,'item_info'),(14,224,'slot_info')]:
  d=new[m];(work/(n+'.ljbc')).write_bytes(standalone(d,trees(d),i))
 d=old[14];(work/'reset_old.ljbc').write_bytes(standalone(d,trees(d),437))
 d=new[30];(work/'table_register.ljbc').write_bytes(standalone(d,trees(d),193,{0:jump(0,33),42:jump(42,57),69:ad('RET0',0,1)}))
 d=new[12];(work/'tooltip_header.ljbc').write_bytes(standalone(d,trees(d),296,{8:ad('RET1',3,2)}))
 (work/'books.lua').write_bytes((W/'book_names_regression_v193.lua').read_text().encode('gbk'));runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'books.lua'),str(work),mode],capture_output=True,timeout=90);(work/(mode+'.log')).write_bytes(r.stdout+r.stderr)
  assert r.returncode==0,(r.stdout+r.stderr).decode('gbk','replace')[-3500:]
  output=r.stdout.decode('gbk');assert 'BOOK_NAMES_V193_PASS'in output;print(output,flush=True);runs.append({'mode':mode,'output':output})
 names=['patch_v193.py','test_v193.py','book_names_regression_v193.lua','package_v193.py','player_changes_v193.json']
 result={'version':'v1.193','all_passed':True,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'renamed_books':148,'runs':runs,'test_scope':'book_templates_and_item_restore','historical_suites_rerun':False,'full_windows_game_run':False,'full_client_save_load':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v193.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');x=a.parse_args();main(str(Path(x.runtime).resolve())if x.runtime else str(ensure_runtime()))
