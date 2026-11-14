"""Distinguish level-four and level-five enhancement books by display name."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import ad,abc,jump,gcid,encstr,rebuild_proto,rebuild_dump
from bytecode_relocate import replace_instructions
from patch_v181 import save_table
from ljdis import OPS
from resource_tools import decode
W=Path(__file__).resolve().parent
BASE_SHA='56032988b1fa172a4400b2e21d0671015f6a4381d010c81d463ddb2334ab0082'

def rename_templates(p):
 names=[]
 for logical in range(p.nkgc):
  v=p.gc(logical)
  if not(isinstance(v,tuple)and v[0]=='table'):continue
  a=dict(v[2]);name=a.get('名称'.encode('gbk'))
  if not(isinstance(name,bytes)and name.startswith(('四级'.encode('gbk'),'五级'.encode('gbk')))):continue
  old=a['显示名'.encode('gbk')];assert old==name[4:]+'(秘籍)'.encode('gbk')
  new=name+'(秘籍)'.encode('gbk')
  save_table(p,logical,('table',v[1],[(k,new if k=='显示名'.encode('gbk')else x)for k,x in v[2]]))
  names.append(name.decode('gbk'))
 assert len(names)==148 and len(set(names))==148
 return Proto(rebuild_proto(p),p.idx),names

def repair_reset(p):
 # Normalize only the cosmetic saved override before the original updater
 # applies it and formats the cached tooltip. Internal item keys stay intact.
 assert(p.params,p.frame,p.nbc)==(6,15,192)
 ids={k:gcid(p,k)for k in ['强化书','显示名','type','table']};p=Proto(rebuild_proto(p),p.idx)
 block=[abc('TGETS',11,9,gcid(p,'附加')),abc('TGETS',11,11,ids['强化书']),ad('KSHORT',12,4),ad('ISEQV',11,12),0,ad('KSHORT',12,5),ad('ISEQV',11,12),0,0,ad('GGET',11,ids['type']),ad('MOV',12,4),abc('CALL',11,2,2),ad('ISEQS',11,ids['table']),0,0,abc('TGETS',11,9,ids['显示名']),abc('TSETS',11,4,ids['显示名']),p.bc[124]]
 raw,mp=replace_instructions(p,{124:block});q=Proto(raw,p.idx)
 for at,to in [(4,9),(7,9),(8,17),(13,15),(14,17)]:q.bc[mp[124]+at]=jump(mp[124]+at,mp[124]+to,15)
 return Proto(rebuild_proto(q),p.idx),mp

def build(runtime=None,rebuild_history=False):
 # The predecessor is an immutable, hash-pinned build input. Reusing it
 # does not claim to have recompiled or retested its historical sources.
 path=W/'game_v192.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  print('Building predecessor resource (missing, mismatched, or explicitly requested).',flush=True)
  subprocess.run(['python3',str(W/'patch_v192.py')]+(['--rebuild-history']if rebuild_history else [])+(['--runtime',runtime]if runtime else []),cwd=W,check=True,stdout=subprocess.DEVNULL)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30]);mods[12].protos[4090],names=rename_templates(mods[12].protos[4090]);mods[14].protos[437],mp=repair_reset(mods[14].protos[437])
 for d in mods.values():
  for i,p in enumerate(d.protos):
   touched=False
   for k,v in enumerate(p.kgc):
    if isinstance(v,bytes):
     n=v.replace(b'Guimeng patch v1.192',b'Guimeng patch v1.193').replace(b'Guimeng v1.192 diagnostics',b'Guimeng v1.193 diagnostics').replace(b'patch=v1.192',b'patch=v1.193')
     if n!=v:p.kgc[k]=n;p.kraw[k]=encstr(n);touched=True
   if touched:d.protos[i]=Proto(rebuild_proto(p),i)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(old[m].protos)if p.raw!=d.protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v193.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  encrypted=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=encrypted if m==12 else encrypted.hex().upper().encode()
  p=outer.protos[0];k=p.nkgc-1-m;p.kgc[k]=value;p.kraw[k]=encstr(value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v193.res').write_bytes(data)
 result={'version':'v1.193','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'renamed_books':names,'reset_relocations':mp,'rules_changed':False}
 (W/'build_v193.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print({k:v for k,v in result.items()if k not in ('reset_relocations','renamed_books')})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true',help='Rebuild predecessor sources instead of reusing the hash-pinned resource');x=a.parse_args();build(str(Path(x.runtime).resolve())if x.runtime else None,x.rebuild_history)
