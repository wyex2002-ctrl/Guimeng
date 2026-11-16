"""Keep native latest-cast replacement and append the two defensive BUFF hints."""
from patch_v237 import *
BASE_SHA='34c4c380b0442471928106b83fb5c838cf4db443cbdc8b45930c3fae88b5d5ed'
HINT='攻击元素总和越高，加成越高'

def build(runtime=None,rebuild_history=False):
 path=W/'game_v237.res'
 if rebuild_history or not path.exists():
  subprocess.run(['python3',str(W/'patch_v237.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30,40]);p=mods[40].protos[19]
 # The two existing constructor branches already rebuild the actual description
 # after applying attributes, including old saved states. Extend their CAT only.
 # R16 is a free temporary inside this block; self/closure registers remain live.
 sites=[915,941];replacements={}
 for pc in sites:
  assert p.bc[pc]==abc('CAT',10,10,15)
  replacements[pc]=[ad('KSTR',16,gcid(p,'\n'+HINT)),abc('CAT',10,10,16)]
 raw,mapping=replace_instructions(p,replacements);mods[40].protos[19]=Proto(raw,19)
 for mid,d in mods.items():
  for p in list(d.protos):
   touched=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.237',b'v1.238')
    if mid==12 and p.idx in [76,22194]:new=new.replace(b'1.237',b'1.238')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);touched=True
   if touched:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for mid,d in mods.items():
  changes[mid]=[p.idx for p in d.protos if p.raw!=old[mid].protos[p.idx].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw
  (W/f'module_{mid}_v238.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v238.res').write_bytes(data)
 report={'version':'v1.238','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'constructor_map':mapping,'hint':HINT,'replacement':'existing native nonstacking removal/rebuild; latest cast wins even if weaker','formula_changed':False,'new_engine_apis':False}
 (W/'build_v238.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items()if k!='constructor_map'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
