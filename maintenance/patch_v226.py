"""Use the existing skill-slot CD animation with explicit translucent tint."""
from patch_v225 import *
from patch_v139 import jump
BASE_SHA='0e829464df1000f41bcf5577de07f0c451b1e3ff1449d1484c6806e72e943037'
def build(runtime=None,rebuild_history=False):
 path=W/'game_v225.res'
 if rebuild_history or not path.exists():
  subprocess.run(['python3',str(W/'patch_v225.py')]+(['--runtime',runtime]if runtime else []),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30,36]);p=mods[36].protos[1]
 # Existing CD animation is a bound closure table (16/39), not a class instance.
 # Apply white RGB to preserve the supplied texture; alpha 136/255.
 key=gcid(p,'置颜色');assert key<256
 # Two 16-bit halves avoid touching the native number encoding.
 frag=[abc('TGETS',9,0,38),abc('TGETS',9,9,key),ad('KSHORT',10,65416),ad('KSHORT',11,256),abc('MULVV',10,10,11),ad('KSHORT',12,255),abc('ADDVV',10,10,12),abc('MULVV',10,10,11),abc('ADDVV',10,10,12),abc('MULVV',10,10,11),abc('ADDVV',10,10,12),abc('CALL',9,1,2)]
 raw,mp=replace_instructions(p,{102:frag+[p.bc[102]]});mods[36].protos[1]=Proto(raw,1)
 for mid,d in mods.items():
  for p in list(d.protos):
   touched=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.225',b'v1.226')
    if mid==12 and p.idx in [76,22194]:new=new.replace(b'1.225',b'1.226')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);touched=True
   if touched:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for mid,d in mods.items():
  changes[mid]=[i for i,p in enumerate(old[mid].protos)if p.raw!=d.protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw
  (W/f'module_{mid}_v226.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v226.res').write_bytes(data)
 r={'version':'v1.226','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'base_sha256':BASE_SHA,'cd_argb':'88FFFFFF','rules_changed':False}
 (W/'build_v226.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(r)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
