from test_v225 import *
from patch_v262 import BASE_SHA

def main(runtime):
 work=W/'native_work/v262';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v261.res').read_bytes();b=(W/'game_v262.res').read_bytes();assert hashlib.sha256(a).hexdigest()==BASE_SHA
 _,old=decode(a,range(2,86,2));_,new=decode(b,range(2,86,2));build=json.loads((W/'build_v262.json').read_text());cnt=build['merc_helper_count']
 expected={12:{76,22196},14:{653,689,705},22:{89,97},30:{39,87}}
 for mid,d in new.items():
  trees(d);assert d.rebuild()==d.raw
  pre=[p for p in old[mid].protos if mid!=14 or not 399<=p.idx<418];post=[p for p in d.protos if mid!=14 or not 399<=p.idx<399+cnt]
  assert len(pre)==len(post);assert {i for i,(p,q)in enumerate(zip(pre,post))if p.raw!=q.raw}==expected.get(mid,set()),mid
  for p in d.protos:
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc
 for idx in [89,97]:
  p,q=old[22].protos[idx],new[22].protos[idx];mp={int(k):v for k,v in build['pose_maps'][str(idx)].items()}
  for pc,x in enumerate(p.bc):
   at=mp[pc]+(4 if idx==89 else 3)if pc==0 else mp[pc];y=q.bc[at]
   if OPS[x&255]in BRANCHES:assert y&65535==x&65535 and at+1+(y>>16)-32768==mp[pc+1+(x>>16)-32768]
   else:assert x==y,(idx,pc)
 def export(d,idx,name,patches=None): (work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx,patches))
 for label,mods in [('old',old),('new',new)]:
  export(mods[22],121,'class_'+label)
  export(mods[22],35,'finish_'+label,{0:ad('KSHORT',1,0),1:jump(1,672,2),748:ad('RET0',0,1),884:ad('RET0',0,1)})
 export(new[20],8,'anim_update');export(new[20],6,'anim_reverse');export(new[20],21,'anim_reset')
 (work/'mode.ljbc').write_bytes((W/'merc_mode_v262.ljbc').read_bytes())
 src=work/'wait.lua';src.write_bytes((W/'party_wait_regression_v262.lua').read_text().encode('gbk'));runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(src),str(work),mode],capture_output=True,timeout=90);out=(r.stdout+r.stderr).decode('gbk','replace');print(out,flush=True);(work/(mode+'.log')).write_text(out);assert r.returncode==0,(mode,out[-5000:]);runs.append({'mode':mode,'output':out})
 names=['patch_v262.py','test_v262.py','package_v262.py','player_changes_v262.json','merc_mode_v262.lua','merc_mode_v262.ljbc','party_wait_regression_v262.lua']
 report={'version':'v1.262','all_passed':True,'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'all_42_modules_checked':True,'historical_suites_rerun':False,'full_windows_game_run':False,'scope':'actual event class methods, native attack-finish branch and motion/state/reset plus original20 animation update; finite actions, render sinks and event monitoring; party ownership and safe fallback cases; attack/skill/AI code otherwise byte-identical; not complete original frame or Windows visual test','tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v262.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');a=p.parse_args();main(a.runtime or str(ensure_runtime()))
