"""Restore legacy talisman accumulation without replacing Ling's mechanism."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import ad,abc,jump,gcid,encstr,rebuild_proto,rebuild_dump
from bytecode_relocate import replace_instructions
from ljdis import OPS
from resource_tools import decode
W=Path(__file__).resolve().parent
BASE_SHA='4bb6eb706e39cb4f900805f26cb8a0bb842c67c234158e39b94a2f606cad86c7'

def repair(p):
 assert (p.params,p.frame,p.nbc)==(6,20,422)
 name=gcid(p,'名称');item=gcid(p,'道具');ling=gcid(p,'聚灵符咒_灵')
 assert p.bc[415]==ad('ISNES',9,ling) and OPS[p.bc[416]&255]=='JMP'
 assert 416+1+(p.bc[416]>>16)-32768==396 and p.bc[396]==ad('RET0',0,1)
 assert p.bc[397]==ad('KNUM',8,1) and 398+1+(p.bc[398]>>16)-32768==52
 assert p.bc[417]==ad('FNEW',9,72) and p.bc[382]==jump(382,6,0)
 # JMP's A field controls recorder liveness, not just the branch offset.
 # Preserve all original live registers through historical trampolines.
 p.bc=[(x&~0xff00)|(20<<8)if OPS[x&255]=='JMP'and (x>>8&255)<20 else x for x in p.bc]
 p=Proto(rebuild_proto(p),p.idx)
 extra={s:gcid(p,s)for s in ['type','number','huge','math']};p=Proto(rebuild_proto(p),p.idx)
 repl={};fix=[]
 # Run the exact existing Ling helper once, with the unchanged raw storage
 # amount, on the original storage-only route. Normal XP / claims bypass it.
 repl[382]=[ad('GGET',8,extra['type']),ad('MOV',9,1),abc('CALL',8,2,2),ad('ISNES',8,extra['number']),0,ad('KSHORT',8,0),ad('ISLE',1,8),0,ad('ISNEV',1,1),0,ad('GGET',8,extra['math']),abc('TGETS',8,8,extra['huge']),ad('ISEQV',1,8),0,ad('FNEW',8,72),ad('KSHORT',9,0),ad('MOV',10,1),abc('CALL',8,1,3),0]
 for at in [4,7,9,13]:fix.append((382,at,396))
 fix.append((382,len(repl[382])-1,6))
 # Legacy selection remains hero first. Ling has already processed both
 # owners independently, and must not block a legacy talisman on the other.
 for pc,slot,skip in [(22,'物品格子12',24),(44,'物品格子408',45)]:
  repl[pc]=[ad('GGET',8,gcid(p,slot)),abc('TGETS',8,8,item),abc('TGETS',8,8,name),ad('ISEQS',8,ling),0,p.bc[pc]]
  fix.append((pc,4,skip))
 repl[416]=[0];fix.append((416,0,397))
 raw,mp=replace_instructions(p,repl);q=Proto(raw,p.idx)
 for pc,at,to in fix:q.bc[mp[pc]+at]=jump(mp[pc]+at,mp[to],20)
 return Proto(rebuild_proto(q),p.idx),mp,{str(k):len(v)for k,v in repl.items()}

def build(runtime=None):
 subprocess.run(['python3',str(W/'patch_v189.py')]+(['--runtime',runtime]if runtime else []),cwd=W,check=True,stdout=subprocess.DEVNULL)
 base=(W/'game_v189.res').read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30]);mods[12].protos[258],mp,sizes=repair(mods[12].protos[258])
 for d in mods.values():
  for i,p in enumerate(d.protos):
   touched=False
   for k,v in enumerate(p.kgc):
    if isinstance(v,bytes):
     n=v.replace(b'Guimeng patch v1.189',b'Guimeng patch v1.190').replace(b'Guimeng v1.189 diagnostics',b'Guimeng v1.190 diagnostics').replace(b'patch=v1.189',b'patch=v1.190')
     if n!=v:p.kgc[k]=n;p.kraw[k]=encstr(n);touched=True
   if touched:d.protos[i]=Proto(rebuild_proto(p),i)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(old[m].protos)if p.raw!=d.protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v190.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  encrypted=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=encrypted if m==12 else encrypted.hex().upper().encode()
  p=outer.protos[0];k=p.nkgc-1-m;p.kgc[k]=value;p.kraw[k]=encstr(value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v190.res').write_bytes(data)
 result={'version':'v1.190','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'storage_relocations':mp,'inserted_blocks':sizes,'ling_helpers_unchanged':[35,36,256,257],'legacy_priority':'hero first, mercenary fallback; Ling processed independently once','rules_changed':False}
 (W/'build_v190.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print({k:v for k,v in result.items()if k!='storage_relocations'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');x=a.parse_args();build(str(Path(x.runtime).resolve())if x.runtime else None)
