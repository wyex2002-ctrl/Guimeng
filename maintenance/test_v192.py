"""Real load-time control list versus live inventory, real medicine scripts."""
from pathlib import Path
import argparse,hashlib,json,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from bytecode_relocate import BRANCHES,numeric_and_debug
from ljdis import OPS
from patch_v139 import ad,jump
from runtime import ensure_runtime
W=Path(__file__).resolve().parent

def lua(v):
 if v is None:return 'nil'
 if isinstance(v,bool):return str(v).lower()
 if isinstance(v,(int,float)):return repr(v)
 if isinstance(v,bytes):return json.dumps(v.decode('gbk'),ensure_ascii=False)
 if isinstance(v,tuple)and v[0]in ('int','num'):return repr(v[1])
 if isinstance(v,dict):return '{'+','.join('['+lua(k)+']='+lua(x)for k,x in v.items())+'}'
 raise ValueError(v)

def prepare():
 work=W/'native_work/v192';work.mkdir(parents=True,exist_ok=True)
 base=(W/'game_v191.res').read_bytes();data=(W/'game_v192.res').read_bytes()
 ao,old=decode(base,range(2,86,2));bo,new=decode(data,range(2,86,2));b=json.loads((W/'build_v192.json').read_text())
 changes={int(k):v for k,v in b['changed_prototypes'].items()};assert changes=={12:[283],14:[632,668,684],30:[39,87]},changes
 assert ao.protos[0].bc==bo.protos[0].bc and base[-10:]==data[-10:]
 for m,d in new.items():
  trees(d);assert d.rebuild()==d.raw and len(d.protos)==len(old[m].protos)
  for i,(p,q)in enumerate(zip(d.protos,old[m].protos)):
   assert(p.raw!=q.raw)==(i in changes.get(m,[])),(m,i)
   assert numeric_and_debug(p)[0]==numeric_and_debug(q)[0],(m,i)
   assert(p.flags,p.params,p.frame,p.nuv,p.uv,p.nkgc)==(q.flags,q.params,q.frame,q.nuv,q.uv,q.nkgc+(2 if m==12 and i==283 else 0)),(m,i)
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(m,i,pc)
 p,q=old[12].protos[283],new[12].protos[283];mp={int(k):v for k,v in b['aux_relocations'].items()}
 skipped={i for pc in [18,198,244]for i in range(pc,pc+5)}
 for pc,x in enumerate(p.bc):
  if pc in skipped:continue
  at=mp[pc]+(2 if pc==23 else 0);expected=x
  if OPS[x&255]in BRANCHES:expected=(x&65535)|((mp[pc+1+(x>>16)-32768]-at-1+32768)<<16)
  assert q.bc[at]==expected,(pc,at)
 assert q.bc[mp[23]+1]==jump(mp[23]+1,mp[57],10)
 used={q.gc(x>>16)for x in q.bc if OPS[x&255]=='GGET'}
 assert b'Sys'not in used and used<={p.gc(x>>16)for x in old[12].protos[283].bc if OPS[x&255]=='GGET'},used
 # Existing Gly lookup is explicitly exported from its real factory.
 g=new[14].protos[301];assert g.gc(g.bc[157]>>16&255)=='取控件对象'.encode('gbk')and (g.bc[157]>>8&255)==39
 extracts=[(14,397,'use'),(14,458,'proxy'),(14,381,'dispatch'),(14,416,'public_get'),(14,13,'public_sys'),(12,37,'item_event'),(12,283,'aux'),(12,126,'role_a'),(12,132,'role_b'),(12,129,'config_a'),(12,134,'config_b'),(12,128,'slots_get'),(34,31,'inventory_class'),(48,25,'add_control'),(48,23,'bind_control'),(14,683,'profile'),(14,301,'gly_factory')]
 for m,i,name in extracts:
  d=new[m];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),i))
 d=new[14];(work/'sandbox_install.ljbc').write_bytes(standalone(d,trees(d),378,{0:jump(0,597,13),609:ad('RET0',0,1)}))
 d=old[12];(work/'aux_old.ljbc').write_bytes(standalone(d,trees(d),283))
 d=new[12];(work/'periodic.ljbc').write_bytes(standalone(d,trees(d),20,{0:jump(0,1016,10),1028:ad('RET0',0,1)}))
 d=new[12];(work/'initialize_controls.ljbc').write_bytes(standalone(d,trees(d),179,{0:jump(0,456,18),498:ad('RET0',0,1)}))
 # Preserve exact TDUP fields, numeric zero flags and actual drug factories.
 stack=[];children={}
 for p in d.protos:
  kids={}
  for j,k in enumerate(p.kgc):
   if k==('child',):kids[p.nkgc-1-j]=stack.pop()
  children[p.idx]=kids;stack.append(p.idx)
 p=d.protos[4090];templates={}
 for name,pc in [('金创药_小',7270),('魔法药_小',8270),('太阳水',9270),('强效太阳水',9370),('万年雪霜',9470)]:
  assert OPS[p.bc[pc]&255]=='TDUP';t=p.gc(p.bc[pc]>>16);item=dict(t[2]);assert item['名称'.encode('gbk')]==name.encode('gbk')
  flags=[p.gc(x>>16).decode('gbk')for x in p.bc[pc-65:pc]if OPS[x&255]=='KSTR'and(x>>8&255)==4][-1]
  props={}
  for s in flags.split('ぃ'):
   if s:
    k,v=s.split('ぅ');props[k.encode('gbk')]=int(v)if v.isdigit()else v.encode('gbk')
  item['风格提示'.encode('gbk')]=dict(p.gc(p.bc[pc+3]>>16)[2]);item['附加'.encode('gbk')]=props;templates[name.encode('gbk')]=item
  fnew=next(x for x in p.bc[pc:pc+20]if OPS[x&255]=='FNEW');idx=children[4090][fnew>>16]
  (work/('script_'+name.encode('gbk').hex()+'.ljbc')).write_bytes(standalone(d,trees(d),idx))
 (work/'templates.lua').write_bytes(('return '+lua(templates)+'\n').encode('gbk'))
 (work/'autopotion.lua').write_bytes((W/'autopotion_regression_v192.lua').read_text().encode('gbk'))
 return work,data

