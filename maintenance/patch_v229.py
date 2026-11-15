"""Long-hold ranged hotkey repeat and cached green perimeter indicator."""
from patch_v228 import *
from patch_v139 import jump
BASE_SHA='c9315e482e0f1bde0945c8f4f11db9247a569a1849734335f47155a9e5a6a4c5'
def build(runtime=None,rebuild_history=False):
 path=W/'game_v228.res'
 if rebuild_history or not path.exists():
  subprocess.run(['python3',str(W/'patch_v228.py')]+(['--runtime',runtime]if runtime else []),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,26,30,36])
 runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 compiler=work/'compile_repeat_v229.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 def compile_one(name):
  src=work/(name+'_gbk.lua');src.write_bytes((W/(name+'.lua')).read_text().encode('gbk'))
  subprocess.run([runtime,str(compiler),str(src),str(W/(name+'.ljbc'))],check=True)
  helper=Dump((W/(name+'.ljbc')).read_bytes());assert len(helper.protos)==1 and helper.protos[0].nuv==0
  return helper.protos[0]
 control=compile_one('repeat_skill_v229');border=compile_one('repeat_border_v229')
 def install(mid,root_idx,class_name,key,helper):
  d=mods[mid];root=d.protos[root_idx];child=root.nkgc
  root.kgc.insert(0,('child',));root.kraw.insert(0,uleb(0));root.nkgc+=1
  field=gcid(root,key);assert field<256
  root=Proto(rebuild_proto(root),root_idx);last=root.nbc-1
  if mid==26:
   root.bc[156:156]=[ad('FNEW',1,child),abc('TSETS',1,0,field)] # Native hero class lives in R0; no global class getter.
  else:
   root.bc[last:last+1]=[ad('GGET',0,gcid(root,class_name)),ad('FNEW',1,child),abc('TSETS',1,0,field),root.bc[last]]
  d.protos[root_idx]=Proto(rebuild_proto(root),root_idx);d.protos.insert(root_idx,Proto(helper.raw,root_idx))
  for i,p in enumerate(d.protos):p.idx=i
 maps={}
 # v139's constructor trampoline keeps parameters R0..R6 and state R7 live.
 # Preserve those slots on JIT trace exits, rather than JMP A=0.
 p=mods[26].protos[54]
 for pc in [6,587,590]:
  assert OPS[p.bc[pc]&255]=='JMP' and ((p.bc[pc]>>8)&255)==0
  p.bc[pc]=(p.bc[pc]&~0xff00)|(8<<8)
 mods[26].protos[54]=Proto(rebuild_proto(p),54)
 def insert_call(mid,idx,pc,key,cleanup=False):
  p=mods[mid].protos[idx];a=p.frame;p.frame+=4
  keyidx=gcid(p,key)
  frag=[ad('KSTR',a,keyidx),abc('TGETV',a,0,a),ad('MOV',a+1,0)]
  if cleanup:frag += [ad('KPRI',a+2,2)]
  frag += [abc('CALL',a,1,3 if cleanup else 2)]
  p=Proto(rebuild_proto(p),idx);raw,mp=replace_instructions(p,{pc:frag+[p.bc[pc]]})
  mods[mid].protos[idx]=Proto(raw,idx);maps[str(mid)+'/'+str(idx)]=mp
 control_key='__gm_repeat_control_v229';border_key='__gm_repeat_draw_v229'
 insert_call(26,3,0,control_key)
 p=mods[26].protos[0];a=p.frame;p.frame+=2;field=gcid(p,'__gm_repeat_skill_v229')
 p=Proto(rebuild_proto(p),0);raw,mp=replace_instructions(p,{0:[ad('KSTR',a,field),ad('KPRI',a+1,0),abc('TSETV',a+1,0,a),p.bc[0]]});mods[26].protos[0]=Proto(raw,0);maps['26/0']=mp
 insert_call(36,5,mods[36].protos[5].nbc-1,border_key)
 insert_call(36,10,0,border_key,True)
 p=mods[14].protos[391];a=p.frame;p.frame+=4;hero=gcid(p,'Hero');method=gcid(p,control_key);cancel=gcid(p,'cancel');assert hero<256
 frag=[ad('UGET',a,0),abc('TGETS',a,a,hero),ad('ISF',0,a),0,ad('KSTR',a+1,method),abc('TGETV',a+1,a,a+1),ad('MOV',a+2,a),ad('KSTR',a+3,cancel),abc('CALL',a+1,1,3)]
 frag[3]=jump(3,len(frag),a)
 p=Proto(rebuild_proto(p),391);raw,mp=replace_instructions(p,{0:frag+[p.bc[0]]});mods[14].protos[391]=Proto(raw,391);maps['14/391']=mp
 install(26,88,'类_主角',control_key,control)
 install(36,12,'类_格子_技能格子',border_key,border)
 for mid,d in mods.items():
  for p in list(d.protos):
   touched=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.228',b'v1.229')
    if mid==12 and p.idx in [76,22194]:new=new.replace(b'1.228',b'1.229')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);touched=True
   if touched:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for mid,d in mods.items():
  changes[mid]=[i for i,p in enumerate(old[mid].protos)if p.raw!=d.protos[i+(1 if (mid==26 and i>=88)or(mid==36 and i>=12)else 0)].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw
  (W/f'module_{mid}_v229.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v229.res').write_bytes(data)
 r={'version':'v1.229','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'base_sha256':BASE_SHA,'cd_argb':'88000000','relocation_maps':maps,'control_index':88,'border_index':12,'native_skill_rules_changed':False,'auto_repeat_hold_ms':2000}
 (W/'build_v229.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in r.items()if k!='relocation_maps'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
