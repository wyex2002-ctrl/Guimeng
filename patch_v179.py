from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zipfile,zlib,shutil
from ljtool import Dump,Proto,rc4,uleb
from patch_v139 import ad,abc,encstr,rebuild_dump,rebuild_proto
from bytecode_relocate import replace_instructions,numeric_and_debug,BRANCHES
from ljdis import OPS
from resource_tools import decode
W=Path(__file__).resolve().parent

def build(runtime=None):
 work=W/'compile_work'/'v179_base';work.mkdir(parents=True,exist_ok=True)
 for p in W.iterdir():
  if p.is_file() and p.suffix in ('.py','.zip','.ljbc','.json','.lua','.txt','.gz'):shutil.copy2(p,work/p.name)
 subprocess.run(['python3','patch_v177.py'],cwd=work,check=True,stdout=subprocess.DEVNULL)
 base=(work/'game_v177.res').read_bytes()
 assert hashlib.sha256(base).hexdigest()=='18d317b5dc21073320d5d1998a68e210308da76a6cd746b696a32cea1095755f'
 if runtime:
  for name in ['diagnostics_v179','kill_reputation_v179','attach_diagnostics_v179']:
   src=work/(name+'_gbk.lua');src.write_bytes((W/(name+'.lua')).read_text().encode('gbk'))
   compiler=work/'compile_diag.lua';compiler.write_text('local f=assert(io.open(arg[1],"rb"));local s=f:read("*a");f:close();local c=assert(loadstring(s,arg[3]));local o=assert(io.open(arg[2],"wb"));o:write(string.dump(c));o:close()')
   subprocess.run([runtime,str(compiler),str(src),str(W/(name+'.ljbc')),'@'+name+'.lua'],check=True)
 diagnostic=Dump((W/'diagnostics_v179.ljbc').read_bytes()).protos[:-1]
 assert diagnostic[-1].params==1 and diagnostic[-1].nuv==0
 outer,mods=decode(base,[14,22]);d=mods[14];p=d.protos[645]
 # New child is serialized immediately before installer; existing child IDs stay stable.
 child=p.nkgc;p.kgc.insert(0,('child',));p.kraw.insert(0,uleb(0));p.nkgc+=1
 p.raw=rebuild_proto(p)
 raw,_=replace_instructions(p,{88:[ad('FNEW',22,child),ad('MOV',23,0),abc('CALL',22,1,2),p.bc[88]]})
 d.protos[645]=Proto(raw,645)
 # Only installer header version changes; all gameplay prototypes remain byte-identical.
 p=d.protos[645]
 for i,s in enumerate(p.kgc):
  if isinstance(s,bytes) and b'Guimeng patch v1.177 |' in s:
   p.kgc[i]=s.replace(b'v1.177',b'v1.179');p.kraw[i]=encstr(p.kgc[i])
 p.raw=rebuild_proto(p);d.protos[645]=Proto(p.raw,645)
 for idx in [632,645]:
  p=d.protos[idx]
  for i,value in enumerate(p.kgc):
   if isinstance(value,bytes) and b'v1.105' in value:
    p.kgc[i]=value.replace(b'v1.105',b'v1.179');p.kraw[i]=encstr(p.kgc[i])
  p.raw=rebuild_proto(p);d.protos[idx]=Proto(p.raw,idx)
 d.protos[645:645]=diagnostic
 rep=Dump((W/'kill_reputation_v179.ljbc').read_bytes()).protos[:-1]
 assert len(rep)==4 and rep[-1].nuv==0
 for index,p in enumerate(rep,60):mods[22].protos[index]=p
 attach=Dump((W/'attach_diagnostics_v179.ljbc').read_bytes()).protos[:-1]
 event=mods[22];p=event.protos[-1];child=p.nkgc
 p.kgc.insert(0,('child',));p.kraw.insert(0,uleb(0));p.nkgc+=1
 # New string constant uses the next free logical ID; new child remains first serialized.
 cid=p.nkgc;p.kgc.insert(0,'类_事件'.encode('gbk'));p.kraw.insert(0,encstr('类_事件'.encode('gbk')));p.nkgc+=1
 p.raw=rebuild_proto(p);last=len(p.bc)-1
 assert not any(OPS[i&255] in BRANCHES for i in p.bc)
 # Root registration has nonstandard local-debug tail; no original PC moves except final RET.
 numeric,debug=numeric_and_debug(p);width=1 if p.lines<256 else 2 if p.lines<65536 else 4
 if debug:
  split=last*width;debug=debug[:split]+debug[split:split+width]*3+debug[split:]
 p.bc[last:last]=[ad('FNEW',0,child),ad('GGET',1,cid),abc('CALL',0,1,2)]
 header=bytes([p.flags,p.params,p.frame,p.nuv])+uleb(p.nkgc)+uleb(p.nkn)+uleb(len(p.bc))+uleb(len(debug))
 if debug:header+=uleb(p.first)+uleb(p.lines)
 raw=header+struct.pack('<'+'I'*len(p.bc),*p.bc)+p.uv+b''.join(p.kraw)+numeric+debug
 event.protos[-1]=Proto(raw,p.idx);event.protos[-1:-1]=attach
 for module,d in mods.items():
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw
  (W/f'module_{module}_v179.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  value=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30')).hex().upper().encode()
  root=outer.protos[0];i=root.nkgc-1-module;root.kgc[i]=value;root.kraw[i]=encstr(value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:]
 (W/'game_v179.res').write_bytes(data)
 result={'version':'v1.179','base_sha256':hashlib.sha256(base).hexdigest(),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'added_prototypes':len(diagnostic),'added_event_prototypes':len(attach),'changed_original_prototypes':{'14':[632,645],'22':[60,61,62,63,109]},'reward_rules_changed':False}
 (W/'build_v179.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');build(a.parse_args().runtime)
