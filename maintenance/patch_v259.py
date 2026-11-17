"""Twelve-turn mercenary spin, boss-only oil and once-per-role login gift."""
from patch_v258 import *
BASE_SHA='7a61c8de436d12e514bd72f147a93c4eaa89cbb252d20a0dc5d4c7d0d57e7b8e'

def build(runtime=None,rebuild_history=False):
 path=W/'game_v258.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v258.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,22,30]);runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 compiler=work/'compile259.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 src=work/'merc_mode_v259_gbk.lua';src.write_bytes((W/'merc_mode_v259.lua').read_text().encode('gbk'));out=W/'merc_mode_v259.ljbc';subprocess.run([runtime,str(compiler),str(src),str(out)],check=True)
 helper=Dump(out.read_bytes());assert helper.protos[-1].nuv==0
 mods[14].protos[399:417]=[Proto(p.raw,399+i)for i,p in enumerate(helper.protos)]
 def compile_helper(name):
  src=work/(name+'_gbk.lua');src.write_bytes((W/(name+'.lua')).read_text().encode('gbk'));out=W/(name+'.ljbc')
  subprocess.run([runtime,str(compiler),str(src),str(out)],check=True);return Dump(out.read_bytes())
 oil=compile_helper('oil_drop_v259');assert len(oil.protos)==1
 mods[22].protos[112]=Proto(oil.protos[0].raw,112)
 gift=compile_helper('oil_gift_v259');assert len(gift.protos)==1 and gift.protos[0].nuv==0
 login_maps={}
 # Add a private child to each story's native save/load function. Only the
 # successful load tail executes it; save/invalid-load jumps keep their target.
 for idx,pc in [(179,613),(149,319)]:
  p=mods[12].protos[idx];logical=p.nkgc;p.kgc.insert(0,('child',));p.kraw.insert(0,uleb(0));p.nkgc+=1
  r=p.frame;p.frame+=1
  raw,mp=replace_instructions(p,{pc:[p.bc[pc],ad('FNEW',r,logical),abc('CALL',r,1,1)]})
  mods[12].protos[idx]=Proto(raw,idx);mods[12].protos[idx:idx]=[Proto(gift.protos[0].raw,idx)]
  login_maps[str(idx)]=mp
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   p.idx=i;changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.258',b'v1.259')
    if mid==12 and i in [76,22196]:new=new.replace(b'1.258',b'1.259')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v259.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v259.res').write_bytes(data)
 report={'version':'v1.259','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'merc_helper_count':len(helper.protos),'merc_helper_at':399,'helper_installer':399+len(helper.protos),'native_visual_count':8,'native_visual_at':113,'native_actor_root':121,'ranged_cells':6,'fireball_speed_ratio':1.2,'story_base_speeds':[450,350],'effective_speeds':[540,420],'rotation_turns_per_second':12,'previous_rotation_turns_per_second':9,'oil_boss_chance':[3,1000],'oil_small_mob_drop':False,'login_maps':login_maps,'ui_root':22196,'gift_children':[149,180],'maps':json.loads((W/'build_v255.json').read_text())['maps']}
 (W/'build_v259.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items()if k not in['maps','construct_map']})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
