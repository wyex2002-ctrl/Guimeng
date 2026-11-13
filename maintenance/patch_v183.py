"""Restore the original startup API registration and disabled-check ABI."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import ad,encstr,rebuild_proto,rebuild_dump
from bytecode_relocate import replace_instructions
from resource_tools import decode
W=Path(__file__).resolve().parent
BASE_SHA='c232a3c0195ba6096c6f2e03c1e8ec94b9ed5dcde0ce2fcc5c5011bbe253e5b2'

def build(runtime=None):
 subprocess.run(['python3',str(W/'patch_v182.py')]+(['--runtime',runtime]if runtime else []),cwd=W,check=True,stdout=subprocess.DEVNULL)
 base=(W/'game_v182.res').read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30,34]);changes={};relocations={}
 # Recover only the six ORIGINAL mode binding instructions; this getter is
 # used by channels, shops, item handling and loading, not an anti-cheat test.
 _,prior=decode((W/'game_v180.res').read_bytes(),[12,34])
 p=mods[12].protos[87];original=prior[12].protos[87]
 assert p.kgc==original.kgc and p.uv==original.uv
 raw,mp=replace_instructions(p,{0:original.bc[74:80]+[p.bc[0]]})
 mods[12].protos[87]=Proto(raw,87)
 relocations['12:87']={str(k):v for k,v in mp.items()}
 # The factory still returns its original nine-method table, but every method
 # is inert. Never reintroduce the old HTTP reports, checks or punishment.
 mods[12].protos[86]=Proto(prior[12].protos[86].raw,86)
 for i in range(77,86):assert mods[12].protos[i].bc==[ad('RET0',0,1)]
 # The removed inventory timer callback originally returns true. Retain that
 # return contract without invoking the old hack_item_copy action.
 p=mods[34].protos[7];original=prior[34].protos[7]
 raw,_=replace_instructions(p,{0:original.bc[-2:]})
 mods[34].protos[7]=Proto(raw,7)
 # Keep error-report version labels accurate in both legacy callback installers.
 for module,d in mods.items():
  for index,p in enumerate(d.protos):
   touched=False
   for k,value in enumerate(p.kgc):
    if isinstance(value,bytes):
     value2=value.replace(b'Guimeng patch v1.182',b'Guimeng patch v1.183').replace(b'Guimeng v1.182 diagnostics',b'Guimeng v1.183 diagnostics').replace(b'patch=v1.182',b'patch=v1.183')
     if value2!=value:p.kgc[k]=value2;p.kraw[k]=encstr(value2);touched=True
   if touched:p.raw=rebuild_proto(p);d.protos[index]=Proto(p.raw,index)
 _,old=decode(base,mods)
 for module,d in mods.items():
  changes[module]=[i for i,(p,q)in enumerate(zip(old[module].protos,d.protos))if p.raw!=q.raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw
  (W/f'module_{module}_v183.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  payload=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));encoded=payload if module==12 else payload.hex().upper().encode()
  p=outer.protos[0];k=p.nkgc-1-module;p.kgc[k]=encoded;p.kraw[k]=encstr(encoded)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v183.res').write_bytes(data)
 result={'version':'v1.183','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'relocations':relocations,'rules_changed':False}
 (W/'build_v183.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in result.items()if k!='relocations'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');build(a.parse_args().runtime)
