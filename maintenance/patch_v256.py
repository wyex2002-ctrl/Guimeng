"""Fireball-relative companion flight speed with nonblocking native hit delivery."""
from patch_v255 import *
BASE_SHA='b023153ae48bb5aa48b4dc8a1c65cd13bd705dd07e979eb52298ba0cc936045c'

def build(runtime=None,rebuild_history=False):
 path=W/'game_v255.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v255.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,22,30]);runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 compiler=work/'compile256.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 src=work/'merc_mode_v256_gbk.lua';src.write_bytes((W/'merc_mode_v256.lua').read_text().encode('gbk'));out=W/'merc_mode_v256.ljbc';subprocess.run([runtime,str(compiler),str(src),str(out)],check=True)
 helper=Dump(out.read_bytes());assert helper.protos[-1].nuv==0
 mods[14].protos[399:413]=[Proto(p.raw,399+i)for i,p in enumerate(helper.protos)]
 p=mods[22].protos[53];p.frame=38;at=399
 assert p.bc[at+2]==abc('CALL',35,1,2)
 raw,mp=replace_instructions(p,{at+2:[ad('MOV',37,23),abc('CALL',35,1,3)]});mods[22].protos[53]=Proto(raw,53)
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   p.idx=i;changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.255',b'v1.256')
    if mid==12 and i in [76,22194]:new=new.replace(b'1.255',b'1.256')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v256.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v256.res').write_bytes(data)
 report={'version':'v1.256','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'merc_helper_count':len(helper.protos),'merc_helper_at':399,'helper_installer':399+len(helper.protos),'native_visual_count':8,'native_visual_at':113,'native_actor_root':121,'ranged_cells':6,'fireball_speed_ratio':1.2,'story_base_speeds':[450,350],'effective_speeds':[540,420],'construct_map':mp,'maps':json.loads((W/'build_v255.json').read_text())['maps']}
 (W/'build_v256.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items()if k not in['maps','construct_map']})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
