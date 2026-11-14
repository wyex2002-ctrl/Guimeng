"""Change only accuracy/evasion hit ratios for both sides; preserve all stats."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4,Reader,uleb
from patch_v139 import ad,abc,jump,gcid,encstr,rebuild_proto,rebuild_dump,Asm
from bytecode_relocate import replace_instructions,numeric_and_debug
from ljdis import OPS
from resource_tools import decode
W=Path(__file__).resolve().parent
BASE_SHA='50db3654b8612e5dd025ce8fedfcc27e06bfdd59289af37607eaabc97dca7cd4'

def number_pool(p):
 r=Reader(p.raw[p.kend:]);values=[]
 for _ in range(p.nkn):
  x=r.u()
  values.append(struct.unpack('<d',struct.pack('<II',(x>>1)&0xffffffff,r.u()&0xffffffff))[0]if x&1 else x>>1)
 return values

def append_factor(p):
 # Append one exact binary 2.5; existing numeric indices/bytes stay intact.
 numeric,debug=numeric_and_debug(p)
 lo,hi=struct.unpack('<II',struct.pack('<d',2.5))
 header=bytes([p.flags,p.params,p.frame,p.nuv])+uleb(p.nkgc)+uleb(p.nkn+1)+uleb(p.nbc)+uleb(p.ndbg)
 if p.ndbg:header+=uleb(p.first)+uleb(p.lines)
 raw=header+struct.pack('<'+'I'*p.nbc,*p.bc)+p.uv+b''.join(p.kraw)+numeric+uleb((lo<<1)|1)+uleb(hi)+debug
 return Proto(raw,p.idx),p.nkn

def hit_sites(mods):
 out=[];representative=mods[12].protos[10298]
 for p in mods[12].protos:
  if p.bc==representative.bc and p.kgc==representative.kgc:out.append((12,p.idx,469))
 assert len(out)==247
 out.extend([(12,278,56),(12,18008,106),(22,44,346),(22,44,542),(26,29,461)])
 return sorted(out)

def repair_formula(p,sites):
 p,k=append_factor(p);assert k<256 and number_pool(p)[k]==2.5
 changes={}
 for pc in sites:
  x,y,z=p.bc[pc:pc+3]
  assert [OPS[v&255]for v in[x,y,z]]==['ADDVV','DIVVV','MULVN']
  dest,a,d=x>>8&255,x>>24,x>>16&255
  numerator=y>>24;result=y>>8&255
  assert y>>16&255==dest and dest!=numerator and dest!=d
  assert number_pool(p)[z>>16&255]==100
  # A/(A+D/2.5) is algebraically 2.5A/(2.5A+D). Only the
  # old denominator scratch is changed: never write an accuracy field or
  # multiply a live accuracy local later used in another probability.
  changes[pc]=[abc('DIVVN',dest,d,k),abc('ADDVV',dest,numerator,dest)]
  zero=number_pool(p).index(0)
  changes[pc+1]=[ad('ISNEN',dest,zero),0,ad('KSHORT',result,0),0,y]
 raw,mapping=replace_instructions(p,changes);q=Proto(raw,p.idx)
 for pc in sites:
  at=mapping[pc+1]
  q.bc[at+1]=jump(at+1,at+4,q.frame)
  q.bc[at+3]=jump(at+3,mapping[pc+3],q.frame)
 return Proto(rebuild_proto(q),p.idx),mapping

def build(runtime=None,rebuild_history=False):
 # The predecessor is an immutable, hash-pinned build input. Reusing it
 # does not claim to have recompiled or retested its historical sources.
 path=W/'game_v195.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  print('Building predecessor resource (missing, mismatched, or explicitly requested).',flush=True)
  subprocess.run(['python3',str(W/'patch_v195.py')]+(['--rebuild-history']if rebuild_history else [])+(['--runtime',runtime]if runtime else []),cwd=W,check=True,stdout=subprocess.DEVNULL)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,22,26,30]);sites=hit_sites(mods);relocations={}
 grouped={}
 for m,i,pc in sites:grouped.setdefault((m,i),[]).append(pc)
 for (m,i),pcs in grouped.items():mods[m].protos[i],relocations[f'{m}/{i}']=repair_formula(mods[m].protos[i],pcs)
 for d in mods.values():
  for i,p in enumerate(d.protos):
   touched=False
   for k,v in enumerate(p.kgc):
    if isinstance(v,bytes):
     n=v.replace(b'Guimeng patch v1.195',b'Guimeng patch v1.196').replace(b'Guimeng v1.195 diagnostics',b'Guimeng v1.196 diagnostics').replace(b'patch=v1.195',b'patch=v1.196')
     if n!=v:p.kgc[k]=n;p.kraw[k]=encstr(n);touched=True
   if touched:d.protos[i]=Proto(rebuild_proto(p),i)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(old[m].protos)if p.raw!=d.protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v196.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  encrypted=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=encrypted if m==12 else encrypted.hex().upper().encode()
  p=outer.protos[0];k=p.nkgc-1-m;p.kgc[k]=value;p.kraw[k]=encstr(value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v196.res').write_bytes(data)
 result={'version':'v1.196','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'hit_sites':sites,'relocations':relocations,'hit_formula':'2.5*A/(2.5*A+D), evaluated as A/(A+D/2.5); both sides','rules_changed':True}
 (W/'build_v196.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print({k:v for k,v in result.items()if k not in ('hit_sites','relocations','changed_prototypes')})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true',help='Rebuild predecessor sources instead of reusing the hash-pinned resource');x=a.parse_args();build(str(Path(x.runtime).resolve())if x.runtime else None,x.rebuild_history)
