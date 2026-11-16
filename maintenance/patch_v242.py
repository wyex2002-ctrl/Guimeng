"""Water buff amounts; pickup controls/timer/radius; red test blessing-oil drops."""
from patch_v241 import *
from patch_v139 import Asm
BASE_SHA='d2358f6eeb9c6cb3971135d2591e676435abca37047496a2c2af2ce0a167fffd'
OIL_DESC='蕴含神秘祝福的油剂，使用后有机会提升已装备坐骑的幸运。'
WATERS=[('攻击神水','最大破坏','破坏上限'),('自然神水','最大自然','自然上限'),('灵魂神水','最大灵魂','灵魂上限'),('疾风神水','攻击速度','攻击速度'),('体力强效神水','最大生命','生命上限'),('魔法强效神水','最大法力','法力上限')]

def add_root_helper(d,compiled,key):
 root=d.protos[-1];index=root.idx;logical=root.nkgc
 root.kgc.insert(0,('child',));root.kraw.insert(0,uleb(0));root.nkgc+=1
 scratch=root.frame;root.frame+=1;root=Proto(rebuild_proto(root),index)
 at=root.nbc-1;assert OPS[root.bc[at]&255]=='RET0'
 # Only the final RET is extended: all original instruction PCs stay fixed.
 # Preserve the legacy class root's opaque debug tail rather than parse it.
 original=root.bc[at];root.bc[at:]=[ad('FNEW',scratch,logical),ad('GSET',scratch,gcid(root,key)),original]
 mp={pc:pc for pc in range(at+1)};mp[at+1]=at+3
 d.protos[index]=Proto(rebuild_proto(root),index)
 d.protos[index:index]=[Proto(p.raw,index+i)for i,p in enumerate(compiled.protos)]
 for i,p in enumerate(d.protos):p.idx=i
 return index,len(compiled.protos),mp

