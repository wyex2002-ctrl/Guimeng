"""Six-cell companion range and visual-only native spinning weapon flights."""
from patch_v254 import *
from bytecode_relocate import numeric_and_debug
BASE_SHA='f2cdbeb004e96967677d153dcfdf1c9b9c7d2c986d11435a79f9ffc62cb970a5'

def build(runtime=None,rebuild_history=False):
 path=W/'game_v254.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v254.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,22,30,46]);runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 compiler=work/'compile255.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 src=work/'merc_mode_v255_gbk.lua';src.write_bytes((W/'merc_mode_v255.lua').read_text().encode('gbk'));out=W/'merc_mode_v255.ljbc';subprocess.run([runtime,str(compiler),str(src),str(out)],check=True)
 helper=Dump(out.read_bytes());assert helper.protos[-1].nuv==0
 mods[14].protos[399:409]=[Proto(p.raw,399+i)for i,p in enumerate(helper.protos)]
 maps={}
 def edit(mid,idx,repl):
  d=mods[mid];p=d.protos[idx];raw,mp=replace_instructions(p,repl);d.protos[idx]=Proto(raw,idx);maps[f'{mid}/{idx}']=mp;return mp
 # Private copy of the native flight constructor/lifecycle, never the monster
 # skill callback or damage implementation. Replace the entire damage method
 # with its original zero-return contract. Global module46 stays byte-identical.
 native=mods[46];private=[Proto(p.raw,p.idx)for p in native.protos[:8]]
 p=private[1];private[1]=Proto(bytes([p.flags,p.params,1,p.nuv])+uleb(0)+uleb(0)+uleb(1)+uleb(0)+struct.pack('<I',ad('RET0',0,1))+p.uv,1)
 # A private image branch takes the same preloaded texture used by the real
 # dropped item. Create a fresh sprite; never rotate a shared ground sprite.
 p=private[7]
 frag=[ad('MOV',17,8),jump(1,5,26)]
 # Replacements use absolute fragment-PC offsets after relocation below.
 raw,mp=replace_instructions(p,{301:frag,302:[],303:[],304:[],208:[ad('KSHORT',18,0),abc('TSETS',18,17,gcid(p,'__gm_spin_v255')),p.bc[208]]})
 q=Proto(raw,7);q.bc[mp[301]+1]=jump(mp[301]+1,mp[305],26);private[7]=Proto(rebuild_proto(q),7)
 maps['private/7']=mp
 # The original renderer's scale/position/visibility remain; only this private
 # image's angle is driven by a frame-time spin value.
 p=private[4];raw,mp=replace_instructions(p,{73:[abc('TGETS',5,5,gcid(p,'子弹信息')),abc('TGETS',5,5,gcid(p,'__gm_spin_v255'))]});private[4]=Proto(raw,4);maps['private/4']=mp
 packet=native.header+b''.join(uleb(len(p.raw))+p.raw for p in private)+b'\0';(W/'merc_flight_native_v255.ljbc').write_bytes(packet);assert Dump(packet).rebuild()==packet
 d=mods[22];root=d.protos[113];logical=root.nkgc;root.kgc.insert(0,('child',));root.kraw.insert(0,uleb(0));root.nkgc+=1
 # Earlier root insertions left stale debug ranges; recover the pristine
 # root line table instead of parsing that historical malformed tail.
 import zipfile
 _,pristine=decode(zipfile.ZipFile(W/'base_v176.zip').read('Lib/game.res'),[22]);original=pristine[22].protos[-1]
 assert root.bc[:original.nbc-1]==original.bc[:-1] and original.nuv==0
 _,debug=numeric_and_debug(original);width=2
 assert len(debug)==original.nbc*width+1 and debug[-1:]==b'\0'
 root.bc[-1:-1]=[ad('FNEW',0,logical),ad('GSET',0,gcid(root,'__gm_merc_visual_factory_v255'))]
 numeric,_=numeric_and_debug(root)
 debug=debug[:(original.nbc-1)*width]+debug[(original.nbc-1)*width:original.nbc*width]*(len(root.bc)-original.nbc+1)+b'\0'
 header=bytes([root.flags,root.params,root.frame,root.nuv])+uleb(root.nkgc)+uleb(root.nkn)+uleb(len(root.bc))+uleb(len(debug))+uleb(root.first)+uleb(root.lines)
 d.protos[113]=Proto(header+struct.pack('<'+'I'*len(root.bc),*root.bc)+root.uv+b''.join(root.kraw)+numeric+debug,113)
 # Construct-time capture is read-only. Each native refresh issues at most one
 # decorative flight and continues its exact original FX and damage branches.
 p=d.protos[53];r=p.frame;p.frame=r+2
 edit(22,53,{399:[ad('GGET',r,gcid(p,'__gm_merc_visual_prepare_v255')),ad('MOV',r+1,8),abc('CALL',r,1,2),p.bc[399]]})
 p=d.protos[52];r=p.frame;p.frame=r+2
 edit(22,52,{29:[ad('GGET',r,gcid(p,'__gm_merc_visual_step_v255')),ad('UGET',r+1,0),abc('CALL',r,1,2),p.bc[29]]})
 d.protos[113:113]=[Proto(p.raw,113+i)for i,p in enumerate(private)]
 # v253 pursuit had an inline eight-cell short; its classification remains
 # unified with the six-cell helper and the existing Chant range check.
 p=d.protos[73];mp253=json.loads((W/'build_v253.json').read_text())['maps'];second={int(k):v for k,v in mp253['22/73_second'].items()};first={int(k):v for k,v in mp253['22/73'].items()};pc=second[first[103]]+5
 assert p.bc[pc]==ad('KSHORT',p.frame-2,8);p.bc[pc]=ad('KSHORT',p.frame-2,6);d.protos[73]=Proto(rebuild_proto(p),73)
 for mid in [12,14,22,30]:
  d=mods[mid]
  for i,p in enumerate(d.protos):
   p.idx=i;changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.254',b'v1.255')
    if mid==12 and i in [76,22194]:new=new.replace(b'1.254',b'1.255')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v255.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v255.res').write_bytes(data)
 report={'version':'v1.255','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'merc_helper_count':len(helper.protos),'merc_helper_at':399,'helper_installer':399+len(helper.protos),'native_visual_count':8,'native_visual_at':113,'native_actor_root':121,'ranged_cells':6,'pursuit_range_pc':pc,'maps':maps,'visual_damage_method':'RET0; original monster damage bytecode removed','global_native_projectile_unchanged':True}
 (W/'build_v255.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items()if k!='maps'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
