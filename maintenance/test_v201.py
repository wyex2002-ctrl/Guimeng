"""Focused actual bytecode/configuration regression for the beast range change."""
from pathlib import Path
import argparse,hashlib,json,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from patch_v201 import CONFIGS,unpack_config,pack_config
from patch_v139 import ad,jump
from bytecode_relocate import numeric_and_debug
from runtime import ensure_runtime
from test_v192 import lua
W=Path(__file__).resolve().parent

def main(runtime):
 (W/'validation_v201.json').unlink(missing_ok=True);work=W/'native_work/v201';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v200.res').read_bytes();b=(W/'game_v201.res').read_bytes();ao,old=decode(a,range(2,86,2));bo,new=decode(b,range(2,86,2))
 expected={12:[76,6464,6466,22187],14:[632,668,684],30:[39,87]}
 assert ao.protos[0].bc==bo.protos[0].bc and a[-10:]==b[-10:]
 for m,d in new.items():
  assert d.rebuild()==d.raw and len(d.protos)==len(old[m].protos)
  for i,(p,q)in enumerate(zip(d.protos,old[m].protos)):
   assert(p.raw!=q.raw)==(i in expected.get(m,[])),(m,i)
   assert p.bc==q.bc and p.uv==q.uv and (p.params,p.frame,p.nkn,p.nkgc)==(q.params,q.frame,q.nkn,q.nkgc),(m,i)
   assert numeric_and_debug(p)==numeric_and_debug(q),(m,i)
   if i in expected.get(m,[]) and not(m==12 and i in CONFIGS):
    for logical in range(p.nkgc):
     v=q.gc(logical);wanted=v
     if isinstance(v,bytes):
      wanted=v.replace(b'Guimeng patch v1.200',b'Guimeng patch v1.201').replace(b'Guimeng v1.200 diagnostics',b'Guimeng v1.201 diagnostics').replace(b'patch=v1.200',b'patch=v1.201')
      if m==12 and i in [76,22187]:
       if v==b'1.200':wanted=b'1.201'
       if v=='魔改版 1.200'.encode('gbk'):wanted='魔改版 1.201'.encode('gbk')
     assert p.gc(logical)==wanted,(m,i,logical)
   if i not in CONFIGS or m!=12:continue
   for logical in range(p.nkgc):
    if logical not in CONFIGS[i]:assert p.gc(logical)==q.gc(logical)
 configs={}
 for index,entries in CONFIGS.items():
  for logical,name in entries.items():
   before=unpack_config(old[12].protos[index].gc(logical));after=unpack_config(new[12].protos[index].gc(logical))
   key=('施法距离'if index==6464 else'攻击距离').encode('gbk')
   assert after==before.replace(key+b'=1\r\n',key+b'=2\r\n')
   assert pack_config(after)==new[12].protos[index].gc(logical)
   configs[name.encode('gbk')]={b'old':before,b'new':after}
 # The only two map-event templates using the three changed attacks are the
 # summoned beasts. All other monster definitions, AI, skills and formulas stay exact.
 bindings=[]
 for k in new[12].protos[18520].kgc:
  if isinstance(k,bytes)and k.startswith(b'4BD5'):
   body=unpack_config(k)
   if any(('绑定技能='+n+'\r\n').encode('gbk')in body for n in CONFIGS[6464].values()):
    lines=dict(s.split(b'=',1)for s in body.split(b'\r\n')if b'='in s);bindings.append((int(lines['事件标识'.encode('gbk')]),lines['绑定属性'.encode('gbk')].decode('gbk')))
 assert sorted(bindings)==[(1109,'神兽'),(1363,'超强神兽')]
 (work/'configs.lua').write_bytes(('return '+lua(configs)).encode('gbk'))
 exports=[(12,4091,'skill_factory'),(12,6465,'attr_factory'),(12,240,'upgrade'),(12,425,'transform'),(12,239,'control'),(12,4498,'new_4498'),(12,17206,'death'),(12,17218,'destroy'),(12,5086,'formula'),(22,72,'attack_ai'),(22,73,'pursue'),(22,47,'start_attack'),(30,80,'distance'),(30,81,'range'),(30,97,'helix'),(30,43,'rotate')]
 for m,i,name in exports:(work/f'{name}.ljbc').write_bytes(standalone(new[m],trees(new[m]),i))
 (work/'sandbox_install.ljbc').write_bytes(standalone(new[14],trees(new[14]),378,{0:jump(0,597,13),609:ad('RET0',0,1)}))
 # Reuse only the explicit finite summon scene setup, not the old historical suite.
 prefix=(W/'summon_regression_v195.lua').read_text().split('-- Baseline control:')[0]
 prefix=prefix.replace("local attr={['名称']=kind or '租赁怪物',['附加']={}}", "local attr=copy(beast_attributes[enhanced and '超强神兽' or '神兽']);attr['名称']=kind or '租赁怪物';attr['附加']={}")
 prefix=prefix[prefix.index('local skeleton,beast='):]
 source=(W/'beast_range_regression_v201.lua').read_text().replace('-- INSERT_SUMMON_SCENE',prefix)
 (work/'range.lua').write_bytes(source.encode('gbk'));runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'range.lua'),str(work),mode],capture_output=True,timeout=60);(work/(mode+'.log')).write_bytes(r.stdout+r.stderr)
  assert r.returncode==0,(r.stdout+r.stderr).decode('gbk','replace')[-2500:]
  output=r.stdout.decode('gbk');assert 'BEAST_RANGE_V201_PASS'in output;print(output,flush=True);runs.append({'mode':mode,'output':output})
 names=['patch_v201.py','test_v201.py','beast_range_regression_v201.lua','summon_regression_v195.lua','package_v201.py','player_changes_v201.json']
 result={'version':'v1.201','all_passed':True,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'test_scope':'actual_config_factories_range_AI_attack_start_formula_upgrade_transform_and_resummon','historical_suites_rerun':False,'full_windows_game_run':False,'real_map_obstacles_tested':False,'full_damage_tick_tested':False,'save_reload_tested':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v201.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');x=a.parse_args();main(str(Path(x.runtime).resolve())if x.runtime else str(ensure_runtime()))
