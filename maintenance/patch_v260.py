"""Original companion active timings; party-to-monster accuracy bonus only."""
from patch_v259 import *
from patch_v196 import number_pool
BASE_SHA='4cbbfa27e2fa1268e01a79fcae473e61dec43821e37a89869aa97e6053e4fd69'

def build(runtime=None,rebuild_history=False):
 path=W/'game_v259.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v259.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,22,26,30]);runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 compiler=work/'compile260.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 src=work/'merc_mode_v260_gbk.lua';src.write_bytes((W/'merc_mode_v260.lua').read_text().encode('gbk'));out=W/'merc_mode_v260.ljbc';subprocess.run([runtime,str(compiler),str(src),str(out)],check=True)
 helper=Dump(out.read_bytes());assert helper.protos[-1].nuv==0
 mods[14].protos[399:417]=[Proto(p.raw,399+i)for i,p in enumerate(helper.protos)]
 hit_maps={};sites=[]
 for mid in [12,22,26]:
  for idx,p in enumerate(mods[mid].protos):
   nums=number_pool(p);pcs=[]
   for pc in range(p.nbc-7):
    x=p.bc[pc];ops=[OPS[v&255]for v in p.bc[pc:pc+8]]
    if ops==['DIVVN','ADDVV','ISNEN','JMP','KSHORT','JMP','DIVVV','MULVN']and nums[x>>16&255]==2.5 and nums[p.bc[pc+7]>>16&255]==100:pcs.append(pc)
   if not pcs:continue
   sites += [(mid,idx,pc)for pc in pcs];r=p.frame;p.frame+=3;repl={}
   for pc in pcs:
    x=p.bc[pc];dest=x>>8&255;dreg=x>>24
    ins=[ad('GGET',r,gcid(p,'__gm_hit_factor_v260'))]
    if mid==12 and idx==280:ins += [ad('KSHORT',r+1,0)]
    elif mid==12 and idx==18010:ins += [ad('GGET',r+1,gcid(p,'Ux雌')),abc('TGETS',r+1,r+1,gcid(p,'佣兵对象'))]
    elif mid==12:ins += [ad('UGET',r+1,0),abc('TGETS',r+1,r+1,gcid(p,'对象'))]
    else:ins += [ad('MOV',r+1,0)]
    ins += [ad('MOV',r+2,0 if mid==12 else 1),abc('CALL',r,2,3),abc('DIVVV',dest,dreg,r)]
    repl[pc]=ins
   raw,mp=replace_instructions(p,repl);mods[mid].protos[idx]=Proto(raw,idx);hit_maps[f'{mid}/{idx}']=mp
 assert len(sites)==252,(len(sites),sites)
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   p.idx=i;changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.259',b'v1.260')
    if mid==12 and i in [76,22196]:new=new.replace(b'1.259',b'1.260')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v260.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v260.res').write_bytes(data)
 report={'version':'v1.260','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'merc_helper_count':len(helper.protos),'merc_helper_at':399,'helper_installer':399+len(helper.protos),'native_visual_count':8,'native_visual_at':113,'native_actor_root':121,'ranged_cells':6,'fireball_speed_ratio':1.2,'story_base_speeds':[450,350],'effective_speeds':[540,420],'rotation_turns_per_second':12,'hit_sites':sites,'hit_maps':hit_maps,'active_projectiles':False,'active_original_hit_timing':True,'maps':json.loads((W/'build_v255.json').read_text())['maps']}
 (W/'build_v260.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items()if k not in['maps','hit_maps','hit_sites']})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
