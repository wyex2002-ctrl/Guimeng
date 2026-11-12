from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from ljdis import OPS
from patch_v139 import ad,abc,jump,gcid,encstr,rebuild_proto,rebuild_dump
from bytecode_relocate import replace_instructions
from resource_tools import decode
W=Path(__file__).resolve().parent

def build(runtime=None):
 subprocess.run(['python3',str(W/'patch_v179.py')],cwd=W,check=True,stdout=subprocess.DEVNULL)
 base=(W/'game_v179.res').read_bytes()
 assert hashlib.sha256(base).hexdigest()=='2e6f04d2bcdd97e3c50b457cce58238d576df689c4032fb2dfc138f8648d842c'
 if runtime:
  work=W/'compile_work/v180';work.mkdir(parents=True,exist_ok=True)
  src=work/'accuracy_gbk.lua';src.write_bytes((W/'accuracy_v180.lua').read_text(encoding='utf-8').encode('gbk'))
  compiler=work/'compile.lua';compiler.write_text('local f=assert(io.open(arg[1],"rb"));local s=f:read("*a");f:close();local c=assert(loadstring(s,"@accuracy_v180.lua"));local o=assert(io.open(arg[2],"wb"));o:write(string.dump(c));o:close()')
  subprocess.run([runtime,str(compiler),str(src),str(W/'accuracy_v180.ljbc')],check=True)
 outer,mods=decode(base,[12,14]);d=mods[12]
 # A genuine initialization callback previously overwrote the saved difficulty with normal.
 p=d.protos[18526];assert p.bc[19]==ad('KSTR',4,gcid(p,'难度选择'))
 p.bc[19]=ad('KSTR',4,gcid(p,'难度恢复'));p.raw=rebuild_proto(p);d.protos[18526]=Proto(p.raw,18526)
 p=d.protos[76];assert p.bc[13]==ad('ISNES',2,gcid(p,'难度选择'))
 block=[ad('ISNES',2,gcid(p,'难度恢复')),0,
  ad('GGET',3,gcid(p,'tonumber')),ad('GGET',4,gcid(p,'读配置项')),
  ad('KSTR',5,gcid(p,'Dat/Options.ini')),ad('KSTR',6,gcid(p,'Main')),ad('KSTR',7,gcid(p,'GuimengDifficulty')),
  abc('CALL',4,2,4),abc('CALL',3,2,2),ad('KSHORT',4,1),ad('ISEQV',3,4),0,
  ad('KSHORT',4,2),ad('ISEQV',3,4),0,ad('KSTR',1,gcid(p,'普通')),0,
  ad('KSTR',1,gcid(p,'简单')),0,ad('KSTR',1,gcid(p,'困难')),ad('KSTR',2,gcid(p,'难度选择')),p.bc[13]]
 for index,to in [(1,len(block)-1),(11,17),(14,19),(16,20),(18,20)]:block[index]=jump(index,to,5)
 p.raw=rebuild_proto(p);raw,mp=replace_instructions(p,{13:block});d.protos[76]=Proto(raw,76)
 # All slot candidate pools pass through this branch; remove before the unique affix draw.
 p=d.protos[193]
 at=next(i for i,v in enumerate(p.bc) if v==ad('ISEQS',11,gcid(p,'击中回蓝')))
 removal=next(i for i in range(at,len(p.bc)) if p.bc[i]==ad('GGET',12,gcid(p,'table')) and OPS[p.bc[i+4]&255]=='CALL')
 assert at==1246 and removal==1273
 p.bc[at+1]=jump(at+1,removal,8);p.raw=rebuild_proto(p);d.protos[193]=Proto(p.raw,193)
 skill=Dump((W/'accuracy_v180.ljbc').read_bytes()).protos[:-1]
 assert len(skill)==1 and skill[0].nuv==0 and skill[0].params==1
 d.protos[231]=skill[0]
 p=d.protos[6464];idx=p.nkgc-1-710;old=p.kgc[idx];assert '攻杀剑术'.encode('gbk') in old
 p.kgc[idx]=old+'\n#md学会后增加准确，0级+1，每升一级再+1。'.encode('gbk');p.kraw[idx]=encstr(p.kgc[idx]);p.raw=rebuild_proto(p);d.protos[6464]=Proto(p.raw,6464)
 changes={12:[76,193,231,6464,18526],14:[]}
 # Change only visible diagnostic version labels, not attachment protocol names.
 for i,p in enumerate(mods[14].protos):
  hit=False
  for k,value in enumerate(p.kgc):
   if isinstance(value,bytes):
    new=value.replace(b'Guimeng patch v1.179',b'Guimeng patch v1.180').replace(b'Guimeng v1.179 diagnostics',b'Guimeng v1.180 diagnostics').replace(b' patch=v1.179 ',b' patch=v1.180 ')
    if new!=value:p.kgc[k]=new;p.kraw[k]=encstr(new);hit=True
  if hit:p.raw=rebuild_proto(p);mods[14].protos[i]=Proto(p.raw,i);changes[14].append(i)
 for module,d in mods.items():
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw
  (W/f'module_{module}_v180.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  encrypted=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
  enc=encrypted if module==12 else encrypted.hex().upper().encode()
  p=outer.protos[0];i=p.nkgc-1-module;p.kgc[i]=enc;p.kraw[i]=encstr(enc)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v180.res').write_bytes(data)
 result={'version':'v1.180','base_sha256':hashlib.sha256(base).hexdigest(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'difficulty_relocation':{str(k):v for k,v in mp.items()},'accuracy':'learned level + 1, existing basic/spirit bonus preserved','removed_random_affixes':['击中回蓝']}
 (W/'build_v180.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in result.items() if k!='difficulty_relocation'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');build(a.parse_args().runtime)
