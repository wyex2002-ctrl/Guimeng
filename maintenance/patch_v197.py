"""Show already-generated comfort stats in the current equipment tooltip."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import ad,abc,jump,gcid,encstr,rebuild_proto,rebuild_dump,Asm
from bytecode_relocate import replace_instructions
from ljdis import OPS
from resource_tools import decode
W=Path(__file__).resolve().parent
BASE_SHA='4772c6cce8892a4826b362f1558243fb3792d427e956b50f04f0cdb7ff24090b'

def repair_tooltip(p):
 assert(p.params,p.frame,p.nbc)==(3,24,3261)
 assert p.bc[702]==abc('TGETS',5,4,gcid(p,'身体舒适'))
 # The historical base-only line still executes after elemental formatting.
 # Keep the integrated current/base line and suppress the duplicate base row.
 p.bc[702]=jump(702,710,24)
 a=Asm(p);start=a.base
 a.const(11,'\n#md#W舒适:');a.emit('KSHORT',9,0)
 a.emit('ISLE',7,9);a.jmp('done',24)
 a.const(11,'\n#md#c(-8323200)舒适:')
 a.mark('done');a.jmp(2779,24);a.finish();p.bc[2778]=jump(2778,start,24)
 return Proto(rebuild_proto(p),p.idx)

def build(runtime=None,rebuild_history=False):
 # The predecessor is an immutable, hash-pinned build input. Reusing it
 # does not claim to have recompiled or retested its historical sources.
 path=W/'game_v196.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  print('Building predecessor resource (missing, mismatched, or explicitly requested).',flush=True)
  subprocess.run(['python3',str(W/'patch_v196.py')]+(['--rebuild-history']if rebuild_history else [])+(['--runtime',runtime]if runtime else []),cwd=W,check=True,stdout=subprocess.DEVNULL)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30]);mods[12].protos[300]=repair_tooltip(mods[12].protos[300])
 p=mods[12].protos[193];assert p.bc[1066]==ad('ISEQS',11,gcid(p,'敏捷几率'))
 p.bc[1067]=jump(1067,1089,8);mods[12].protos[193]=Proto(rebuild_proto(p),193)
 for d in mods.values():
  for i,p in enumerate(d.protos):
   touched=False
   for k,v in enumerate(p.kgc):
    if isinstance(v,bytes):
     n=v.replace(b'Guimeng patch v1.196',b'Guimeng patch v1.197').replace(b'Guimeng v1.196 diagnostics',b'Guimeng v1.197 diagnostics').replace(b'patch=v1.196',b'patch=v1.197')
     if n!=v:p.kgc[k]=n;p.kraw[k]=encstr(n);touched=True
   if touched:d.protos[i]=Proto(rebuild_proto(p),i)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(old[m].protos)if p.raw!=d.protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v197.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  encrypted=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=encrypted if m==12 else encrypted.hex().upper().encode()
  p=outer.protos[0];k=p.nkgc-1-m;p.kgc[k]=value;p.kraw[k]=encstr(value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v197.res').write_bytes(data)
 result={'version':'v1.197','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'scope':'comfort single row + green bonus label; no new random agility; existing name/colors retained','rules_changed':True}
 (W/'build_v197.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print({k:v for k,v in result.items()if k!='unused'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true',help='Rebuild predecessor sources instead of reusing the hash-pinned resource');x=a.parse_args();build(str(Path(x.runtime).resolve())if x.runtime else None,x.rebuild_history)
