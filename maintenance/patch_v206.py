"""Allow deployed dead mercenaries to store half XP and retain talisman claims."""
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
BASE_SHA='0b52da139c2c106aed921aa00e55b809d1621392ca6878120fd515a363a05012'


def set_string(p,logical,value):
 i=p.nkgc-1-logical;p.kgc[i]=value;p.kraw[i]=encstr(value)

def build(runtime=None,rebuild_history=False):
 path=W/'game_v205.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  subprocess.run(['python3',str(W/'patch_v205.py')]+(['--rebuild-history']if rebuild_history else [])+(['--runtime',runtime]if runtime else []),check=True,cwd=W)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30]);d=mods[12]
 runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 source=work/'talisman_dead_v206_gbk.lua';source.write_bytes((W/'talisman_dead_v206.lua').read_text().encode('gbk'))
 compiler=work/'compile_talisman_v206.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 subprocess.run([runtime,str(compiler),str(source),str(W/'talisman_dead_v206.ljbc')],check=True)
 compiled=Dump((W/'talisman_dead_v206.ljbc').read_bytes());assert len(compiled.protos)==2
 assert compiled.protos[1].params==3 and compiled.protos[1].nuv==0 and compiled.protos[0].nuv==0
 d=mods[12]
 for getter,parent in [(35,36),(256,257)]:
  d.protos[getter]=Proto(compiled.protos[0].raw,getter);d.protos[parent]=Proto(compiled.protos[1].raw,parent)
 # Legacy hero-first storage remains, but a deployed dead mercenary can also
 # be selected when it is the original fallback owner. Its input is halved.
 p=d.protos[258];assert p.nbc==450
 p.bc[409]=abc('CALL',8,2,3)
 pending=gcid(p,'聚灵符咒_佣兵补发');p=Proto(rebuild_proto(p),258)
 repl={};fix=[]
 repl[410]=[ad('MOV',3,8),p.bc[410]]
 repl[39]=[ad('IST',0,3),0,p.bc[39]];fix.append((39,1,49))
 block=[ad('ISF',0,3),0,ad('GGET',11,gcid(p,'物品格子408')),ad('ISNEV',4,11),0,ad('KSHORT',13,2),abc('DIVVV',12,1,13),ad('MOV',1,12),p.bc[118]]
 repl[118]=block;fix.extend([(118,1,118),(118,4,118)])
 # New internal tag uses the already registered XP closure; no new public API.
 repl[387]=[ad('ISNES',3,pending),0,ad('FNEW',8,72),ad('KSHORT',9,2),ad('KSHORT',10,0),abc('CALL',8,1,3),ad('RET0',0,1),p.bc[387]]
 raw,mp=replace_instructions(p,repl);q=Proto(raw,258)
 from patch_v139 import jump
 q.bc[mp[410]+1]=jump(mp[410]+1,mp[6],20)
 q.bc[mp[39]+1]=jump(mp[39]+1,mp[49],20)
 for at in[1,4]:q.bc[mp[118]+at]=jump(mp[118]+at,mp[118]+8,20)
 q.bc[mp[387]+1]=jump(mp[387]+1,mp[387]+7,20)
 d.protos[258]=Proto(rebuild_proto(q),258)
 # Persist successful deployment and flush queued XP after original XP restore.
 p=d.protos[261];assert p.nbc==1110
 marker=gcid(p,'__gm_talisman_summoned_v206');exp=gcid(p,'经验获得');tag=gcid(p,'聚灵符咒_佣兵补发');p=Proto(rebuild_proto(p),261)
 assert marker<256 and exp<256
 reg=[abc('TGETS',4,3,gcid(p,'佣兵')),ad('KPRI',5,2),abc('TSETS',5,4,marker),p.bc[581]]
 flush=[ad('UGET',4,0),abc('TGETS',4,4,exp),ad('KSHORT',5,0),ad('KSHORT',6,0),ad('KSHORT',7,1),ad('KSTR',8,tag),abc('CALL',4,1,5),p.bc[628]]
 raw,spawnmap=replace_instructions(p,{581:reg,628:flush});d.protos[261]=Proto(raw,261)
 for m,d in mods.items():
  for p in list(d.protos):
   touched=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'Guimeng patch v1.205',b'Guimeng patch v1.206').replace(b'Guimeng v1.205 diagnostics',b'Guimeng v1.206 diagnostics').replace(b'patch=v1.205',b'patch=v1.206')
    if m==12 and p.idx in [76,22187]:
     if v==b'1.205':new=b'1.206'
     if v=='魔改版 1.205'.encode('gbk'):new='魔改版 1.206'.encode('gbk')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);touched=True
   if touched:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(d.protos)if p.raw!=old[m].protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v206.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=enc if m==12 else enc.hex().upper().encode()
  set_string(outer.protos[0],m,value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v206.res').write_bytes(data)
 r={'version':'v1.206','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'xp_relocations':mp,'spawn_relocations':spawnmap,'dead_storage_ratio':0.5,'rules_changed':True}
 (W/'build_v206.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in r.items()if not k.endswith("relocations")})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
