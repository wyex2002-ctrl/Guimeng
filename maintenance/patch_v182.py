"""Fix v181 startup copy/check mismatch without restoring data enforcement."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import encstr,rebuild_proto,rebuild_dump
from bytecode_relocate import replace_instructions
from resource_tools import decode
W=Path(__file__).resolve().parent
BASE_SHA='1552a692f4b431067daac8743c118fa6f825a027b31018d1a59df3c99882db03'
# Original v181 PCs, end exclusive. Keep proxy tags and task/story callbacks.
REMOVALS={12:{2:[(15,26)],3:[(3,32)],4:[(30,45)]},30:{9:[(0,77)],12:[(7,11)],22:[(9,14)],23:[(11,37),(65,93)]}}

def build(runtime=None):
 subprocess.run(['python3',str(W/'patch_v181.py')]+(['--runtime',runtime]if runtime else []),cwd=W,check=True,stdout=subprocess.DEVNULL)
 base=(W/'game_v181.res').read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30]);changes={};relocations={}
 for module,entries in REMOVALS.items():
  for index,spans in entries.items():
   p=mods[module].protos[index];repl={pc:[]for start,end in spans for pc in range(start,end)}
   raw,mp=replace_instructions(p,repl);mods[module].protos[index]=Proto(raw,index)
   relocations[f'{module}:{index}']={str(k):v for k,v in mp.items()}
 # Keep error-report version labels accurate in both legacy callback installers.
 for module,d in mods.items():
  for index,p in enumerate(d.protos):
   touched=False
   for k,value in enumerate(p.kgc):
    if isinstance(value,bytes):
     value2=value.replace(b'Guimeng patch v1.181',b'Guimeng patch v1.182').replace(b'Guimeng v1.181 diagnostics',b'Guimeng v1.182 diagnostics').replace(b' patch=v1.181 ',b' patch=v1.182 ').replace(b'patch=v1.105',b'patch=v1.182')
     if value2!=value:p.kgc[k]=value2;p.kraw[k]=encstr(value2);touched=True
   if touched:p.raw=rebuild_proto(p);d.protos[index]=Proto(p.raw,index)
 _,old=decode(base,mods)
 for module,d in mods.items():
  changes[module]=[i for i,(p,q)in enumerate(zip(old[module].protos,d.protos))if p.raw!=q.raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw
  (W/f'module_{module}_v182.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  payload=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));encoded=payload if module==12 else payload.hex().upper().encode()
  p=outer.protos[0];k=p.nkgc-1-module;p.kgc[k]=encoded;p.kraw[k]=encstr(encoded)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v182.res').write_bytes(data)
 result={'version':'v1.182','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'relocations':relocations,'rules_changed':False}
 (W/'build_v182.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in result.items()if k!='relocations'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');build(a.parse_args().runtime)
