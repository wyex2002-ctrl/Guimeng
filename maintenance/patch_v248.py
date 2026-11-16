"""Reset mercenary skill damage bounds after element/gear scratch locals."""
from patch_v247 import *
BASE_SHA='f8c4a10efae182ce39570259c66779c58c35f7bd49105f3587dd6864a1428b31'

def build(runtime=None,rebuild_history=False):
 path=W/'game_v247.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v247.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30])
 p=mods[12].protos[18008]
 assert OPS[p.bc[385]&255]=='TGETS'and p.gc(p.bc[385]>>16&255)=='加成比例'.encode('gbk')
 assert p.bc[389]==abc('TGETS',21,6,gcid(p,'最小伤害'))
 # R11/R12 held temporary equipment/element key / passive proc probability.
 # Establish 0..0 before native optional skill bounds, matching the hero path.
 raw,mp=replace_instructions(p,{385:[ad('KSHORT',11,0),ad('KSHORT',12,0),p.bc[385]]});mods[12].protos[18008]=Proto(raw,18008)
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.247',b'v1.248')
    if mid==12 and i in [76,22194]:new=new.replace(b'1.247',b'1.248')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v248.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v248.res').write_bytes(data)
 report={'version':'v1.248','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'helper_count':21,'helper_installer':399,'merc_defaults_map':mp,'rules_file':'luck_rules_v246.lua','new_instructions':2,'luck_probabilities_unchanged':True}
 (W/'build_v248.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items()if not k.endswith('_map')})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
