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
BASE_SHA='64270144a464a5d8eecfea812a92bfe89627164914cdbd1d5a3871bfe94d60d3'


def set_string(p,logical,value):
 i=p.nkgc-1-logical;p.kgc[i]=value;p.kraw[i]=encstr(value)

def build(runtime=None,rebuild_history=False):
 path=W/'game_v224.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  subprocess.run(['python3',str(W/'patch_v224.py')]+(['--rebuild-history']if rebuild_history else [])+(['--runtime',runtime]if runtime else []),check=True,cwd=W)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[10,12,14,30,56])
 runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 from portal_routes_v213 import extract
 from test_v192 import lua
 routes,_=extract(mods[12])
 body=(W/'portal_labels_v225.lua').read_text().replace('local routes = {} -- ROUTES_GENERATED','local routes = '+lua({k:v.encode('gbk')for k,v in routes.items()}))
 source=work/'portal_labels_v225_gbk.lua';source.write_bytes(body.encode('gbk'))
 compiler=work/'compile_portals_v225.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 subprocess.run([runtime,str(compiler),str(source),str(W/'portal_labels_v225.ljbc')],check=True)
 compiled=Dump((W/'portal_labels_v225.ljbc').read_bytes());assert len(compiled.protos)==3
 mods[10].protos[39:42]=[Proto(q.raw,39+i)for i,q in enumerate(compiled.protos)]
 # Restore the original native renderer, removing v224's scaling-only extension.
 import zipfile
 original=zipfile.ZipFile(W/'base_v176.zip').read('Lib/game.res')
 _,reference=decode(original,[56]);p=reference[56].protos[7]
 assert hashlib.sha256(p.raw).hexdigest()=='a1dee87388348d38487fcf5e65b1dfcfce10a6335bcafcbcf582df7a40cacd30'
 mods[56].protos[7]=Proto(p.raw,7)
 helper_count=7
 for m,d in mods.items():
  for p in list(d.protos):
   touched=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'Guimeng patch v1.224',b'Guimeng patch v1.225').replace(b'Guimeng v1.224 diagnostics',b'Guimeng v1.225 diagnostics').replace(b'patch=v1.224',b'patch=v1.225')
    if m==12 and p.idx in [76,22187+helper_count]:
     if v==b'1.224':new=b'1.225'
     if v=='魔改版 1.224'.encode('gbk'):new='魔改版 1.225'.encode('gbk')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);touched=True
   if touched:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(old[m].protos)if p.raw!=d.protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v225.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=enc if m==12 else enc.hex().upper().encode()
  set_string(outer.protos[0],m,value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v225.res').write_bytes(data)
 r={'version':'v1.225','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'helper_count':helper_count,'helper_index':22187,'root_index':22187+helper_count,'scroll_stack_cap':999,'rules_changed':False,'portal_scale':1,'font_renderer_restored':True}
 (W/'build_v225.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in r.items()if not k.endswith("_maps") and not k.endswith("_map")})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
