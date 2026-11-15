"""Fix map-label plugin API boundary and temporary Otherworld destinations."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import encstr,rebuild_proto,rebuild_dump,ad,abc,gcid
from bytecode_relocate import replace_instructions,numeric_and_debug
from ljtool import uleb
from portal_routes_v213 import extract
from test_v192 import lua
from resource_tools import decode
from runtime import ensure_runtime
from ljdis import OPS
W=Path(__file__).resolve().parent
BASE_SHA='c78b4300961129d516ed2f84cb2a85d8d4191e59462819b19bb076331a9eb1ad'


def set_string(p,logical,value):
 i=p.nkgc-1-logical;p.kgc[i]=value;p.kraw[i]=encstr(value)

def build(runtime=None,rebuild_history=False):
 path=W/'game_v212.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  subprocess.run(['python3',str(W/'patch_v212.py')]+(['--rebuild-history']if rebuild_history else [])+(['--runtime',runtime]if runtime else []),check=True,cwd=W)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[10,12,14,30]);d=mods[12]
 runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 routes,evidence=extract(mods[12])
 (W/'portal_routes_v213.json').write_text(json.dumps({'routes':routes,'evidence':evidence},ensure_ascii=False,indent=2)+'\n')
 source=work/'portal_labels_v213_gbk.lua';body=(W/'portal_labels_v213.lua').read_text().replace('local routes = {} -- ROUTES_GENERATED','local routes = '+lua({k:v.encode('gbk')for k,v in routes.items()}))
 source.write_bytes(body.encode('gbk'))
 compiler=work/'compile_portals_v213.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 subprocess.run([runtime,str(compiler),str(source),str(W/'portal_labels_v213.ljbc')],check=True)
 compiled=Dump((W/'portal_labels_v213.ljbc').read_bytes());assert compiled.protos[-1].params==6 and compiled.protos[-1].nuv==0
 d=mods[10];helper_count=len(compiled.protos);assert len(d.protos)==44 and helper_count==3
 # Replace just the existing three-prototype helper, leaving renderer/constructor intact.
 d.protos[39:42]=[Proto(q.raw,39+i)for i,q in enumerate(compiled.protos)]
 maps={}
 for m,d in mods.items():
  for p in list(d.protos):
   touched=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'Guimeng patch v1.212',b'Guimeng patch v1.213').replace(b'Guimeng v1.212 diagnostics',b'Guimeng v1.213 diagnostics').replace(b'patch=v1.212',b'patch=v1.213')
    if m==12 and p.idx in [76,22187]:
     if v==b'1.212':new=b'1.213'
     if v=='魔改版 1.212'.encode('gbk'):new='魔改版 1.213'.encode('gbk')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);touched=True
   if touched:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(old[m].protos)if p.raw!=d.protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v213.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=enc if m==12 else enc.hex().upper().encode()
  set_string(outer.protos[0],m,value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v213.res').write_bytes(data)
 r={'version':'v1.213','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'relocations':maps,'helper_start':39,'helper_count':helper_count,'map_root':42,'portal_count':len(routes),'rules_changed':False}
 (W/'build_v213.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in r.items()if not k.endswith("relocations")})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
