"""Measure actual native update/render phases without changing their work."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import ad,abc,jump,gcid,encstr,rebuild_proto,rebuild_dump
from bytecode_relocate import replace_instructions,BRANCHES
from ljdis import OPS
from resource_tools import decode
W=Path(__file__).resolve().parent
BASE_SHA='75e9453207c8edf635deda05e91b1bb227f697c75c93b729d24d7472844b724b'
PHASES={2:'prepare',230:'input',408:'effects_update',597:'actors_update',647:'map_update',650:'hero_update',2766:'bulk_sale',2723:'alt_pickup',656:'windows_order',797:'world_render',884:'map_draw',887:'world_overlay',1145:'tooltip',1146:'bubbles',1229:'scene_composite',1318:'mask_draw',1558:'windows_draw',1678:'labels_effects',1779:'sprite_update',2010:'final_ui',2385:'timers',2465:'debug',2546:'http_queue',2636:'end'}

def instrument(p):
 assert p.frame==27
 ids={s:gcid(p,s)for s in ['__gm_perf_phase_v186','type','function',*PHASES.values()]}
 assert ids['__gm_perf_phase_v186']<256
 p.frame=30;p=Proto(rebuild_proto(p),p.idx);repl={}
 for pc,name in PHASES.items():
  # New scratch registers never overlap live original registers R0..R26.
  block=[ad('UGET',27,0),abc('TGETS',27,27,ids['__gm_perf_phase_v186']),ad('GGET',28,ids['type']),ad('MOV',29,27),abc('CALL',28,2,2),ad('ISNES',28,ids['function']),jump(pc+6,pc+9,27),ad('KSTR',28,ids[name]),abc('CALL',27,1,2),p.bc[pc]]
  repl[pc]=block
 # Internal branches in fragments must account for all prior insertions.
 shift=0
 for pc in sorted(repl):
  repl[pc][6]=jump(pc+shift+6,pc+shift+9,27);shift+=len(repl[pc])-1
 raw,mp=replace_instructions(p,repl);out=Proto(raw,p.idx)
 # Original branch instructions inside replaced fragments need relocation too.
 for pc in PHASES:
  ins=p.bc[pc]
  if OPS[ins&255] in BRANCHES:
   at=mp[pc]+9;target=mp[pc+1+(ins>>16)-32768]
   out.bc[at]=(ins&65535)|((target-at-1+32768)<<16)
 return Proto(rebuild_proto(out),p.idx),mp

def build(runtime=None):
 subprocess.run(['python3',str(W/'patch_v185.py')]+(['--runtime',runtime]if runtime else []),cwd=W,check=True,stdout=subprocess.DEVNULL)
 base=(W/'game_v185.res').read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 if runtime:
  work=W/'compile_work/v186';work.mkdir(parents=True,exist_ok=True)
  src=work/'profiling_gbk.lua';src.write_bytes((W/'profiling_v186.lua').read_text().encode('gbk'))
  c=work/'compile.lua';c.write_text('local f=assert(io.open(arg[1],"rb"));local s=f:read("*a");f:close();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(assert(loadstring(s,"@profiling_v186.lua"))));o:close()')
  subprocess.run([runtime,str(c),str(src),str(W/'profiling_v186.ljbc')],check=True)
 outer,mods=decode(base,[14,30]);d=mods[14]
 d.protos[385],mp=instrument(d.protos[385])
 profile=Dump((W/'profiling_v186.ljbc').read_bytes()).protos[:-1];n=len(profile);delta=n-9
 assert profile[-1].params==1 and profile[-1].nuv==0
 d.protos[669:678]=profile
 for i,p in enumerate(d.protos):p.idx=i
 for module,d in mods.items():
  for index,p in enumerate(d.protos):
   touched=False
   for k,value in enumerate(p.kgc):
    if isinstance(value,bytes):
     v=value.replace(b'Guimeng patch v1.185',b'Guimeng patch v1.186').replace(b'Guimeng v1.185 diagnostics',b'Guimeng v1.186 diagnostics').replace(b'patch=v1.185',b'patch=v1.186')
     if v!=value:p.kgc[k]=v;p.kraw[k]=encstr(v);touched=True
   if touched:p.raw=rebuild_proto(p);d.protos[index]=Proto(p.raw,index)
 changes={};_,old=decode(base,mods)
 for module,d in mods.items():
  changes[module]=[i for i,p in enumerate(old[module].protos)if not(module==14 and 669<=i<678)and p.raw!=d.protos[i+delta if module==14 and i>=678 else i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw
  (W/f'module_{module}_v186.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  value=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30')).hex().upper().encode()
  p=outer.protos[0];k=p.nkgc-1-module;p.kgc[k]=value;p.kraw[k]=encstr(value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v186.res').write_bytes(data)
 result={'version':'v1.186','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_original_prototypes':changes,'old_profile_count':9,'profile_count':n,'profile_delta':delta,'frame_phase_entries':{str(k):v for k,v in PHASES.items()},'frame_relocations':{str(k):v for k,v in mp.items()},'rules_changed':False}
 (W/'build_v186.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in result.items()if k!='frame_relocations'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');build(a.parse_args().runtime)
