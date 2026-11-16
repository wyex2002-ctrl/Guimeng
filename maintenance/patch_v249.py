"""Tiered blessing oil and hero/hero-summon B3 equipment luck."""
from patch_v248 import *
BASE_SHA='6c81f4d45b10cb6037f2548a05a8d393b9e7dad697bfd18dbb6bb187fbf13280'

def build(runtime=None,rebuild_history=False):
 path=W/'game_v248.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v248.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30]);runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 compiler=work/'compile249.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 source=(W/'luck_system_v249.lua').read_text().replace('-- RULES_GENERATED','local Rules=(function()\n'+(W/'luck_rules_v249.lua').read_text()+'\nend)()')
 src=work/'luck_system_v249_gbk.lua';src.write_bytes(source.encode('gbk'));out=W/'luck_system_v249.ljbc';subprocess.run([runtime,str(compiler),str(src),str(out)],check=True)
 helper=Dump(out.read_bytes());assert helper.protos[-1].nuv==0;count=len(helper.protos)
 mods[14].protos[378:399]=[Proto(p.raw,378+i)for i,p in enumerate(helper.protos)]
 for i,p in enumerate(mods[14].protos):p.idx=i
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.248',b'v1.249')
    if mid==12 and i in [76,22194]:new=new.replace(b'1.248',b'1.249')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v249.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v249.res').write_bytes(data)
 report={'version':'v1.249','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'helper_count':count,'helper_installer':378+count,'rules_file':'luck_rules_v249.lua','combat_scope':'B3 hero and hero-owned summons; companion legacy combat unchanged','blessing_oil_cap':7,'safe_b3_luck_cap':9}
 (W/'build_v249.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(report)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
