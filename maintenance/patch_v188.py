"""Guard native item dereferences, retaining original item use and scripts."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import ad,abc,jump,gcid,encstr,rebuild_proto,rebuild_dump
from bytecode_relocate import replace_instructions
from resource_tools import decode
W=Path(__file__).resolve().parent
BASE_SHA='f11e73b523a25de870abd87eda64e65074395d72f5aadb4253f1617a79bdf543'

def protect(p):
 assert p.params==2 and p.frame==26
 strings=['type','table','nil','function','pcall','tostring','__gm_item_invalid_v188','__gm_detail_v179','item.use.invalid',' type=',' requested_slot=','inventory.entry','inventory.item','dispatch.entry','dispatch.item','dispatch.plot_item']
 ids={s:gcid(p,s)for s in strings};assert max(ids.values())<256
 p.frame=37;p=Proto(rebuild_proto(p),p.idx)
 replacements={};fixups={}
 for pc in [15,27,61,63]:
  out=[];refs=[]
  def branch(target):
   refs.append((len(out),target));out.append(0)
  def guard(reg,context):
   out.extend([ad('GGET',26,ids['type']),ad('MOV',27,reg),abc('CALL',26,2,2),ad('ISEQS',26,ids['table'])]);good_ref=len(out);branch(None)
   # Empty cells are normal. Bad non-table entries are skipped and produce at
   # most one native detail/critical record per process, never per update tick.
   out.append(ad('ISEQS',26,ids['nil']));branch(('old',91))
   out.extend([ad('UGET',28,0),abc('TGETS',29,28,ids['__gm_item_invalid_v188']),ad('IST',0,29)]);branch(('old',91))
   out.extend([ad('KPRI',29,2),abc('TSETS',29,28,ids['__gm_item_invalid_v188']),abc('TGETS',29,28,ids['__gm_detail_v179']),ad('GGET',30,ids['type']),ad('MOV',31,29),abc('CALL',30,2,2),ad('ISNES',30,ids['function'])]);branch(('old',91))
   out.extend([ad('GGET',28,ids['pcall']),ad('KSTR',30,ids['item.use.invalid']),ad('KSTR',31,ids[context]),ad('KSTR',32,ids[' type=']),ad('MOV',33,26),ad('KSTR',34,ids[' requested_slot=']),ad('GGET',35,ids['tostring']),ad('MOV',36,23),abc('CALL',35,2,2),abc('CAT',31,31,35),ad('KPRI',32,2),abc('CALL',28,1,5)])
   branch(('old',91))
   refs[refs.index((good_ref,None))]=(good_ref,('local',len(out)))
  if pc in [15,61]:guard(6,'inventory.entry'if pc==15 else 'dispatch.entry')
  out.append(p.bc[pc])
  if pc in [27,61,63]:guard({27:7,61:18,63:19}[pc],{27:'inventory.item',61:'dispatch.item',63:'dispatch.plot_item'}[pc])
  replacements[pc]=out;fixups[pc]=refs
 raw,mp=replace_instructions(p,replacements);q=Proto(raw,p.idx)
 for pc,refs in fixups.items():
  for offset,(kind,target)in refs:
   at=mp[pc]+offset;dest=mp[target]if kind=='old'else mp[pc]+target
   q.bc[at]=jump(at,dest,0)
 return Proto(rebuild_proto(q),p.idx),mp,{str(pc):len(out)for pc,out in replacements.items()}

def build(runtime=None):
 subprocess.run(['python3',str(W/'patch_v187.py')]+(['--runtime',runtime]if runtime else []),cwd=W,check=True,stdout=subprocess.DEVNULL)
 base=(W/'game_v187.res').read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[14,30]);mods[14].protos[397],mp,sizes=protect(mods[14].protos[397])
 for m,d in mods.items():
  for i,p in enumerate(d.protos):
   touched=False
   for k,v in enumerate(p.kgc):
    if isinstance(v,bytes):
     n=v.replace(b'Guimeng patch v1.187',b'Guimeng patch v1.188').replace(b'Guimeng v1.187 diagnostics',b'Guimeng v1.188 diagnostics').replace(b'patch=v1.187',b'patch=v1.188')
     if n!=v:p.kgc[k]=n;p.kraw[k]=encstr(n);touched=True
   if touched:d.protos[i]=Proto(rebuild_proto(p),i)
 _,old=decode(base,mods);changes={}
 for m,d in mods.items():
  changes[m]=[i for i,p in enumerate(old[m].protos)if p.raw!=d.protos[i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{m}_v188.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);value=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30')).hex().upper().encode()
  p=outer.protos[0];k=p.nkgc-1-m;p.kgc[k]=value;p.kraw[k]=encstr(value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v188.res').write_bytes(data)
 result={'version':'v1.188','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'item_relocations':{str(k):v for k,v in mp.items()},'inserted_blocks':sizes,'rules_changed':False,'checks_restored':False}
 (W/'build_v188.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in result.items()if k!='item_relocations'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');x=a.parse_args();build(str(Path(x.runtime).resolve())if x.runtime else None)
