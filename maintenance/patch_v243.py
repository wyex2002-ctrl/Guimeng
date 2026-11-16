"""Remove pickup UI/timer and fix oil native drop argument order."""
from patch_v242 import *
BASE_SHA='d0d94815241e5011b23cf0fa23ef692e9c65cda0f624976651648643094b1cda'

def build(runtime=None,rebuild_history=False):
 path=W/'game_v242.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v242.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,22,26,30]);_,prior=decode((W/'game_v241.res').read_bytes(),[12,14,26])
 # Remove nine UI helper prototypes and restore the original UI constructor.
 d=mods[12];del d.protos[22194:22203];d.protos[22194]=Proto(prior[12].protos[22194].raw,22194)
 # Remove timer child/root hook; original Alt gate and hero initialization.
 d=mods[14];del d.protos[688];d.protos[688]=Proto(prior[14].protos[688].raw,688)
 p=Proto(prior[14].protos[385].raw,385);source=p.gc(222).replace(b'for dy=-4,4 do for dx=-4,4 do',b'for dy=-5,5 do for dx=-5,5 do');set_string(p,222,source);d.protos[385]=Proto(rebuild_proto(p),385)
 mods[26].protos[0]=Proto(prior[26].protos[0].raw,0)
 # Correct public native API: (mode, ITEM, COUNT, x, y, from_x, from_y).
 runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 src=work/'oil_drop_v243_gbk.lua';src.write_bytes((W/'oil_drop_v243.lua').read_text().encode('gbk'))
 compiler=work/'compile243.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 subprocess.run([runtime,str(compiler),str(src),str(W/'oil_drop_v243.ljbc')],check=True)
 helper=Dump((W/'oil_drop_v243.ljbc').read_bytes());assert len(helper.protos)==1;mods[22].protos[112]=Proto(helper.protos[0].raw,112)
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   p.idx=i;changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    v2=v.replace(b'v1.242',b'v1.243')
    if mid==12 and i in [76,22194]:v2=v2.replace(b'1.241',b'1.243').replace(b'1.242',b'1.243')
    if v2!=v:p.kgc[j]=v2;p.kraw[j]=encstr(v2);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v243.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v243.res').write_bytes(data)
 report={'version':'v1.243','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'removed_pickup_checkboxes':True,'removed_auto_pickup_timer':True,'pickup_radius':11,'alt_auto_sale':True,'oil_drop_each_kill':1,'oil_api_order':'mode,item,count,x,y,from_x,from_y','oil_luck_implemented':False}
 (W/'build_v243.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(report)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
