"""Restore the original autosave cadence lost with v181 checker removal."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import jump,encstr,rebuild_dump
from bytecode_relocate import replace_instructions,numeric_and_debug
from resource_tools import decode
W=Path(__file__).resolve().parent
BASE_SHA='69907c7a45057290904df0c804f8734866c3960af50e3f4dc951cf9dab8024a4'

def build(runtime=None):
 subprocess.run(['python3',str(W/'patch_v186.py')]+(['--runtime',runtime]if runtime else []),cwd=W,check=True,stdout=subprocess.DEVNULL)
 base=(W/'game_v186.res').read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30]);_,historical=decode((W/'game_v180.res').read_bytes(),[12])
 p=mods[12].protos[20];q=historical[12].protos[20]
 assert p.kraw==q.kraw and numeric_and_debug(p)[0]==numeric_and_debug(q)[0]
 # Original 662..669 guarded the whole old check/autosave block. Restore
 # just this timing/release-mode gate directly before the retained autosave.
 assert p.bc[119:132]==q.bc[932:945]
 guard=list(q.bc[662:670]);at=119;after=132+len(guard)
 for i in [3,7]:guard[i]=jump(at+i,after,1)
 raw,mp=replace_instructions(p,{at:guard+[p.bc[at]]});mods[12].protos[20]=Proto(raw,20)
 for m,d in mods.items():
  for i,p in enumerate(d.protos):
   touched=False
   for k,value in enumerate(p.kgc):
    if isinstance(value,bytes):
     v=value.replace(b'Guimeng patch v1.186',b'Guimeng patch v1.187').replace(b'Guimeng v1.186 diagnostics',b'Guimeng v1.187 diagnostics').replace(b'patch=v1.186',b'patch=v1.187')
     if v!=value:p.kgc[k]=v;p.kraw[k]=encstr(v);touched=True
   if touched:
    from patch_v139 import rebuild_proto
    d.protos[i]=Proto(rebuild_proto(p),i)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(old[m].protos)if p.raw!=d.protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw
  (W/f'module_{m}_v187.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
  value=enc if m==12 else enc.hex().upper().encode()
  p=outer.protos[0];k=p.nkgc-1-m;p.kgc[k]=value;p.kraw[k]=encstr(value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v187.res').write_bytes(data)
 result={'version':'v1.187','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'restored_original_instructions':'v180 module12/proto20 PCs662..669 only','autosave_ticks':3000,'timer_period_ms':100,'timer_relocations':{str(k):v for k,v in mp.items()},'rules_changed':False,'checks_restored':False}
 (W/'build_v187.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in result.items()if k!='timer_relocations'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');x=a.parse_args();build(str(Path(x.runtime).resolve())if x.runtime else None)
