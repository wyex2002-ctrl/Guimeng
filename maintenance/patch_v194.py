"""Show already-generated comfort stats in the current equipment tooltip."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import ad,abc,jump,gcid,encstr,rebuild_proto,rebuild_dump
from bytecode_relocate import replace_instructions
from ljdis import OPS
from resource_tools import decode
W=Path(__file__).resolve().parent
BASE_SHA='90467c334b610e571ef94bbf50313463492d002996ea25d208fc1b509a6226f5'

def repair_tooltip(p):
 assert(p.params,p.frame,p.nbc)==(3,24,3232)
 key=gcid(p,'身体舒适');oldkey=gcid(p,'敏捷几率');label=gcid(p,'\n#md#W舒适:')
 p=Proto(rebuild_proto(p),p.idx)
 block=[]
 for pc in range(2734,2763):
  x=p.bc[pc];op=OPS[x&255]
  if pc==2749:
   assert op=='JMP';x=ad('KSTR',11,label)
  elif op=='TGETS'and(x>>16&255)==oldkey:x=(x&~0xff0000)|(key<<16)
  elif op in ('JMP','UCLO','FORI','FORL','LOOP','ISNEXT','ITERL'):
   assert 2734<=pc+1+(x>>16)-32768<=2763,(pc,x)
   if op=='JMP':x=(x&~0xff00)|(24<<8)
  block.append(x)
 assert len(block)==29
 # Incoming original jumps to the end of the preceding stat must also
 # enter this new block; all original targets/debug ranges are relocated.
 raw,mp=replace_instructions(p,{2763:block+[p.bc[2763]]})
 return Proto(raw,p.idx),mp

def build(runtime=None,rebuild_history=False):
 # The predecessor is an immutable, hash-pinned build input. Reusing it
 # does not claim to have recompiled or retested its historical sources.
 path=W/'game_v193.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  print('Building predecessor resource (missing, mismatched, or explicitly requested).',flush=True)
  subprocess.run(['python3',str(W/'patch_v193.py')]+(['--rebuild-history']if rebuild_history else [])+(['--runtime',runtime]if runtime else []),cwd=W,check=True,stdout=subprocess.DEVNULL)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30]);mods[12].protos[300],mp=repair_tooltip(mods[12].protos[300])
 for d in mods.values():
  for i,p in enumerate(d.protos):
   touched=False
   for k,v in enumerate(p.kgc):
    if isinstance(v,bytes):
     n=v.replace(b'Guimeng patch v1.193',b'Guimeng patch v1.194').replace(b'Guimeng v1.193 diagnostics',b'Guimeng v1.194 diagnostics').replace(b'patch=v1.193',b'patch=v1.194')
     if n!=v:p.kgc[k]=n;p.kraw[k]=encstr(n);touched=True
   if touched:d.protos[i]=Proto(rebuild_proto(p),i)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(old[m].protos)if p.raw!=d.protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v194.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  encrypted=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=encrypted if m==12 else encrypted.hex().upper().encode()
  p=outer.protos[0];k=p.nkgc-1-m;p.kgc[k]=value;p.kraw[k]=encstr(value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v194.res').write_bytes(data)
 result={'version':'v1.194','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'tooltip_relocations':mp,'inserted_stat':'身体舒适','rules_changed':False}
 (W/'build_v194.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print({k:v for k,v in result.items()if k!='tooltip_relocations'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true',help='Rebuild predecessor sources instead of reusing the hash-pinned resource');x=a.parse_args();build(str(Path(x.runtime).resolve())if x.runtime else None,x.rebuild_history)
