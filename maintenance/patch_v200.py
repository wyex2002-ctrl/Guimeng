"""Show already-generated comfort stats in the current equipment tooltip."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4,Reader,uleb
from patch_v139 import ad,abc,jump,gcid,encstr,rebuild_proto,rebuild_dump,Asm
from bytecode_relocate import replace_instructions
from ljdis import OPS
from resource_tools import decode
W=Path(__file__).resolve().parent
BASE_SHA='7721c00163d1a53fd579aa57d2dac813c8280f4320ff3e07195e8df80cbc2319'

VERSION='1.200'
GOLD=0xffffe6a3
OUTLINE=0xff4a2c12
FONT='宋_9_鎏金'

def numbers(p,replace=None,append=()):
 r=Reader(p.raw[p.kend:]);parts=[]
 for i in range(p.nkn):
  at=r.p;x=r.u()
  if x&1:r.u()
  parts.append(uleb(replace[i]*2)if replace and i in replace else r.b[at:r.p])
 numeric=b''.join(parts)+b''.join(uleb(v*2)for v in append);debug=r.b[r.p:]
 header=bytes([p.flags,p.params,p.frame,p.nuv])+uleb(p.nkgc)+uleb(p.nkn+len(append))+uleb(p.nbc)+uleb(p.ndbg)
 if p.ndbg:header+=uleb(p.first)+uleb(p.lines)
 return Proto(header+struct.pack('<'+'I'*p.nbc,*p.bc)+p.uv+b''.join(p.kraw)+numeric+debug,p.idx)

def version_display(p):
 assert p.nbc==258
 i=p.nkgc-1-gcid(p,'] V');p.kgc[i]='] 魔改版 '.encode('gbk');p.kraw[i]=encstr(p.kgc[i])
 v=gcid(p,VERSION);title=gcid(p,'魔改版 '+VERSION)
 p.bc[110]=ad('KSTR',9,v);p.bc[111]=jump(111,114,10)
 p.bc[194]=ad('KSTR',7,v);p.bc[195]=jump(195,198,10)
 p.bc[228]=ad('KSTR',4,title);p.bc[229]=jump(229,234,10)
 return Proto(rebuild_proto(p),p.idx)

def name_display(p):
 p=numbers(p,{1:GOLD});assert p.nbc==437
 a=Asm(p);start=a.base;a.emit('KSHORT',8,7);a.emit('ISNEV',6,8);a.jmp('done',33)
 a.emit('MOV',9,0);a.get(8,0,'gsub');a.const(10,'#md#f%(宋_9_炭灰,');a.const(11,'#md#f('+FONT+',');a.emit('KSHORT',12,1);a.emit('CALL',8,b=2,c=5);a.emit('MOV',0,8)
 a.mark('done');a.ins.append(p.bc[86]);a.jmp(87,33);a.finish();p.bc[86]=jump(86,start,33)
 return Proto(rebuild_proto(p),p.idx)

def ground_style(p):
 p=numbers(p,{13:GOLD},(OUTLINE,));k=p.nkn-1;assert p.nbc==490
 a=Asm(p);start=a.base;a.emit('KSHORT',16,7);a.emit('ISNEV',15,16);a.jmp('old',17)
 a.emit('KPRI',10,2);a.emit('KNUM',11,k);a.jmp(450,17)
 a.mark('old');a.ins.append(p.bc[449]);a.jmp(450,17);a.finish();p.bc[449]=jump(449,start,17)
 return Proto(rebuild_proto(p),p.idx)

def font_alias(d):
 # A private copy of the existing renderer closure changes only its forced
 # outline value and captures the same original Q_文字 local.
 custom=numbers(Proto(d.protos[1].raw,2),{0:OUTLINE})
 p=d.protos[2];alias=gcid(p,FONT);child=p.nkgc;p.kgc.insert(0,('child',));p.kraw.insert(0,uleb(0));p.nkgc+=1
 a=Asm(p);entry=a.base;a.emit('ISEQS',0,alias);a.jmp(2,6);a.ins.append(p.bc[0]);a.jmp(13,6);a.jmp(2,6)
 choose=a.base+len(a.ins);a.emit('ISEQS',0,alias);a.jmp('new',6);a.ins.append(p.bc[4]);a.jmp(5,6);a.mark('new');a.emit('FNEW',3,child);a.jmp(5,6);a.finish()
 p.bc[0]=jump(0,entry,6);p.bc[4]=jump(4,choose,6);d.protos[2]=Proto(rebuild_proto(p),2);d.protos.insert(2,custom)

def build(runtime=None,rebuild_history=False):
 # The predecessor is an immutable, hash-pinned build input. Reusing it
 # does not claim to have recompiled or retested its historical sources.
 path=W/'game_v199.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  print('Building predecessor resource (missing, mismatched, or explicitly requested).',flush=True)
  subprocess.run(['python3',str(W/'patch_v199.py')]+(['--rebuild-history']if rebuild_history else [])+(['--runtime',runtime]if runtime else []),cwd=W,check=True,stdout=subprocess.DEVNULL)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30,52,76]);d=mods[12]
 d.protos[76]=version_display(d.protos[76]);d.protos[193]=numbers(d.protos[193],{24:GOLD});d.protos[299]=name_display(d.protos[299])
 p=d.protos[22187];found=0
 for i,v in enumerate(p.kgc):
  if v=='当前版本号：V0.01'.encode('gbk'):p.kgc[i]=('魔改版 '+VERSION).encode('gbk');p.kraw[i]=encstr(p.kgc[i]);found+=1
 assert found==1;d.protos[22187]=Proto(rebuild_proto(p),p.idx)
 mods[76].protos[0]=ground_style(mods[76].protos[0]);font_alias(mods[52])
 for d in mods.values():
  for i,p in enumerate(d.protos):
   touched=False
   for k,v in enumerate(p.kgc):
    if isinstance(v,bytes):
     n=v.replace(b'Guimeng patch v1.199',b'Guimeng patch v1.200').replace(b'Guimeng v1.199 diagnostics',b'Guimeng v1.200 diagnostics').replace(b'patch=v1.199',b'patch=v1.200')
     if n!=v:p.kgc[k]=n;p.kraw[k]=encstr(n);touched=True
   if touched:d.protos[i]=Proto(rebuild_proto(p),i)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(old[m].protos)if p.raw!=d.protos[i+(1 if m==52 and i>=2 else 0)].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v200.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  encrypted=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=encrypted if m==12 else encrypted.hex().upper().encode()
  p=outer.protos[0];k=p.nkgc-1-m;p.kgc[k]=value;p.kraw[k]=encstr(value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v200.res').write_bytes(data)
 result={'version':'v1.200','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'display_version':VERSION,'seven_color':GOLD,'seven_outline':OUTLINE,'added_font_prototype':{'module':52,'index':2},'rules_changed':False}
 (W/'build_v200.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print({k:v for k,v in result.items()if k!='unused'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true',help='Rebuild predecessor sources instead of reusing the hash-pinned resource');x=a.parse_args();build(str(Path(x.runtime).resolve())if x.runtime else None,x.rebuild_history)
