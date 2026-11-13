"""v181: explicitly reviewed anti-cheat spans, shoe affixes, diagnostic labels.

Ranges use v180 PCs (end exclusive). They remove executable checks and punitive
branches, not the engine's ordinary quit API, file decoding or gameplay gates.
Unused constants/child slots remain to preserve the original LuaJIT closure ABI.
"""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4,uleb
from ljdis import OPS
from patch_v139 import ad,abc,jump,gcid,encstr,rebuild_proto,rebuild_dump
from bytecode_relocate import replace_instructions
from resource_tools import decode
W=Path(__file__).resolve().parent

def table_value(v):
 if v is None:return uleb(0)
 if v is False:return uleb(1)
 if v is True:return uleb(2)
 if isinstance(v,bytes):return encstr(v)
 if v[0]=='int':return uleb(3)+uleb(v[1])
 if v[0]=='num':return uleb(4)+uleb(v[1])+uleb(v[2])
 raise ValueError(v)

def save_table(p,logical,value):
 k=p.nkgc-1-logical;assert value[0]=='table'
 p.kgc[k]=value;p.kraw[k]=uleb(1)+uleb(len(value[1]))+uleb(len(value[2]))+b''.join(table_value(v) for v in value[1])+b''.join(table_value(k)+table_value(v)for k,v in value[2])

def build(runtime=None):
 subprocess.run(['python3',str(W/'patch_v180.py')]+(['--runtime',runtime] if runtime else []),check=True,cwd=W,stdout=subprocess.DEVNULL)
 base=(W/'game_v180.res').read_bytes();spec=json.loads((W/'check_removal_v181.json').read_text())
 assert hashlib.sha256(base).hexdigest()==spec['base_sha256']
 outer,mods=decode(base,range(2,86,2));changes={};relocations={}
 targets=set(spec['remove_ranges'])|set(spec['force_return'])|{f'{m}:{p}' for m,ps in spec['stubs'].items() for p in ps}
 for target in sorted(targets):
  m,i=map(int,target.split(':'));p=mods[m].protos[i];repl={}
  if i in spec['stubs'].get(str(m),[]):
   repl={pc:[]for pc in range(len(p.bc))};repl[0]=[ad('RET0',0,1)]
  else:
   for start,end in spec['remove_ranges'].get(target,[]):
    assert 0<=start<end<=len(p.bc),(target,start,end)
    repl.update({pc:[]for pc in range(start,end)})
   if target in spec['force_return']:repl[spec['force_return'][target]]=[ad('RET0',0,1)]
  if target=='12:20':
   # This owner binding is shared by later regeneration code, not a check.
   for pc in range(729,733):repl.pop(pc,None)
  if target=='14:438':p.bc[186]=jump(186,256,3)
  p=Proto(rebuild_proto(p),i);raw,mp=replace_instructions(p,repl);mods[m].protos[i]=Proto(raw,i)
  if target in {'12:20','12:37','12:179','12:185','12:191','12:193','14:301','14:340','14:378','14:438','14:456','14:457','14:458'}:
   relocations[target]={str(k):v for k,v in mp.items()}
 # Existing defensive pool feeds shoes; make comfort reachable, with exact 0.2.
 p=mods[12].protos[142];pool=p.gc(589);comfort='身体舒适'.encode('gbk')
 assert comfort not in pool[1];save_table(p,589,('table',pool[1]+[comfort],pool[2]))
 coeff=p.gc(591);lo,hi=struct.unpack('<II',struct.pack('<d',0.2))
 assert dict(coeff[2])[comfort]==('int',0)
 save_table(p,591,('table',coeff[1],[(k,('num',lo,hi) if k==comfort else v)for k,v in coeff[2]]))
 p.raw=rebuild_proto(p);mods[12].protos[142]=Proto(p.raw,142)
 # Shoe automatic HP/MP regeneration is replaced in the random candidate pool.
 p=mods[12].protos[193]
 oldmap=relocations.get('12:193');at=int(oldmap['1182']) if oldmap else 1182
 remove=int(oldmap['1273']) if oldmap else 1273
 block=[ad('ISNES',10,gcid(p,'鞋子')),0,
        ad('ISEQS',11,gcid(p,'自动回血')),0,ad('ISEQS',11,gcid(p,'自动回蓝')),0,0,
        ad('ISEQS',11,gcid(p,'身体舒适')),0,p.bc[at]]
 # Branches inside inserted fragments are already final-PC-relative.
 for ix,target in [(1,at+7),(3,remove+len(block)-1),(5,remove+len(block)-1),(6,at+9),(8,remove+len(block)-1)]:block[ix]=jump(at+ix,target,12)
 p=Proto(rebuild_proto(p),193);raw,mp=replace_instructions(p,{at:block});mods[12].protos[193]=Proto(raw,193)
 if oldmap:relocations['12:193']={pc:mp[v]for pc,v in oldmap.items()}
 else:relocations['12:193']={str(k):v for k,v in mp.items()}
 for m,d in mods.items():
  for i,p in enumerate(d.protos):
   hit=False
   for k,value in enumerate(p.kgc):
    if isinstance(value,bytes):
     new=value.replace(b'Guimeng patch v1.180',b'Guimeng patch v1.181').replace(b'Guimeng v1.180 diagnostics',b'Guimeng v1.181 diagnostics').replace(b' patch=v1.180 ',b' patch=v1.181 ')
     if new!=value:p.kgc[k]=new;p.kraw[k]=encstr(new);hit=True
   if hit:p.raw=rebuild_proto(p);d.protos[i]=Proto(p.raw,i)
 # Compare each raw prototype to identify the precise changed set.
 _,original=decode(base,mods)
 for m,d in mods.items():
  changed=[i for i,(p,q)in enumerate(zip(original[m].protos,d.protos))if p.raw!=q.raw]
  if not changed:continue
  changes[m]=changed;raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw
  (W/f'module_{m}_v181.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  encrypted=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));enc=encrypted if m==12 else encrypted.hex().upper().encode()
  p=outer.protos[0];k=p.nkgc-1-m;p.kgc[k]=enc;p.kraw[k]=encstr(enc)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v181.res').write_bytes(data)
 result={'version':'v1.181','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'base_sha256':spec['base_sha256'],'changed_prototypes':changes,'relocations':relocations,'shoe_comfort_coefficient':0.2}
 (W/'build_v181.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in result.items()if k not in ['relocations','changed_prototypes']})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');build(a.parse_args().runtime)
