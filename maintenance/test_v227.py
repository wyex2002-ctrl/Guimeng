"""Execute real slot constructor/display and animation wrapper, with finite graphics."""
from test_v225 import *
def main(runtime):
 work=W/'native_work/v227';work.mkdir(parents=True,exist_ok=True)
 _,old=decode((W/'game_v226.res').read_bytes(),range(2,86,2));_,new=decode((W/'game_v227.res').read_bytes(),range(2,86,2))
 build=json.loads((W/'build_v227.json').read_text());expected={int(k):v for k,v in build['changed_prototypes'].items()}
 assert expected[36]==[1,5,10,11]
 for mid,d in new.items():
  trees(d)
  for i,p in enumerate(d.protos):
   if not(mid==36 and i==11):
    oi=i-(1 if mid==36 and i>=12 else 0)
    assert (p.raw!=old[mid].protos[oi].raw)==(oi in expected.get(mid,[])),(mid,i)
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc
 from patch_v201 import unpack_config
 from test_v192 import lua
 import re
 cfg={};p=new[12].protos[6464];name=None;rows=[]
 for x in p.bc:
  if OPS[x&255]=='KSTR':
   a=(x>>8)&255;v=p.gc(x>>16)
   if a==4:name=v
   if a==7 and isinstance(v,bytes)and v.endswith(b'*'):
    cfg[name]=unpack_config(v)
    cd=re.search(rb'^'+ '冷却时间'.encode('gbk')+rb'=(.*)',cfg[name],re.M)
    rows.append({'name':name.decode('gbk'),'base_cd':cd[1].strip().decode()if cd else None})
 (W/'cooldown_audit_v227.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 (work/'configs.lua').write_bytes(('return '+lua(cfg)).encode('gbk'));(work/'scripts.lua').write_bytes(b'return {}')
 for mid,idx,name in [(26,88,'class_new'),(20,8,'animation'),(20,6,'reverse'),(20,21,'reset'),(12,4091,'skill_factory'),(30,43,'rotate'),(36,12,'slot_class'),(16,39,'cd_factory'),(16,73,'sprite_factory'),(14,416,'getter'),(14,13,'readonly')]:
  d=new[mid];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx))
 d=new[26];(work/'tick_new.ljbc').write_bytes(standalone(d,trees(d),3,{0:jump(0,839,3),848:ad('RET0',0,1)}))
 prefix=(W/'melee_regression_v210.lua').read_text().split("local melee={'普通攻击'")[0]
 (work/'test.lua').write_bytes((prefix+(W/'cooldown_regression_v227.lua').read_text()).encode('gbk'))
 runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'test.lua'),str(work),mode],capture_output=True,timeout=90);out=(r.stdout+r.stderr).decode('gbk','replace');assert r.returncode==0,out;print(out);runs.append(out)
 names=['patch_v227.py','test_v227.py','cooldown_regression_v227.lua','package_v227.py','player_changes_v227.json','cooldown_mask_v227.lua','cooldown_mask_v227.ljbc','cooldown_audit_v227.json']
 result={'version':'v1.227','all_passed':True,'sha256':build['sha256'],'runs':runs,'all_42_modules_checked':True,'full_windows_game_run':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v227.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');a=p.parse_args();main(a.runtime or str(ensure_runtime()))
