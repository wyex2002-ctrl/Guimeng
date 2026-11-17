"""Rebind the existing automatic retaliation toggle from F to Tab."""
from patch_v260 import *
BASE_SHA='989525b5ade7167d511523135de5862283fc241d38d374dfe554eb29f9ea7a7e'

def build(runtime=None,rebuild_history=False):
 path=W/'game_v260.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v260.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30]);p=mods[12].protos[52]
 nums=number_pool(p);assert nums[25]==70 and nums[29]==9
 assert p.bc[370]==ad('ISNEN',0,25) and p.bc[469]==ad('ISNEN',0,29)
 p.bc[370]=ad('ISNEN',0,29)
 # Tab exits via the original retaliation branch. Explicitly bypass its old
 # skill-lock block so it can never toggle both modes on a single key event.
 p.bc[469]=jump(469,501,2);mods[12].protos[52]=Proto(rebuild_proto(p),52)
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   p.idx=i;changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.260',b'v1.261')
    if mid==12 and i in [76,22196]:new=new.replace(b'1.260',b'1.261')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v261.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v261.res').write_bytes(data)
 report={'version':'v1.261','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'key_handler':52,'retaliation_condition_pc':370,'old_tab_bypass_pc':469,'tab_keycode':9,'former_keycode':70,'new_helpers':0}
 (W/'build_v261.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(report)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
