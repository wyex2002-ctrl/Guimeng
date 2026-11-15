"""Draw a cached radial mask with the real solid sprite wrapper; keep native CD timing."""
from patch_v227 import *
from patch_v139 import jump
BASE_SHA='6aa0017b66fe0b2b4016cbe0b7a01f5c523886c7e1f3e141dc04673d1ac09ac2'
def build(runtime=None,rebuild_history=False):
 path=W/'game_v227.res'
 if rebuild_history or not path.exists():
  subprocess.run(['python3',str(W/'patch_v227.py')]+(['--runtime',runtime]if runtime else []),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30,36])
 runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 src=work/'cooldown_mask_v228_gbk.lua';src.write_bytes((W/'cooldown_mask_v228.lua').read_text().encode('gbk'))
 compiler=work/'compile_mask_v228.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 subprocess.run([runtime,str(compiler),str(src),str(W/'cooldown_mask_v228.ljbc')],check=True)
 helper=Dump((W/'cooldown_mask_v228.ljbc').read_bytes());assert len(helper.protos)==1 and helper.protos[0].nuv==0
 mods[36].protos[11]=Proto(helper.protos[0].raw,11)
 for mid,d in mods.items():
  for p in list(d.protos):
   touched=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.227',b'v1.228')
    if mid==12 and p.idx in [76,22194]:new=new.replace(b'1.227',b'1.228')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);touched=True
   if touched:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for mid,d in mods.items():
  changes[mid]=[i for i,p in enumerate(old[mid].protos)if p.raw!=d.protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw
  (W/f'module_{mid}_v228.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v228.res').write_bytes(data)
 r={'version':'v1.228','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'base_sha256':BASE_SHA,'cd_argb':'88000000','helper_index':11,'rules_changed':False}
 (W/'build_v228.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(r)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
