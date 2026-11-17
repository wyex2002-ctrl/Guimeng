"""Level-sensitive blessing-oil drops; no numerical probabilities in player notes."""
from patch_v266 import *
BASE_SHA='a3416e3f159cfca6d5b86205d13439755097f6d681c8e35947fe4616b6f5653d'
def build(runtime=None,rebuild_history=False):
 path=W/'game_v266.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v266.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,22,30]);runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 compiler=work/'compile265.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 src=work/'oil_drop_v267_gbk.lua';src.write_bytes((W/'oil_drop_v267.lua').read_text().encode('gbk'));out=W/'oil_drop_v267.ljbc';subprocess.run([runtime,str(compiler),str(src),str(out)],check=True)
 helper=Dump(out.read_bytes());assert len(helper.protos)==1 and helper.protos[0].nuv==0;mods[22].protos[112]=Proto(helper.protos[0].raw,112)
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.266',b'v1.267')
    if mid==12 and i in [76,22196]:new=new.replace(b'1.266',b'1.267')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v267.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v267.res').write_bytes(data)
 report={'version':'v1.267','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'drop_helper_index':112,'player_note_count':54,'ordinary_level_offset':-20,'boss_level_offset':-20,'roll_max':50000,'ordinary_threshold':5,'boss_threshold':500,'fallback_threshold':1,'low_boss_roll_max':300,'low_boss_threshold':1}
 (W/'build_v267.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(report)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
