"""Main-character melee timing test: faster presentation, original attack cadence."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import encstr,rebuild_proto,rebuild_dump,ad,abc,gcid
from bytecode_relocate import replace_instructions,numeric_and_debug
from ljtool import uleb
from portal_routes_v212 import extract
from test_v192 import lua
from resource_tools import decode
from runtime import ensure_runtime
from ljdis import OPS
W=Path(__file__).resolve().parent
BASE_SHA='c32dc885ca298a41d4b4a1b51f4a84b6047fb2df798ec501e22670a062e2a542'


def set_string(p,logical,value):
 i=p.nkgc-1-logical;p.kgc[i]=value;p.kraw[i]=encstr(value)

def build(runtime=None,rebuild_history=False):
 path=W/'game_v211.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  subprocess.run(['python3',str(W/'patch_v211.py')]+(['--rebuild-history']if rebuild_history else [])+(['--runtime',runtime]if runtime else []),check=True,cwd=W)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[10,12,14,30]);d=mods[12]
 runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 routes,evidence=extract(mods[12])
 (W/'portal_routes_v212.json').write_text(json.dumps({'routes':routes,'evidence':evidence},ensure_ascii=False,indent=2)+'\n')
 source=work/'portal_labels_v212_gbk.lua';body=(W/'portal_labels_v212.lua').read_text().replace('local routes = {} -- ROUTES_GENERATED','local routes = '+lua({k:v.encode('gbk')for k,v in routes.items()}))
 source.write_bytes(body.encode('gbk'))
 compiler=work/'compile_portals_v212.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 subprocess.run([runtime,str(compiler),str(source),str(W/'portal_labels_v212.ljbc')],check=True)
 compiled=Dump((W/'portal_labels_v212.ljbc').read_bytes());assert compiled.protos[-1].params==6 and compiled.protos[-1].nuv==0
 d=mods[10];helper_count=len(compiled.protos);assert len(d.protos)==41
 maps={};key='__gm_portal_labels_call_v212'
 p=d.protos[27];method=gcid(p,key)
 def call(mode):return [ad('UGET',21,0),abc('TGETS',20,21,method),ad('KSTR',22,gcid(p,mode))]
 begin=call('begin')+[abc('CALL',20,1,3)]
 draw=call('draw')+[abc('CALL',20,1,3)]
 collect=call('collect')+[ad('UGET',23,0),abc('TGETS',23,23,gcid(p,'事件组')),abc('TGETV',23,23,7),ad('MOV',24,15),ad('MOV',25,16),abc('TGETS',26,21,gcid(p,'附加标识组')),abc('TGETS',27,23,gcid(p,'id')),abc('TGETV',26,26,27),abc('TGETV',26,26,13),abc('TGETB',26,26,1),abc('CALL',20,1,7)]
 p.frame=30;p=Proto(rebuild_proto(p),27)
 raw,maps['render']=replace_instructions(p,{17:begin+[p.bc[17]],323:collect+[p.bc[323]],520:draw+[p.bc[520]]});d.protos[27]=Proto(raw,27)
 p=d.protos[39];child=p.nkgc;p.kgc.insert(0,('child',));p.kraw.insert(0,uleb(0));p.nkgc+=1;field=gcid(p,key);p=Proto(rebuild_proto(p),39)
 raw,maps['constructor']=replace_instructions(p,{99:[ad('FNEW',7,child),abc('TSETS',7,2,field),p.bc[99]]})
 d.protos[39]=Proto(raw,39)
 d.protos[39:39]=[Proto(q.raw,39+i)for i,q in enumerate(compiled.protos)]
 for i,q in enumerate(d.protos):q.idx=i
 for m,d in mods.items():
  for p in list(d.protos):
   touched=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'Guimeng patch v1.211',b'Guimeng patch v1.212').replace(b'Guimeng v1.211 diagnostics',b'Guimeng v1.212 diagnostics').replace(b'patch=v1.211',b'patch=v1.212')
    if m==12 and p.idx in [76,22187]:
     if v==b'1.211':new=b'1.212'
     if v=='魔改版 1.211'.encode('gbk'):new='魔改版 1.212'.encode('gbk')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);touched=True
   if touched:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(old[m].protos)if p.raw!=d.protos[i+(helper_count if m==10 and i>=39 else 0)].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v212.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=enc if m==12 else enc.hex().upper().encode()
  set_string(outer.protos[0],m,value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v212.res').write_bytes(data)
 r={'version':'v1.212','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'relocations':maps,'helper_start':39,'helper_count':helper_count,'map_root':39+helper_count,'portal_count':len(routes),'render_insertions':{'17':len(begin),'323':len(collect),'520':len(draw)},'rules_changed':False}
 (W/'build_v212.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in r.items()if not k.endswith("relocations")})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
