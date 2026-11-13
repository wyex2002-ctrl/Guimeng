"""Execute real XP registration, legacy storage, Ling claims and data export."""
from pathlib import Path
import argparse,hashlib,json,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from bytecode_relocate import BRANCHES,numeric_and_debug
from ljdis import OPS
from ljtool import Proto
from patch_v139 import ad,jump,rebuild_proto
from runtime import ensure_runtime
W=Path(__file__).resolve().parent

def main(runtime):
 (W/'validation_v190.json').unlink(missing_ok=True);work=W/'native_work/v190';work.mkdir(parents=True,exist_ok=True)
 base=(W/'game_v189.res').read_bytes();data=(W/'game_v190.res').read_bytes()
 ao,old=decode(base,range(2,86,2));bo,new=decode(data,range(2,86,2));b=json.loads((W/'build_v190.json').read_text(encoding='utf-8'))
 changes={int(k):v for k,v in b['changed_prototypes'].items()};assert changes=={12:[258],14:[632,668,684],30:[39,87]},changes
 assert ao.protos[0].bc==bo.protos[0].bc and base[-10:]==data[-10:]
 for m,d in new.items():
  trees(d);assert d.rebuild()==d.raw and len(d.protos)==len(old[m].protos)
  for i,(p,q)in enumerate(zip(d.protos,old[m].protos)):
   assert(p.raw!=q.raw)==(i in changes.get(m,[])),(m,i)
   assert numeric_and_debug(p)[0]==numeric_and_debug(q)[0],(m,i)
   assert(p.flags,p.params,p.frame,p.nuv,p.uv,p.nkgc)==(q.flags,q.params,q.frame,q.nuv,q.uv,q.nkgc+(3 if m==12 and i==258 else 0)),(m,i)
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(m,i,pc)
 p,q=old[12].protos[258],new[12].protos[258];mp={int(k):v for k,v in b['storage_relocations'].items()}
 for pc,x in enumerate(p.bc):
  if pc==416:assert q.bc[mp[pc]]==jump(mp[pc],mp[397],20);continue
  at=mp[pc]+(5 if pc in (22,44)else b['inserted_blocks']['382']-1 if pc==382 else 0);expected=x
  if OPS[x&255]=='JMP':expected=jump(at,mp[pc+1+(x>>16)-32768],20)
  elif OPS[x&255]in BRANCHES:expected=(x&65535)|((mp[pc+1+(x>>16)-32768]-at-1+32768)<<16)
  assert q.bc[at]==expected,(pc,at)
 assert {p.gc(x>>16)for x in p.bc if OPS[x&255]=='GGET'}|{b'type'}=={q.gc(x>>16)for x in q.bc if OPS[x&255]=='GGET'}
 exported={new[14].protos[378].gc((x>>16)&255)for x in new[14].protos[378].bc if OPS[x&255]=='TSETS'};assert b'type'in exported
 # Registration instructions create the XP closure with its actual owner UV.
 d=old[12];reference=Proto(d.protos[258].raw,258);reference.bc[416]=jump(416,397,20)
 reference.bc=[(x&~0xff00)|(20<<8)if OPS[x&255]=='JMP'else x for x in reference.bc];reference=Proto(rebuild_proto(reference),258)
 for label,mods in [('old',old),('new',new),('reference',old)]:
  d=mods[12];saved=d.protos[258]
  if label=='reference':d.protos[258]=reference
  (work/('register_'+label+'.ljbc')).write_bytes(standalone(d,trees(d),292,{0:jump(0,156,2),159:ad('RET0',0,1)}))
  d.protos[258]=saved
 for m,i,name in [(14,458,'proxy'),(14,416,'public_get'),(14,13,'public_sys'),(14,224,'export_item'),(14,220,'entity'),(12,126,'role_a'),(12,132,'role_b'),(12,129,'config_a'),(12,134,'config_b'),(12,128,'slots_get'),(12,37,'item_event'),(12,257,'ling'),(22,43,'merc_exp')]:
  d=new[m];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),i))
 d=new[30];(work/'table_register.ljbc').write_bytes(standalone(d,trees(d),193,{0:jump(0,33),42:jump(42,57),69:ad('RET0',0,1)}))
 # Original item configs are kept in the real template string format. Tests
 # consume these values rather than inventing capacities or usage counts.
 p=new[12].protos[4090];config={}
 for name,pc in [('小',58915),('中',59015),('大',59115),('特',102115)]:config[name]=p.gc(p.bc[pc]>>16).decode('gbk')
 (work/'configs.lua').write_bytes(('return {'+','.join("['"+k+"']='"+v+"'"for k,v in config.items())+'}').encode('gbk'))
 (work/'talisman.lua').write_bytes((W/'talisman_regression_v190.lua').read_text(encoding='utf-8').encode('gbk'))
 runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'talisman.lua'),str(work),mode],capture_output=True,timeout=120)
  (work/(mode+'.log')).write_bytes(r.stdout+r.stderr);assert r.returncode==0,(mode,(r.stdout+r.stderr)[-4000:].decode('gbk','replace'))
  output=r.stdout.decode('gbk');assert 'TALISMAN_V190_PASS'in output;print(output,flush=True);runs.append({'mode':mode,'output':output})
 r=subprocess.run(['python3',str(W/'test_v189.py'),'--runtime',runtime],capture_output=True)
 (work/'baseline.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0,(r.stdout+r.stderr)[-3000:]
 integration=W/'native_work/v179';d=new[14];(integration/'installer179.ljbc').write_bytes(standalone(d,trees(d),684))
 for name in ['diagnostics.lua','integration.lua']:
  for mode in ['normal','hot']:
   r=subprocess.run([runtime,str(integration/name),str(integration),mode],capture_output=True,timeout=90)
   (work/(name+'.'+mode+'.log')).write_bytes(r.stdout+r.stderr);assert r.returncode==0,(name,mode,r.stdout[-1500:],r.stderr[-1500:])
 names=['patch_v190.py','test_v190.py','talisman_regression_v190.lua','player_changes_v190.json','package_v190.py']
 result={'version':'v1.190','all_passed':True,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'talisman_runs':runs,'v189_and_prior_regressions_rerun':True,'current_diagnostics_public_integration':True,'all_42_modules_and_non_target_prototypes_verified':True,'ling_helpers_byte_identical':True,'full_windows_game_run':False,'full_client_save_load':False,'rules_changed':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v190.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');x=a.parse_args();main(str(Path(x.runtime).resolve())if x.runtime else str(ensure_runtime()))
