"""Smaller pixel luck gaps; original Xiang Kong launch target joins hit check."""
from patch_v246 import *
BASE_SHA='7194ebfee3e8a325a9cd080dd64b2b2856c848bbc11080fa9cd3065d9ee62a26'

def build(runtime=None,rebuild_history=False):
 path=W/'game_v246.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v246.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,26,30]);runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 compiler=work/'compile247.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 def compile(name,source):
  src=work/(name+'_gbk.lua');src.write_bytes(source.encode('gbk'));out=W/(name+'.ljbc');subprocess.run([runtime,str(compiler),str(src),str(out)],check=True);return Dump(out.read_bytes())
 helper=compile('luck_system_v247',(W/'luck_system_v247.lua').read_text().replace('-- RULES_GENERATED','local Rules=(function()\n'+(W/'luck_rules_v246.lua').read_text()+'\nend)()'))
 count=len(helper.protos);assert count==21 and helper.protos[-1].nuv==0
 mods[14].protos[378:399]=[Proto(p.raw,378+i)for i,p in enumerate(helper.protos)]
 timing=compile('melee_timing_v247',(W/'melee_timing_v247.lua').read_text());assert len(timing.protos)==1 and timing.protos[0].nuv==0;mods[26].protos[87]=Proto(timing.protos[0].raw,87)
 # Capture param2 before the native self-centred skill replaces its anchor.
 p=mods[26].protos[54];assert OPS[p.bc[586]&255]=='ISNES'and p.gc(p.bc[586]>>16)=='刺杀剑术'.encode('gbk')
 raw,capture=replace_instructions(p,{586:[ad('ISEQS',8,gcid(p,'刺杀剑术')),0,ad('ISNES',8,gcid(p,'翔空剑法'))]});p=Proto(raw,54)
 p.bc[capture[586]+1]=jump(capture[586]+1,capture[588],8);mods[26].protos[54]=Proto(rebuild_proto(p),54)
 # Native area collection is complete here. Invoke the hero's existing private
 # timing method before the unchanged legacy thrust merge/effects/damage.
 p=mods[26].protos[53];assert OPS[p.bc[1347]&255]=='JMP'and 1348+(p.bc[1347]>>16)-32768==2434
 code=[ad('UGET',3,0),abc('TGETS',4,3,gcid(p,'施法者')),abc('TGETS',4,4,gcid(p,'__gm_melee_timing_v208')),abc('TGETS',5,3,gcid(p,'施法者')),ad('KSTR',6,gcid(p,'locked_hit')),ad('MOV',7,3),ad('MOV',8,1),abc('CALL',4,1,5),p.bc[1347]]
 # No live persistent local lives above R2 at this boundary. CALL4 preserves
 # faction R1 and original grid-list locals; original merge reloads R3 itself.
 raw,merge=replace_instructions(p,{1347:code});mods[26].protos[53]=Proto(raw,53)
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.246',b'v1.247')
    if mid==12 and i in [76,22194]:new=new.replace(b'1.246',b'1.247')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v247.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v247.res').write_bytes(data)
 report={'version':'v1.247','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'helper_count':count,'helper_installer':399,'capture_map':capture,'merge_map':merge,'rules_file':'luck_rules_v246.lua','luck_gap_pixels':2,'native_area_config_unchanged':True}
 (W/'build_v247.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items()if not k.endswith('_map')})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
