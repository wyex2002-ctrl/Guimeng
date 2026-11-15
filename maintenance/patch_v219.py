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
BASE_SHA='73ef3a71b7c0f5827a234b8fa6a031532fda71fed2fa65f4a1b647da771edb88'


def set_string(p,logical,value):
 i=p.nkgc-1-logical;p.kgc[i]=value;p.kraw[i]=encstr(value)

def build(runtime=None,rebuild_history=False):
 path=W/'game_v218.res';base=path.read_bytes()if path.is_file()else b''
 reused=not rebuild_history and hashlib.sha256(base).hexdigest()==BASE_SHA
 if not reused:
  subprocess.run(['python3',str(W/'patch_v218.py')]+(['--rebuild-history']if rebuild_history else [])+(['--runtime',runtime]if runtime else []),check=True,cwd=W)
  base=path.read_bytes()
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30,34]);d=mods[12]
 runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 source=work/'warehouse_button_v219_gbk.lua';source.write_bytes((W/'warehouse_button_v219.lua').read_text().encode('gbk'))
 compiler=work/'compile_warehouse_v219.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 subprocess.run([runtime,str(compiler),str(source),str(W/'warehouse_button_v219.ljbc')],check=True)
 compiled=Dump((W/'warehouse_button_v219.ljbc').read_bytes());assert compiled.protos[-1].nuv==0
 helper_count=len(compiled.protos)
 # Final unit price (including wrong-shop discount) is multiplied exactly once.
 p=d.protos[37];replacements={265:[],266:[],267:[]}
 for pc in [285,1362]:
  replacements[pc]=[abc('TGETS',7,5,7),abc('TGETS',7,7,10),abc('MULVV',6,6,7),p.bc[pc]]
 raw,sale_map=replace_instructions(p,replacements);d.protos[37]=Proto(raw,37)
 # Return scroll template and its existing attribute parser carry the stack cap.
 p=d.protos[4090]
 logical=p.bc[9670]>>16;table=p.gc(logical)
 from patch_v181 import save_table
 fields=[(k,('int',1) if k=='叠加'.encode('gbk') else v) for k,v in table[2]]
 value=('table',table[1],fields);save_table(p,logical,value)
 assert p.gc(p.bc[9612]>>16)=='快捷物品ぅ0ぃ商店ぅ杂货店ぃ'.encode('gbk')
 p.bc[9612]=ad('KSTR',4,gcid(p,'快捷物品ぅ0ぃ商店ぅ杂货店ぃ叠加上限ぅ999ぃ'))
 d.protos[4090]=Proto(rebuild_proto(p),4090)
 # Existing quantity validators cover pickup, reload, split and consumption.
 # Extend their existing bounded whitelist, retaining all numeric boundaries.
 whitelist_changes={}
 for mid,dump in mods.items():
  for q in list(dump.protos):
   changed=False
   for j,v in enumerate(q.kgc):
    if isinstance(v,tuple) and v[0]=='table' and ('金创药_小'.encode('gbk'),True) in v[2]:
     assert not any(k=='回城卷'.encode('gbk') for k,_ in v[2])
     save_table(q,q.nkgc-1-j,('table',v[1],v[2]+[('回城卷'.encode('gbk'),True)]));changed=True
   if changed:
    dump.protos[q.idx]=Proto(rebuild_proto(q),q.idx);whitelist_changes.setdefault(mid,[]).append(q.idx)
 d=mods[12]
 # Add the compiled subtree to the UI root; no existing callback is replaced.
 p=d.protos[22187];child=p.nkgc;p.kgc.insert(0,('child',));p.kraw.insert(0,uleb(0));p.nkgc+=1
 last=p.nbc-1;assert OPS[p.bc[last]&255]=='RET0'
 p=Proto(rebuild_proto(p),22187)
 raw,ui_map=replace_instructions(p,{last:[ad('FNEW',96,child),abc('CALL',96,1,1),p.bc[last]]})
 d.protos[22187]=Proto(raw,22187)
 d.protos[22187:22187]=[Proto(q.raw,22187+i)for i,q in enumerate(compiled.protos)]
 for i,q in enumerate(d.protos):q.idx=i
 for m,d in mods.items():
  for p in list(d.protos):
   touched=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'Guimeng patch v1.218',b'Guimeng patch v1.219').replace(b'Guimeng v1.218 diagnostics',b'Guimeng v1.219 diagnostics').replace(b'patch=v1.218',b'patch=v1.219')
    if m==12 and p.idx in [76,22187+helper_count]:
     if v==b'1.218':new=b'1.219'
     if v=='魔改版 1.218'.encode('gbk'):new='魔改版 1.219'.encode('gbk')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);touched=True
   if touched:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(old[m].protos)if p.raw!=d.protos[i+(helper_count if m==12 and i>=22187 else 0)].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v219.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=enc if m==12 else enc.hex().upper().encode()
  set_string(outer.protos[0],m,value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v219.res').write_bytes(data)
 r={'version':'v1.219','base_sha256':BASE_SHA,'base_reused':reused,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'sale_map':sale_map,'ui_map':ui_map,'helper_count':helper_count,'helper_index':22187,'root_index':22187+helper_count,'whitelist_changes':whitelist_changes,'scroll_stack_cap':999,'rules_changed':'stack sale total, return-scroll stacking, remote warehouse button'}
 (W/'build_v219.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in r.items()if not k.endswith("_map")})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
