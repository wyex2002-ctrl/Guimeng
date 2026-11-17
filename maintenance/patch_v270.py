"""Game-local exit request traces; do not change gameplay or exit semantics."""
from patch_v269 import *
BASE_SHA='f2a1c059e9dbadf01008effaffec3af055ca9decdcc23b8ef89e313a98d09e10'

def build(runtime=None,rebuild_history=False):
 path=W/'game_v269.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v269.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30]);runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 compiler=work/'compile270.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 src=work/'exit_watch_v270_gbk.lua';src.write_bytes((W/'exit_watch_v270.lua').read_text().encode('gbk'));out=W/'exit_watch_v270.ljbc';subprocess.run([runtime,str(compiler),str(src),str(out)],check=True)
 helper=Dump(out.read_bytes());assert helper.protos[-1].nuv==0
 d=mods[14];p=d.protos[749];logical=p.nkgc;p.kgc.insert(0,('child',));p.kraw.insert(0,uleb(0));p.nkgc+=1;p.flags|=1
 # The existing watch CALL has returned. R2/R3 are still scratch, before the
 # unchanged public-export code. Preserve the old watch and public.run ABI.
 raw,mp=replace_instructions(p,{283:[ad('FNEW',2,logical),ad('MOV',3,0),abc('CALL',2,1,2),p.bc[283]]})
 d.protos[749]=Proto(raw,749);d.protos[749:749]=[Proto(p.raw,749+i)for i,p in enumerate(helper.protos)]
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   p.idx=i;changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.269',b'v1.270')
    if mid==12 and i in [76,22196]:new=new.replace(b'1.269',b'1.270')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v270.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v270.res').write_bytes(data)
 report={'version':'v1.270','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'exit_watch_at':749,'exit_watch_count':len(helper.protos),'constructor':749+len(helper.protos),'install_map':mp,'diagnostic_only':True,'crash_root_cause_confirmed':False,'autosave_seconds':180,'windows_recording_required':False}
 (W/'build_v270.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items()if k!='install_map'})

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
