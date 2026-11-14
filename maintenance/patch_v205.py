"""Bind the existing HP overlay lexically; do not read private class fields."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import encstr,rebuild_proto,rebuild_dump,ad,abc
from bytecode_relocate import replace_instructions,numeric_and_debug
from ljtool import uleb
from resource_tools import decode
from ljdis import OPS
W=Path(__file__).resolve().parent
BASE_SHA='7120c15efd2a4acd6599924119e5d6448b59e9ebdb6c272815d823007a252dee'


def set_string(p,logical,value):
 i=p.nkgc-1-logical;p.kgc[i]=value;p.kraw[i]=encstr(value)

def build(runtime=None,rebuild_history=False):
 path=W/'game_v204.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  subprocess.run(['python3',str(W/'patch_v204.py')]+(['--rebuild-history']if rebuild_history else [])+(['--runtime',runtime]if runtime else []),check=True,cwd=W)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30,48]);d=mods[12]
 # The engine's class descriptor is not a readable method table. Capture the
 # already-compiled helper in the display closure instead of looking it up.
 d=mods[48];p=d.protos[7];assert p.nuv==0 and p.nbc==4007
 p.bc[3754:3759]=[ad('UGET',6,0),ad('MOV',7,0),abc('CALL',6,1,2),ad('RET0',0,1),ad('RET0',0,1)]
 p=Proto(rebuild_proto(p),7)
 numeric,debug=numeric_and_debug(p);width=1 if p.lines<256 else 2 if p.lines<65536 else 4
 linebytes=p.nbc*width
 debug=debug[:linebytes]+b'window_hp_overlay\0'+debug[linebytes:]
 head=bytes([p.flags,p.params,p.frame,1])+uleb(p.nkgc)+uleb(p.nkn)+uleb(p.nbc)+uleb(len(debug))
 if debug:head+=uleb(p.first)+uleb(p.lines)
 # local, immutable upvalue: register 2 in the module initialization closure.
 d.protos[7]=Proto(head+struct.pack('<'+'I'*p.nbc,*p.bc)+struct.pack('<H',0xc002)+b''.join(p.kraw)+numeric+debug,7)
 root=d.protos[44];assert root.nbc==107 and root.frame==2
 assert OPS[root.bc[104]&255]=='FNEW';child=root.bc[104]>>16
 root.frame=3;root=Proto(rebuild_proto(root),44)
 # Capture only after the class() call has returned, before any FNEW display
 # closure. The remaining registrations do not call over live register 2.
 replacements={3:[ad('FNEW',2,child),root.bc[3]],103:[ad('UCLO',0,32768),ad('RET0',0,1)],104:[],105:[],106:[]}
 raw,mapping=replace_instructions(root,replacements);d.protos[44]=Proto(raw,44)
 for m,d in mods.items():
  for p in list(d.protos):
   touched=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'Guimeng patch v1.204',b'Guimeng patch v1.205').replace(b'Guimeng v1.204 diagnostics',b'Guimeng v1.205 diagnostics').replace(b'patch=v1.204',b'patch=v1.205')
    if m==12 and p.idx in [76,22187]:
     if v==b'1.204':new=b'1.205'
     if v=='魔改版 1.204'.encode('gbk'):new='魔改版 1.205'.encode('gbk')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);touched=True
   if touched:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(d.protos)if p.raw!=old[m].protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v205.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=enc if m==12 else enc.hex().upper().encode()
  set_string(outer.protos[0],m,value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v205.res').write_bytes(data)
 r={'version':'v1.205','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'display_helper_upvalue':2,'module_root_index':44,'helper_index':43,'root_relocations':mapping,'rules_changed':False}
 (W/'build_v205.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(r)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