def build(runtime=None,rebuild_history=False):
 path=W/'game_v241.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v241.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,22,26,30,40]);runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 compiler=work/'compile242.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 def compile(name):
  src=work/(name+'_gbk.lua');src.write_bytes((W/(name+'.lua')).read_text().encode('gbk'));out=W/(name+'.ljbc');subprocess.run([runtime,str(compiler),str(src),str(out)],check=True);return Dump(out.read_bytes())
 maps={}
 # Actual native Buff post-attribute/pre-tooltip point, retaining timed water.
 d=mods[40];p=d.protos[19];assert p.bc[952]==jump(952,973,8)
 a=Asm(p);start=a.base;a.get(7,5,'状态');a.get(7,7,'标识')
 for i,(name,field,label)in enumerate(WATERS):a.emit('ISEQS',7,gcid(p,name));a.jmp('water'+str(i),8)
 a.jmp('done',7)
 for i,(name,field,label)in enumerate(WATERS):
  a.mark('water'+str(i));a.const(8,field);a.const(9,label+'增加：');a.jmp('format',10)
 a.mark('format');a.get(10,5,'配置表');a.emit('TGETV',10,b=10,c=8);a.emit('IST',d=10);a.jmp('value',11);a.emit('KSHORT',10,0);a.mark('value');a.emit('CAT',9,b=9,c=10)
 a.get(10,5,'状态');a.get(10,10,'状态说明');a.emit('ISEQS',10,gcid(p,''));a.jmp('text',11);a.const(11,'\n');a.emit('MOV',12,9);a.emit('CAT',9,b=10,c=12)
 a.mark('text');a.set(9,5,'状态说明');a.get(10,5,'附加属性表');a.set(9,10,'状态说明');a.mark('done');a.jmp(973,7);a.finish();p.bc[952]=jump(952,start,8);assert p.nkgc<256;d.protos[19]=Proto(rebuild_proto(p),19)
 # UI adds separate helper children; existing warehouse callbacks stay exact.
 ui=compile('pickup_options_v242');d=mods[12];p=d.protos[22194];logical=p.nkgc;p.kgc.insert(0,('child',));p.kraw.insert(0,uleb(0));p.nkgc+=1;p=Proto(rebuild_proto(p),p.idx)
 at=p.nbc-1;raw,mp=replace_instructions(p,{at:[ad('FNEW',96,logical),abc('CALL',96,1,1),p.bc[at]]});d.protos[22194]=Proto(raw,22194)
 ui_count=len(ui.protos);d.protos[22194:22194]=[Proto(p.raw,22194+i)for i,p in enumerate(ui.protos)]
 for i,p in enumerate(d.protos):p.idx=i
 maps['ui']=mp;ui_root=22194+ui_count
 # Default is session-local and reinitialized on every real hero initialize.
 d=mods[26];p=d.protos[0];temp=p.frame;p.frame+=2;p=Proto(rebuild_proto(p),0);fragment=[]
 for key,flag in [('__gm_pickup_sell_v242',2),('__gm_auto_pickup_v242',1)]:fragment +=[ad('KPRI',temp,flag),ad('KSTR',temp+1,gcid(p,key)),abc('TSETV',temp,0,temp+1)]
 raw,mp=replace_instructions(p,{0:fragment+[p.bc[0]]});d.protos[0]=Proto(raw,0);maps['hero_init']=mp
 # Same original manual pickup source and engine entry for automatic ticks.
 d=mods[14];p=d.protos[385];oldsource=p.gc(222);newsource=(W/'range_pickup_v242.lua').read_text().encode('gbk')
 assert oldsource.replace(b'for dy=-4,4 do for dx=-4,4 do',b'for dy=-5,5 do for dx=-5,5 do').replace(b'local sale_ok=safe_sell(it)',b'local sale_ok=hero.__gm_pickup_sell_v242~=false and safe_sell(it)')==newsource
 set_string(p,222,newsource);fragment=[ad('MOV',2,1),ad('GGET',1,gcid(p,'__gm_pickup_due_v242')),ad('UGET',3,0),abc('TGETS',3,3,gcid(p,'Hero')),ad('GGET',4,gcid(p,'dt')),abc('CALL',1,2,4),p.bc[2962]]
 raw,mp=replace_instructions(p,{2962:fragment});d.protos[385]=Proto(raw,385);maps['frame']=mp
 tick=compile('pickup_tick_v242');assert len(tick.protos)==1;tick_index,tick_count,mp=add_root_helper(d,tick,'__gm_pickup_due_v242');maps['timer_install']=mp
 # Oil remains the existing preview-only item; change requested metadata only.
 d=mods[12];p=d.protos[4089];set_string(p,6,OIL_DESC.encode('gbk'))
 raw,mp=replace_instructions(p,{15:[p.bc[15],ad('KSHORT',2,-256),ad('KSHORT',3,256),abc('MULVV',2,2,3),abc('TSETS',2,1,gcid(p,'颜色值'))]});d.protos[4089]=Proto(raw,4089);maps['oil_template']=mp
 reset=compile('oil_reset_v242');assert len(reset.protos)==2 and reset.protos[0].uv==mods[14].protos[685].uv;mods[14].protos[685]=Proto(reset.protos[0].raw,685)
 # One independent test drop per hostile life, using existing public API and
 # original killer/owner semantics. Original normal loot/reputation unchanged.
 d=mods[22];oil=compile('oil_drop_v242');assert len(oil.protos)==1;oil_index,oil_count,mp=add_root_helper(d,oil,'__gm_oil_drop_v242');maps['oil_install']=mp
 p=d.protos[64];fragment=[ad('GGET',5,gcid(p,'__gm_oil_drop_v242')),ad('MOV',6,0),ad('MOV',7,1),ad('MOV',8,4),abc('CALL',5,1,4),p.bc[65]]
 raw,mp=replace_instructions(p,{65:fragment});d.protos[64]=Proto(raw,64);maps['death']=mp
 p=d.protos[3];repl={}
 for pc,x in enumerate(p.bc):
  if OPS[x&255]=='TSETS'and p.gc(x>>16&255)=='__gm_rep_done_v168'.encode('gbk'):repl[pc]=[x,abc('TSETS',x>>8&255,0,gcid(p,'__gm_oil_done_v242'))]
 assert len(repl)==2;raw,mp=replace_instructions(p,repl);d.protos[3]=Proto(raw,3);maps['respawn']=mp
 for mid,d in mods.items():
  for p in list(d.protos):
   changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.241',b'v1.242')
    if mid==12 and p.idx in [76,ui_root]:new=new.replace(b'1.241',b'1.242')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[p.idx]=Proto(rebuild_proto(p),p.idx)
 _,old=decode(base,mods);changes={};insertions={12:(22194,ui_count),14:(tick_index,tick_count),22:(oil_index,oil_count)}
 for mid,d in mods.items():
  at,count=insertions.get(mid,(len(d.protos),0));changes[mid]=[p.idx for p in old[mid].protos if p.raw!=d.protos[p.idx+(count if p.idx>=at else 0)].raw]
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v242.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v242.res').write_bytes(data)
 report={'version':'v1.242','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'changed_original_prototypes':changes,'insertions':insertions,'maps':maps,'ui_root':ui_root,'ui_helper_count':ui_count,'timer_index':tick_index,'oil_index':oil_index,'pickup_radius':11,'oil_drop_each_kill':1,'oil_description':OIL_DESC,'oil_luck_implemented':False}
 (W/'build_v242.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items()if k!='maps'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
