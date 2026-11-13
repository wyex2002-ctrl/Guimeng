"""Validate item controls and decode dropped books using bookstore semantics."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zlib
from ljtool import Dump,Proto,rc4
from patch_v139 import ad,abc,jump,gcid,encstr,rebuild_proto,rebuild_dump
from bytecode_relocate import replace_instructions,BRANCHES
from ljdis import OPS
from resource_tools import decode
W=Path(__file__).resolve().parent
BASE_SHA='0c81618c71f01465074934c65ccef6e2fd32567d4515a65f010fa153379f6713'

def controls(p):
 assert p.frame==37 and p.params==2
 # JMP A is a live-register bound in the LuaJIT recorder. Historical
 # trampolines used A=0, which loses live inventory registers on side exits.
 p.bc=[(ins&~0xff00)|(26<<8) if OPS[ins&255]=='JMP'and (ins>>8&255)<26 else ins for ins in p.bc]
 ids={s:gcid(p,s)for s in ['type','table','function','pcall','使用物品','__gm_item_control_v189','控件组','__gm_item_seq_v189']}
 p.frame=40;p=Proto(rebuild_proto(p),p.idx)
 code=[p.bc[228]];labels={};fix=[]
 def mark(s):labels[s]=len(code)
 def branch(s):fix.append((len(code),s));code.append(0)
 code += [ad('GGET',26,ids['type']),ad('MOV',27,20),abc('CALL',26,2,2),ad('ISEQS',26,ids['table'])];branch('method')
 branch('invalid')
 mark('method');code += [abc('TGETS',26,20,ids['使用物品']),ad('GGET',27,ids['type']),ad('MOV',28,26),abc('CALL',27,2,2),ad('ISEQS',27,ids['function'])];branch('good')
 mark('invalid')
 # Only diagnostic formatting/emission is protected; original item callbacks
 # still execute directly and their errors retain their identity and stack.
 code += [ad('UGET',26,0),abc('TGETS',27,26,ids['__gm_item_control_v189']),ad('GGET',28,ids['type']),ad('MOV',29,27),abc('CALL',28,2,2),ad('ISNES',28,ids['function'])];branch('skip')
 code += [ad('GGET',28,ids['pcall']),ad('MOV',29,27),ad('MOV',30,0),ad('MOV',31,7),abc('TGETV',32,9,13),abc('TGETS',33,32,ids['控件组']),abc('TGETV',33,33,17),ad('MOV',34,20),ad('MOV',35,23),abc('CALL',28,1,8)]
 mark('skip');branch('next_control')
 mark('good')
 # A quick-item DB event consumes the real bag item recursively, then the
 # actual UI method deliberately returns false to stop its own default use.
 # Track successful native calls, preserving that UI method's return ABI.
 # R8 is the old result accumulator, safely below CALL20's callee frame.
 seq=ids['__gm_item_seq_v189']
 before=[ad('UGET',26,0),abc('TGETS',8,26,seq),ad('IST',0,8),0,ad('KSHORT',8,0),p.bc[231]]
 after=[];more_labels={};more_fix=[]
 def lab(s):more_labels[s]=len(after)
 def br(s):more_fix.append((len(after),s));after.append(0)
 after += [ad('IST',0,20)];br('success')
 after += [ad('UGET',26,0),abc('TGETS',27,26,seq),ad('ISF',0,27)];br('original')
 after += [ad('ISLE',27,8)];br('original')
 after += [ad('KSHORT',28,1),ad('ISLT',7,28)];br('original')
 after += [ad('KSHORT',28,6),ad('ISLE',7,28)];br('handled')
 after += [ad('KSHORT',28,21),ad('ISLT',7,28)];br('original')
 after += [ad('KSHORT',28,26),ad('ISGT',7,28)];br('original')
 lab('handled');after += [ad('KPRI',20,2),ad('RET1',20,2)]
 lab('success');after += [ad('UGET',26,0),abc('TGETS',27,26,seq),ad('IST',0,27)];br('increment')
 after += [ad('KSHORT',27,0)]
 lab('increment');after += [ad('KSHORT',28,1),abc('ADDVV',27,27,28),abc('TSETS',27,26,seq)]
 lab('original');after.append(p.bc[232])
 replacements={228:code,230:[ad('MOV',20,26)],231:before,232:after}
 raw,mp=replace_instructions(p,replacements);q=Proto(raw,p.idx)
 q.bc[mp[231]+3]=jump(mp[231]+3,mp[231]+5,26)
 for at,label in more_fix:q.bc[mp[232]+at]=jump(mp[232]+at,mp[232]+more_labels[label],29)
 for at,label in fix:
  dest=mp[249] if label=='next_control'else mp[228]+labels[label]
  q.bc[mp[228]+at]=jump(mp[228]+at,dest,27 if label=='good'else 26)
 return Proto(rebuild_proto(q),p.idx),mp,{str(k):len(v)for k,v in replacements.items()}

def books(p):
 assert p.params==5 and p.frame==14
 names=['Gly独','取随机数','解读','残篇','显示名','价格','取道具信息_名称','math','ceil','(残篇)','(秘籍)']
 ids={s:gcid(p,s)for s in names};p=Proto(rebuild_proto(p),p.idx)
 code=[];labels={};fix=[]
 def emit(op,a=0,d=0,b=None,c=None):code.append(ad(op,a,d)if b is None else abc(op,a,b,c))
 def get(a,b,s):emit('TGETS',a,b=b,c=ids[s])
 def put(a,b,s):emit('TSETS',a,b=b,c=ids[s])
 def branch(s):fix.append((len(code),s));code.append(0)
 # Original pre-v173 generator: uniform engine integer in [1,2]. The
 # bookstore tests 解读==1 for fragments (its numeric constant #0 is 1).
 emit('GGET',5,ids['Gly独']);get(5,5,'取随机数');emit('KSHORT',6,1);emit('KSHORT',7,2);emit('CALL',5,b=2,c=3)
 emit('KPRI',6,0);put(6,4,'解读');emit('KSHORT',6,1);emit('ISEQV',5,6);branch('fragment')
 emit('TNEW',5,0);emit('MOV',6,2);emit('KSTR',7,ids['(秘籍)']);emit('CAT',6,b=6,c=7);put(6,5,'显示名');emit('RET1',5,2)
 labels['fragment']=len(code)
 emit('KSHORT',5,0);put(5,4,'残篇');emit('TNEW',5,0);emit('MOV',6,2);emit('KSTR',7,ids['(残篇)']);emit('CAT',6,b=6,c=7);put(6,5,'显示名')
 emit('GGET',6,ids['Gly独']);get(6,6,'取道具信息_名称');emit('MOV',7,2);emit('CALL',6,b=2,c=2);get(6,6,'价格')
 emit('KSHORT',7,2);emit('DIVVV',7,b=6,c=7);emit('GGET',6,ids['math']);get(6,6,'ceil');emit('CALL',6,b=2,c=2);put(6,5,'价格');emit('RET1',5,2)
 replacements={56:code,**{pc:[]for pc in range(57,64)}}
 raw,mp=replace_instructions(p,replacements);q=Proto(raw,p.idx)
 for at,label in fix:q.bc[mp[56]+at]=jump(mp[56]+at,mp[56]+labels[label],5)
 return Proto(rebuild_proto(q),p.idx),mp

def actors(p):
 assert p.frame==30
 ids={s:gcid(p,s)for s in ['__gm_perf_actor_v189','type','function','pcall']};p.frame=34;p=Proto(rebuild_proto(p),p.idx)
 repl={};fix=[]
 for pc,start in [(649,True),(650,False)]:
  block=[ad('UGET',30,0),ad('KSTR',31,ids['__gm_perf_actor_v189']),abc('TGETV',30,30,31),ad('GGET',31,ids['type']),ad('MOV',32,30),abc('CALL',31,2,2),ad('ISNES',31,ids['function']),0,ad('MOV',31,30),ad('GGET',30,ids['pcall']),ad('KPRI',32,2 if start else 1),ad('MOV',33,6)if start else ad('KPRI',33,0),abc('CALL',30,1,4),p.bc[pc]]
  repl[pc]=block
 raw,mp=replace_instructions(p,repl);q=Proto(raw,p.idx)
 for pc in repl:q.bc[mp[pc]+7]=jump(mp[pc]+7,mp[pc]+13,30)
 return Proto(rebuild_proto(q),p.idx),mp

def build(runtime=None):
 subprocess.run(['python3',str(W/'patch_v188.py')]+(['--runtime',runtime]if runtime else []),cwd=W,check=True,stdout=subprocess.DEVNULL)
 base=(W/'game_v188.res').read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 if runtime:
  work=W/'compile_work/v189';work.mkdir(parents=True,exist_ok=True)
  src=work/'profiling_gbk.lua';src.write_bytes((W/'profiling_v189.lua').read_text(encoding='utf-8').encode('gbk'))
  c=work/'compile.lua';c.write_text('local f=assert(io.open(arg[1],"rb"));local s=f:read("*a");f:close();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(assert(loadstring(s,"@profiling_v189.lua"))));o:close()')
  subprocess.run([runtime,str(c),str(src),str(W/'profiling_v189.ljbc')],check=True)
 outer,mods=decode(base,[12,14,30]);d=mods[14]
 d.protos[397],item_map,item_sizes=controls(d.protos[397]);mods[12].protos[14],book_map=books(mods[12].protos[14]);d.protos[385],actor_map=actors(d.protos[385])
 # The companion auxiliary quick-slot trampoline has the same historical
 # A=0 hints; repeated real auxiliary calls reproduce numeric-index errors.
 p=mods[12].protos[283]
 p.bc=[(ins&~0xff00)|(p.frame<<8) if OPS[ins&255]=='JMP'and (ins>>8&255)<p.frame else ins for ins in p.bc]
 mods[12].protos[283]=Proto(rebuild_proto(p),283)
 profile=Dump((W/'profiling_v189.ljbc').read_bytes()).protos[:-1];delta=len(profile)-12
 assert profile[-1].params==1 and profile[-1].nuv==0
 d.protos[669:681]=profile
 for i,p in enumerate(d.protos):p.idx=i
 for module,d in mods.items():
  for index,p in enumerate(d.protos):
   touched=False
   for k,value in enumerate(p.kgc):
    if isinstance(value,bytes):
     v=value.replace(b'Guimeng patch v1.188',b'Guimeng patch v1.189').replace(b'Guimeng v1.188 diagnostics',b'Guimeng v1.189 diagnostics').replace(b'patch=v1.188',b'patch=v1.189')
     if v!=value:p.kgc[k]=v;p.kraw[k]=encstr(v);touched=True
   if touched:d.protos[index]=Proto(rebuild_proto(p),index)
 changes={};_,old=decode(base,mods)
 for module,d in mods.items():
  changes[module]=[i for i,p in enumerate(old[module].protos)if not(module==14 and 669<=i<681)and p.raw!=d.protos[i+delta if module==14 and i>=681 else i].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{module}_v189.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);encrypted=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));value=encrypted if module==12 else encrypted.hex().upper().encode()
  p=outer.protos[0];k=p.nkgc-1-module;p.kgc[k]=value;p.kraw[k]=encstr(value)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v189.res').write_bytes(data)
 result={'version':'v1.189','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_original_prototypes':changes,'profile_delta':delta,'profile_count':len(profile),'item_relocations':item_map,'item_inserted_blocks':item_sizes,'book_relocations':book_map,'actor_relocations':actor_map,'rules_changed':['dropped ordinary skill books now use bookstore decoding results'],'checks_restored':False}
 (W/'build_v189.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print({k:v for k,v in result.items()if 'relocations'not in k})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');x=a.parse_args();build(str(Path(x.runtime).resolve())if x.runtime else None)
