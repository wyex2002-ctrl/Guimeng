from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zipfile,zlib,shutil
from ljtool import Dump,Proto,rc4,uleb
from patch_v139 import ad,abc,encstr,rebuild_dump,rebuild_proto
from bytecode_relocate import replace_instructions
from resource_tools import decode
W=Path(__file__).resolve().parent

def build(runtime=None):
 work=W/'compile_work'/'v178_base';work.mkdir(parents=True,exist_ok=True)
 for p in W.iterdir():
  if p.is_file() and p.suffix in ('.py','.zip','.ljbc','.json','.lua','.txt','.gz'):shutil.copy2(p,work/p.name)
 subprocess.run(['python3','patch_v177.py'],cwd=work,check=True,stdout=subprocess.DEVNULL)
 base=(work/'game_v177.res').read_bytes()
 assert hashlib.sha256(base).hexdigest()=='18d317b5dc21073320d5d1998a68e210308da76a6cd746b696a32cea1095755f'
 if runtime:
  src=work/'diagnostics_gbk.lua';src.write_bytes((W/'diagnostics_v178.lua').read_text().encode('gbk'))
  compiler=work/'compile_diag.lua';compiler.write_text('local f=assert(io.open(arg[1],"rb"));local s=f:read("*a");f:close();local c=assert(loadstring(s,"@diagnostics_v178.lua"));local o=assert(io.open(arg[2],"wb"));o:write(string.dump(c));o:close()')
  subprocess.run([runtime,str(compiler),str(src),str(W/'diagnostics_v178.ljbc')],check=True)
 diagnostic=Dump((W/'diagnostics_v178.ljbc').read_bytes()).protos[:-1]
 assert diagnostic[-1].params==1 and diagnostic[-1].nuv==0
 outer,mods=decode(base,[14]);d=mods[14];p=d.protos[645]
 # New child is serialized immediately before installer; existing child IDs stay stable.
 child=p.nkgc;p.kgc.insert(0,('child',));p.kraw.insert(0,uleb(0));p.nkgc+=1
 p.raw=rebuild_proto(p)
 raw,_=replace_instructions(p,{88:[ad('FNEW',22,child),ad('MOV',23,0),abc('CALL',22,1,2),p.bc[88]]})
 d.protos[645]=Proto(raw,645)
 # Only installer header version changes; all gameplay prototypes remain byte-identical.
 p=d.protos[645]
 for i,s in enumerate(p.kgc):
  if isinstance(s,bytes) and b'Guimeng patch v1.177 |' in s:
   p.kgc[i]=s.replace(b'v1.177',b'v1.178');p.kraw[i]=encstr(p.kgc[i])
 p.raw=rebuild_proto(p);d.protos[645]=Proto(p.raw,645)
 d.protos[645:645]=diagnostic
 raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw
 (W/'module_14_v178.ljbc').write_bytes(raw)
 packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
 value=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30')).hex().upper().encode()
 root=outer.protos[0];i=root.nkgc-1-14;root.kgc[i]=value;root.kraw[i]=encstr(value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:]
 (W/'game_v178.res').write_bytes(data)
 result={'version':'v1.178','base_sha256':hashlib.sha256(base).hexdigest(),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'added_prototypes':len(diagnostic),'changed_original_prototypes':{'14':[645]},'game_rules_changed':False}
 (W/'build_v178.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');build(a.parse_args().runtime)
