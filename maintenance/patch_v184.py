"""Reduce diagnostic allocations and batch high-frequency trace file writes."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import ad,abc,jump,gcid,encstr,rebuild_proto,rebuild_dump
from bytecode_relocate import replace_instructions
from resource_tools import decode
W=Path(__file__).resolve().parent
BASE_SHA='90368ad96daa92ed4669a84bb3afb93204bb4f7a2d28663fe64e67ce96fcfb65'

def build(runtime=None):
 subprocess.run(['python3',str(W/'patch_v183.py')]+(['--runtime',runtime]if runtime else []),cwd=W,check=True,stdout=subprocess.DEVNULL)
 base=(W/'game_v183.res').read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 if runtime:
  work=W/'compile_work/v184';work.mkdir(parents=True,exist_ok=True)
  src=work/'diagnostics_gbk.lua';src.write_bytes((W/'diagnostics_v184.lua').read_text().encode('gbk'))
  compiler=work/'compile.lua';compiler.write_text('local f=assert(io.open(arg[1],"rb"));local s=f:read("*a");f:close();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(assert(loadstring(s,"@diagnostics_v184.lua"))));o:close()')
  subprocess.run([runtime,str(compiler),str(src),str(W/'diagnostics_v184.ljbc')],check=True)
 outer,mods=decode(base,[14,30]);changes={}
 diagnostic=Dump((W/'diagnostics_v184.ljbc').read_bytes()).protos[:-1]
 assert len(diagnostic)==24 and diagnostic[-1].params==1 and diagnostic[-1].nuv==0
 # Replace the entire existing isolated diagnostic subtree. Original native
 # prototypes and parent closure slots keep their IDs and serialized ABI.
 mods[14].protos[645:669]=[Proto(p.raw,645+i)for i,p in enumerate(diagnostic)]
 p=mods[14].protos[630];key=gcid(p,'script.dispatch');p=Proto(rebuild_proto(p),630)
 # Record every trace in the bounded in-memory ring, but serialize/write only
 # each 16th dispatch. Non-dispatch checkpoints (including errors/exits/load
 # milestones) flush immediately, preserving pending pre-error context.
 at=39;block=[ad('ISNES',0,key),jump(at+1,at+10,2),ad('UGET',2,1),ad('KSHORT',3,16),abc('MODVV',2,2,3),ad('KSHORT',3,0),abc('ISEQV',2,0,3),jump(at+7,at+10,2),ad('RET0',0,1),ad('MOV',2,2),p.bc[at]]
 # The harmless MOV occupies the unused fall-through slot so all continuation
 # branches have one shared target at the original UGET instruction.
 raw,_=replace_instructions(p,{at:block});mods[14].protos[630]=Proto(raw,630)
 for m,d in mods.items():
  for i,p in enumerate(d.protos):
   touched=False
   for k,value in enumerate(p.kgc):
    if isinstance(value,bytes):
     v=value.replace(b'Guimeng patch v1.183',b'Guimeng patch v1.184').replace(b'Guimeng v1.183 diagnostics',b'Guimeng v1.184 diagnostics').replace(b'patch=v1.183',b'patch=v1.184')
     if v!=value:p.kgc[k]=v;p.kraw[k]=encstr(v);touched=True
   if touched:p.raw=rebuild_proto(p);d.protos[i]=Proto(p.raw,i)
 _,old=decode(base,mods)
 for m,d in mods.items():
  changes[m]=[i for i,(p,q)in enumerate(zip(old[m].protos,d.protos))if p.raw!=q.raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw
  (W/f'module_{m}_v184.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  encoded=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30')).hex().upper().encode()
  p=outer.protos[0];k=p.nkgc-1-m;p.kgc[k]=encoded;p.kraw[k]=encstr(encoded)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v184.res').write_bytes(data)
 result={'version':'v1.184','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'diagnostics_subtree':[645,668],'dispatch_write_batch':16,'rules_changed':False}
 (W/'build_v184.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');build(a.parse_args().runtime)
