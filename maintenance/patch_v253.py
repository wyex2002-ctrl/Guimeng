"""Companion effective weapon modes and paler ground coin tint."""
from patch_v252 import *
from bytecode_relocate import BRANCHES
BASE_SHA='d8814f1cfe13235bcbd9f2868a4bcb9437e5982732bd3603c0b85a6d8dd51244'

def build(runtime=None,rebuild_history=False):
 path=W/'game_v252.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v252.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,22,30,34,76]);runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 compiler=work/'compile253.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 def compile(name,source):
  src=work/(name+'_gbk.lua');src.write_bytes(source.encode('gbk'));out=W/(name+'.ljbc');subprocess.run([runtime,str(compiler),str(src),str(out)],check=True);return Dump(out.read_bytes())
 maps={}
 def edit(mid,idx,repl):
  d=mods[mid];p=d.protos[idx];raw,mp=replace_instructions(p,repl);d.protos[idx]=Proto(raw,idx);maps[f'{mid}/{idx}']=mp;return mp
 # Native helpers are installed alongside the existing private script sandbox.
 helper=compile('merc_mode_v253',(W/'merc_mode_v253.lua').read_text());d=mods[14];p=d.protos[399];logical=p.nkgc;p.kgc.insert(0,('child',));p.kraw.insert(0,uleb(0));p.nkgc+=1
 edit(14,399,{566:[ad('FNEW',20,logical),ad('UGET',21,0),ad('MOV',22,12),abc('CALL',20,1,3),p.bc[566]]})
 # Per-actor overrides at original range decisions; DB skill configurations stay intact.
 for idx in [4,72,73,74]:
  p=mods[22].protos[idx];repl={};r=p.frame;p.frame=r+4
  for pc,x in enumerate(p.bc):
   op=OPS[x&255]
   if (op=='TSETS'and p.gc(x>>16&255)=='本次攻击距离'.encode('gbk'))or(idx==4 and pc==1101):
    dest=(x>>8)&255
    # TSETS A holds the computed distance; combo TGETS A holds its result.
    frag=[x,ad('GGET',r,gcid(p,'__gm_merc_range_v253')),ad('MOV',r+1,0),ad('MOV',r+2,dest)]
    if idx==4:frag.append(abc('TGETS',r+3,8,gcid(p,'连招技能')))
    else:frag.append(ad('KPRI',r+3,0))
    frag +=[abc('CALL',r,2,4),ad('MOV',dest,r)]
    if op=='TSETS':frag.append(x)
    repl[pc]=frag
  edit(22,idx,repl)
 # While already in range, reuse the native attack branch before FindPath.
 p=mods[22].protos[73];mp=maps['22/73'];at=mp[103];r=p.frame;p.frame=r+2
 frag=[ad('GGET',r,gcid(p,'__gm_merc_ranged_v253')),ad('MOV',r+1,0),abc('CALL',r,2,2),ad('ISF',0,r),0,ad('KSHORT',r,8),ad('ISGT',1,r),0,0,p.bc[at]]
 raw,mp2=replace_instructions(p,{at:frag});q=Proto(raw,73);start=mp2[at]
 q.bc[start+4]=jump(start+4,start+9,r+1);q.bc[start+7]=jump(start+7,start+9,r+1);q.bc[start+8]=jump(start+8,mp2[mp[131]],r+1)
 mods[22].protos[73]=Proto(rebuild_proto(q),73);maps['22/73_second']=mp2
 # Reset default effective binding on equipping any weapon without a binding.
 p=mods[12].protos[262];p.frame=max(p.frame,15)
 frag=[ad('GGET',12,gcid(p,'__gm_merc_binding_v253')),abc('TGETS',13,4,gcid(p,'道具')),abc('CALL',12,2,2),ad('GGET',13,gcid(p,'Ux雌')),abc('TGETS',13,13,gcid(p,'佣兵对象')),abc('TSETS',12,13,gcid(p,'绑定技能')),p.bc[68]]
 edit(12,262,{68:frag})
 # Ranged Chant retains all cooldown, MP, state and facing/cast logic, but
 # bypasses valid-adjacent-position lookup and the actual teleport call.
 p=mods[12].protos[18009];p.frame=18
 def chantcall():return [ad('GGET',14,gcid(p,'__gm_merc_chant_v253')),ad('MOV',15,0),abc('CALL',14,2,2)]
 frag=chantcall()+[ad('KSHORT',15,2),ad('ISEQV',14,15),0,ad('KSHORT',15,1),ad('ISEQV',14,15),0,p.bc[57]]
 frag2=chantcall()+[ad('KSHORT',15,1),ad('ISEQV',14,15),0,p.bc[99]]
 mp=edit(12,18009,{57:frag,99:frag2});q=mods[12].protos[18009];s=mp[57];q.bc[s+5]=jump(s+5,mp[128],16);q.bc[s+8]=jump(s+8,mp[78],16);s=mp[99];q.bc[s+5]=jump(s+5,mp[105],16);mods[12].protos[18009]=Proto(rebuild_proto(q),18009)
 # Guard each user mutation entrance before mouse/quantity/item writes.
 for idx,operation in [(3,'use'),(4,'place'),(11,'swap'),(16,'take'),(18,'place')]:
  p=mods[34].protos[idx];r=p.frame;p.frame=r+3
  frag=[ad('GGET',r,gcid(p,'__gm_merc_block_v253')),ad('MOV',r+1,0),ad('KSTR',r+2,gcid(p,operation)),abc('CALL',r,2,3),ad('ISF',0,r),0,p.bc[0]]
  # A true block exits with false for predicates/use and no values otherwise.
  frag[5]=jump(5,8,r+1);frag=frag[:6]+[ad('KPRI',r,1),ad('RET1',r,2)]+frag[6:]
  # The copied old entry can be a branch (v188 exchange trampoline).
  mp=edit(34,idx,{0:frag});q=mods[34].protos[idx]
  if OPS[p.bc[0]&255]in BRANCHES:q.bc[8]=jump(8,mp[1+(p.bc[0]>>16)-32768],p.bc[0]>>8&255)
  mods[34].protos[idx]=Proto(rebuild_proto(q),idx)
 # Last native quick-request gate, shared by all UI routes. Restoration uses
 # native data reconstruction rather than these user request opcodes.
 p=mods[14].protos[449];p.frame=6
 edit(14,449,{0:[ad('GGET',4,gcid(p,'__gm_merc_request_v253')),ad('MOV',5,0),abc('CALL',4,2,2),ad('ISF',0,4),jump(4,8,5),ad('KPRI',4,1),ad('KPRI',5,1),ad('RET',4,3),p.bc[0]]})
 # Dynamic returned display metadata: never change templates or saved fields.
 for idx,itemreg,namekey,slot in [(223,1,'显示名',None),(224,1,'显示名',0)]:
  p=mods[14].protos[idx];pc=p.nbc-1;r=p.frame;p.frame=r+5
  frag=[ad('GGET',r,gcid(p,'__gm_merc_name_v253')),ad('MOV',r+1,itemreg),abc('TGETS',r+2,2,gcid(p,namekey)),ad('MOV',r+3,slot)if slot is not None else ad('KPRI',r+3,0),abc('CALL',r,2,4),abc('TSETS',r,2,gcid(p,namekey)),p.bc[pc]]
  edit(14,idx,{pc:frag})
 # Explicit assassin ranged weapons on ground use the same classifier.
 p=mods[76].protos[1];repl={};r=p.frame;p.frame=r+4
 for pc,x in enumerate(p.bc):
  if OPS[x&255]=='TGETS'and p.gc(x>>16&255)=='显示名'.encode('gbk'):
   dest=x>>8&255;src=x>>24&255
   repl[pc]=[x,ad('GGET',r,gcid(p,'__gm_merc_name_v253')),abc('TGETS',r+1,0,gcid(p,'物品')),ad('MOV',r+2,dest),ad('KPRI',r+3,0),abc('CALL',r,2,4),ad('MOV',dest,r)]
 edit(76,1,repl)
 ground=compile('ground_name_color_v253',(W/'ground_name_color_v253.lua').read_text()) # #FFF5CC
 mods[76].protos[0]=Proto(ground.protos[0].raw,0)
 count=len(helper.protos);d=mods[14];d.protos[399:399]=[Proto(p.raw,399+i)for i,p in enumerate(helper.protos)]
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   p.idx=i;changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.252',b'v1.253')
    if mid==12 and i in [76,22194]:new=new.replace(b'1.252',b'1.253')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v253.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v253.res').write_bytes(data)
 report={'version':'v1.253','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'merc_helper_count':count,'merc_helper_at':399,'helper_count':21,'helper_installer':399+count,'gold_ground_color':'#FFF5CC','maps':maps}
 (W/'build_v253.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items()if k!='maps'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
