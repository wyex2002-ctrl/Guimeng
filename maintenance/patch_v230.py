"""Allow hotbar hover and ground movement during repeat; use native frame seconds."""
from patch_v229 import *
from patch_v139 import jump
BASE_SHA='7dbcdac166a32aea7153aa661d27774e1490c8724221d7eabb445fe5d889705f'
def build(runtime=None,rebuild_history=False):
 path=W/'game_v229.res'
 if rebuild_history or not path.exists():
  subprocess.run(['python3',str(W/'patch_v229.py')]+(['--runtime',runtime]if runtime else []),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,26,30,36])
 runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 src=work/'repeat_skill_v230_gbk.lua';src.write_bytes((W/'repeat_skill_v230.lua').read_text().encode('gbk'))
 compiler=work/'compile_repeat_v230.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 subprocess.run([runtime,str(compiler),str(src),str(W/'repeat_skill_v230.ljbc')],check=True)
 helper=Dump((W/'repeat_skill_v230.ljbc').read_bytes());assert len(helper.protos)==1 and helper.protos[0].nuv==0
 mods[26].protos[88]=Proto(helper.protos[0].raw,88)
 for mid,d in mods.items():
  for p in list(d.protos):
   touched=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.229',b'v1.230')
    if mid==12 and p.idx in [76,22194]:new=new.replace(b'1.229',b'1.230')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);touched=True
   if touched:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for mid,d in mods.items():
  changes[mid]=[i for i,p in enumerate(old[mid].protos)if p.raw!=d.protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw
  (W/f'module_{mid}_v230.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v230.res').write_bytes(data)
 r={'version':'v1.230','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'base_sha256':BASE_SHA,'cd_argb':'88000000','control_index':88,'rules_changed':False}
 (W/'build_v230.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(r)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
