"""Restore standard equipment-name outlines; retain the bright orange text."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import encstr,rebuild_proto,rebuild_dump
from resource_tools import decode
W=Path(__file__).resolve().parent
BASE_SHA='b3844bcb535ecbff67fd52c6b767629a0aac7d887e6ae049489432831968ebde'
ORANGE=0xffffad32

def set_string(p,logical,value):
 i=p.nkgc-1-logical;p.kgc[i]=value;p.kraw[i]=encstr(value)

def build(runtime=None,rebuild_history=False):
 path=W/'game_v202.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  subprocess.run(['python3',str(W/'patch_v202.py')]+(['--rebuild-history']if rebuild_history else [])+(['--runtime',runtime]if runtime else []),check=True,cwd=W)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30,76]);d=mods[12]
 # v200 retained the original instructions in the appended private-style blocks.
 # Restore only the two entry instructions; leave the unused blocks/constants
 # intact so debug information and all existing prototype IDs remain stable.
 p=mods[12].protos[299];assert p.nbc==449
 from ljdis import OPS
 assert OPS[p.bc[86]&255]=='JMP' and OPS[p.bc[447]&255]=='GGET'
 p.bc[86]=p.bc[447];mods[12].protos[299]=Proto(rebuild_proto(p),p.idx)
 p=mods[76].protos[0];assert p.nbc==498
 assert OPS[p.bc[449]&255]=='JMP' and OPS[p.bc[496]&255]=='KNUM' and p.bc[496]>>16==12
 p.bc[449]=p.bc[496];mods[76].protos[0]=Proto(rebuild_proto(p),p.idx)
 for m,d in mods.items():
  for p in list(d.protos):
   touched=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'Guimeng patch v1.202',b'Guimeng patch v1.203').replace(b'Guimeng v1.202 diagnostics',b'Guimeng v1.203 diagnostics').replace(b'patch=v1.202',b'patch=v1.203')
    if m==12 and p.idx in [76,22187]:
     if v==b'1.202':new=b'1.203'
     if v=='魔改版 1.202'.encode('gbk'):new='魔改版 1.203'.encode('gbk')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);touched=True
   if touched:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(d.protos)if p.raw!=old[m].protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v203.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=enc if m==12 else enc.hex().upper().encode()
  set_string(outer.protos[0],m,value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v203.res').write_bytes(data)
 r={'version':'v1.203','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'seven_color':ORANGE,'seven_outline':0xff292c28,'ground_outline_policy':'same global setting as other equipment','rules_changed':False}
 (W/'build_v203.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(r)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
