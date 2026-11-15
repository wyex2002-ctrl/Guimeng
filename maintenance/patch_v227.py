"""Draw a cached radial mask with the real solid sprite wrapper; keep native CD timing."""
from patch_v226 import *
from patch_v139 import jump
BASE_SHA='7da64a943f93010f9ff2c02170f27a29c9f9404a40378190cdb01ffa7c12aa51'
def build(runtime=None,rebuild_history=False):
 path=W/'game_v226.res'
 if rebuild_history or not path.exists():
  subprocess.run(['python3',str(W/'patch_v226.py')]+(['--runtime',runtime]if runtime else []),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30,36]);d=mods[36]
 # Remove v226's ineffective texture tint; original CD resource lifecycle remains.
 _,original=decode((W/'game_v225.res').read_bytes(),[36]);d.protos[1]=Proto(original[36].protos[1].raw,1)
 runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 src=work/'cooldown_mask_v227_gbk.lua';src.write_bytes((W/'cooldown_mask_v227.lua').read_text().encode('gbk'))
 compiler=work/'compile_mask_v227.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 subprocess.run([runtime,str(compiler),str(src),str(W/'cooldown_mask_v227.ljbc')],check=True)
 helper=Dump((W/'cooldown_mask_v227.ljbc').read_bytes());assert len(helper.protos)==1 and helper.protos[0].nuv==0
 key='__gm_draw_cooldown_v227'
 p=d.protos[5];field=gcid(p,key);assert field<256
 frag=[abc('TGETS',6,0,field),ad('MOV',7,0),abc('CALL',6,1,2)]
 edits={i:[]for i in range(181,217)};edits[181]=frag
 raw,_=replace_instructions(p,edits);d.protos[5]=Proto(raw,5)
 p=d.protos[10];field=gcid(p,key);assert field<256
 raw,_=replace_instructions(p,{0:[abc('TGETS',1,0,field),ad('MOV',2,0),ad('KPRI',3,2),abc('CALL',1,1,3),p.bc[0]]});d.protos[10]=Proto(raw,10)
 root=d.protos[11];child=root.nkgc;root.kgc.insert(0,('child',));root.kraw.insert(0,uleb(0));root.nkgc+=1
 field=gcid(root,key);assert field<256
 root=Proto(rebuild_proto(root),11);last=root.nbc-1
 root.bc[last:last+1]=[ad('GGET',0,gcid(root,'类_格子_技能格子')),ad('FNEW',1,child),abc('TSETS',1,0,field),root.bc[last]]
 d.protos[11]=Proto(rebuild_proto(root),11);d.protos.insert(11,Proto(helper.protos[0].raw,11))
 for i,p in enumerate(d.protos):p.idx=i
 for mid,d in mods.items():
  for p in list(d.protos):
   touched=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.226',b'v1.227')
    if mid==12 and p.idx in [76,22194]:new=new.replace(b'1.226',b'1.227')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);touched=True
   if touched:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for mid,d in mods.items():
  changes[mid]=[i for i,p in enumerate(old[mid].protos)if p.raw!=d.protos[i+(1 if mid==36 and i>=11 else 0)].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw
  (W/f'module_{mid}_v227.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v227.res').write_bytes(data)
 r={'version':'v1.227','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'base_sha256':BASE_SHA,'cd_argb':'88000000','helper_index':11,'rules_changed':False}
 (W/'build_v227.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(r)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
