"""One-second ranged repeat hold and concise, renumbered player notes."""
from patch_v264 import *
BASE_SHA='1ccfaa0fd56071f2001440f218778b1f5d35e5a37f3304072dac8b3e9efd9a0d'
def build(runtime=None,rebuild_history=False):
 path=W/'game_v264.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v264.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,26,30]);runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 compiler=work/'compile265.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 src=work/'repeat_skill_v265_gbk.lua';src.write_bytes((W/'repeat_skill_v265.lua').read_text().encode('gbk'));out=W/'repeat_skill_v265.ljbc';subprocess.run([runtime,str(compiler),str(src),str(out)],check=True)
 helper=Dump(out.read_bytes());assert len(helper.protos)==1 and helper.protos[0].nuv==0;mods[26].protos[88]=Proto(helper.protos[0].raw,88)
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.264',b'v1.265')
    if mid==12 and i in [76,22196]:new=new.replace(b'1.264',b'1.265')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v265.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v265.res').write_bytes(data)
 report={'version':'v1.265','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'auto_repeat_hold_seconds':1,'repeat_helper_index':88,'player_note_count':54,'removed_old_note_numbers':[22,42]}
 (W/'build_v265.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(report)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
