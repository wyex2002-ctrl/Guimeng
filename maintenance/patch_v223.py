"""Correct stack sale totals, stack return scrolls, add a native warehouse button."""
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
BASE_SHA='22b7ab8268a6e84d9704485962f990cbfa873ce483d18740093ba65c00ca7c61'


def set_string(p,logical,value):
 i=p.nkgc-1-logical;p.kgc[i]=value;p.kraw[i]=encstr(value)

def build(runtime=None,rebuild_history=False):
 path=W/'game_v222.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  subprocess.run(['python3',str(W/'patch_v222.py')]+(['--rebuild-history']if rebuild_history else [])+(['--runtime',runtime]if runtime else []),check=True,cwd=W)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30]);d=mods[12]
 runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 source=work/'warehouse_button_v223_gbk.lua';source.write_bytes((W/'warehouse_button_v223.lua').read_text().encode('gbk'))
 compiler=work/'compile_warehouse_v223.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 subprocess.run([runtime,str(compiler),str(source),str(W/'warehouse_button_v223.ljbc')],check=True)
 compiled=Dump((W/'warehouse_button_v223.ljbc').read_bytes());assert len(compiled.protos)==7
 d.protos[22187:22194]=[Proto(q.raw,22187+i)for i,q in enumerate(compiled.protos)]
 helper_count=7
 for m,d in mods.items():
  for p in list(d.protos):
   touched=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'Guimeng patch v1.222',b'Guimeng patch v1.223').replace(b'Guimeng v1.222 diagnostics',b'Guimeng v1.223 diagnostics').replace(b'patch=v1.222',b'patch=v1.223')
    if m==12 and p.idx in [76,22187+helper_count]:
     if v==b'1.222':new=b'1.223'
     if v=='魔改版 1.222'.encode('gbk'):new='魔改版 1.223'.encode('gbk')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);touched=True
   if touched:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(old[m].protos)if p.raw!=d.protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v223.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=enc if m==12 else enc.hex().upper().encode()
  set_string(outer.protos[0],m,value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v223.res').write_bytes(data)
 r={'version':'v1.223','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'helper_count':helper_count,'helper_index':22187,'root_index':22187+helper_count,'scroll_stack_cap':999,'rules_changed':False}
 (W/'build_v223.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in r.items()if not k.endswith("_map")})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
