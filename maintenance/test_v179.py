from pathlib import Path
import argparse,hashlib,json,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from ljdis import OPS
from bytecode_relocate import BRANCHES
from runtime import ensure_runtime
W=Path(__file__).resolve().parent

def main(runtime):
 base=W/'compile_work/v179_base';data=(W/'game_v179.res').read_bytes();prior=(base/'game_v177.res').read_bytes()
 oldouter,old=decode(prior,range(2,86,2));outer,new=decode(data,range(2,86,2))
 b=json.loads((W/'build_v179.json').read_text());n=b['added_prototypes']
 assert prior[-10:]==data[-10:] and oldouter.protos[0].bc==outer.protos[0].bc
 assert [i for i,(a,c) in enumerate(zip(oldouter.protos[0].kraw,outer.protos[0].kraw)) if a!=c]==sorted([outer.protos[0].nkgc-1-14,outer.protos[0].nkgc-1-22])
 for m,d in new.items():
  trees(d);assert d.rebuild()==d.raw
  for i,p in enumerate(old[m].protos):
   j=i+n if m==14 and i>=645 else i
   if (m==14 and i in [632,645]) or (m==22 and i in [60,61,62,63,109]):continue
   assert p.raw==d.protos[j].raw,(m,i)
  for p in d.protos:
   for pc,ins in enumerate(p.bc):
    op=OPS[ins&255]
    if op in BRANCHES:assert 0<=pc+1+(ins>>16)-32768<len(p.bc)
    if op in ['KSTR','GGET','GSET','FNEW','TDUP','ISEQS','ISNES']:assert ins>>16<p.nkgc
    if op in ['TGETS','TSETS']:assert ((ins>>16)&255)<p.nkgc
 work=W/'native_work/v179';work.mkdir(parents=True,exist_ok=True)
 d=new[14];(work/'installer179.ljbc').write_bytes(standalone(d,trees(d),645+n))
 (work/'diagnostics.lua').write_bytes((W/'diagnostics_regression_v179.lua').read_text().encode('gbk'))
 runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'diagnostics.lua'),str(work),mode],capture_output=True)
  (work/(mode+'.stdout')).write_bytes(r.stdout);(work/(mode+'.stderr')).write_bytes(r.stderr)
  assert r.returncode==0,(r.stdout,r.stderr)
  assert b'DIAGNOSTICS_PASS' in r.stdout;runs.append(r.stdout.decode());print(r.stdout.decode())
 # Every original gameplay prototype is unchanged. Re-execute existing end-to-end bytecode fixtures.
 r=subprocess.run(['python3','test_v177.py','--runtime',runtime],cwd=base,capture_output=True)
 (work/'gameplay.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0,(r.stdout[-1000:],r.stderr)
 # Replace generated death fixture with v1.179; retain original old/currency/spawn primitives.
 import shutil
 for p in (base/'native_work').glob('*.ljbc'):shutil.copy2(p,work/p.name)
 d=new[22];(work/'death_new.ljbc').write_bytes(standalone(d,trees(d),64))
 d=old[22];(work/'death_v177.ljbc').write_bytes(standalone(d,trees(d),64))
 d=old[14]
 for name,index in [('public_sys',13),('public_get',416),('rng_original',90)]:
  (work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),index))
 (work/'reputation.lua').write_bytes((W/'reputation_regression_v179.lua').read_text().encode('gbk'))
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'reputation.lua'),str(work),mode],capture_output=True)
  (work/(mode+'.reputation.log')).write_bytes(r.stdout+r.stderr)
  assert r.returncode==0,(r.stdout[-1000:],r.stderr)
  runs.append(r.stdout.decode());print(r.stdout.decode())
 # Actual event module registration, isolated logger environment, actual public read-only facade/getter.
 d=new[22];(work/'event_root.ljbc').write_bytes(d.raw)
 fixture=(W/'reputation_regression_v179.lua').read_text().split('for reward=1,3 do')[0]
 fixture+='''
local s=make();local files={};local public=s.env.Sys
local env=setmetatable({Sys=s.sys,['核心']={['读入文件']=function()end,['写到文件']=function(p,t)files[p]=t end}}, {__index=_G})
local install=assert(loadfile(work..'/installer179.ljbc'));setfenv(install,env);install(s.sys)
assert(s.sys.__gm_hooks_ready_v179==nil,'installer cannot see event class yet')
local C={};s.env.class=function()return C end
local root=assert(loadfile(work..'/event_root.ljbc'));setfenv(root,setmetatable(s.env,{__index=_G}));root()
assert(s.sys.__gm_hooks_ready_v179,'class must attach via public getter bridge')
s.death=C['死亡'];s.live['属性']['等级']=21;s.roll=2;s.kill(7,42,false)
eq(s.hero['胶布香港'][3],2)
local log=assert(files['Log/guimeng_critical_latest.txt'])
for _,stage in ipairs({'hooks.ready','death.enter','ordinary roll=','award kind=ordinary','death.return'})do assert(log:find(stage,1,true),stage)end
-- Item restoration must not evict combat records from the critical ring.
for i=1,500 do s.sys.__gm_diag_checkpoint_v159('load.restore.item','item')end
assert(files['Log/guimeng_critical_latest.txt']:find('death.enter',1,true))
print('PUBLIC_INTEGRATION_PASS',mode,count)
'''
 (work/'integration.lua').write_bytes(fixture.encode('gbk'))
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'integration.lua'),str(work),mode],capture_output=True)
  assert r.returncode==0,(r.stdout[-1500:],r.stderr)
  runs.append(r.stdout.decode());print(r.stdout.decode())
 result={'version':'v1.179','all_passed':True,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'diagnostics_runs':runs,'gameplay_regressions':json.loads((base/'validation_v177.json').read_text())['runs'],'public_sys_interface_tested':True,'full_windows_game_run':False}
 (W/'validation_v179.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');args=a.parse_args();main(str(Path(args.runtime).resolve()) if args.runtime else str(ensure_runtime()))
