"""Permanent defensive spells; sum the seven actual public attack elements once."""
from patch_v219 import *
from patch_v181 import save_table
from patch_v201 import unpack_config,pack_config
from patch_v139 import Asm,jump
BASE_SHA='cd3e3495410db0b4eba83328808cd4b5aeaac5c545e6fc857d8420a2773b861f'
DISPATCHERS=[4498,4511,4539,4552,4565,4583,4596,4609,4627,4640,4653,4666,4679,4692,4710,4723,4741,4987,5000]
SPELLS=[('幽灵盾','魔防','真伤'),('神圣战甲术','防御','暴击')]

def get(p,a,b,key,tmp=14):
 k=gcid(p,key)
 return [abc('TGETS',a,b,k)]if k<256 else[ad('KSTR',tmp,k),abc('TGETV',a,b,tmp)]
def put(p,a,b,key,tmp=14):
 k=gcid(p,key)
 return [abc('TSETS',a,b,k)]if k<256 else[ad('KSTR',tmp,k),abc('TSETV',a,b,tmp)]

def build(runtime=None,rebuild_history=False):
 path=W/'game_v236.res'
 if rebuild_history or not path.exists():
  subprocess.run(['python3',str(W/'patch_v236.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30,40]);d=mods[12];maps={}
 reference=d.protos[DISPATCHERS[0]].bc
 for idx in DISPATCHERS:
  p=d.protos[idx];assert p.bc==reference
  repl={}
  for start,(name,defense,resist)in zip([950,973],SPELLS):
   assert p.gc((p.bc[start+4]>>16)&255)=='主角攻暗元素'.encode('gbk')
   fragment=get(p,9,6,'状态效果')+[ad('GGET',10,gcid(p,'math'))]+get(p,10,10,'ceil')
   # FX public 属性 includes each custom attribute's native base + bonus. Do
   # not sum 主角攻幻元素: v176 deliberately makes that alias an aggregate.
   fragment += [ad('GGET',11,gcid(p,'FXru胃啪'))]+get(p,11,11,'属性')
   for n,e in enumerate('火冰雷风神暗幻'):
    fragment+=get(p,12 if n==0 else 13,11,'攻'+e+'元素')
    if n:fragment+=[abc('ADDVV',12,12,13)]
   fragment += [ad('KSHORT',13,2),abc('DIVVV',11,12,13),abc('CALL',10,2,2),abc('ADDVV',9,9,10)]
   fragment+=put(p,9,7,'最大'+defense)+put(p,9,7,'抵抗'+resist)
   fragment += [ad('KSHORT',10,0)]+put(p,10,7,'持续时间')
   fragment += [ad('KSTR',10,gcid(p,('魔法防御'if defense=='魔防'else'物理防御')+'增加：0-')),ad('MOV',11,9),ad('KSTR',12,gcid(p,'\n'+resist+'抵抗增加：')),ad('MOV',13,9),abc('CAT',10,10,13)]
   fragment+=put(p,10,7,'状态说明')
   repl.update({pc:[]for pc in range(start,start+18)});repl[start]=fragment
  raw,mapping=replace_instructions(p,repl);d.protos[idx]=Proto(raw,idx);maps[idx]=mapping
 # UI levels 0..5 index rows 1..6; retain tier base, MP and material costs.
 p=d.protos[142]
 for pc in [2677,2679,2681,2683,2685,2687,2692,2694,2696,2698,2700,2702]:
  assert OPS[p.bc[pc]&255]=='TDUP';k=p.bc[pc]>>16;t=p.gc(k)
  assert dict(t[2])['持续时间'.encode('gbk')][1]>0
  save_table(p,k,('table',t[1],[(a,('int',0)if a=='持续时间'.encode('gbk')else v)for a,v in t[2]]))
 d.protos[142]=Proto(rebuild_proto(p),142)
 p=d.protos[725]
 for pc in [14818,15435]:
  k=p.bc[pc]>>16;t=p.gc(k);fields=[]
  for a,v in t[2]:
   if a=='持续时间'.encode('gbk'):v=('int',0)
   if a=='配置项文本'.encode('gbk'):
    body=unpack_config(v);assert '持续时间='.encode('gbk') not in body
    assert pack_config(body)==v # duration resides in the template, not this config
   fields.append((a,v))
  save_table(p,k,('table',t[1],fields))
 d.protos[725]=Proto(rebuild_proto(p),725)
 # Old saved overrides can carry a positive timer and no description. At the
 # real constructor's post-attribute/pre-icon boundary normalize ONLY these
 # two identifiers, using the actual applied attributes (no save migration).
 p=mods[40].protos[19];a=Asm(p);entry=a.base
 a.get(7,5,'状态');a.get(7,7,'标识')
 a.emit('ISEQS',7,gcid(p,'幽灵盾'));a.jmp('ghost',8)
 a.emit('ISEQS',7,gcid(p,'神圣战甲术'));a.jmp('armor',8)
 a.jmp('done',7)
 for label,(_,defense,resist)in zip(['ghost','armor'],SPELLS):
  a.mark(label);a.emit('KSHORT',7,0);a.set(7,5,'持续时间');a.set(7,5,'时间计次')
  a.get(8,5,'附加属性表');a.set(7,8,'持续时间');a.set(7,8,'剩余时间')
  a.get(9,5,'配置表')
  a.const(10,('魔法防御'if defense=='魔防'else'物理防御')+'增加：')
  a.get(11,9,'最小'+defense);a.emit('IST',d=11);a.jmp(label+'min',12);a.emit('KSHORT',11,0);a.mark(label+'min')
  a.const(12,'-');a.get(13,9,'最大'+defense);a.emit('IST',d=13);a.jmp(label+'max',14);a.emit('KSHORT',13,0);a.mark(label+'max')
  a.const(14,'\n'+resist+'抵抗增加：');a.get(15,9,'抵抗'+resist);a.emit('IST',d=15);a.jmp(label+'resist',16);a.emit('KSHORT',15,0);a.mark(label+'resist')
  a.emit('CAT',10,b=10,c=15);a.set(10,5,'状态说明');a.set(10,8,'状态说明');a.jmp('done',7)
 a.mark('done');a.ins.append(p.bc[707]);a.jmp(708,7);a.finish();p.bc[707]=jump(707,entry,7)
 assert all(((x>>16)&255)<256 for x in a.ins if OPS[x&255]in('TGETS','TSETS'))
 mods[40].protos[19]=Proto(rebuild_proto(p),19)
 for mid,d in mods.items():
  for p in list(d.protos):
   changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.236',b'v1.237')
    if mid==12 and p.idx in [76,22194]:new=new.replace(b'1.236',b'1.237')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for mid,d in mods.items():
  changes[mid]=[p.idx for p in d.protos if p.raw!=old[mid].protos[p.idx].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw
  (W/f'module_{mid}_v237.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v237.res').write_bytes(data)
 report={'version':'v1.237','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'dispatch_maps':maps,'permanent_statuses':[x[0]for x in SPELLS],'element_source':'actual FX public 属性; fire/ice/lightning/wind/holy/dark/illusion once each','formula':'base + ceil(sum / 2)','native_constructor_hook':entry}
 (W/'build_v237.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items()if k!='dispatch_maps'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
