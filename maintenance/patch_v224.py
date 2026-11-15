"""Correct stack sale totals, stack return scrolls, add a native warehouse button."""
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
BASE_SHA='ec9f095881fee5ffc0d51c9e331e434681b5a9aa231fcc79a900b7a19ee6d130'


def set_string(p,logical,value):
 i=p.nkgc-1-logical;p.kgc[i]=value;p.kraw[i]=encstr(value)

def build(runtime=None,rebuild_history=False):
 path=W/'game_v223.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  subprocess.run(['python3',str(W/'patch_v223.py')]+(['--rebuild-history']if rebuild_history else [])+(['--runtime',runtime]if runtime else []),check=True,cwd=W)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[10,12,14,22,30,56]);d=mods[12]
 runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 source=work/'warehouse_button_v224_gbk.lua';source.write_bytes((W/'warehouse_button_v224.lua').read_text().encode('gbk'))
 compiler=work/'compile_warehouse_v224.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 subprocess.run([runtime,str(compiler),str(source),str(W/'warehouse_button_v224.ljbc')],check=True)
 compiled=Dump((W/'warehouse_button_v224.ljbc').read_bytes());assert len(compiled.protos)==7
 d.protos[22187:22194]=[Proto(q.raw,22187+i)for i,q in enumerate(compiled.protos)]
 helper_count=7
 def compile_source(name,body=None):
  src=work/(name+'_gbk.lua');src.write_bytes((body if body is not None else (W/(name+'.lua')).read_text()).encode('gbk'))
  out=W/(name+'.ljbc');subprocess.run([runtime,str(compiler),str(src),str(out)],check=True);return Dump(out.read_bytes())
 from portal_routes_v213 import extract
 from test_v192 import lua
 routes,_=extract(mods[12])
 body=(W/'portal_labels_v224.lua').read_text().replace('local routes = {} -- ROUTES_GENERATED','local routes = '+lua({k:v.encode('gbk')for k,v in routes.items()}))
 port=compile_source('portal_labels_v224',body);assert len(port.protos)==3
 mods[10].protos[39:42]=[Proto(q.raw,39+i)for i,q in enumerate(port.protos)]
 font=compile_source('font_layout_v224');assert len(font.protos)==1 and font.protos[0].nuv==0
 mods[56].protos[7]=Proto(font.protos[0].raw,7)
 guard=compile_source('guard_ignore_v224');assert len(guard.protos)==1 and guard.protos[0].nuv==0
 d=mods[22];key='__gm_guard_ignore_v224';maps={}
 from patch_v139 import jump
 for idx in [47,69,70,72,73]:
  p=d.protos[idx];method=gcid(p,key)
  assert method<256
  if idx==69:
   p.frame=5;p=Proto(rebuild_proto(p),idx)
   fragment=[ad('UGET',1,0),ad('MOV',3,1),abc('TGETS',2,1,method),ad('MOV',4,0),abc('CALL',2,2,3),ad('ISF',0,2),jump(6,8,5),ad('RET0',0,1)]
   raw,mp=replace_instructions(p,{0:fragment+[p.bc[0]]})
  elif idx==70:
   p.frame=18;p=Proto(rebuild_proto(p),idx)
   fragment=[ad('MOV',16,0),abc('TGETS',15,0,method),ad('MOV',17,13),abc('CALL',15,2,3),ad('IST',0,15),jump(5,6,15)]
   raw,mp=replace_instructions(p,{87:fragment+[p.bc[87]]})
   q=Proto(raw,idx);q.bc[mp[87]+5]=jump(mp[87]+5,mp[109],15);raw=rebuild_proto(q)
  else:
   scratch=p.frame;p.frame+=4
   target=[ad('MOV',scratch+2,2)]if idx==47 else [abc('TGETS',scratch+2,0,gcid(p,'攻击来源'))]
   fragment=[ad('MOV',scratch+1,0),abc('TGETS',scratch,0,method)]+target+[abc('CALL',scratch,2,3),ad('ISF',0,scratch),0]
   if idx==47:tail=[ad('KPRI',scratch,1),ad('RET1',scratch,2)]
   else:tail=[ad('KPRI',scratch,0),abc('TSETS',scratch,0,gcid(p,'攻击来源')),ad('MOV',scratch+1,0),abc('TGETS',scratch,0,gcid(p,'停止')),abc('CALL',scratch,1,2),ad('RET0',0,1)]
   fragment+=tail;fragment[5]=jump(5,len(fragment),scratch)
   p=Proto(rebuild_proto(p),idx);raw,mp=replace_instructions(p,{0:fragment+[p.bc[0]]})
  d.protos[idx]=Proto(raw,idx);maps[str(idx)]=mp
 root=d.protos[111];child=root.nkgc;root.kgc.insert(0,('child',));root.kraw.insert(0,uleb(0));root.nkgc+=1
 field=gcid(root,key);assert field<256
 root=Proto(rebuild_proto(root),111);last=root.nbc-1
 root.bc[last:last+1]=[ad('GGET',0,gcid(root,'类_事件')),ad('FNEW',1,child),abc('TSETS',1,0,field),root.bc[last]]
 raw=rebuild_proto(root)
 d.protos[111]=Proto(raw,111);d.protos.insert(111,Proto(guard.protos[0].raw,111))
 for i,p in enumerate(d.protos):p.idx=i
 for m,d in mods.items():
  for p in list(d.protos):
   touched=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'Guimeng patch v1.223',b'Guimeng patch v1.224').replace(b'Guimeng v1.223 diagnostics',b'Guimeng v1.224 diagnostics').replace(b'patch=v1.223',b'patch=v1.224')
    if m==12 and p.idx in [76,22187+helper_count]:
     if v==b'1.223':new=b'1.224'
     if v=='魔改版 1.223'.encode('gbk'):new='魔改版 1.224'.encode('gbk')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);touched=True
   if touched:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(old[m].protos)if p.raw!=d.protos[i+(1 if m==22 and i>=111 else 0)].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v224.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=enc if m==12 else enc.hex().upper().encode()
  set_string(outer.protos[0],m,value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v224.res').write_bytes(data)
 r={'version':'v1.224','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'helper_count':helper_count,'helper_index':22187,'root_index':22187+helper_count,'guard_maps':maps,'scroll_stack_cap':999,'rules_changed':'town guards ignore player-owned summons; white portal labels scaled three pixels shorter'}
 (W/'build_v224.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in r.items()if not k.endswith("_maps") and not k.endswith("_map")})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
