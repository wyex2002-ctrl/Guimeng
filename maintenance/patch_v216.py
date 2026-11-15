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
BASE_SHA='174859216117b5735d55377523d40e646ff9440a7984be73e0af448aa5dffa86'


def set_string(p,logical,value):
 i=p.nkgc-1-logical;p.kgc[i]=value;p.kraw[i]=encstr(value)

def build(runtime=None,rebuild_history=False):
 path=W/'game_v215.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  subprocess.run(['python3',str(W/'patch_v215.py')]+(['--rebuild-history']if rebuild_history else [])+(['--runtime',runtime]if runtime else []),check=True,cwd=W)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,26,30]);d=mods[12]
 runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 source=work/'melee_timing_v216_gbk.lua';source.write_bytes((W/'melee_timing_v216.lua').read_text().encode('gbk'))
 compiler=work/'compile_melee_v216.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 subprocess.run([runtime,str(compiler),str(source),str(W/'melee_timing_v216.ljbc')],check=True)
 compiled=Dump((W/'melee_timing_v216.ljbc').read_bytes());assert len(compiled.protos)==1
 helper=compiled.protos[0];assert helper.params==5 and helper.nuv==0
 d=mods[26];assert len(d.protos)==89
 d.protos[87]=Proto(helper.raw,87)
 maps={}
 p=d.protos[0];scratch=p.frame;p.frame+=2;field=gcid(p,'__gm_auto_charge_v216')
 p=Proto(rebuild_proto(p),0)
 raw,maps['init']=replace_instructions(p,{0:[ad('KPRI',scratch,0),ad('KSTR',scratch+1,field),abc('TSETV',scratch,0,scratch+1),p.bc[0]]});d.protos[0]=Proto(raw,0)
 p=d.protos[55];scratch=p.frame;p.frame+=8;method=gcid(p,'__gm_melee_timing_v208')
 def helper(mode,arg,result=None):
  body=[abc('TGETS',scratch,0,method),ad('MOV',scratch+1,0),ad('KSTR',scratch+2,gcid(p,mode)),ad('MOV',scratch+3,arg)]
  if result is not None:body+=[ad('MOV',scratch+4,result),abc('CALL',scratch,2,5),ad('MOV',result,scratch)]
  else:body+=[abc('CALL',scratch,1,4)]
  return body
 select=helper('charge_select',1,12);commit=helper('charge_commit',1)
 p=Proto(rebuild_proto(p),55)
 raw,maps['cast']=replace_instructions(p,{17:select+[p.bc[17]],982:commit+[p.bc[982]]});d.protos[55]=Proto(raw,55)
 for m,d in mods.items():
  for p in list(d.protos):
   touched=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'Guimeng patch v1.215',b'Guimeng patch v1.216').replace(b'Guimeng v1.215 diagnostics',b'Guimeng v1.216 diagnostics').replace(b'patch=v1.215',b'patch=v1.216')
    if m==12 and p.idx in [76,22187]:
     if v==b'1.215':new=b'1.216'
     if v=='魔改版 1.215'.encode('gbk'):new='魔改版 1.216'.encode('gbk')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);touched=True
   if touched:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(old[m].protos)if p.raw!=d.protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v216.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=enc if m==12 else enc.hex().upper().encode()
  set_string(outer.protos[0],m,value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v216.res').write_bytes(data)
 r={'version':'v1.216','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'relocations':maps,'helper_index':87,'root_index':88,'melee_time_ratio':0.5,'effect_interval_ratio':0.5,'select_insertions':{17:len(select),982:len(commit)},'rules_changed':'auto-charge convenience only; original cooldowns/costs/damage retained'}
 (W/'build_v216.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in r.items()if not k.endswith("relocations")})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
