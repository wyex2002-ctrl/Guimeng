"""Brighten seven-affix equipment names to orange, preserving the current outline."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import encstr,rebuild_proto,rebuild_dump
from patch_v200 import numbers
from resource_tools import decode
W=Path(__file__).resolve().parent
BASE_SHA='cef3081779f6cf8cb574985006d7fd9eb99b5b251547c7327ddfd53627c2164b'
ORANGE=0xffffad32

def set_string(p,logical,value):
 i=p.nkgc-1-logical;p.kgc[i]=value;p.kraw[i]=encstr(value)

def build(runtime=None,rebuild_history=False):
 path=W/'game_v201.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  subprocess.run(['python3',str(W/'patch_v201.py')]+(['--rebuild-history']if rebuild_history else [])+(['--runtime',runtime]if runtime else []),check=True,cwd=W)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30,76]);d=mods[12]
 for m,i,k in [(12,193,24),(12,299,1),(76,0,13)]:
  mods[m].protos[i]=numbers(mods[m].protos[i],{k:ORANGE})
 for m,d in mods.items():
  for p in list(d.protos):
   touched=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'Guimeng patch v1.201',b'Guimeng patch v1.202').replace(b'Guimeng v1.201 diagnostics',b'Guimeng v1.202 diagnostics').replace(b'patch=v1.201',b'patch=v1.202')
    if m==12 and p.idx in [76,22187]:
     if v==b'1.201':new=b'1.202'
     if v=='魔改版 1.201'.encode('gbk'):new='魔改版 1.202'.encode('gbk')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);touched=True
   if touched:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(d.protos)if p.raw!=old[m].protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v202.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=enc if m==12 else enc.hex().upper().encode()
  set_string(outer.protos[0],m,value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v202.res').write_bytes(data)
 r={'version':'v1.202','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'seven_color':ORANGE,'seven_outline':0xff4a2c12,'rules_changed':False}
 (W/'build_v202.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(r)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
