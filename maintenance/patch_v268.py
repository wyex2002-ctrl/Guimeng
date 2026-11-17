"""Bounded native crash breadcrumbs; gameplay remains v267."""
from patch_v267 import *
BASE_SHA='d8e3bf30f4f813633602441610ba2ee04aa66dcaa23f36c3bc416ff94a3c9341'
def build(runtime=None,rebuild_history=False):
 path=W/'game_v267.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v267.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30]);runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 compiler=work/'compile268.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 src=work/'native_watch_v268_gbk.lua';src.write_bytes((W/'native_watch_v268.lua').read_text().encode('gbk'));out=W/'native_watch_v268.ljbc';subprocess.run([runtime,str(compiler),str(src),str(out)],check=True)
 helper=Dump(out.read_bytes());assert helper.protos[-1].nuv==0
 d=mods[14];p=d.protos[729];logical=p.nkgc;p.kgc.insert(0,('child',));p.kraw.insert(0,uleb(0));p.nkgc+=1;p.flags|=1
 # R0 Sys is live; original Class assignment has finished, R2/R3 are scratch
 # and are overwritten by the original public-export construction immediately.
 raw,install_map=replace_instructions(p,{280:[ad('FNEW',2,logical),ad('MOV',3,0),abc('CALL',2,1,2),p.bc[280]]});d.protos[729]=Proto(raw,729)
 d.protos[729:729]=[Proto(p.raw,729+i)for i,p in enumerate(helper.protos)]
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   p.idx=i;changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.267',b'v1.268')
    if mid==12 and i in [76,22196]:new=new.replace(b'1.267',b'1.268')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v268.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v268.res').write_bytes(data)
 report={'version':'v1.268','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'watch_at':729,'watch_count':len(helper.protos),'constructor':729+len(helper.protos),'install_map':install_map,'diagnostic_only':True,'crash_root_cause_confirmed':False,'sample_seconds':.25,'ring_records':48}
 (W/'build_v268.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items()if k!='install_map'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
