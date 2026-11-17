"""Complete ranged weapon tooltip titles; remove companion combat equip guards."""
from patch_v253 import *
BASE_SHA='528aede944a8a66d87568c752ee5872d8e38e4bf784dcfe9b3b633aac70a3fe2'
PREVIOUS_HELPERS=15

def build(runtime=None,rebuild_history=False):
 path=W/'game_v253.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v253.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30,34]);_,unlocked=decode((W/'game_v252.res').read_bytes(),[14,34])
 runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 compiler=work/'compile254.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 src=work/'merc_mode_v254_gbk.lua';src.write_bytes((W/'merc_mode_v254.lua').read_text().encode('gbk'));out=W/'merc_mode_v254.ljbc';subprocess.run([runtime,str(compiler),str(src),str(out)],check=True)
 helper=Dump(out.read_bytes());assert helper.protos[-1].nuv==0
 # Restore exactly the native user methods and final request before v253's gates.
 for idx in [3,4,11,16,18]:mods[34].protos[idx]=Proto(unlocked[34].protos[idx].raw,idx)
 mods[14].protos[449+PREVIOUS_HELPERS]=Proto(unlocked[14].protos[449].raw,449+PREVIOUS_HELPERS)
 mods[14].protos[399:399+PREVIOUS_HELPERS]=[Proto(p.raw,399+i)for i,p in enumerate(helper.protos)]
 # Complete tooltip reads display names directly, bypassing metadata. Intercept
 # only the two title loads, before native rich-text composition and styling.
 p=mods[12].protos[300];repl={};r=p.frame;p.frame=r+4
 for pc in [524,536]:
  x=p.bc[pc];assert OPS[x&255]=='TGETS'and p.gc(x>>16&255)=='显示名'.encode('gbk')and(x>>8&255)==9
  repl[pc]=[x,ad('GGET',r,gcid(p,'__gm_merc_name_v253')),ad('MOV',r+1,0),ad('MOV',r+2,9),ad('MOV',r+3,2),abc('CALL',r,2,4),ad('MOV',9,r)]
 raw,mp=replace_instructions(p,repl);mods[12].protos[300]=Proto(raw,300)
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   p.idx=i;changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.253',b'v1.254')
    if mid==12 and i in [76,22194]:new=new.replace(b'1.253',b'1.254')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v254.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v254.res').write_bytes(data)
 report={'version':'v1.254','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'merc_helper_count':len(helper.protos),'merc_helper_at':399,'helper_installer':399+len(helper.protos),'tooltip_map':mp,'restored_slot_methods':[3,4,11,16,18],'combat_weapon_guards_removed':True}
 (W/'build_v254.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items()if k!='tooltip_map'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
