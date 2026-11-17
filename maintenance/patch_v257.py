"""Run the trusted companion visual tick directly in its private native update."""
from patch_v256 import *
BASE_SHA='1532ce3fdafe132a2a2990cf17fe9f52338833db582d93b6362d43ea9b5686f5'

def build(runtime=None,rebuild_history=False):
 path=W/'game_v256.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v256.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,22,30]);p=mods[22].protos[115]
 # Original Sys.run('fun', closure, args) silently skips unregistered closures
 # in native14/420. This factory receives only our trusted engine-side tick.
 # Keep all four arguments and execute it directly; shared module46 is intact.
 assert p.bc[89]==ad('GGET',0,gcid(p,'Sys')) and p.bc[107]==abc('CALL',0,1,4)
 frag=[ad('UGET',0,0),abc('TGETS',0,0,gcid(p,'托管脚本'))]
 for reg,key in [(1,'攻击方id'),(2,'被攻击方id'),(3,'子弹信息'),(4,'附加信息')]:
  frag += [ad('UGET',reg,0),abc('TGETS',reg,reg,gcid(p,key))]
 frag += [abc('CALL',0,1,5)]
 repl={i:[]for i in range(89,108)};repl[89]=frag
 raw,mp=replace_instructions(p,repl);mods[22].protos[115]=Proto(raw,115)
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   p.idx=i;changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.256',b'v1.257')
    if mid==12 and i in [76,22194]:new=new.replace(b'1.256',b'1.257')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v257.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v257.res').write_bytes(data)
 old=json.loads((W/'build_v256.json').read_text());report={k:v for k,v in old.items()if k not in ['version','base_sha256','bytes','sha256','construct_map']}
 report.update(version='v1.257',base_sha256=BASE_SHA,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),visual_tick_map=mp,visual_tick_call='private22/115 direct trusted closure; native14/420 skips unregistered closures',rotation_radians_per_second='6*pi; unchanged from v256',gameplay_helper_byte_identical=True)
 (W/'build_v257.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items()if k not in ['maps','visual_tick_map']})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
