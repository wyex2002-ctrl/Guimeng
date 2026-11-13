"""Batch actual skill/checkpoint traffic; add bounded frame timing evidence."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4,uleb
from patch_v139 import ad,abc,jump,gcid,encstr,rebuild_proto,rebuild_dump
from bytecode_relocate import replace_instructions
from resource_tools import decode
W=Path(__file__).resolve().parent
BASE_SHA='559c611484d9eb85b7c6fadcdd6bd9f052d956be74197e2436002707d7bb351b'

def gate(p):
 # Start from original v183 writer, before the v184 dispatch-only gate.
 names=['type','string','find','error','script.dispatch','load.restore.item','sub','skill.','os','clock','__gm_flush_time_v185','__gm_flush_count_v185']
 ids={n:gcid(p,n)for n in names};p=Proto(rebuild_proto(p),p.idx)
 code=[];labels={};fix=[];base=39
 def emit(op,a=0,d=0,b=None,c=None):code.append(ad(op,a,d)if b is None else abc(op,a,b,c))
 def glob(r,n):emit('GGET',r,ids[n])
 def get(a,b,n):emit('TGETS',a,b=b,c=ids[n])
 def put(a,b,n):emit('TSETS',a,b=b,c=ids[n])
 def const(r,n):emit('KSTR',r,ids[n])
 def mark(n):labels[n]=base+len(code)
 def branch(n):fix.append((len(code),n));emit('JMP',2,32768)
 glob(2,'type');emit('MOV',3,0);emit('CALL',2,b=2,c=2)
 emit('ISNES',2,gcid(p,'string'));branch('flush')
 glob(2,'string');get(2,2,'find');emit('MOV',3,0);const(4,'error');emit('KSHORT',5,1);emit('KPRI',6,2);emit('CALL',2,b=2,c=5)
 emit('IST',0,2);branch('flush')
 emit('ISEQS',0,ids['script.dispatch']);branch('gate')
 emit('ISEQS',0,ids['load.restore.item']);branch('gate')
 glob(2,'string');get(2,2,'sub');emit('MOV',3,0);emit('KSHORT',4,1);emit('KSHORT',5,6);emit('CALL',2,b=2,c=4)
 emit('ISNES',2,ids['skill.']);branch('flush')
 mark('gate');emit('UGET',2,2);get(3,2,'__gm_flush_time_v185');emit('IST',0,3);branch('last');emit('KSHORT',3,0)
 mark('last');glob(4,'os');get(4,4,'clock');emit('CALL',4,b=2,c=1)
 emit('SUBVV',5,b=4,c=3);emit('KSHORT',6,2);emit('MULVV',5,b=5,c=6)
 get(6,2,'__gm_flush_count_v185');emit('IST',0,6);branch('count');emit('KSHORT',6,0)
 mark('count');emit('ADDVN',6,b=6,c=1);emit('KSHORT',7,256);emit('ISGE',6,7);branch('save')
 emit('KSHORT',7,1);emit('ISGE',5,7);branch('save')
 put(6,2,'__gm_flush_count_v185');emit('RET0',0,1)
 mark('save');put(4,2,'__gm_flush_time_v185');emit('KSHORT',5,0);put(5,2,'__gm_flush_count_v185')
 mark('flush');code.append(p.bc[39])
 for at,label in fix:code[at]=jump(base+at,labels[label],2)
 raw,_=replace_instructions(p,{39:code});return Proto(raw,p.idx)

def build(runtime=None):
 subprocess.run(['python3',str(W/'patch_v184.py')]+(['--runtime',runtime]if runtime else []),cwd=W,check=True,stdout=subprocess.DEVNULL)
 base=(W/'game_v184.res').read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 if runtime:
  work=W/'compile_work/v185';work.mkdir(parents=True,exist_ok=True)
  src=work/'profiling_gbk.lua';src.write_bytes((W/'profiling_v185.lua').read_text().encode('gbk'))
  c=work/'compile.lua';c.write_text('local f=assert(io.open(arg[1],"rb"));local s=f:read("*a");f:close();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(assert(loadstring(s,"@profiling_v185.lua"))));o:close()')
  subprocess.run([runtime,str(c),str(src),str(W/'profiling_v185.ljbc')],check=True)
 outer,mods=decode(base,[14,30]);_,prior=decode((W/'game_v183.res').read_bytes(),[14]);d=mods[14]
 d.protos[630]=gate(prior[14].protos[630])
 profile=Dump((W/'profiling_v185.ljbc').read_bytes()).protos[:-1];n=len(profile)
 assert profile[-1].params==1 and profile[-1].nuv==0
 p=d.protos[669];child=p.nkgc;p.kgc.insert(0,('child',));p.kraw.insert(0,uleb(0));p.nkgc+=1;p=Proto(rebuild_proto(p),669)
 raw,_=replace_instructions(p,{91:[ad('FNEW',22,child),ad('MOV',23,0),abc('CALL',22,1,2),p.bc[91]]});d.protos[669]=Proto(raw,669)
 d.protos[669:669]=profile
 for i,p in enumerate(d.protos):p.idx=i
 for module,d in mods.items():
  for index,p in enumerate(d.protos):
   touched=False
   for k,value in enumerate(p.kgc):
    if isinstance(value,bytes):
     v=value.replace(b'Guimeng patch v1.184',b'Guimeng patch v1.185').replace(b'Guimeng v1.184 diagnostics',b'Guimeng v1.185 diagnostics').replace(b'patch=v1.184',b'patch=v1.185')
     if v!=value:p.kgc[k]=v;p.kraw[k]=encstr(v);touched=True
   if touched:p.raw=rebuild_proto(p);d.protos[index]=Proto(p.raw,index)
 changes={};_,old=decode(base,mods)
 for module,d in mods.items():
  changes[module]=[i for i,p in enumerate(old[module].protos)if p.raw!=d.protos[i+n if module==14 and i>=669 else i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw
  (W/f'module_{module}_v185.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  value=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30')).hex().upper().encode()
  p=outer.protos[0];k=p.nkgc-1-module;p.kgc[k]=value;p.kraw[k]=encstr(value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v185.res').write_bytes(data)
 result={'version':'v1.185','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_original_prototypes':changes,'added_profile_prototypes':n,'insert_before':669,'routine_flush_clock_seconds':0.5,'routine_flush_max_events':256,'rules_changed':False}
 (W/'build_v185.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');build(a.parse_args().runtime)
