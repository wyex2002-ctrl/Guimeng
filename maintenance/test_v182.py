from pathlib import Path
import argparse,hashlib,json,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from patch_v139 import ad,jump
from bytecode_relocate import BRANCHES,numeric_and_debug
from ljdis import OPS
from runtime import ensure_runtime
W=Path(__file__).resolve().parent

def main(runtime):
 (W/'validation_v182.json').unlink(missing_ok=True)
 work=W/'native_work/v182';work.mkdir(parents=True,exist_ok=True)
 base=(W/'game_v181.res').read_bytes();data=(W/'game_v182.res').read_bytes()
 ao,old=decode(base,range(2,86,2));bo,new=decode(data,range(2,86,2));build=json.loads((W/'build_v182.json').read_text())
 changes={int(k):v for k,v in build['changed_prototypes'].items()}
 assert ao.protos[0].bc==bo.protos[0].bc and base[-10:]==data[-10:]
 for m,d in new.items():
  trees(d);assert d.rebuild()==d.raw and len(d.protos)==len(old[m].protos)
  assert [i for i,(p,q)in enumerate(zip(old[m].protos,d.protos))if p.raw!=q.raw]==changes.get(m,[])
  for p in d.protos:
   q=old[m].protos[p.idx];assert numeric_and_debug(p)[0]==numeric_and_debug(q)[0]
   assert (p.flags,p.params,p.frame,p.nuv,p.uv)==(q.flags,q.params,q.frame,q.nuv,q.uv)
   for pc,ins in enumerate(p.bc):
    op=OPS[ins&255]
    if op in BRANCHES:assert 0<=pc+1+(ins>>16)-32768<len(p.bc),(m,p.idx,pc)
    if op in ['KSTR','GGET','GSET','FNEW','TDUP','ISEQS','ISNES']:assert ins>>16<p.nkgc
    if op in ['TGETS','TSETS']:assert ((ins>>16)&255)<p.nkgc
 # Actual original registration, original copy subtree, actual native hero init.
 def emit(d,index,name,patches=None):
  (work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),index,patches))
 for label,mods in [('old',old),('new',new)]:
  emit(mods[30],193,'table_register_'+label,{0:jump(0,33),42:jump(42,57),69:ad('RET0',0,1)})
  emit(mods[12],4,'global_proxy_'+label)
 emit(new[14],458,'data_proxy')
 # Stop only before rendering/skill setup, after the complete startup copy and
 # attribute assignment which failed in the client's native constructor.
 emit(new[26],0,'hero_init',{212:ad('RET0',0,1)})
 emit(new[26],0,'hero_defaults',{133:ad('RET0',0,1)})
 (work/'startup.lua').write_bytes((W/'startup_regression_v182.lua').read_text().encode('gbk'))
 runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'startup.lua'),str(work),mode],capture_output=True,timeout=90)
  (work/(mode+'.startup.log')).write_bytes(r.stdout+r.stderr)
  assert r.returncode==0,(mode,r.stdout[-1000:],r.stderr)
  assert b'V181_STARTUP_REPRODUCED' in r.stdout and b'STARTUP_AND_TABLE_PASS' in r.stdout
  output=r.stdout.decode('gbk');print(output,flush=True);runs.append({'mode':mode,'output':output})
 # The prior gameplay and public-interface regressions are rerun this turn.
 r=subprocess.run(['python3',str(W/'test_v181.py'),'--runtime',runtime],capture_output=True)
 (work/'baseline.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0,(r.stdout[-1000:],r.stderr)
 for m in changes:
  loader=work/'load.lua';loader.write_text('for i=1,#arg do assert(loadfile(arg[i]))end;print("LOAD_PASS")')
  subprocess.run([runtime,str(loader),str(W/f'module_{m}_v182.ljbc')],check=True)
 # There must be no remaining executable checksum operations in these helpers.
 for m,index in [(12,2),(12,3),(30,9),(30,12),(30,22),(30,23)]:
  p=new[m].protos[index]
  for ins in p.bc:
   if OPS[ins&255] in ['GGET','TGETS']:
    k=p.gc(ins>>16 if OPS[ins&255]=='GGET'else(ins>>16)&255)
    assert k not in [b'reverse',b'check',b'debug_msg'],(m,index,k)
 # Constructor may capture string.reverse for the unchanged closure ABI, but
 # no checker uses it (constructor PC20 is unused local binding only).
 result={'version':'v1.182','all_passed':True,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'startup_runs':runs,'v181_regressions_rerun':True,'rules_changed':False,'full_windows_game_run':False}
 names=['patch_v182.py','test_v182.py','startup_regression_v182.lua','bytecode_relocate.py','player_changes_v182.json']
 result['tested_files']={n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}
 (W/'validation_v182.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');x=a.parse_args();main(str(Path(x.runtime).resolve())if x.runtime else str(ensure_runtime()))
