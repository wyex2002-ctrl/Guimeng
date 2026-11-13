"""Real inventory class construction, bookstore result parity, native timing."""
from pathlib import Path
import argparse,hashlib,json,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from bytecode_relocate import BRANCHES,numeric_and_debug
from ljdis import OPS
from patch_v139 import ad,jump
from runtime import ensure_runtime
W=Path(__file__).resolve().parent

def main(runtime):
 (W/'validation_v189.json').unlink(missing_ok=True)
 work=W/'native_work/v189';work.mkdir(parents=True,exist_ok=True)
 base=(W/'game_v188.res').read_bytes();data=(W/'game_v189.res').read_bytes()
 ao,old=decode(base,range(2,86,2));bo,new=decode(data,range(2,86,2));build=json.loads((W/'build_v189.json').read_text(encoding='utf-8'));delta=build['profile_delta']
 assert ao.protos[0].bc==bo.protos[0].bc and base[-10:]==data[-10:]
 changes={int(k):v for k,v in build['changed_original_prototypes'].items()}
 assert changes=={12:[14,283],14:[385,397,632,668,681],30:[39,87]},changes
 for m,d in new.items():
  trees(d);assert d.rebuild()==d.raw and len(d.protos)==len(old[m].protos)+(delta if m==14 else 0)
  for i,q in enumerate(old[m].protos):
   if m==14 and 669<=i<681:continue
   p=d.protos[i+delta if m==14 and i>=681 else i]
   assert (p.raw!=q.raw)==(i in changes.get(m,[])),(m,i)
   assert numeric_and_debug(p)[0]==numeric_and_debug(q)[0],(m,i)
   assert(p.flags,p.params,p.frame,p.nuv,p.uv)==(q.flags,q.params,40 if m==14 and i==397 else 34 if m==14 and i==385 else q.frame,q.nuv,q.uv),(m,i)
  for p in d.protos:
   for pc,ins in enumerate(p.bc):
    if OPS[ins&255]in BRANCHES:assert 0<=pc+1+(ins>>16)-32768<len(p.bc),(m,p.idx,pc)
 p,q=old[12].protos[283],new[12].protos[283]
 assert q.bc==[(i&~0xff00)|(p.frame<<8) if OPS[i&255]=='JMP'and (i>>8&255)<p.frame else i for i in p.bc]
 # Book decoding only uses pre-existing explicit database/native exports.
 p=new[12].protos[14];used={p.gc(i>>16).decode('gbk')for i in p.bc if OPS[i&255]=='GGET'}
 assert used=={p.gc(i>>16).decode('gbk')for i in old[12].protos[14].bc if OPS[i&255]=='GGET'}
 exported={new[14].protos[301].gc((i>>16)&255).decode('gbk')for i in new[14].protos[301].bc if OPS[i&255]=='TSETS'}
 assert {'取随机数','取道具信息_名称'}<=exported
 # Every original item/frame instruction is retained; relocated old jumps are
 # checked for exact destinations, including replacement-fragment originals.
 for idx,key,sizes,offset in [(397,'item_relocations',{int(k):v for k,v in build['item_inserted_blocks'].items()},lambda pc:build['item_inserted_blocks'].get(str(pc),1)-1 if pc in (231,232)else 0),(385,'actor_relocations',{649:14,650:14},lambda pc:13 if pc in (649,650)else 0)]:
  p,q=old[14].protos[idx],new[14].protos[idx];mp={int(k):v for k,v in build[key].items()}
  for pc,ins in enumerate(p.bc):
   at=mp[pc]+offset(pc);expected=ad('MOV',20,26) if idx==397 and pc==230 else ins
   if OPS[ins&255]in BRANCHES:
    low=(ins&65535);low=(low&~0xff00)|(26<<8) if idx==397 and OPS[ins&255]=='JMP'and (ins>>8&255)<26 else low
    expected=low|((mp[pc+1+(ins>>16)-32768]-at-1+32768)<<16)
   assert q.bc[at]==expected,(idx,pc)
 # Original bookstore conversion is an independent reference, executed from
 # its real bytecode (PC1829..1864), with only entry/return test boundaries.
 d=new[12];p=d.protos[37]
 patches={0:jump(0,1829,7),1851:ad('RET0',0,1),1864:ad('RET0',0,1)}
 (work/'bookstore.ljbc').write_bytes(standalone(d,trees(d),37,patches,7))
 extracts=[(14,397,'use'),(14,458,'proxy'),(14,381,'dispatch'),(14,416,'public_get'),(14,13,'public_sys'),(14,403,'drop'),(14,223,'item_info'),(12,14,'drop_event'),(12,37,'item_event'),(12,283,'aux'),(12,126,'role_a'),(12,132,'role_b'),(12,129,'config_a'),(12,134,'config_b'),(12,128,'slots_get'),(34,31,'inventory_class'),(48,25,'add_control'),(48,23,'bind_control'),(14,680+delta,'profile')]
 for m,i,name in extracts:
  d=new[m];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),i))
 d=old[14];(work/'use_old.ljbc').write_bytes(standalone(d,trees(d),397))
 runs=[]
 d=new[14];(work/'profile_only.ljbc').write_bytes(standalone(d,trees(d),680+delta))
 for label,mods in [('old',old),('new',new)]:
  d=mods[14];(work/('frame_'+label+'.ljbc')).write_bytes(standalone(d,trees(d),385))
 for name in ['regression_v189','native_frame_regression_v189','liveness_regression_v189']:
  (work/(name+'.lua')).write_bytes((W/(name+'.lua')).read_text(encoding='utf-8').encode('gbk'))
  for mode in ['normal','hot']:
   r=subprocess.run([runtime,str(work/(name+'.lua')),str(work),mode],capture_output=True,timeout=120)
   (work/(name+'.'+mode+'.log')).write_bytes(r.stdout+r.stderr)
   assert r.returncode==0,(name,mode,r.stdout[-3500:],r.stderr[-2500:])
   output=r.stdout.decode('gbk');assert ('REGRESSION_V189_PASS' if name=='regression_v189'else 'FULL_NATIVE_FRAME_PHASE_PASS' if name=='native_frame_regression_v189'else 'LIVENESS_V189_PASS')in output;print(output,flush=True);runs.append({'mode':mode,'output':output})
 r=subprocess.run(['python3',str(W/'test_v188.py'),'--runtime',runtime],capture_output=True)
 (work/'baseline.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0,(r.stdout[-2000:],r.stderr[-2500:])
 # Re-run the current complete installer and public API integration; earlier
 # tests intentionally retain their historical resource snapshots.
 integration=W/'native_work/v179';d=new[14]
 (integration/'installer179.ljbc').write_bytes(standalone(d,trees(d),681+delta))
 for name in ['diagnostics.lua','integration.lua']:
  for mode in ['normal','hot']:
   r=subprocess.run([runtime,str(integration/name),str(integration),mode],capture_output=True,timeout=90)
   (work/(name+'.'+mode+'.log')).write_bytes(r.stdout+r.stderr);assert r.returncode==0,(name,mode,r.stdout[-2000:],r.stderr[-2000:])
 names=['patch_v189.py','test_v189.py','regression_v189.lua','native_frame_regression_v189.lua','liveness_regression_v189.lua','package_v189.py','profiling_v189.lua','profiling_v189.ljbc','player_changes_v189.json']
 result={'version':'v1.189','all_passed':True,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'runs':runs,'v188_and_prior_regressions_rerun':True,'current_public_sys_integration':True,'all_42_modules_and_non_target_prototypes_verified':True,'full_windows_game_run':False,'incident_control_identity_known':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v189.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');x=a.parse_args();main(str(Path(x.runtime).resolve())if x.runtime else str(ensure_runtime()))
