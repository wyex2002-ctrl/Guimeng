"""Show already-generated comfort stats in the current equipment tooltip."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import ad,abc,jump,gcid,encstr,rebuild_proto,rebuild_dump,Asm
from bytecode_relocate import replace_instructions
from ljdis import OPS
from resource_tools import decode
W=Path(__file__).resolve().parent
BASE_SHA='67ba8f011fc6ff4dcade7fb5b05c6d2cb00672294f7ac2ba7b933fcddb72b86b'

DISPLAY_SHA='90467c334b610e571ef94bbf50313463492d002996ea25d208fc1b509a6226f5'

def repair_tooltip(p):
 assert(p.params,p.frame,p.nbc)==(3,24,3232)
 # Start from the user-confirmed v193 display. Only its historical comfort
 # row branches to a replacement; every other original instruction is kept.
 a=Asm(p);start=a.base
 a.emit('MOV',15,4);a.get(5,0,'附加');a.get(5,5,'鉴定')
 a.emit('ISNEP',5,0);a.jmp('source',24);a.emit('MOV',15,0)
 a.mark('source');a.get(5,15,'身体舒适');a.emit('IST',d=5);a.jmp('value',24);a.emit('KSHORT',5,0)
 a.mark('value');a.get(7,4,'身体舒适');a.emit('IST',d=7);a.jmp('base',24);a.emit('KSHORT',7,0)
 a.mark('base');a.emit('SUBVV',7,b=5,c=7);a.emit('KSHORT',9,0)
 a.emit('ISNEV',5,9);a.jmp('row',24);a.emit('ISEQV',7,9);a.jmp(710,24)
 a.mark('row');a.emit('MOV',10,3);a.const(11,'\n#md#W舒适:')
 a.emit('ISLE',7,9);a.jmp('total',24);a.const(11,'\n#md#c(-8323200)舒适:')
 a.mark('total');a.emit('MOV',12,5);a.emit('CAT',3,b=10,c=12)
 a.emit('ISEQV',7,9);a.jmp(710,24)
 a.const(11,'#c(-8323200) (+');a.emit('ISGE',7,9);a.jmp('bonus',24);a.const(11,'#c(-45824) (')
 a.mark('bonus');a.emit('MOV',10,3);a.emit('MOV',12,7);a.const(13,')#W');a.emit('CAT',3,b=10,c=13);a.jmp(710,24)
 a.finish();p.bc[702]=jump(702,start,24)
 return Proto(rebuild_proto(p),p.idx)

def build(runtime=None,rebuild_history=False):
 # The predecessor is an immutable, hash-pinned build input. Reusing it
 # does not claim to have recompiled or retested its historical sources.
 path=W/'game_v197.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  print('Building predecessor resource (missing, mismatched, or explicitly requested).',flush=True)
  subprocess.run(['python3',str(W/'patch_v197.py')]+(['--rebuild-history']if rebuild_history else [])+(['--runtime',runtime]if runtime else []),cwd=W,check=True,stdout=subprocess.DEVNULL)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 display_path=W/'game_v193.res'
 if not display_path.exists()or hashlib.sha256(display_path.read_bytes()).hexdigest()!=DISPLAY_SHA:
  subprocess.run(['python3',str(W/'patch_v193.py')]+(['--runtime',runtime]if runtime else []),cwd=W,check=True,stdout=subprocess.DEVNULL)
 display=display_path.read_bytes();assert hashlib.sha256(display).hexdigest()==DISPLAY_SHA
 _,reference=decode(display,[12]);outer,mods=decode(base,[12,14,30])
 assert mods[12].protos[299].raw==reference[12].protos[299].raw
 mods[12].protos[300]=repair_tooltip(reference[12].protos[300])
 for d in mods.values():
  for i,p in enumerate(d.protos):
   touched=False
   for k,v in enumerate(p.kgc):
    if isinstance(v,bytes):
     n=v.replace(b'Guimeng patch v1.197',b'Guimeng patch v1.198').replace(b'Guimeng v1.197 diagnostics',b'Guimeng v1.198 diagnostics').replace(b'patch=v1.197',b'patch=v1.198')
     if n!=v:p.kgc[k]=n;p.kraw[k]=encstr(n);touched=True
   if touched:d.protos[i]=Proto(rebuild_proto(p),i)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(old[m].protos)if p.raw!=d.protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v198.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  encrypted=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=encrypted if m==12 else encrypted.hex().upper().encode()
  p=outer.protos[0];k=p.nkgc-1-m;p.kgc[k]=value;p.kraw[k]=encstr(value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v198.res').write_bytes(data)
 result={'version':'v1.198','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'display_reference_sha256':DISPLAY_SHA,'scope':'v193 display restored; only original comfort row replaced','rules_changed':False}
 (W/'build_v198.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print({k:v for k,v in result.items()if k!='unused'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true',help='Rebuild predecessor sources instead of reusing the hash-pinned resource');x=a.parse_args();build(str(Path(x.runtime).resolve())if x.runtime else None,x.rebuild_history)
