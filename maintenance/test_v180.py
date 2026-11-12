from pathlib import Path
import argparse,json,hashlib,subprocess,shutil
from resource_tools import decode
from native_test_utils import trees,standalone
from bytecode_relocate import BRANCHES
from patch_v139 import ad,jump
from ljdis import OPS
from runtime import ensure_runtime
W=Path(__file__).resolve().parent

def main(runtime):
 # Mandatory baseline and current public-interface/diagnostic regressions.
 r=subprocess.run(['python3',str(W/'test_v179.py'),'--runtime',runtime],capture_output=True)
 work=W/'native_work/v180';work.mkdir(parents=True,exist_ok=True)
 (work/'baseline.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0,(r.stdout[-2000:],r.stderr)
 before=(W/'game_v179.res').read_bytes();data=(W/'game_v180.res').read_bytes()
 a,old=decode(before,range(2,86,2));b,new=decode(data,range(2,86,2));build=json.loads((W/'build_v180.json').read_text())
 assert a.protos[0].bc==b.protos[0].bc and before[-10:]==data[-10:]
 changes={int(k):v for k,v in build['changed_prototypes'].items()}
 for module,d in new.items():
  trees(d);assert d.rebuild()==d.raw;assert len(d.protos)==len(old[module].protos)
  assert [i for i,(p,q) in enumerate(zip(old[module].protos,d.protos)) if p.raw!=q.raw]==changes.get(module,[]),(module,changes)
  for p in d.protos:
   for pc,ins in enumerate(p.bc):
    op=OPS[ins&255]
    if op in BRANCHES:assert 0<=pc+1+(ins>>16)-32768<len(p.bc)
    if op in ['KSTR','GGET','GSET','FNEW','TDUP','ISEQS','ISNES']:assert ins>>16<p.nkgc
    if op in ['TGETS','TSETS']:assert ((ins>>16)&255)<p.nkgc
 for p in (W/'native_work/v179').glob('*.ljbc'):shutil.copy2(p,work/p.name)
 def emit(d,name,index,patches=None,params=None):
  (work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),index,patches,params))
 for label,mods in [('old',old),('new',new)]:
  d=mods[12];emit(d,'ui_'+label,76);emit(d,'init_'+label,18526)
 d=new[12]
 emit(d,'register_pre',142,{0:jump(0,209),213:ad('RET0',0,1)},2)
 emit(d,'register_next',142,{0:jump(0,688),692:ad('RET0',0,1)},2)
 emit(d,'register_accuracy',292,{0:jump(0,90),93:ad('RET0',0,1)})
 emit(d,'learn_refresh',200,{0:jump(0,455),458:ad('RET0',0,1)})
 emit(d,'login_refresh',179,{0:jump(0,990),993:ad('RET0',0,1)})
 emit(d,'generator_new',193,{0:jump(0,874,3)})
 (work/'gameplay.lua').write_bytes((W/'gameplay_regression_v180.lua').read_text(encoding='utf-8').encode('gbk'))
 # Existing 10-slot / 3..7 affix generator regression, strengthened to exclude mana-on-hit everywhere.
 fixture=(W/'systems_regression_v177.lua').read_text(encoding='utf-8')
 fixture=fixture.replace("eq(gen(t,40,tier),t);eq(t['附加']['条数'],tier)","eq(gen(t,40,tier),t);eq(t['附加']['条数'],tier);eq(rawget(t,'击中回蓝'),nil,'new equipment excludes mana-on-hit')")
 (work/'systems.lua').write_bytes(fixture.encode('gbk'))
 runs=[]
 for filename in ['gameplay.lua','systems.lua']:
  for mode in ['normal','hot']:
   r=subprocess.run([runtime,str(work/filename),str(work),mode],capture_output=True,timeout=120)
   (work/(filename+'.'+mode+'.log')).write_bytes(r.stdout+r.stderr)
   assert r.returncode==0,(filename,mode,r.stdout[-1500:],r.stderr)
   assert b'PASS\t'+mode.encode() in r.stdout
   output=r.stdout.decode('gbk');print(output,flush=True);runs.append({'fixture':filename,'mode':mode,'output':output})
 # Ensure the changed module and skill description load in the official runtime.
 loader=work/'load.lua';loader.write_text('for i=1,#arg do assert(loadfile(arg[i]))end;print("LOAD_PASS")')
 subprocess.run([runtime,str(loader)]+[str(W/f'module_{m}_v180.ljbc') for m in changes],check=True)
 result={'version':'v1.180','all_passed':True,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'runs':runs,'v179_regressions_passed':True,'full_windows_game_run':False}
 (W/'validation_v180.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');args=a.parse_args();main(str(Path(args.runtime).resolve()) if args.runtime else str(ensure_runtime()))
