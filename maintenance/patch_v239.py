"""Permanent magic shield with actual bonuses and unconditional recast replacement."""
from patch_v238 import *
BASE_SHA='a9f429b5db92fa849dc16b8fc31e84bab8789ed59327c22801bd52f9be4e5778'
MAGIC_DISPATCHERS=[4115,4130,4145,4160,4175,4190,4215,4230,4245,4260,4275,4295,4310,4325,4340,4355,4370,4385,4405,4420,4435,4450,4465,4480,4766,4781,4796,4811,5622,5637,5652,5667,6025,6040]

def build(runtime=None,rebuild_history=False):
 path=W/'game_v238.res'
 if rebuild_history or not path.exists():
  subprocess.run(['python3',str(W/'patch_v238.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30,40]);d=mods[12];maps={};reference=d.protos[4115].bc
 assert [p.idx for p in d.protos if p.bc==reference]==MAGIC_DISPATCHERS
 for idx in MAGIC_DISPATCHERS:
  p=d.protos[idx];assert p.gc(p.bc[808]>>16)=='魔法盾'.encode('gbk')
  # Delete the old instance BEFORE replaying the shield animation. The native
  # old state's disappearance callback hides that animation on destruction.
  # Keeping the old "already present" guard would block all later upgrades.
  for pc,x in enumerate(p.bc):
   if OPS[x&255]in ('JMP','UCLO','FORI','FORL','ITERL','LOOP','ISNEXT'):
    to=pc+1+(x>>16)-32768
    assert not(810<to<838 and not 810<=pc<838),(idx,pc,to)
  repl={pc:[]for pc in range(810,838)}
  repl[810]=[ad('GGET',7,gcid(p,'FXru胃啪'))]+get(p,7,7,'删除状态')+[ad('KSTR',8,gcid(p,'魔法盾')),abc('CALL',7,1,2)]
  assert OPS[p.bc[883]&255]=='TSETS'and p.gc((p.bc[883]>>16)&255)=='持续时间'.encode('gbk')
  repl[883]=[ad('KSHORT',8,0),p.bc[883]]
  raw,mapping=replace_instructions(p,repl);d.protos[idx]=Proto(raw,idx);maps[idx]=mapping
 # Only time changes in the six rows; reduction, resistance, MP, costs and
 # the learned-level mapping remain native (20/30/40/50/55/60, half resist).
 p=d.protos[142]
 for pc in [2430,2432,2434,2436,2438,2440]:
  assert OPS[p.bc[pc]&255]=='TDUP';k=p.bc[pc]>>16;t=p.gc(k)
  save_table(p,k,('table',t[1],[(a,('int',0)if a=='持续时间'.encode('gbk')else v)for a,v in t[2]]))
 d.protos[142]=Proto(rebuild_proto(p),142)
 # v238 already normalizes the other two shields at this post-attribute,
 # pre-icon boundary. Extend only its non-target exit, without moving or
 # rewriting those existing branches, for old saved magic-shield timers too.
 p=mods[40].protos[19];assert p.nbc==949 and p.bc[892]==jump(892,947,7)
 a=Asm(p);entry=a.base
 a.get(7,5,'状态');a.get(7,7,'标识');a.emit('ISNES',7,gcid(p,'魔法盾'));a.jmp('done',8)
 a.emit('KSHORT',7,0);a.set(7,5,'持续时间');a.set(7,5,'时间计次')
 a.get(8,5,'附加属性表');a.set(7,8,'持续时间');a.set(7,8,'剩余时间')
 a.get(9,5,'配置表');a.const(10,'伤害减免增加：');a.get(11,9,'伤害减免')
 a.emit('IST',d=11);a.jmp('reduction',12);a.emit('KSHORT',11,0);a.mark('reduction')
 a.const(12,'\n破防抵抗增加：');a.get(13,9,'抵抗真伤')
 a.emit('IST',d=13);a.jmp('resist',14);a.emit('KSHORT',13,0);a.mark('resist')
 a.emit('CAT',10,b=10,c=13);a.set(10,5,'状态说明');a.set(10,8,'状态说明')
 a.mark('done');a.jmp(947,7);a.finish();p.bc[892]=jump(892,entry,7)
 assert p.nkgc<256,'Asm string access requires one-byte constants'
 mods[40].protos[19]=Proto(rebuild_proto(p),19)
 for mid,d in mods.items():
  for p in list(d.protos):
   changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.238',b'v1.239')
    if mid==12 and p.idx in [76,22194]:new=new.replace(b'1.238',b'1.239')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={}
 for mid,d in mods.items():
  changes[mid]=[p.idx for p in d.protos if p.raw!=old[mid].protos[p.idx].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw
  (W/f'module_{mid}_v239.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v239.res').write_bytes(data)
 report={'version':'v1.239','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_prototypes':changes,'dispatch_maps':maps,'native_constructor_hook':entry,'duration':0,'bonuses_unchanged':True,'recast':'destroy old shield before playing animation; native insertion applies current learned tier'}
 (W/'build_v239.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items()if k!='dispatch_maps'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
