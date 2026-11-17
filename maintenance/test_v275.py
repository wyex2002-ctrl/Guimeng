from test_v225 import *
from patch_v275 import BASE_SHA
from patch_v139 import encstr,rebuild_proto
from ljtool import Proto

def main(runtime,resume=False,suites=None):
 work=W/'native_work/v275';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v274.res').read_bytes();b=(W/'game_v275.res').read_bytes();assert hashlib.sha256(a).hexdigest()==BASE_SHA
 _,old=decode(a,range(2,86,2));_,new=decode(b,range(2,86,2));build=json.loads((W/'build_v275.json').read_text());ctor=build['constructor'];end=ctor
 for mid,d in new.items():
  trees(d);assert d.rebuild()==d.raw
  before=[p for p in old[mid].protos if mid!=14 or not 729<=p.idx<777]
  after=[p for p in d.protos if mid!=14 or not 729<=p.idx<end]
  assert len(before)==len(after)
  for p,q in zip(before,after):
   restored=Proto(q.raw,q.idx)
   for j,v in enumerate(restored.kgc):
    if not isinstance(v,bytes):continue
    back=v.replace(b'v1.275',b'v1.274')
    if mid==12 and p.idx in [76,22196]:back=back.replace(b'1.275',b'1.274')
    if back!=v:restored.kgc[j]=back;restored.kraw[j]=encstr(back)
   if (mid,p.idx)!=(36,0):assert rebuild_proto(restored)==p.raw,(mid,p.idx,q.idx)
  for p in d.protos:
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,p.idx,pc)
 from selector_trace_v275 import repair,BRANCH
 p=old[36].protos[0];q=new[36].protos[0];fixed,report=repair(p)
 from bytecode_relocate import numeric_and_debug
 assert fixed.raw==q.raw and q.kgc==p.kgc and numeric_and_debug(q)[0]==numeric_and_debug(p)[0] and q.uv==p.uv
 mp={int(k):v for k,v in build['selector_trace']['map'].items()}
 prefixes={1222,1225,1245,1267,1309}
 for pc,x in enumerate(p.bc):
  at=mp[pc]+(1 if pc in prefixes else 0);y=q.bc[at];op=OPS[x&255]
  assert op==OPS[y&255]
  if op in BRANCH:
   assert at+1+(y>>16)-32768==mp[pc+1+(x>>16)-32768],(pc,'original branch destination')
  elif pc<1131:assert x==y,(pc,'original selector instruction')
 assert (p.bc[0]>>8&255)==40 and (q.bc[0]>>8&255)==1
 assert q.nbc==p.nbc+5
 def export(mid,idx,name,patches=None,params=None,baseline=False):
  d=(old if baseline else new)[mid];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx,patches,params))
 for mid,idx,name in [(14,build['exit_at']-1,'watch'),(14,ctor-1,'exit_watch'),(14,13,'readonly'),(14,726,'legacy_diag'),(30,1,'os_exit'),(14,99,'native_quit'),(14,12,'native_error'),(12,154,'save_quit'),(46,7,'projectile_factory'),(46,8,'projectile_register')]:export(mid,idx,name)
 export(14,ctor,'constructor',{0:ad('MOV',0,0),1:jump(1,280,1)},1)
 for mid,idx,name in [(12,126,'role_a'),(12,132,'role_b'),(12,129,'config_a'),(12,134,'config_b'),(12,73,'mode_get'),(12,154,'quit153'),(12,190,'quit188'),(14,167,'timer_factory'),(14,725,'profile_only'),(14,13,'public_sys'),(14,427,'native_frame'),(14,458,'public_get'),(26,55,'hero_skill'),(36,9,'skill_slot'),(36,0,'selector')]:export(mid,idx,name)
 # Resolve the actual S.fun registration, rather than borrowing an index from
 # an older helper layout (the current dispatcher is 423, not the old 420).
 from portal_routes_v213 import child_refs
 refs=child_refs(new[14]);registers={};dispatch=None
 for x in new[14].protos[ctor].bc:
  op=OPS[x&255];reg=(x>>8)&255
  if op=='FNEW':registers[reg]=refs[ctor,x>>16]
  if op=='TSETS'and new[14].protos[ctor].gc((x>>16)&255)==b'fun':dispatch=registers[reg]
 assert dispatch is not None;export(14,dispatch,'dispatch')
 export(36,0,'selector_old',baseline=True)
 export(36,1,'slot_init')
 export(36,1,'slot_init_old',baseline=True)
 export(26,87,'melee_timing')
 export(12,20,'timer_new',{140:ad('RET0',0,1)});export(12,20,'timer_old',{140:ad('RET0',0,1)},baseline=True)
 export(14,ctor,'native_exports',{0:jump(0,280)},1)
 for version in ['old','new']:
  export(14,726,'installer_'+version,baseline=version=='old')
  export(14,777 if version=='old'else ctor,'native_exports_'+version,{0:jump(0,280)},1,baseline=version=='old')
 sources={'watch':(W/'native_watch_regression_v274.lua').read_text(),'skill':(W/'skill_trace_regression_v274.lua').read_text(),'exit':(W/'exit_watch_regression_v270.lua').read_text()}
 sources={k:v.replace('v1.274','v1.275')for k,v in sources.items()}
 sources['exit']=sources['exit'].replace("local wrapper=e.os.exit;", "assert(files['Log/guimeng_exit_latest.txt']:find('Guimeng v1.275 game exit watch | ',1,true));assert(files['Log/guimeng_exit_latest.txt']:match('%d%d%d%d%-%d%d%-%d%d %d%d:%d%d:%d%d'));local wrapper=e.os.exit;")
 # Current save interval is identical in the baseline and diagnostic resource.
 auto=(W/'autosave_regression_v273.lua').read_text().replace("version=='old'and 2 or 8","8")
 auto=auto.replace("load('native_exports',env)","load('native_exports_'..version,env)")
 # Extend the actual full frame at its real actor hooks: finite owned actors
 # clear only their screen entries during update, before unrelated rendering.
 # This covers the newly observed hot continuation failure with party targets,
 # and compares original engine callback order across old/new diagnostics.
 auto=auto.replace('local costs={}', 'local costs={}\nlocal frame_order')
 auto=auto.replace(' for i=1,401 do public.run();elapsed=elapsed+0.1 end', '''
 S.Hero.id=0
 local target={id=101,属性={hp=100},是否有效=true,已经消失=false}
 local party={}
 for index=1,3 do
  local slot=index
  local a={id=index,属性={hp=100},主人id=0,是否有效=true,已经消失=false,远程目标=target,临时焦点触发=op('party.focus')}
  a.更新=function(self)eq(self,a);op('party.update')();S.屏幕事件组[slot]=nil end
  party[index]=a
 end
 for i=1,401 do
  S.Hero.远程目标=i<50 and target or nil
  if i==50 then target.属性.hp=0;target.已经消失=true end
  for j=1,3 do S.屏幕事件组[j]=party[j]end
  public.run();elapsed=elapsed+0.1
 end
 if frame_order then eq(table.concat(events,'|'),frame_order,'full native engine callback order unchanged')else frame_order=table.concat(events,'|')end
''')
 sources['autosave']=auto
 for name in ['target','projectile','selector']:
  file=W/(name+'_trace_regression_v275.lua'if name=='selector'else name+'_trace_regression_v274.lua')
  if file.exists():sources[name]=file.read_text().replace('v1.274','v1.275')
 runs=[]
 for suite,code in sources.items():
  if suites and suite not in suites:continue
  src=work/(suite+'.lua');src.write_bytes(code.encode('gbk'))
  for mode in ['normal','hot']:
   receipt=work/(suite+'.'+mode+'.passed.json');identity={'resource':hashlib.sha256(b).hexdigest(),'source':hashlib.sha256(src.read_bytes()).hexdigest(),'mode':mode}
   if resume and receipt.exists():
    saved=json.loads(receipt.read_text())
    if saved['identity']==identity:runs.append(saved['run']);print('Reuse '+suite+' '+mode,flush=True);continue
   r=subprocess.run([runtime,str(src),str(work),mode],capture_output=True,timeout=120);out=(r.stdout+r.stderr).decode('gbk','replace');print(out,flush=True);(work/(suite+'.'+mode+'.log')).write_text(out);assert r.returncode==0,(suite,mode,out[-5000:])
   run={'suite':suite,'mode':mode,'output':out};runs.append(run);receipt.write_text(json.dumps({'identity':identity,'run':run},ensure_ascii=False))
 if suites:return
 assert set(sources)=={'watch','target','projectile','skill','exit','autosave','selector'}
 names=['patch_v275.py','test_v275.py','package_v275.py','player_changes_v275.json','native_watch_v275.lua','native_watch_v275.ljbc','exit_watch_v275.lua','exit_watch_v275.ljbc','selector_trace_v275.py','selector_trace_regression_v275.lua','native_watch_regression_v274.lua','skill_trace_regression_v274.lua','target_trace_regression_v274.lua','projectile_trace_regression_v274.lua','autosave_regression_v273.lua','exit_watch_regression_v270.lua']
 result={'version':'v1.275','all_passed':True,'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'diagnostic_only':True,'autosave_seconds':5,'sample_seconds':.5,'crash_root_cause_confirmed':False,'all_42_modules_checked':True,'full_windows_game_run':False,'scope':'layered Lua error identity, bounded snapshots and frozen observed target/life/skill/projectile events; actual constructor/read-only public run, original slot->hero->checkpoint/dispatcher, original projectile construction/update/hit/disposal with finite engine/graphics sinks, native frame/autosave and original exit; not client crash reproduction','tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v275.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');p.add_argument('--resume',action='store_true');p.add_argument('--suite',action='append');a=p.parse_args();main(a.runtime or str(ensure_runtime()),a.resume,a.suite)
