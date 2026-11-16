"""Cover every registered copy of the generic consumable divine-water branch."""
from patch_v240 import *
from portal_routes_v213 import child_refs
BASE_SHA='4141efd73343539ad8520b3141ec5d390ed1222ece06e8fc1e6cd0c0516391cd'

def water_sites(d):
 result={}
 for p in d.protos:
  for pc,x in enumerate(p.bc):
   if OPS[x&255]!='TDUP':continue
   t=p.gc(x>>16)
   if isinstance(t,tuple)and t[0]=='table'and ('灵魂神水'.encode('gbk'),'最大灵魂'.encode('gbk'))in t[2]:
    assert p.idx not in result;result[p.idx]=pc
 return result

def registered_consumables(d,sites):
 refs=child_refs(d);root=d.protos[4090];result={}
 for pc,x in enumerate(root.bc):
  if OPS[x&255]!='TDUP':continue
  t=root.gc(x>>16)
  if not isinstance(t,tuple)or t[0]!='table':continue
  name=dict(t[2]).get('名称'.encode('gbk'))
  if not name:continue
  fsites=[j for j in range(pc,min(pc+25,root.nbc))if OPS[root.bc[j]&255]=='FNEW']
  if not fsites:continue
  factory=refs[4090,root.bc[fsites[0]]>>16];q=d.protos[factory]
  for j,y in enumerate(q.bc):
   if OPS[y&255]=='TSETS'and q.gc(y>>16&255)==b'Main'and OPS[q.bc[j-1]&255]=='FNEW':
    main=refs[factory,q.bc[j-1]>>16]
    if main in sites:result[name.decode('gbk')]={'factory':factory,'main':main,'template_pc':pc}
 return result

def build(runtime=None,rebuild_history=False):
 path=W/'game_v240.res'
 if rebuild_history or not path.exists():
  subprocess.run(['python3',str(W/'patch_v240.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30]);d=mods[12];sites=water_sites(d);bindings=registered_consumables(d,sites)
 assert len(sites)==len(bindings)==49 and {r['main']for r in bindings.values()}==set(sites)
 maps={};already=[]
 for idx,pc in sites.items():
  p=d.protos[idx]
  if pc==148:
   assert p.bc[147]==ad('KSHORT',5,1);already.append(idx);continue
  assert pc==147 and p.nbc==374 and p.bc[167]==abc('MULVV',7,7,5)
  raw,mp=replace_instructions(p,{pc:[ad('KSHORT',5,1),p.bc[pc]]});d.protos[idx]=Proto(raw,idx);maps[idx]=mp
 assert already==[1256,1259] and len(maps)==47
 for mid,d in mods.items():
  for p in list(d.protos):
   changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.240',b'v1.241')
    if mid==12 and p.idx in [76,22194]:new=new.replace(b'1.240',b'1.241')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for mid,d in mods.items():
  changes[mid]=[p.idx for p in d.protos if p.raw!=old[mid].protos[p.idx].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v241.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v241.res').write_bytes(data)
 report={'version':'v1.241','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'water_maps':maps,'registered_consumables':bindings,'already_fixed':already,'registered_script_count':49,'newly_fixed_count':47,'reported_script':1262,'reported_item':'体力强效神水_小','reported_line':61411}
 (W/'build_v241.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items()if k not in ['water_maps','registered_consumables']})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
