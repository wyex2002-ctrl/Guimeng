from pathlib import Path
import argparse,hashlib,json,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from ljdis import OPS
from bytecode_relocate import BRANCHES
W=Path(__file__).resolve().parent

def main(runtime):
 base=W/'compile_work/v178_base';data=(W/'game_v178.res').read_bytes();prior=(base/'game_v177.res').read_bytes()
 oldouter,old=decode(prior,range(2,86,2));outer,new=decode(data,range(2,86,2))
 b=json.loads((W/'build_v178.json').read_text());n=b['added_prototypes']
 assert prior[-10:]==data[-10:] and oldouter.protos[0].bc==outer.protos[0].bc
 assert [i for i,(a,c) in enumerate(zip(oldouter.protos[0].kraw,outer.protos[0].kraw)) if a!=c]==[outer.protos[0].nkgc-1-14]
 for m,d in new.items():
  trees(d);assert d.rebuild()==d.raw
  for i,p in enumerate(old[m].protos):
   j=i+n if m==14 and i>=645 else i
   if m==14 and i==645:continue
   assert p.raw==d.protos[j].raw,(m,i)
  for p in d.protos:
   for pc,ins in enumerate(p.bc):
    op=OPS[ins&255]
    if op in BRANCHES:assert 0<=pc+1+(ins>>16)-32768<len(p.bc)
    if op in ['KSTR','GGET','GSET','FNEW','TDUP','ISEQS','ISNES']:assert ins>>16<p.nkgc
    if op in ['TGETS','TSETS']:assert ((ins>>16)&255)<p.nkgc
 work=W/'native_work/v178';work.mkdir(parents=True,exist_ok=True)
 d=new[14];(work/'installer178.ljbc').write_bytes(standalone(d,trees(d),645+n))
 (work/'diagnostics.lua').write_bytes((W/'diagnostics_regression_v178.lua').read_text().encode('gbk'))
 runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'diagnostics.lua'),str(work),mode],capture_output=True)
  (work/(mode+'.stdout')).write_bytes(r.stdout);(work/(mode+'.stderr')).write_bytes(r.stderr)
  assert r.returncode==0,(r.stdout,r.stderr)
  assert b'DIAGNOSTICS_PASS' in r.stdout;runs.append(r.stdout.decode());print(r.stdout.decode())
 # Every original gameplay prototype is unchanged. Re-execute existing end-to-end bytecode fixtures.
 r=subprocess.run(['python3','test_v177.py','--runtime',runtime],cwd=base,capture_output=True)
 (work/'gameplay.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0,(r.stdout[-1000:],r.stderr)
 # Exercise actual v1.177 death/reputation bytecode through the newly installed hooks.
 fixture=(W/'reputation_regression_v177.lua').read_text().split('for reward=1,3 do')[0]
 fixture+='''
local s=make();local files={}
local C={['死亡']=s.death,['发生伤害']=function()end,['事件回调']=function()end}
local env=setmetatable({Sys=s.sys,['类_事件']=C,['核心']={['读入文件']=function()end,['写到文件']=function(p,t)files[p]=t end}},{__index=_G})
local install=assert(loadfile(arg[3]..'/installer178.ljbc'));setfenv(install,env);install(s.sys)
s.death=C['死亡'];s.live['属性']['等级']=21;s.chance=1;s.roll=2
s.kill(7,42,false)
eq(s.hero['胶布香港'][3],2)
local log=assert(files['Log/guimeng_critical_latest.txt'])
assert(log:find('death.enter',1,true));assert(log:find('ordinary roll=',1,true))
assert(log:find('award kind=ordinary',1,true));assert(log:find('death.return',1,true))
print('INTEGRATION_PASS',mode,count)
'''
 (work/'integration.lua').write_bytes(fixture.encode('gbk'))
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'integration.lua'),str(base/'native_work'),mode,str(work)],capture_output=True)
  assert r.returncode==0,(r.stdout,r.stderr)
  runs.append(r.stdout.decode());print(r.stdout.decode())
 result={'version':'v1.178','all_passed':True,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'diagnostics_runs':runs,'gameplay_regressions':json.loads((base/'validation_v177.json').read_text())['runs'],'only_original_installer_changed':True,'full_windows_game_run':False}
 (W/'validation_v178.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime',required=True);main(a.parse_args().runtime)
