from pathlib import Path
import argparse,hashlib,json,os,subprocess,tarfile,zipfile
from ljtool import Dump
from ljdis import OPS
from patch_v139 import ad,jump
from bytecode_relocate import BRANCHES
from native_test_utils import trees,standalone
from resource_tools import decode
from patch_v177 import W,BASE,BASE_SHA,MENUS,STARTS

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--runtime');a=ap.parse_args()
 with zipfile.ZipFile(BASE) as z:before=z.read('Lib/game.res')
 after=(W/'game_v177.res').read_bytes();b=json.loads((W/'build_v177.json').read_text());assert hashlib.sha256(before).hexdigest()==BASE_SHA
 x,old=decode(before,range(2,86,2));y,new=decode(after,range(2,86,2));changes={int(k):v for k,v in b['changed_prototypes'].items()}
 assert x.protos[0].bc==y.protos[0].bc and before[-10:]==after[-10:]
 assert sorted(x.protos[0].nkgc-1-i for i,(u,v) in enumerate(zip(x.protos[0].kraw,y.protos[0].kraw)) if u!=v)==[12,14,22]
 for m,d in new.items():
  trees(d);assert d.rebuild()==d.raw and len(d.protos)==len(old[m].protos)
  assert [i for i,(p,q) in enumerate(zip(old[m].protos,d.protos)) if p.raw!=q.raw]==changes.get(m,[])
  for p in d.protos:
   for pc,i in enumerate(p.bc):
    op=OPS[i&255]
    if op in BRANCHES:assert 0<=pc+1+(i>>16)-32768<p.nbc,(m,p.idx,pc)
    if op in ['KSTR','GGET','GSET','FNEW','TDUP','ISEQS','ISNES']:assert i>>16<p.nkgc
    if op in ['TGETS','TSETS']:assert ((i>>16)&255)<p.nkgc
 native=new[14].protos[378];exports={native.gc((i>>16)&255).decode('gbk') for i in native.bc if OPS[i&255]=='TSETS' and i>>24==12}
 for idx in [109]+STARTS:
  p=new[12].protos[idx];used={p.gc(i>>16).decode('gbk') for i in p.bc if OPS[i&255]=='GGET'}
  assert used <= exports|{'对话窗口'},(idx,used-exports)
  assert not {'pcall','xpcall'}&used and not any(OPS[i&255]=='GSET' for i in p.bc)
 for idx in [76,129,134,179]:assert new[12].protos[idx].raw==old[12].protos[idx].raw
 assert new[22].protos[64].raw==old[22].protos[64].raw
 # Installer645 is passed the Sys instance by constructor648; its diagnostic
 # functions are fields of Sys, not globals. This evidence is preserved.
 assert new[14].protos[648].bc[298]==ad('MOV',3,0)
 assert len(after)<2700000
 work=W/'native_work';work.mkdir(exist_ok=True)
 if a.runtime:runtime=Path(a.runtime).resolve()
 else:
  with tarfile.open(W/'LuaJIT-2.0-b83bcba.tar.gz') as z:z.extractall(work,filter='data')
  tmp=work/'tmp';tmp.mkdir(exist_ok=True)
  r=subprocess.run(['make','-j4'],cwd=work/'luajit20',env=os.environ|{'TMPDIR':str(tmp)},capture_output=True)
  (work/'build.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0
  runtime=work/'luajit20/src/luajit'
 for label,mods in [('old',old),('new',new)]:
  d=mods[12];tree=trees(d)
  def emit(name,idx,patches=None,params=None):(work/(name+'_'+label+'.ljbc')).write_bytes(standalone(d,tree,idx,patches,params))
  emit('register_daily',122,{0:jump(0,3,0),6:ad('RET1',1,2)})
  emit('load_daily',179,{0:jump(0,400,4),408:ad('RET0',0,1)});emit('create_daily',175,{0:jump(0,438,4),443:ad('RET0',0,1)})
  for idx in MENUS+STARTS:emit('menu'+str(idx),idx)
  for idx,name in [(471,'buff_begin'),(472,'buff_tick'),(473,'buff_end')]:emit(name,idx)
  emit('affix_config',142,{0:jump(0,1238,0),1248:ad('RET1',2,2)})
  mp=b['generator_relocations'] if label=='new' else {}
  emit('generator',193,{0:jump(0,mp.get('874',874),3)})
  emit('currency',191);emit('save',179,{0:jump(0,107,4),145:ad('RET0',0,1)})
  d=mods[22];(work/('death_'+label+'.ljbc')).write_bytes(standalone(d,trees(d),64))
 d=new[14];tree=trees(d)
 (work/'builtin_exports.ljbc').write_bytes(standalone(d,tree,378,{0:jump(0,433,13),451:ad('RET1',12,2)},13))
 (work/'sandbox_install.ljbc').write_bytes(standalone(d,tree,378,{0:jump(0,635,6),647:ad('RET0',0,1)},6))
 (work/'fx_getter.ljbc').write_bytes(standalone(d,tree,339));(work/'data_protection.ljbc').write_bytes(standalone(d,tree,458))
 d=new[84];(work/'ux_init.ljbc').write_bytes(standalone(d,trees(d),18,{0:jump(0,198,0),203:ad('RET1',4,2)}))
 d=new[22];(work/'spawn.ljbc').write_bytes(standalone(d,trees(d),3))
 runs=[]
 for name in ['systems_regression_v177.lua','reputation_regression_v177.lua']:
  src=work/name;src.write_bytes((W/name).read_text().encode('gbk'))
  for mode in ['normal','hot']:
   r=subprocess.run([str(runtime),str(src),str(work),mode],capture_output=True,timeout=60)
   (work/(name+'.'+mode+'.stdout')).write_bytes(r.stdout);(work/(name+'.'+mode+'.stderr')).write_bytes(r.stderr)
   assert r.returncode==0 and b'PASS\t'+mode.encode() in r.stdout,(name,mode,r.returncode,r.stdout[-1500:],r.stderr[-2200:])
   output=r.stdout.decode('gbk');print(output,flush=True);runs.append({'fixture':name,'mode':mode,'output':output})
 loader=work/'load.lua';loader.write_text('for i=1,#arg do assert(loadfile(arg[i]))end;print("LOAD_PASS")')
 subprocess.run([str(runtime),str(loader)]+[str(W/f'module_{m}_v177.ljbc') for m in changes],check=True)
 result={'version':'v1.177','all_passed':True,'sha256':hashlib.sha256(after).hexdigest(),'bytes':len(after),'native_luajit_run':True,'full_windows_game_run':False,
  'reputation_remaining_client_cause_unconfirmed':True,'runs':runs,
  'checks':['daily 2h/active-membership4h, actual buff membership flag, same-day topup from old marker, toggling/reload/dedupe/cap/next day',
   'all seven actual menus and activation closures preserve owner and display active balance without duplicate buff',
   'actual original shared-balance buff tick consumes time; new DB globals limited to original exports under actual sandbox protection',
   'actual rarity generation 10 slots x 3..7 affixes x250: critical/penetration occur on all five allowed slots and nowhere else; clothes/shoes have no attack elements',
   'actual death/currency/save/respawn; numeric-string compatibility and actual data protection wrapper; Sys-owned logging without global alias',
   'all other prototypes byte-identical, including recent startup fixes and original native protection'],
  'limitations':'Native LuaJIT2.0 with actual export/protection and callback bytecode, engine primitives mocked; no Windows client; no new live kill log to establish the remaining ordinary-reputation root cause.'}
 (W/'validation_v177.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='runs'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
