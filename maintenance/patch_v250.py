"""Brighter oil feedback, compact lucky row and original name outlines."""
from patch_v249 import *
BASE_SHA='fdbba82d0933a3d7a61d33ce52ac7de4424d17038b775a616f4d18788a93175b'

def build(runtime=None,rebuild_history=False):
 path=W/'game_v249.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v249.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30,52]);runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 compiler=work/'compile250.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 source=(W/'luck_system_v250.lua').read_text().replace('-- RULES_GENERATED','local Rules=(function()\n'+(W/'luck_rules_v249.lua').read_text()+'\nend)()')
 src=work/'luck_system_v250_gbk.lua';src.write_bytes(source.encode('gbk'));out=W/'luck_system_v250.ljbc';subprocess.run([runtime,str(compiler),str(src),str(out)],check=True)
 helper=Dump(out.read_bytes());assert helper.protos[-1].nuv==0;count=len(helper.protos)
 mods[14].protos[378:399]=[Proto(p.raw,378+i)for i,p in enumerate(helper.protos)]
 for i,p in enumerate(mods[14].protos):p.idx=i
 # Lucky font keeps its private marker so native name recoloring cannot
 # recolor the stat. Reuse the EXACT normal equipment-name outline closure.
 mods[52].protos[3]=Proto(mods[52].protos[1].raw,3)
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.249',b'v1.250')
    if mid==12 and i in [76,22194]:new=new.replace(b'1.249',b'1.250')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v250.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v250.res').write_bytes(data)
 report={'version':'v1.250','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'helper_count':count,'helper_installer':378+count,'rules_file':'luck_rules_v249.lua','feedback_colors':['#7AD99B','#F28F94'],'luck_extra_gap_pixels':0,'lucky_outline':'native equipment name; native seven-affix outline for seven-affix mounts','blessing_oil_cap':7,'safe_b3_luck_cap':9}
 (W/'build_v250.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(report)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
