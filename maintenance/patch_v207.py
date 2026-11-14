"""Store full XP for dead deployed mercenaries and grant dead Ling claims to hero."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import encstr,rebuild_proto,rebuild_dump,ad,abc,gcid
from bytecode_relocate import replace_instructions,numeric_and_debug
from ljtool import uleb
from resource_tools import decode
from runtime import ensure_runtime
from ljdis import OPS
W=Path(__file__).resolve().parent
BASE_SHA='714d9e0b753eaf28399022acb9b99603658d76dfffffc684d3ee59e0c1814d38'


def set_string(p,logical,value):
 i=p.nkgc-1-logical;p.kgc[i]=value;p.kraw[i]=encstr(value)

def build(runtime=None,rebuild_history=False):
 path=W/'game_v206.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  subprocess.run(['python3',str(W/'patch_v206.py')]+(['--rebuild-history']if rebuild_history else [])+(['--runtime',runtime]if runtime else []),check=True,cwd=W)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30]);d=mods[12]
 runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 source=work/'talisman_dead_v207_gbk.lua';source.write_bytes((W/'talisman_dead_v207.lua').read_text().encode('gbk'))
 compiler=work/'compile_talisman_v207.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 subprocess.run([runtime,str(compiler),str(source),str(W/'talisman_dead_v207.ljbc')],check=True)
 compiled=Dump((W/'talisman_dead_v207.ljbc').read_bytes());assert len(compiled.protos)==2
 assert compiled.protos[1].params==3 and compiled.protos[1].nuv==0 and compiled.protos[0].nuv==0
 d=mods[12]
 for getter,parent in [(35,36),(256,257)]:
  d.protos[getter]=Proto(compiled.protos[0].raw,getter);d.protos[parent]=Proto(compiled.protos[1].raw,parent)
 # Delete only v206's eight-instruction legacy dead-input division.
 # Keep its eligibility gate, original hero-first selection and restore hook.
 p=d.protos[258]
 previous=json.loads((W/'build_v206.json').read_text())
 at=previous['xp_relocations']['118']
 assert [OPS[x&255] for x in p.bc[at:at+9]]==['ISF','JMP','GGET','ISNEV','JMP','KSHORT','DIVVV','MOV','ADDVV']
 for pc,ins in enumerate(p.bc):
  if OPS[ins&255] in {'JMP','UCLO','FORI','JFORI','FORL','IFORL','ITERL','IITERL','LOOP','ILOOP','ISNEXT'}:
   target=pc+1+(ins>>16)-32768
   assert not (at<target<at+8 and not at<=pc<at+8),(pc,target)
 raw,mp=replace_instructions(p,{pc:[] for pc in range(at,at+8)})
 d.protos[258]=Proto(raw,258)
 for m,d in mods.items():
  for p in list(d.protos):
   touched=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'Guimeng patch v1.206',b'Guimeng patch v1.207').replace(b'Guimeng v1.206 diagnostics',b'Guimeng v1.207 diagnostics').replace(b'patch=v1.206',b'patch=v1.207')
    if m==12 and p.idx in [76,22187]:
     if v==b'1.206':new=b'1.207'
     if v=='魔改版 1.206'.encode('gbk'):new='魔改版 1.207'.encode('gbk')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);touched=True
   if touched:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(d.protos)if p.raw!=old[m].protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v207.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=enc if m==12 else enc.hex().upper().encode()
  set_string(outer.protos[0],m,value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v207.res').write_bytes(data)
 r={'version':'v1.207','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'xp_relocations':mp,'spawn_relocations':previous['spawn_relocations'],'dead_storage_ratio':1.0,'rules_changed':True}
 (W/'build_v207.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in r.items()if not k.endswith("relocations")})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
