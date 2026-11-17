"""Lower-frequency broader diagnostic snapshots and twenty-second autosave."""
from patch_v271 import *
from patch_v200 import numbers
BASE_SHA='a1fc26ac18cb000cbd257ca12242fa4c2f81a692fc4acdc315b4ffbe5038c7f9'
def build(runtime=None,rebuild_history=False):
 path=W/'game_v271.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v271.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30]);runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 compiler=work/'compile271.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 src=work/'native_watch_v272_gbk.lua';src.write_bytes((W/'native_watch_v272.lua').read_text().encode('gbk'));out=W/'native_watch_v272.ljbc';subprocess.run([runtime,str(compiler),str(src),str(out)],check=True)
 helper=Dump(out.read_bytes());assert helper.protos[-1].nuv==0
 mods[14].protos[729:749]=[Proto(p.raw,729+i)for i,p in enumerate(helper.protos)]
 mods[12].protos[20]=numbers(mods[12].protos[20],{25:200})
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   p.idx=i;changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.271',b'v1.272')
    if mid==12 and i in [76,22196]:new=new.replace(b'1.271',b'1.272')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v272.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v272.res').write_bytes(data)
 report={'version':'v1.272','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'watch_at':729,'watch_count':len(helper.protos),'constructor':754+len(helper.protos)-20,'autosave_seconds':20,'autosave_ticks':200,'sample_seconds':.5,'ring_records':256,'immediate_records':False,'crash_root_cause_confirmed':False}
 (W/'build_v272.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(report)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