def main(runtime,focused=False):
 (W/'validation_v192.json').unlink(missing_ok=True);work,data=prepare();runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'autopotion.lua'),str(work),mode],capture_output=True,timeout=120)
  (work/(mode+'.log')).write_bytes(r.stdout+r.stderr)
  assert r.returncode==0,(mode,(r.stdout+r.stderr)[-4500:].decode('gbk','replace'))
  output=r.stdout.decode('gbk');assert 'AUTOPOTION_V192_PASS'in output;print(output,flush=True);runs.append({'mode':mode,'output':output})
 if focused:return
 r=subprocess.run(['python3',str(W/'test_v191.py'),'--runtime',runtime],capture_output=True)
 (work/'baseline.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0,(r.stdout+r.stderr)[-3500:]
 integration=W/'native_work/v179';_,mods=decode(data,[14]);d=mods[14];(integration/'installer179.ljbc').write_bytes(standalone(d,trees(d),684))
 for name in ['diagnostics.lua','integration.lua']:
  for mode in ['normal','hot']:
   r=subprocess.run([runtime,str(integration/name),str(integration),mode],capture_output=True,timeout=90)
   (work/(name+'.'+mode+'.log')).write_bytes(r.stdout+r.stderr);assert r.returncode==0,(r.stdout+r.stderr)[-2500:]
 names=['patch_v192.py','test_v192.py','autopotion_regression_v192.lua','player_changes_v192.json','package_v192.py']
 result={'version':'v1.192','all_passed':True,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'autopotion_runs':runs,'v191_and_prior_regressions_rerun':True,'current_real_event_periodic_chain':True,'event_Sys_unavailable_tested':True,'current_diagnostics_public_integration':True,'all_42_modules_and_non_target_prototypes_verified':True,'real_load_loop_and_public_controls':True,'real_potion_templates_and_scripts':True,'full_windows_game_run':False,'real_effect_tick_timing_tested':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v192.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--focused',action='store_true');x=a.parse_args();main(str(Path(x.runtime).resolve())if x.runtime else str(ensure_runtime()),x.focused)
