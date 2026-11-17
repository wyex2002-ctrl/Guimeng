"""Layered game-local diagnostics; keep v273 autosave and gameplay."""
from patch_v273 import *
BASE_SHA='0cd370eca8143e56a3612ab140bcbc7a08e2a05afe9fce561ccb73c086c3f9a4'

def build(runtime=None,rebuild_history=False):
 path=W/'game_v273.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v273.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30]);runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 compiler=work/'compile274.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 def compile(name):
  src=work/(name+'_gbk.lua');src.write_bytes((W/(name+'.lua')).read_text().encode('gbk'));out=W/(name+'.ljbc');subprocess.run([runtime,str(compiler),str(src),str(out)],check=True)
  d=Dump(out.read_bytes());assert d.protos[-1].nuv==0;return d
 watch=compile('native_watch_v274');exits=compile('exit_watch_v274');assert len(exits.protos)==5
 mods[14].protos[750:755]=[Proto(p.raw,750+i)for i,p in enumerate(exits.protos)]
 mods[14].protos[729:750]=[Proto(p.raw,729+i)for i,p in enumerate(watch.protos)]
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   p.idx=i;changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.273',b'v1.274')
    if mid==12 and i in [76,22196]:new=new.replace(b'1.273',b'1.274')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v274.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v274.res').write_bytes(data)
 count=len(watch.protos)
 report={'version':'v1.274','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'watch_at':729,'watch_count':count,'exit_at':729+count,'exit_count':5,'constructor':734+count,'sample_seconds':.5,'activity_records':256,'frozen_event_records':128,'autosave_seconds':5,'diagnostic_only':True,'crash_root_cause_confirmed':False}
 (W/'build_v274.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(report)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');p.add_argument('--rebuild-history',action='store_true');a=p.parse_args();build(a.runtime,a.rebuild_history)
