"""Change only beast attribute/skill ranges in the pinned current resource."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import encstr,rebuild_proto,rebuild_dump
from resource_tools import decode
W=Path(__file__).resolve().parent
BASE_SHA='e70717ccbeb132243ea281797005818d9cdb4841cfd4c467b7b72c29606dedde'
CONFIGS={6464:{993:'神兽攻击',1713:'超强神兽攻击',2596:'超强神兽攻击1'},6466:{114:'神兽',340:'超强神兽'}}

def unpack_config(value):
 assert value.endswith(b'*') and len(value)%2==1
 body=bytes(x^16 for x in bytes.fromhex(value[:-33].decode('ascii')))
 assert hashlib.md5(body).hexdigest().upper().encode()==value[-33:-1]
 return body

def pack_config(body):
 return bytes(x^16 for x in body).hex().upper().encode()+hashlib.md5(body).hexdigest().upper().encode()+b'*'

def set_string(p,logical,value):
 i=p.nkgc-1-logical;p.kgc[i]=value;p.kraw[i]=encstr(value)

def build(runtime=None,rebuild_history=False):
 path=W/'game_v200.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  subprocess.run(['python3',str(W/'patch_v200.py')]+(['--rebuild-history']if rebuild_history else [])+(['--runtime',runtime]if runtime else []),check=True,cwd=W)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30]);d=mods[12]
 for index,entries in CONFIGS.items():
  p=d.protos[index]
  for logical,name in entries.items():
   assert p.gc(logical-1)==name.encode('gbk')
   body=unpack_config(p.gc(logical));key=('施法距离'if index==6464 else'攻击距离').encode('gbk')
   old=key+b'=1\r\n';assert body.count(old)==1
   set_string(p,logical,pack_config(body.replace(old,key+b'=2\r\n')))
  d.protos[index]=Proto(rebuild_proto(p),index)
 for m,d in mods.items():
  for p in list(d.protos):
   touched=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'Guimeng patch v1.200',b'Guimeng patch v1.201').replace(b'Guimeng v1.200 diagnostics',b'Guimeng v1.201 diagnostics').replace(b'patch=v1.200',b'patch=v1.201')
    if m==12 and p.idx in [76,22187]:
     if v==b'1.200':new=b'1.201'
     if v=='魔改版 1.200'.encode('gbk'):new='魔改版 1.201'.encode('gbk')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);touched=True
   if touched:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(d.protos)if p.raw!=old[m].protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v201.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=enc if m==12 else enc.hex().upper().encode()
  set_string(outer.protos[0],m,value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v201.res').write_bytes(data)
 r={'version':'v1.201','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'config_targets':CONFIGS,'attack_range':2,'cast_range':2,'ai_changed':False}
 (W/'build_v201.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(r)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
