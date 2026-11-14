"""Use existing event-safe control lookup for auxiliary potion searches."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import ad,abc,jump,gcid,encstr,rebuild_proto,rebuild_dump
from bytecode_relocate import replace_instructions
from ljdis import OPS
from resource_tools import decode
W=Path(__file__).resolve().parent
BASE_SHA='10e371990ff742143e4f680ec96286c4d7c15b6d1c843b27370b370a34f8d0ad'

def repair(p):
 assert (p.params,p.frame,p.nbc,p.nkgc)==(3,10,287,47)
 ids={s:gcid(p,s)for s in ['Gly独','取控件对象','物品格子']};p=Proto(rebuild_proto(p),p.idx)
 assert max(ids.values())<256
 repl={}
 for pc,dest in [(18,1),(198,0),(244,0)]:
  assert p.bc[pc]==ad('GGET',7,gcid(p,'Sys'))
  assert p.bc[pc+4]==abc('TGETV',dest,7,6)
  # Existing O(1) exported lookup returns the real public slot control.
  repl[pc]=[ad('GGET',7,ids['Gly独']),abc('TGETS',7,7,ids['取控件对象']),ad('KSTR',8,ids['物品格子']),ad('MOV',9,6),abc('CAT',8,8,9),abc('CALL',7,2,2),ad('MOV',dest,7)]
  for i in range(pc+1,pc+5):repl[i]=[]
 # The bag-capacity fallback had no guard against an absent control.
 # Quick/ordinary potion loops already retain their original type guards.
 repl[23]=[ad('ISEQP',1,0),0,p.bc[23]]
 raw,mp=replace_instructions(p,repl);q=Proto(raw,p.idx)
 q.bc[mp[23]+1]=jump(mp[23]+1,mp[57],10)
 return Proto(rebuild_proto(q),p.idx),mp

def build(runtime=None,rebuild_history=False):
 # The predecessor is an immutable, hash-pinned build input. Reusing it
 # does not claim to have recompiled or retested its historical sources.
 path=W/'game_v191.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  print('Building predecessor resource (missing, mismatched, or explicitly requested).',flush=True)
  subprocess.run(['python3',str(W/'patch_v191.py')]+(['--runtime',runtime]if runtime else []),cwd=W,check=True,stdout=subprocess.DEVNULL)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30]);mods[12].protos[283],mp=repair(mods[12].protos[283])
 for d in mods.values():
  for i,p in enumerate(d.protos):
   touched=False
   for k,v in enumerate(p.kgc):
    if isinstance(v,bytes):
     n=v.replace(b'Guimeng patch v1.191',b'Guimeng patch v1.192').replace(b'Guimeng v1.191 diagnostics',b'Guimeng v1.192 diagnostics').replace(b'patch=v1.191',b'patch=v1.192')
     if n!=v:p.kgc[k]=n;p.kraw[k]=encstr(n);touched=True
   if touched:d.protos[i]=Proto(rebuild_proto(p),i)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(old[m].protos)if p.raw!=d.protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v192.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  encrypted=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=encrypted if m==12 else encrypted.hex().upper().encode()
  p=outer.protos[0];k=p.nkgc-1-m;p.kgc[k]=value;p.kraw[k]=encstr(value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v192.res').write_bytes(data)
 result={'version':'v1.192','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'control_lookup_reads':[18,198,244],'aux_relocations':mp,'rules_changed':False}
 (W/'build_v192.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print({k:v for k,v in result.items()if k!='aux_relocations'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true',help='Rebuild predecessor sources instead of reusing the hash-pinned resource');x=a.parse_args();build(str(Path(x.runtime).resolve())if x.runtime else None,x.rebuild_history)
