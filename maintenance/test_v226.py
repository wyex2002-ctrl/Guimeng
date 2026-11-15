"""Execute real slot constructor/display and animation wrapper, with finite graphics."""
from test_v225 import *
def main(runtime):
 work=W/'native_work/v226';work.mkdir(parents=True,exist_ok=True)
 _,old=decode((W/'game_v225.res').read_bytes(),range(2,86,2));_,new=decode((W/'game_v226.res').read_bytes(),range(2,86,2))
 build=json.loads((W/'build_v226.json').read_text());expected={int(k):v for k,v in build['changed_prototypes'].items()}
 assert expected[36]==[1]
 for mid,d in new.items():
  trees(d)
  for i,p in enumerate(d.protos):
   assert (p.raw!=old[mid].protos[i].raw)==(i in expected.get(mid,[])),(mid,i)
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc
 for mid,idx,name in [(36,1,'init'),(36,5,'draw'),(16,39,'animation')]:
  d=new[mid];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx))
 (work/'test.lua').write_bytes((W/'cooldown_regression_v226.lua').read_text().encode('gbk'))
 runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'test.lua'),str(work),mode],capture_output=True,timeout=90);out=(r.stdout+r.stderr).decode('gbk','replace');assert r.returncode==0,out;print(out);runs.append(out)
 names=['patch_v226.py','test_v226.py','cooldown_regression_v226.lua','package_v226.py','player_changes_v226.json']
 result={'version':'v1.226','all_passed':True,'sha256':build['sha256'],'runs':runs,'all_42_modules_checked':True,'full_windows_game_run':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v226.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');a=p.parse_args();main(a.runtime or str(ensure_runtime()))
