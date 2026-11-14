"""Read live slot-indexed inventory for all auxiliary potion searches."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import ad,abc,gcid,encstr,rebuild_proto,rebuild_dump
from ljdis import OPS
from resource_tools import decode
W=Path(__file__).resolve().parent
BASE_SHA='79cc6f98fc9cedc327a46fa245f6a4112765bd47b0d4aa31ef37caf1d9eca76f'

def repair(p):
 assert (p.params,p.frame,p.nbc,p.nkgc)==(3,10,287,44)
 ids={s:gcid(p,s)for s in ['Sys','get','item_arr']};p=Proto(rebuild_proto(p),p.idx)
 assert max(ids.values())<256
 for pc in [18,198,244]:
  assert p.bc[pc]==ad('GGET',7,gcid(p,'Ux雌'))
  assert p.bc[pc+1]==abc('TGETS',7,7,gcid(p,'胚子考虑'))
  assert p.bc[pc+2]==abc('CALL',7,2,1)
  assert p.bc[pc+3]==abc('TGETS',7,7,gcid(p,'主角格子'))
  assert OPS[p.bc[pc+4]&255]=='TGETV'
  # 主角格子 is a dense public-control list populated by 12/179, not
  # inventory indexed by native slot ID. Use the existing read-only getter.
  p.bc[pc:pc+4]=[ad('GGET',7,ids['Sys']),abc('TGETS',7,7,ids['get']),ad('KSTR',8,ids['item_arr']),abc('CALL',7,2,2)]
 return Proto(rebuild_proto(p),p.idx)

def build(runtime=None):
 subprocess.run(['python3',str(W/'patch_v190.py')]+(['--runtime',runtime]if runtime else []),cwd=W,check=True,stdout=subprocess.DEVNULL)
 base=(W/'game_v190.res').read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30]);mods[12].protos[283]=repair(mods[12].protos[283])
 for d in mods.values():
  for i,p in enumerate(d.protos):
   touched=False
   for k,v in enumerate(p.kgc):
    if isinstance(v,bytes):
     n=v.replace(b'Guimeng patch v1.190',b'Guimeng patch v1.191').replace(b'Guimeng v1.190 diagnostics',b'Guimeng v1.191 diagnostics').replace(b'patch=v1.190',b'patch=v1.191')
     if n!=v:p.kgc[k]=n;p.kraw[k]=encstr(n);touched=True
   if touched:d.protos[i]=Proto(rebuild_proto(p),i)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(old[m].protos)if p.raw!=d.protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v191.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  encrypted=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=encrypted if m==12 else encrypted.hex().upper().encode()
  p=outer.protos[0];k=p.nkgc-1-m;p.kgc[k]=value;p.kraw[k]=encstr(value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v191.res').write_bytes(data)
 result={'version':'v1.191','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'live_inventory_reads':[18,198,244],'rules_changed':False}
 (W/'build_v191.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(result)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');x=a.parse_args();build(str(Path(x.runtime).resolve())if x.runtime else None)
