"""Main-character melee timing test: faster presentation, original attack cadence."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import encstr,rebuild_proto,rebuild_dump,ad,abc,gcid
from bytecode_relocate import replace_instructions,numeric_and_debug
from ljtool import uleb
from resource_tools import decode
from runtime import ensure_runtime
from ljdis import OPS
W=Path(__file__).resolve().parent
BASE_SHA='91f2641bf146e9171d7f63efec939e38527b88e56bfbc45d2d9e704dc1943506'


def set_string(p,logical,value):
 i=p.nkgc-1-logical;p.kgc[i]=value;p.kraw[i]=encstr(value)

def build(runtime=None,rebuild_history=False):
 path=W/'game_v209.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  subprocess.run(['python3',str(W/'patch_v209.py')]+(['--rebuild-history']if rebuild_history else [])+(['--runtime',runtime]if runtime else []),check=True,cwd=W)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,26,30]);d=mods[12]
 runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 source=work/'melee_timing_v210_gbk.lua';source.write_bytes((W/'melee_timing_v210.lua').read_text().encode('gbk'))
 compiler=work/'compile_melee_v210.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 subprocess.run([runtime,str(compiler),str(source),str(W/'melee_timing_v210.ljbc')],check=True)
 compiled=Dump((W/'melee_timing_v210.ljbc').read_bytes());assert len(compiled.protos)==1
 helper=compiled.protos[0];assert helper.params==5 and helper.nuv==0
 d=mods[26];assert len(d.protos)==89
 d.protos[87]=Proto(helper.raw,87)
 # Poll through the original native input guard, before processing mouse actions.
 p=d.protos[26];key=gcid(p,'__gm_melee_timing_v208');mode=gcid(p,'input');p=Proto(rebuild_proto(p),26)
 call=[abc('TGETS',2,0,key),ad('MOV',3,0),ad('KSTR',4,mode),abc('CALL',2,1,3)]
 raw,input_map=replace_instructions(p,{43:call+[p.bc[43]]});d.protos[26]=Proto(raw,26)
 # The 100ms main timer still does all its original work except Shift polling.
 p=mods[12].protos[20]
 assert [OPS[x&255]for x in p.bc[1307:1312]]==['GGET','TGETS','KSTR','TGETV','CALL']
 assert p.gc(p.bc[1309]>>16)=='刺杀剑术'.encode('gbk')
 raw,timer_map=replace_instructions(p,{i:[]for i in range(1307,1312)});mods[12].protos[20]=Proto(raw,20)
 previous=json.loads((W/'build_v209.json').read_text());maps=previous['relocations'];maps['input210']=input_map;maps['timer210']=timer_map
 for m,d in mods.items():
  for p in list(d.protos):
   touched=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'Guimeng patch v1.209',b'Guimeng patch v1.210').replace(b'Guimeng v1.209 diagnostics',b'Guimeng v1.210 diagnostics').replace(b'patch=v1.209',b'patch=v1.210')
    if m==12 and p.idx in [76,22187]:
     if v==b'1.209':new=b'1.210'
     if v=='魔改版 1.209'.encode('gbk'):new='魔改版 1.210'.encode('gbk')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);touched=True
   if touched:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(old[m].protos)if p.raw!=d.protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v210.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=enc if m==12 else enc.hex().upper().encode()
  set_string(outer.protos[0],m,value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v210.res').write_bytes(data)
 r={'version':'v1.210','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'relocations':maps,'helper_index':87,'root_index':88,'melee_time_ratio':0.5,'rules_changed':True,'shift_poll_milliseconds':100,'first_visible_frame_immediate':True}
 (W/'build_v210.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in r.items()if not k.endswith("relocations")})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
