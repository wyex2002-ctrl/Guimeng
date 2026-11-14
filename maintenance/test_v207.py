"""Current full dead storage, hero-only dead claims and legacy pending migration."""
from pathlib import Path
import argparse,hashlib,json,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from patch_v139 import ad,jump
from runtime import ensure_runtime
from ljdis import OPS
W=Path(__file__).resolve().parent

def main(runtime):
 (W/'validation_v207.json').unlink(missing_ok=True);work=W/'native_work/v207';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v206.res').read_bytes();b=(W/'game_v207.res').read_bytes();ao,old=decode(a,range(2,86,2));bo,new=decode(b,range(2,86,2));build=json.loads((W/'build_v207.json').read_text())
 expected={12:[36,76,257,258,22187],14:[632,668,684],30:[39,87]}
 assert ao.protos[0].bc==bo.protos[0].bc and a[-10:]==b[-10:]
 for m,d in new.items():
  assert d.rebuild()==d.raw and len(d.protos)==len(old[m].protos)
  for i,(p,q)in enumerate(zip(d.protos,old[m].protos)):
   assert(p.raw!=q.raw)==(i in expected.get(m,[])),(m,i)
   assert p.params==q.params and p.uv==q.uv,(m,i)
   if i not in [35,36,256,257,258,261]or m!=12:assert p.bc==q.bc,(m,i)
 for label,mods in [('old',old),('new',new)]:
  d=mods[12];(work/f'item_event_{label}.ljbc').write_bytes(standalone(d,trees(d),37));(work/f'register_{label}.ljbc').write_bytes(standalone(d,trees(d),292,{0:jump(0,156,2),159:ad('RET0',0,1)}))
 for m,i,n in[(14,458,'proxy'),(14,416,'public_get'),(14,13,'public_sys'),(14,224,'export_item'),(14,220,'entity'),(12,126,'role_a'),(12,132,'role_b'),(12,129,'config_a'),(12,134,'config_b'),(12,128,'slots_get'),(12,37,'item_event'),(12,257,'ling'),(22,43,'merc_exp'),(34,3,'grid_use')]:
  d=new[m];(work/f'{n}.ljbc').write_bytes(standalone(d,trees(d),i))
 d=new[12];p=d.protos[261];mp={int(k):v for k,v in build['spawn_relocations'].items()}
 (work/'mark_deployed.ljbc').write_bytes(standalone(d,trees(d),261,{0:jump(0,mp[581],4),mp[581]+3:ad('RET0',0,1)},params=4))
 (work/'restore_flush.ljbc').write_bytes(standalone(d,trees(d),261,{0:jump(0,mp[623],4),mp[628]+7:ad('RET0',0,1)},params=4))
 d=new[30];(work/'table_register.ljbc').write_bytes(standalone(d,trees(d),193,{0:jump(0,33),42:jump(42,57),69:ad('RET0',0,1)}))
 p=new[12].protos[4090];config={}
 for name,pc in [('小',58915),('中',59015),('大',59115),('特',102115)]:config[name]=p.gc(p.bc[pc]>>16).decode('gbk')
 (work/'configs.lua').write_bytes(('return {'+','.join("['"+k+"']='"+v+"'"for k,v in config.items())+'}').encode('gbk'))
 (work/'talisman.lua').write_bytes((W/'talisman_dead_regression_v207.lua').read_text().encode('gbk'));runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'talisman.lua'),str(work),mode],capture_output=True,timeout=60);output=(r.stdout+r.stderr).decode('gbk','replace');(work/(mode+'.log')).write_bytes(r.stdout+r.stderr)
  assert r.returncode==0 and 'TALISMAN_V207_PASS'in output,output[-3500:]
  print(output,flush=True);runs.append({'mode':mode,'output':output})
 names=['patch_v207.py','test_v207.py','talisman_dead_v207.lua','talisman_dead_v207.ljbc','talisman_dead_regression_v207.lua','package_v207.py','player_changes_v207.json']
 result={'version':'v1.207','all_passed':True,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'test_scope':'current_normal_XP_recursion_public_entity_claim_pending_and_spawn_restore_fragments','historical_suites_rerun':False,'full_windows_game_run':False,'full_client_save_load':False,'full_spawn_client_run':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v207.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');x=a.parse_args();main(str(Path(x.runtime).resolve())if x.runtime else str(ensure_runtime()))
