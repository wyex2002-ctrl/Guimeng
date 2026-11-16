"""Blank-line lucky padding, stronger feedback tints and ground potion/gold labels."""
from patch_v251 import *
BASE_SHA='f4268e03065912f135b137f64371d77c6d57e7f7952cd98ca58122df2043911d'

def build(runtime=None,rebuild_history=False):
 path=W/'game_v251.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v251.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30,76]);runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 compiler=work/'compile252.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 source=(W/'luck_system_v252.lua').read_text().replace('-- RULES_GENERATED','local Rules=(function()\n'+(W/'luck_rules_v249.lua').read_text()+'\nend)()')
 src=work/'luck_system_v252_gbk.lua';src.write_bytes(source.encode('gbk'));out=W/'luck_system_v252.ljbc';subprocess.run([runtime,str(compiler),str(src),str(out)],check=True)
 helper=Dump(out.read_bytes());assert helper.protos[-1].nuv==0;count=len(helper.protos)
 mods[14].protos[378:399]=[Proto(p.raw,378+i)for i,p in enumerate(helper.protos)]
 for i,p in enumerate(mods[14].protos):p.idx=i
 # Private zero-upvalue ground-color closure, called only when constructing
 # the label. R6..R16 (especially rarity R15) must survive the call.
 src=work/'ground_name_color_v252_gbk.lua';src.write_bytes((W/'ground_name_color_v252.lua').read_text().encode('gbk'));out=W/'ground_name_color_v252.ljbc'
 subprocess.run([runtime,str(compiler),str(src),str(out)],check=True);ground=Dump(out.read_bytes());assert len(ground.protos)==1 and ground.protos[0].nuv==0
 d=mods[76];p=d.protos[0];assert p.frame==17 and OPS[p.bc[489]&255]=='JMP'
 logical=p.nkgc;p.kgc.insert(0,('child',));p.kraw.insert(0,uleb(0));p.nkgc+=1;p.frame=20;p.flags|=1 # PROTO_CHILD: the constructor now owns a real child closure.
 call=[ad('FNEW',17,logical),abc('TGETS',18,0,gcid(p,'物品')),ad('MOV',19,9),abc('CALL',17,2,3),ad('MOV',9,17),p.bc[489]]
 raw,groundmap=replace_instructions(p,{489:call});q=Proto(raw,0)
 # Replaced blocks are not branch-relocated by replace_instructions. This
 # original backward jump crosses the insertion and needs its mapped target.
 q.bc[groundmap[489]+5]=jump(groundmap[489]+5,groundmap[447],17)
 d.protos[0]=Proto(rebuild_proto(q),0);d.protos.insert(0,Proto(ground.protos[0].raw,0))
 for i,p in enumerate(d.protos):p.idx=i
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.251',b'v1.252')
    if mid==12 and i in [76,22194]:new=new.replace(b'1.251',b'1.252')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v252.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v252.res').write_bytes(data)
 report={'version':'v1.252','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'helper_count':count,'helper_installer':378+count,'rules_file':'luck_rules_v249.lua','feedback_colors':['#50E878','#FF7078'],'luck_extra_gap_pixels':0,'luck_blank_lines_each_side':1,'ground_map':groundmap,'ground_helper_count':1,'medicine_ground_color':'#FFFFFF','gold_ground_color':'#FFE7A0','lucky_outline':'native equipment name; native seven-affix outline for seven-affix mounts','blessing_oil_cap':7,'safe_b3_luck_cap':9}
 (W/'build_v252.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items()if k!='ground_map'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
