"""Exercise actual hit arithmetic/decisions; verify every unrelated instruction."""
from pathlib import Path
import argparse,hashlib,json,subprocess
from resource_tools import decode
from native_test_utils import trees,standalone
from bytecode_relocate import BRANCHES,numeric_and_debug
from patch_v196 import hit_sites,number_pool
from patch_v139 import ad,abc,jump
from ljdis import OPS
from runtime import ensure_runtime
W=Path(__file__).resolve().parent

def main(runtime):
 (W/'validation_v196.json').unlink(missing_ok=True);work=W/'native_work/v196';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v195.res').read_bytes();b=(W/'game_v196.res').read_bytes();ao,old=decode(a,range(2,86,2));bo,new=decode(b,range(2,86,2));report=json.loads((W/'build_v196.json').read_text())
 sites=hit_sites(old);assert sites==[tuple(x)for x in report['hit_sites']]and len(sites)==252
 groups={}
 for m,i,pc in sites:groups.setdefault((m,i),[]).append(pc)
 changes={int(k):v for k,v in report['changed_prototypes'].items()}
 expected={m:sorted(i for mm,i in groups if mm==m)for m in [12,22,26]};expected|={14:[632,668,684],30:[39,87]};assert changes==expected
 assert ao.protos[0].bc==bo.protos[0].bc and a[-10:]==b[-10:]
 for m,d in new.items():
  assert d.rebuild()==d.raw and len(d.protos)==len(old[m].protos)
  for i,(p,q)in enumerate(zip(d.protos,old[m].protos)):
   assert(p.raw!=q.raw)==(i in changes.get(m,[])),(m,i)
   assert(p.params,p.frame,p.uv,p.kgc)==(q.params,q.frame,q.uv,q.kgc)if (m,i)in groups else (p.params,p.frame,p.uv)==(q.params,q.frame,q.uv)
   if(m,i)in groups:
    assert number_pool(p)==number_pool(q)+[2.5]
    assert numeric_and_debug(p)[0].startswith(numeric_and_debug(q)[0])
    mp={int(k):v for k,v in report['relocations'][f'{m}/{i}'].items()};pcs=groups[m,i]
    for pc,x in enumerate(q.bc):
     at=mp[pc]
     if pc in pcs:
      y=q.bc[pc+1];dst=x>>8&255;D=x>>16&255;A=y>>24
      assert p.bc[at:at+2]==[abc('DIVVN',dst,D,q.nkn),abc('ADDVV',dst,A,dst)]
     elif pc-1 in pcs:
      at=mp[pc];dst=q.bc[pc-1]>>8&255;res=x>>8&255;zero=number_pool(q).index(0)
      assert p.bc[at:at+5]==[ad('ISNEN',dst,zero),jump(at+1,at+4,p.frame),ad('KSHORT',res,0),jump(at+3,mp[pc+2],p.frame),x]
     else:
      expected_ins=x
      if OPS[x&255]in BRANCHES:expected_ins=(x&65535)|((mp[pc+1+(x>>16)-32768]-at-1+32768)<<16)
      assert p.bc[at]==expected_ins,(m,i,pc,at)
   else:assert numeric_and_debug(p)[0]==numeric_and_debug(q)[0]
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(m,i,pc)
 # Inventory arithmetic lookalikes: all 498 other ratios (crit/break) stay
 # covered by the instruction comparison above, rather than a broad replace.
 ratios=[]
 for m,d in old.items():
  for p in d.protos:
   n=number_pool(p)
   for pc,x in enumerate(p.bc[:-2]):
    y,z=p.bc[pc+1:pc+3]
    if OPS[x&255]=='ADDVV'and OPS[y&255]=='DIVVV'and OPS[z&255]=='MULVN'and n[z>>16&255]==100 and(y>>16&255)==(x>>8&255)and(z>>8&255)==(y>>8&255)and(z>>24)==(y>>8&255):ratios.append((m,p.idx,pc))
 assert len(ratios)==750 and set(sites)<=set(ratios)
 # Six actual layouts: player script, mercenary script, per-monster script,
 # native basic/no-skill, native monster/pet skill, native hero skill.
 layouts=[(12,278,56,51,63,7,'hero'),(12,18008,106,101,135,7,'merc'),(12,10298,469,462,476,21,'monster'),(22,44,346,346,367,28,'basic'),(22,44,542,539,566,26,'native_monster'),(26,29,461,458,485,17,'native_hero')]
 meta=[]
 for m,i,pc,start,end,rollreg,name in layouts:
  p=old[m].protos[i];x,y=p.bc[pc:pc+2];dst=x>>8&255;areg=y>>24;dreg=x>>16&255;result=y>>8&255
  meta.append((name,p.frame,areg,dreg,dst,result))
  for label,mods in [('old',old),('new',new)]:
   d=mods[m];q=d.protos[i];mp={int(k):v for k,v in report['relocations'][f'{m}/{i}'].items()}if label=='new'else{j:j for j in range(p.nbc+1)}
   (work/f'{name}_{label}_ratio.ljbc').write_bytes(standalone(d,trees(d),i,{0:jump(0,mp[pc],q.frame),mp[pc+3]:ad('RET1',result,2)},q.frame))
   (work/f'{name}_{label}_decision.ljbc').write_bytes(standalone(d,trees(d),i,{0:jump(0,mp[start],q.frame),mp[end]:ad('RET1',rollreg,2)},q.frame))
 # Every distinct monster registration is executed once; representative loops
 # are not repeated per monster or per attribute combination.
 for m,i,pc in sites:
  if m==12 and pc==469:
   d=new[m];q=d.protos[i];mp={int(k):v for k,v in report['relocations'][f'{m}/{i}'].items()}
   (work/f'monster_{i}.ljbc').write_bytes(standalone(d,trees(d),i,{0:jump(0,mp[462],q.frame),mp[476]:ad('RET1',21,2)},q.frame))
 (work/'metadata.lua').write_text('return {'+','.join('{'+','.join(json.dumps(v)for v in row)+'}'for row in meta)+'}')
 (work/'monsters.lua').write_text('return {'+','.join(str(i)for m,i,pc in sites if m==12 and pc==469)+'}')
 for m,i,n in [(22,44,'full_monster'),(26,29,'full_hero'),(14,378,'sandbox_install')]:
  d=new[m];patch={0:jump(0,597,13),609:ad('RET0',0,1)}if n=='sandbox_install'else None
  (work/f'{n}.ljbc').write_bytes(standalone(d,trees(d),i,patch))
 (work/'hit.lua').write_bytes((W/'hit_regression_v196.lua').read_text().encode('gbk'));runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'hit.lua'),str(work),mode],capture_output=True,timeout=90);(work/(mode+'.log')).write_bytes(r.stdout+r.stderr)
  assert r.returncode==0,(r.stdout+r.stderr).decode('gbk','replace')[-3500:]
  output=r.stdout.decode('gbk');assert 'HIT_V196_PASS'in output;print(output,flush=True);runs.append({'mode':mode,'output':output})
 names=['patch_v196.py','test_v196.py','hit_regression_v196.lua','package_v196.py','player_changes_v196.json']
 result={'version':'v1.196','all_passed':True,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'test_scope':'all_252_hit_sites_and_six_actual_decision_layouts_plus_native_callback_integration','other_ratio_sites_unchanged':498,'historical_suites_rerun':False,'full_windows_game_run':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v196.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');x=a.parse_args();main(str(Path(x.runtime).resolve())if x.runtime else str(ensure_runtime()))
