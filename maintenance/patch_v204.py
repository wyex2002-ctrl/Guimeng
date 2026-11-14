"""Preserve live registers in the original mercenary HP window overlay."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import encstr,rebuild_proto,rebuild_dump,ad,abc,jump,gcid
from runtime import ensure_runtime
from ljtool import uleb
from resource_tools import decode
W=Path(__file__).resolve().parent
BASE_SHA='96ed8a73e2bac9c21ee17e888804d7d10b4d93b5f916b06645d3eec92b38c479'
from ljdis import OPS

def set_string(p,logical,value):
 i=p.nkgc-1-logical;p.kgc[i]=value;p.kraw[i]=encstr(value)

def build(runtime=None,rebuild_history=False):
 path=W/'game_v203.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  subprocess.run(['python3',str(W/'patch_v203.py')]+(['--rebuild-history']if rebuild_history else [])+(['--runtime',runtime]if runtime else []),check=True,cwd=W)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30,48]);d=mods[12]
 # Compile once; register once. Avoid a new closure/allocation every frame.
 runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 source=work/'window_hp_v204_gbk.lua';source.write_bytes((W/'window_hp_v204.lua').read_text().encode('gbk'))
 compiler=work/'compile_window_hp_v204.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 subprocess.run([runtime,str(compiler),str(source),str(W/'window_hp_v204.ljbc')],check=True)
 compiled=Dump((W/'window_hp_v204.ljbc').read_bytes());assert len(compiled.protos)==1
 helper=compiled.protos[0];assert helper.params==1 and helper.nuv==0
 d=mods[48];p=d.protos[7];assert p.nbc==4007 and p.frame==34
 method='__gm_draw_merc_hp_v204';cls=gcid(p,'类_窗口_基础');key=gcid(p,method)
 assert key<256
 p.bc[3751]=jump(3751,3754,6)
 p.bc[3754:3759]=[ad('GGET',6,cls),abc('TGETS',6,6,key),ad('MOV',7,0),abc('CALL',6,1,2),ad('RET0',0,1)]
 d.protos[7]=Proto(rebuild_proto(p),7)
 root=d.protos[43];assert root.nbc==103
 child=root.nkgc;root.kgc.insert(0,('child',));root.kraw.insert(0,uleb(0));root.nkgc+=1
 key=gcid(root,method);assert key<256
 root.bc[102]=jump(102,103,2)
 root.bc += [ad('GGET',0,gcid(root,'类_窗口_基础')),ad('FNEW',1,child),abc('TSETS',1,0,key),ad('RET0',0,1)]
 # Preserve original debug data; added instructions are mapped by the existing
 # rebuild helper when the root is serialized.
 d.protos[43]=Proto(rebuild_proto(root),43)
 d.protos.insert(43,Proto(helper.raw,43))
 for m,d in mods.items():
  for p in list(d.protos):
   touched=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'Guimeng patch v1.203',b'Guimeng patch v1.204').replace(b'Guimeng v1.203 diagnostics',b'Guimeng v1.204 diagnostics').replace(b'patch=v1.203',b'patch=v1.204')
    if m==12 and p.idx in [76,22187]:
     if v==b'1.203':new=b'1.204'
     if v=='魔改版 1.203'.encode('gbk'):new='魔改版 1.204'.encode('gbk')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);touched=True
   if touched:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(old[m].protos)if p.raw!=d.protos[i+(m==48 and i>=43)].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v204.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=enc if m==12 else enc.hex().upper().encode()
  set_string(outer.protos[0],m,value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v204.res').write_bytes(data)
 r={'version':'v1.204','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'overlay_helper':{'module':48,'index':43,'original_root_index':43,'new_root_index':44},'overlay_call_pcs':[3751,3754,3755,3756,3757,3758],'rules_changed':False}
 (W/'build_v204.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(r)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
