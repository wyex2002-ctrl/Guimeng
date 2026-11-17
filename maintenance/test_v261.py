from test_v225 import *
from patch_v261 import BASE_SHA

def main(runtime):
 work=W/'native_work/v261';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v260.res').read_bytes();b=(W/'game_v261.res').read_bytes();assert hashlib.sha256(a).hexdigest()==BASE_SHA
 _,old=decode(a,range(2,86,2));_,new=decode(b,range(2,86,2))
 expected={12:{52,76,22196},14:{672,708,724},30:{39,87}}
 for mid,d in new.items():
  trees(d);assert d.rebuild()==d.raw and len(d.protos)==len(old[mid].protos)
  changes={i for i,(p,q)in enumerate(zip(d.protos,old[mid].protos))if p.raw!=q.raw};assert changes==expected.get(mid,set()),(mid,changes)
  for p in d.protos:
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc
 p,q=old[12].protos[52],new[12].protos[52]
 assert(p.params,p.frame,p.uv,p.kgc)==(q.params,q.frame,q.uv,q.kgc)
 from bytecode_relocate import numeric_and_debug
 assert numeric_and_debug(p)==numeric_and_debug(q)
 assert[(i,x,y)for i,(x,y)in enumerate(zip(p.bc,q.bc))if x!=y]==[(370,ad('ISNEN',0,25),ad('ISNEN',0,29)),(469,ad('ISNEN',0,29),jump(469,501,2))]
 for label,mods in [('old',old),('new',new)]:
  d=mods[12];(work/(label+'.ljbc')).write_bytes(standalone(d,trees(d),53))
 d=new[12];(work/'counter.ljbc').write_bytes(standalone(d,trees(d),286))
 (work/'settings.ljbc').write_bytes(standalone(d,trees(d),177,{0:jump(0,166,3),169:ad('RET0',0,1)}))
 src=work/'tab.lua';src.write_bytes((W/'tab_retaliation_regression_v261.lua').read_text().encode('gbk'));runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(src),str(work),mode],capture_output=True,timeout=90);out=(r.stdout+r.stderr).decode('gbk','replace');print(out,flush=True);(work/(mode+'.log')).write_text(out);assert r.returncode==0,(mode,out[-4000:]);runs.append({'mode':mode,'output':out})
 names=['patch_v261.py','test_v261.py','tab_retaliation_regression_v261.lua','package_v261.py','player_changes_v261.json']
 report={'version':'v1.261','all_passed':True,'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'all_42_modules_checked':True,'historical_suites_rerun':False,'full_windows_game_run':False,'scope':'actual key event factory/complete Main, previous Tab negative control and former F branch comparison, original checkbox/settings semantics, original counterattack target callback; finite window/control/message/event/FX interfaces; original prequel key behavior preserved; not full Windows input or combat','tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v261.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');a=p.parse_args();main(a.runtime or str(ensure_runtime()))
