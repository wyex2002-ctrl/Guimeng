"""Main-character melee timing test: faster presentation, original attack cadence."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import encstr,rebuild_proto,rebuild_dump,ad,abc,gcid
from bytecode_relocate import replace_instructions,numeric_and_debug
from ljtool import uleb
from resource_tools import decode
from runtime import ensure_runtime
from ljdis import OPS
W=Path(__file__).resolve().parent
BASE_SHA='412810df5e2340f1321ccef30554c392bb6728a43f0649cde90977fbc8617981'


def set_string(p,logical,value):
 i=p.nkgc-1-logical;p.kgc[i]=value;p.kraw[i]=encstr(value)

def build(runtime=None,rebuild_history=False):
 path=W/'game_v207.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  subprocess.run(['python3',str(W/'patch_v207.py')]+(['--rebuild-history']if rebuild_history else [])+(['--runtime',runtime]if runtime else []),check=True,cwd=W)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,26,30]);d=mods[12]
 runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 source=work/'melee_timing_v208_gbk.lua';source.write_bytes((W/'melee_timing_v208.lua').read_text().encode('gbk'))
 compiler=work/'compile_melee_v208.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 subprocess.run([runtime,str(compiler),str(source),str(W/'melee_timing_v208.ljbc')],check=True)
 compiled=Dump((W/'melee_timing_v208.ljbc').read_bytes());assert len(compiled.protos)==1
 helper=compiled.protos[0];assert helper.params==5 and helper.nuv==0
 d=mods[26];method='__gm_melee_timing_v208';maps={}
 def invoke(p,base,mode,args,results=1,selfreg=0):
  key=gcid(p,method);assert key<256
  out=[abc('TGETS',base,selfreg,key),ad('MOV',base+1,selfreg),ad('KSTR',base+2,gcid(p,mode))]
  out += [ad(op,base+3+i,value)for i,(op,value)in enumerate(args)]
  out += [abc('CALL',base,results,len(args)+3)]
  return out
 # Real update clock, alongside the original attack counter, after pause guards.
 p=d.protos[3];call=invoke(p,3,'tick',[('GGET',gcid(p,'dt'))]);p=Proto(rebuild_proto(p),3)
 raw,mp=replace_instructions(p,{843:call+[p.bc[843]]});maps[3]=mp;d.protos[3]=Proto(raw,3)
 # Gate automatic melee before its original counter reset, preserving registers.
 p=d.protos[28];call=invoke(p,8,'gate',[],2);p=Proto(rebuild_proto(p),28)
 raw,mp=replace_instructions(p,{143:call+[ad('ISF',0,8),0,p.bc[143]]});q=Proto(raw,28)
 from patch_v139 import jump
 q.bc[mp[143]+len(call)+1]=jump(mp[143]+len(call)+1,mp[158],14)
 maps[28]=mp;d.protos[28]=Proto(rebuild_proto(q),28)
 # Preserve end-of-animation counter resets at their ORIGINAL frame, while
 # the visible faster animation can already leave the attack state.
 p=d.protos[25];call=invoke(p,2,'end_reset',[]);p=Proto(rebuild_proto(p),25)
 raw,mp=replace_instructions(p,{pc:call+[p.bc[pc]]for pc in [556,622,644,651]});maps[25]=mp;d.protos[25]=Proto(raw,25)
 # All direct/queued skill paths pass the same recovery gate, before costs/CD.
 p=d.protos[55];call=invoke(p,48,'direct_gate',[],2);p=Proto(rebuild_proto(p),55)
 block=call+[ad('IST',0,48),0,ad('ISF',0,2),0,abc('TSETS',1,0,gcid(p,'下次技能')),ad('KPRI',14,1),0,p.bc[87]]
 raw,mp=replace_instructions(p,{87:block});q=Proto(raw,55);at=mp[87]+len(call)
 q.bc[at+1]=jump(at+1,mp[87]+len(block)-1,55)
 q.bc[at+3]=jump(at+3,at+5,55)
 q.bc[at+6]=ad('UCLO',0,mp[976]-(at+6)-1+32768)
 maps[55]=mp;d.protos[55]=Proto(rebuild_proto(q),55)
 # Final instance is adjusted after script overrides/multihit initialization.
 p=d.protos[54];call=invoke(p,24,'instance',[('MOV',7)],selfreg=1);p=Proto(rebuild_proto(p),54)
 raw,mp=replace_instructions(p,{562:call+[p.bc[562]]});maps[54]=mp;d.protos[54]=Proto(raw,54)
 # Original body animation receives a faster factor; its exact old Lua updater
 # advances an invisible scalar-only copy for the original recovery gate.
 p=d.protos[81];advance=invoke(p,2,'advance',[]);call=invoke(p,10,'motion',[('MOV',2),('MOV',3),('MOV',5)],2);p=Proto(rebuild_proto(p),81)
 block=[ad('KSHORT',10,1),ad('ISNEV',9,10),0]+call+[ad('MOV',2,10),p.bc[147]]
 raw,mp=replace_instructions(p,{0:advance+[p.bc[0]],147:block});q=Proto(raw,81)
 q.bc[mp[147]+2]=jump(mp[147]+2,mp[147]+len(block)-1,18)
 maps[81]=mp;d.protos[81]=Proto(rebuild_proto(q),81)
 root=d.protos[87];child=root.nkgc;root.kgc.insert(0,('child',));root.kraw.insert(0,uleb(0));root.nkgc+=1
 key=gcid(root,method);assert key<256;root=Proto(rebuild_proto(root),87)
 raw,mp=replace_instructions(root,{154:[ad('FNEW',1,child),abc('TSETS',1,0,key),root.bc[154]]})
 d.protos[87]=Proto(raw,88);d.protos.insert(87,Proto(helper.raw,87));maps['root']=mp
 for m,d in mods.items():
  for p in list(d.protos):
   touched=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'Guimeng patch v1.207',b'Guimeng patch v1.208').replace(b'Guimeng v1.207 diagnostics',b'Guimeng v1.208 diagnostics').replace(b'patch=v1.207',b'patch=v1.208')
    if m==12 and p.idx in [76,22187]:
     if v==b'1.207':new=b'1.208'
     if v=='魔改版 1.207'.encode('gbk'):new='魔改版 1.208'.encode('gbk')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);touched=True
   if touched:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(old[m].protos)if p.raw!=d.protos[i+(m==26 and i>=87)].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v208.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=enc if m==12 else enc.hex().upper().encode()
  set_string(outer.protos[0],m,value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v208.res').write_bytes(data)
 r={'version':'v1.208','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'relocations':maps,'helper_index':87,'root_index':88,'melee_time_ratio':0.7,'rules_changed':True}
 (W/'build_v208.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in r.items()if not k.endswith("relocations")})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
