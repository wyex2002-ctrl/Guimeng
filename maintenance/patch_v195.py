"""Allow one skeleton and one beast using the existing per-pet registry."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import ad,abc,jump,gcid,encstr,rebuild_proto,rebuild_dump,Asm
from bytecode_relocate import replace_instructions
from ljdis import OPS
from resource_tools import decode
W=Path(__file__).resolve().parent
BASE_SHA='927a9c7e579103f5c3cd29a28f9fd06e724793c98fdf2e12221b3bf8fb653583'

SUMMONERS=[4498,4511,4539,4552,4565,4583,4596,4609,4627,4640,4653,4666,4679,4692,4710,4723,4741,4987,5000]

def repair_summon(p):
 assert(p.params,p.frame,p.nbc)==(6,30,1501)
 assert p.bc[422]==ad('KSHORT',7,1) and p.bc[458]==ad('UCLO',0,32768+1378-459)
 a=Asm(p);start=a.base
 # R0..6 retain the original skill invocation and selected skill data.
 # Iterator state R10..14 is below the scratch CALL base R20.
 a.emit('KSHORT',7,0)
 a.glob(8,'Ux雌');a.get(8,8,'胚子考虑');a.emit('CALL',8,b=2,c=1);a.get(8,8,'宝宝')
 a.emit('UGET',9,0);a.get(9,9,'id')
 a.glob(10,'pairs');a.emit('MOV',11,8);a.emit('CALL',10,b=4,c=2);a.jmp('iter',30)
 a.mark('loop')
 a.glob(20,'type');a.emit('MOV',21,14);a.emit('CALL',20,b=2,c=2)
 a.emit('ISNES',20,gcid(p,'number'));a.jmp('iter',30)
 a.emit('KSHORT',20,0);a.emit('ISGE',20,14);a.jmp('iter',30)
 a.glob(20,'Gly独');a.get(20,20,'事件对象');a.emit('MOV',21,14);a.emit('CALL',20,b=2,c=2)
 a.emit('ISEQP',20,0);a.jmp('iter',30)
 a.get(21,20,'HP');a.emit('KSHORT',22,0);a.emit('ISGE',22,21);a.jmp('iter',30)
 a.get(21,20,'附加');a.get(22,21,'魅惑');a.emit('ISNEP',22,0);a.jmp('iter',30)
 a.get(22,21,'召唤技能');a.emit('ISNEV',22,9);a.jmp('iter',30)
 a.emit('KSHORT',22,0);a.emit('ISEQV',7,22);a.jmp('keep',30)
 # An old enhanced skill may have left two same-kind pets. Retire only
 # extra matching live IDs, leaving the original death bookkeeping intact.
 a.emit('ISEQV',7,14);a.jmp('iter',30)
 a.emit('KSHORT',22,0);a.set(22,20,'HP');a.jmp('iter',30)
 a.mark('keep');a.emit('MOV',7,14)
 a.mark('iter');a.emit('ITERC',13,b=3,c=3);a.jmp('loop',13,'ITERL')
 a.emit('KSHORT',20,0);a.emit('ISEQV',7,20);a.jmp(459,30)
 # Reuse the original per-skill recall path. Never call the kill-all mode 4.
 a.glob(20,'Ux雌');a.get(20,20,'窗口相关');a.get(20,20,'宝宝操作')
 a.emit('KSHORT',21,2);a.emit('MOV',22,9);a.emit('CALL',20,b=1,c=3);a.emit('RET0',0,1)
 a.finish();p.bc[422]=jump(422,start,30)
 return Proto(rebuild_proto(p),p.idx)

def build(runtime=None,rebuild_history=False):
 # The predecessor is an immutable, hash-pinned build input. Reusing it
 # does not claim to have recompiled or retested its historical sources.
 path=W/'game_v194.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  print('Building predecessor resource (missing, mismatched, or explicitly requested).',flush=True)
  subprocess.run(['python3',str(W/'patch_v194.py')]+(['--rebuild-history']if rebuild_history else [])+(['--runtime',runtime]if runtime else []),cwd=W,check=True,stdout=subprocess.DEVNULL)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30]);
 original=mods[12].protos[4498]
 for i in SUMMONERS:
  p=mods[12].protos[i];assert p.bc==original.bc and p.kgc==original.kgc
 # All nineteen registered copies share dispatch code, even though their
 # source/debug records differ. Keep their existing child prototypes.
 for i in SUMMONERS:mods[12].protos[i]=repair_summon(mods[12].protos[i])
 for d in mods.values():
  for i,p in enumerate(d.protos):
   touched=False
   for k,v in enumerate(p.kgc):
    if isinstance(v,bytes):
     n=v.replace(b'Guimeng patch v1.194',b'Guimeng patch v1.195').replace(b'Guimeng v1.194 diagnostics',b'Guimeng v1.195 diagnostics').replace(b'patch=v1.194',b'patch=v1.195')
     if n!=v:p.kgc[k]=n;p.kraw[k]=encstr(n);touched=True
   if touched:d.protos[i]=Proto(rebuild_proto(p),i)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(old[m].protos)if p.raw!=d.protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v195.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  encrypted=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=encrypted if m==12 else encrypted.hex().upper().encode()
  p=outer.protos[0];k=p.nkgc-1-m;p.kgc[k]=value;p.kraw[k]=encstr(value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v195.res').write_bytes(data)
 result={'version':'v1.195','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'summoners':SUMMONERS,'summon_limit':'one live skeleton and one live beast; recall same kind; retire same-kind legacy extras','rules_changed':True}
 (W/'build_v195.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print({k:v for k,v in result.items()if k!='summoners'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true',help='Rebuild predecessor sources instead of reusing the hash-pinned resource');x=a.parse_args();build(str(Path(x.runtime).resolve())if x.runtime else None,x.rebuild_history)
