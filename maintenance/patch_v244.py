"""Instance mount oil and unified event-local luck probabilities."""
from patch_v243 import *
from patch_v200 import numbers
BASE_SHA='f0f57386135a141db4d367b19c57f5dd2055bdb682133a78f25482e843297877'

def span(p,repl,start,end,fragment):
 from bytecode_relocate import BRANCHES
 for pc,x in enumerate(p.bc):
  if OPS[x&255]in BRANCHES and not start<=pc<end and repl.get(pc)!=[]:
   target=pc+1+(x>>16)-32768
   assert not start<target<end,(p.idx,pc,target,start,end)
 repl[start]=fragment
 for pc in range(start+1,end):repl[pc]=[]

def build(runtime=None,rebuild_history=False):
 path=W/'game_v243.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v243.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30,52]);runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 compiler=work/'compile244.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 def compile(name,source):
  src=work/(name+'_gbk.lua');src.write_bytes(source.encode('gbk'));out=W/(name+'.ljbc');subprocess.run([runtime,str(compiler),str(src),str(out)],check=True);return Dump(out.read_bytes())
 source=(W/'luck_system_v244.lua').read_text().replace('-- RULES_GENERATED','local Rules=(function()\n'+(W/'luck_rules_v244.lua').read_text()+'\nend)()')
 helper=compile('luck_system_v244',source);assert helper.protos[-1].nuv==0;d=mods[14];p=d.protos[378];logical=p.nkgc;p.kgc.insert(0,('child',));p.kraw.insert(0,uleb(0));p.nkgc+=1;p=Proto(rebuild_proto(p),378)
 frag=[ad('FNEW',20,logical),ad('UGET',21,0),ad('MOV',22,12),abc('CALL',20,1,3),p.bc[562]]
 raw,installmap=replace_instructions(p,{562:frag});d.protos[378]=Proto(raw,378)
 count=len(helper.protos);d.protos[378:378]=[Proto(p.raw,378+i)for i,p in enumerate(helper.protos)]
 for i,p in enumerate(d.protos):p.idx=i
 # Main oil uses the same native inventory consumption path as any consumable.
 main=compile('oil_use_v244','return function()return __gm_luck_use_v244()end');assert len(main.protos)==1;mods[12].protos[4087]=Proto(main.protos[0].raw,4087)
 p=mods[12].protos[4089];set_string(p,27,b'Main = function() return __gm_luck_use_v244() end,');mods[12].protos[4089]=Proto(rebuild_proto(p),4089)
 # Hero attack: replace two independent old luck rolls with a single sum/roll.
 d=mods[12];p=d.protos[278];repl={};f=[ad('GGET',22,gcid(p,'__gm_luck_pair_v244'))]
 for dest,src in [(23,8),(24,9),(25,11),(26,12),(27,6)]:f.append(ad('MOV',dest,src))
 f +=[ad('GGET',28,gcid(p,'FXru胃啪')),ad('MOV',29,4),abc('CALL',22,3,8),ad('MOV',15,22),ad('MOV',13,23)]
 span(p,repl,300,347,f);raw,mp=replace_instructions(p,repl);d.protos[278]=Proto(raw,278);maps={'hero_attack':mp};generic=[]
 # All 247 bound creature attack/defense callbacks, not just named pets.
 for p in list(d.protos):
  if p.params!=3 or p.nbc!=712 or '取随机数'.encode('gbk')not in p.strings():continue
  assert p.gc(p.bc[82]>>16&255)=='最小破坏'.encode('gbk')and p.gc(p.bc[83]>>16&255)=='最大破坏'.encode('gbk')
  repl={};f=[ad('GGET',21,gcid(p,'__gm_luck_attack_v244')),p.bc[82],p.bc[83],ad('MOV',24,3),ad('UGET',25,0),abc('TGETS',25,25,gcid(p,'对象')),abc('CALL',21,2,5),ad('MOV',7,21)]
  span(p,repl,80,86,f)
  f=[ad('GGET',21,gcid(p,'__gm_luck_defense_v244')),ad('MOV',22,18),ad('KPRI',23,1),abc('CALL',21,3,3),ad('MOV',13,21),ad('MOV',14,22)]
  span(p,repl,136,180,f)
  f=[ad('GGET',21,gcid(p,'__gm_luck_defense_v244')),ad('GGET',22,gcid(p,'FXru胃啪')),ad('KPRI',23,2),abc('CALL',21,3,3),ad('MOV',13,21),ad('MOV',14,22)]
  for pc in range(688,712):repl[pc]=[]
  span(p,repl,313,329,f)
  raw,mp=replace_instructions(p,repl);d.protos[p.idx]=Proto(raw,p.idx);generic.append(p.idx)
 assert len(generic)==247
 # Compact legacy tooltip: only mounts get the custom lucky row.
 p=d.protos[296];a=Asm(p);start=a.base;a.get(5,0,'子类');a.emit('ISNES',5,gcid(p,'坐骑'));a.jmp('old',6)
 a.glob(5,'__gm_luck_line_v244');a.emit('MOV',6,0);a.emit('MOV',7,4);a.emit('CALL',5,b=2,c=3);a.emit('MOV',6,3);a.emit('MOV',7,5);a.emit('CAT',3,b=6,c=7);a.jmp(231,5)
 a.mark('old');a.ins.append(p.bc[203]);a.jmp(204,6);a.finish();p.bc[203]=jump(203,start,5);d.protos[296]=Proto(rebuild_proto(p),296)
 # Main detailed tooltip has no existing luck row. Append beside attributes.
 p=d.protos[300];assert p.bc[742]&255!=OPS.index('RET0');f=[ad('GGET',5,gcid(p,'__gm_luck_line_v244')),ad('MOV',6,0),ad('MOV',7,4),abc('CALL',5,2,3),ad('MOV',6,3),ad('MOV',7,5),abc('CAT',3,6,7),p.bc[742]]
 raw,mp=replace_instructions(p,{742:f});d.protos[300]=Proto(raw,300);maps['tooltip']=mp
 # Dedicated outline alias; use same Q_文字 face/size/layout, no global changes.
 d=mods[52];custom=numbers(Proto(d.protos[1].raw,3),{0:0xff493519});p=d.protos[3];alias=gcid(p,'宋_9_幸运');logical=p.nkgc;p.kgc.insert(0,('child',));p.kraw.insert(0,uleb(0));p.nkgc+=1
 a=Asm(p);start=a.base;a.emit('ISEQS',0,alias);a.jmp(2,6);a.jmp(33,6)
 select=a.base+len(a.ins);a.emit('ISNES',0,alias);a.jmp(38,6);a.emit('FNEW',3,logical);a.jmp(5,6);a.finish();p.bc[0]=jump(0,start,6);p.bc[4]=jump(4,select,6);d.protos[3]=Proto(rebuild_proto(p),3);d.protos.insert(3,custom)
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   p.idx=i;changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.243',b'v1.244')
    if mid==12 and i in [76,22194]:new=new.replace(b'1.243',b'1.244')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v244.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v244.res').write_bytes(data)
 report={'version':'v1.244','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'helper_index':378,'helper_count':count,'font_insert_at':3,'generic_callbacks':generic,'maps':maps,'install_map':installmap,'helper_installer':378+count,'rules_file':'luck_rules_v244.lua'}
 (W/'build_v244.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items()if k not in ['maps','install_map','generic_callbacks']})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
