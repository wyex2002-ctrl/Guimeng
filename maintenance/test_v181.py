from pathlib import Path
import argparse,hashlib,json,subprocess,shutil
from resource_tools import decode
from native_test_utils import trees,standalone
from patch_v139 import ad,jump
from bytecode_relocate import BRANCHES,numeric_and_debug
from ljdis import OPS
from runtime import ensure_runtime
W=Path(__file__).resolve().parent

def main(runtime):
 (W/'validation_v181.json').unlink(missing_ok=True)
 work=W/'native_work/v181';work.mkdir(parents=True,exist_ok=True)
 r=subprocess.run(['python3',str(W/'test_v180.py'),'--runtime',runtime],capture_output=True)
 (work/'baseline.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0,(r.stdout[-1000:],r.stderr)
 before=(W/'game_v180.res').read_bytes();data=(W/'game_v181.res').read_bytes()
 a,old=decode(before,range(2,86,2));b,new=decode(data,range(2,86,2));build=json.loads((W/'build_v181.json').read_text())
 assert a.protos[0].bc==b.protos[0].bc and before[-10:]==data[-10:]
 changes={int(k):v for k,v in build['changed_prototypes'].items()};spec=json.loads((W/'check_removal_v181.json').read_text());exit_rows=[]
 for module,d in new.items():
  trees(d);assert d.rebuild()==d.raw and len(d.protos)==len(old[module].protos)
  assert [i for i,(p,q)in enumerate(zip(old[module].protos,d.protos))if p.raw!=q.raw]==changes.get(module,[])
  for p in d.protos:
   prior=old[module].protos[p.idx]
   assert numeric_and_debug(p)[0]==numeric_and_debug(prior)[0],(module,p.idx,'numeric pool')
   assert (p.flags,p.params,p.frame,p.nuv,p.uv)==(prior.flags,prior.params,prior.frame,prior.nuv,prior.uv)
   for pc,ins in enumerate(p.bc):
    op=OPS[ins&255]
    if op in BRANCHES:assert 0<=pc+1+(ins>>16)-32768<len(p.bc),(module,p.idx,pc)
    if op in ['KSTR','GGET','GSET','FNEW','TDUP','ISEQS','ISNES']:assert ins>>16<p.nkgc
    if op in ['TGETS','TSETS']:
     assert ((ins>>16)&255)<p.nkgc;k=p.gc((ins>>16)&255)
     assert k!='作弊狗'.encode('gbk'),(module,p.idx,pc)
     if k=='结束游戏'.encode('gbk'):
      assert (module==12 and p.idx in spec['normal_exit_prototypes'])or(module==14 and p.idx==301),(module,p.idx,pc)
      exit_rows.append([module,p.idx,pc])
 # The database environment whitelist and core public API are unchanged.
 for m,ids in {14:[13,90,99,339,359,360,416],22:[3,64]}.items():
  for i in ids:assert new[m].protos[i].raw==old[m].protos[i].raw,(m,i)
 for p in (W/'native_work/v180').glob('*.ljbc'):shutil.copy2(p,work/p.name)
 maps=build['relocations']
 def pc(m,i,n):return maps.get(f'{m}:{i}',{}).get(str(n),n)
 def emit(m,i,name,patches=None,params=None,version='new'):
  d=(new if version=='new'else old)[m]
  (work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),i,patches,params))
 for name,i in [('proxy',458)]:
  emit(14,i,name+'_old',version='old');emit(14,i,name+'_new')
 for version in ['old','new']:emit(12,185,'withdraw_'+version,version=version)
 for i in [153,188]:emit(12,i,'quit'+str(i))
 emit(12,189,'settings')
 emit(12,37,'item_event')
 for name,m,i in [('item_copy',14,446),('hack_zb',14,448),('hack_js',14,450),('script_check',14,451),('timer_check',12,291),('resource_check',12,22188)]:emit(m,i,name)
 emit(12,280,'character_check');emit(12,254,'item_check');emit(14,438,'debug_dispatch')
 emit(14,458,'data_protection')
 emit(14,378,'builtin_exports',{0:jump(0,pc(14,378,433),13),pc(14,378,451):ad('RET1',12,2)},13)
 emit(14,378,'sandbox_install',{0:jump(0,pc(14,378,635),6),pc(14,378,647):ad('RET0',0,1)},6)
 emit(14,378,'native_init_old',{79:ad('RET0',0,1)},version='old')
 emit(14,378,'native_init_new',{pc(14,378,79):ad('RET0',0,1)})
 emit(12,193,'generator_new',{0:jump(0,pc(12,193,874),3)})
 emit(12,142,'affix_config_new',{0:jump(0,1238),1248:ad('RET1',2,2)})
 emit(12,191,'currency_new');emit(12,179,'save_new',{0:jump(0,pc(12,179,107),4),pc(12,179,145):ad('RET0',0,1)})
 emit(12,179,'load_daily_new',{0:jump(0,pc(12,179,400),4),pc(12,179,408):ad('RET0',0,1)})
 emit(12,179,'login_refresh',{0:jump(0,pc(12,179,990)),pc(12,179,993):ad('RET0',0,1)})
 # Use original suites with actual CURRENT proxies/currency/config/generator.
 fixture=(W/'systems_regression_v177.lua').read_text()
 fixture=fixture.replace("local config=load('affix_config_new',_G)()", "local config=load('affix_config_new',_G)();eq(config['极品数值']['身体舒适'],0.2)")
 fixture=fixture.replace("eq(gen(t,40,tier),t);eq(t['附加']['条数'],tier)","eq(gen(t,40,tier),t);eq(t['附加']['条数'],tier);eq(rawget(t,'击中回蓝'),nil)")
 fixture=fixture.replace("if kind=='鞋子' then for", "if kind~='鞋子' then eq(rawget(t,'身体舒适'),nil)else eq(rawget(t,'自动回血'),nil);eq(rawget(t,'自动回蓝'),nil);if rawget(t,'身体舒适')then seen[kind]['身体舒适']=true end end\n  if kind=='鞋子' then for")
 fixture=fixture.replace("print('AFFIX_PASS'", "eq(seen['鞋子']['身体舒适'],true,'comfort is reachable on shoes')\nprint('AFFIX_PASS'")
 (work/'systems.lua').write_bytes(fixture.encode('gbk'))
 for src,dest in [('gameplay_regression_v180.lua','gameplay.lua'),('reputation_regression_v179.lua','reputation.lua'),('checks_regression_v181.lua','checks.lua')]:
  (work/dest).write_bytes((W/src).read_text().encode('gbk'))
 runs=[]
 for filename in ['checks.lua','systems.lua','gameplay.lua','reputation.lua']:
  for mode in ['normal','hot']:
   r=subprocess.run([runtime,str(work/filename),str(work),mode],capture_output=True,timeout=120)
   (work/(filename+'.'+mode+'.log')).write_bytes(r.stdout+r.stderr)
   assert r.returncode==0,(filename,mode,r.stdout[-1000:],r.stderr)
   output=r.stdout.decode('gbk');print(output,flush=True);runs.append({'fixture':filename,'mode':mode,'output':output})
 loader=work/'load.lua';loader.write_text('for i=1,#arg do assert(loadfile(arg[i]))end;print("LOAD_PASS")')
 subprocess.run([runtime,str(loader)]+[str(W/f'module_{m}_v181.ljbc')for m in changes],check=True)
 result={'version':'v1.181','all_passed':True,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'runs':runs,'baseline_v180_regressions_passed':True,'changed_prototype_count':sum(map(len,changes.values())),'retained_exit_references':exit_rows,'full_windows_game_run':False}
 result['tested_files']={name:hashlib.sha256((W/name).read_bytes()).hexdigest()for name in ['patch_v181.py','test_v181.py','check_removal_v181.json','checks_regression_v181.lua','bytecode_relocate.py','player_changes_v181.json']}
 (W/'validation_v181.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');args=a.parse_args();main(str(Path(args.runtime).resolve())if args.runtime else str(ensure_runtime()))
