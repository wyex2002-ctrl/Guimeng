"""Actual title, item tooltip, font alias and ground-name style regression."""
from pathlib import Path
import argparse,hashlib,json,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from bytecode_relocate import BRANCHES
from patch_v139 import ad,jump
from patch_v196 import number_pool
from ljdis import OPS
from test_v192 import lua
from runtime import ensure_runtime
W=Path(__file__).resolve().parent

def main(runtime):
 (W/'validation_v200.json').unlink(missing_ok=True);work=W/'native_work/v200';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v199.res').read_bytes();b=(W/'game_v200.res').read_bytes();ao,old=decode(a,range(2,86,2));bo,new=decode(b,range(2,86,2));report=json.loads((W/'build_v200.json').read_text())
 changes={int(k):v for k,v in report['changed_prototypes'].items()};assert changes=={12:[76,193,299,22187],14:[632,668,684],30:[39,87],52:[2],76:[0]}
 assert ao.protos[0].bc==bo.protos[0].bc and a[-10:]==b[-10:]
 for m,d in new.items():
  assert d.rebuild()==d.raw and len(d.protos)==len(old[m].protos)+(m==52)
  for i,q in enumerate(old[m].protos):
   p=d.protos[i+(m==52 and i>=2)]
   assert(p.raw!=q.raw)==(i in changes.get(m,[])),(m,i)
   assert(p.params,p.frame,p.uv)==(q.params,q.frame,q.uv)
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(m,i,pc)
 # Color changes are confined to exactly the seven-affix numeric slots.
 for m,i,index in[(12,193,24),(12,299,1),(76,0,13)]:
  before=number_pool(old[m].protos[i]);after=number_pool(new[m].protos[i]);assert after[:index]==before[:index]and after[index+1:len(before)]==before[index+1:]
  assert after[index]==0xffffe6a3
 assert old[12].protos[193].bc==new[12].protos[193].bc
 assert old[52].protos[1].bc==new[52].protos[2].bc and number_pool(new[52].protos[2])==[0xff4a2c12]
 for label,mods in [('old',old),('new',new)]:
  for m,i,n in[(12,300,'tip'),(12,193,'gen'),(52,2 if label=='old'else 3,'font'),(76,0,'ground')]:
   d=mods[m];patch={0:jump(0,681,5)}if n=='gen'else{0:jump(0,441,17)}if n=='ground'else None
   (work/f'{n}_{label}.ljbc').write_bytes(standalone(d,trees(d),i,patch))
 for m,i,n in[(12,76,'ui'),(14,299,'window_setter'),(52,0,'parser'),(14,458,'proxy'),(14,223,'item_info')]:
  d=new[m];(work/f'{n}.ljbc').write_bytes(standalone(d,trees(d),i))
 d=new[12];(work/'config.ljbc').write_bytes(standalone(d,trees(d),142,{0:jump(0,1238),1248:ad('RET1',2,2)}))
 p=d.protos[4090];pc=13670;t=dict(p.gc(p.bc[pc]>>16)[2]);t['风格提示'.encode('gbk')]=dict(p.gc(p.bc[pc+3]>>16)[2]);(work/'template.lua').write_bytes(('return '+lua(t)).encode('gbk'))
 (work/'display.lua').write_bytes((W/'display_regression_v200.lua').read_text().encode('gbk'));runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'display.lua'),str(work),mode],capture_output=True,timeout=90);(work/(mode+'.log')).write_bytes(r.stdout+r.stderr)
  assert r.returncode==0,(r.stdout+r.stderr).decode('gbk','replace')[-3500:]
  output=r.stdout.decode('gbk');assert 'DISPLAY_V200_PASS'in output;print(output,flush=True);runs.append({'mode':mode,'output':output})
 names=['patch_v200.py','test_v200.py','display_regression_v200.lua','package_v200.py','player_changes_v200.json']
 result={'version':'v1.200','all_passed':True,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'test_scope':'actual_ui_title_setter_tooltip_font_renderer_parser_and_ground_name','historical_suites_rerun':False,'full_windows_game_run':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v200.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');x=a.parse_args();main(str(Path(x.runtime).resolve())if x.runtime else str(ensure_runtime()))
