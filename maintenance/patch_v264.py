"""1..50 oil batches, confirmed welcome gift, unstackable oil, 20-second autosave."""
from patch_v263 import *
BASE_SHA='abe4310a325187b4ac1a76c1ffe1b82bb49b12d69babbf4771ebbf20ede5c92e'

def build(runtime=None,rebuild_history=False):
 path=W/'game_v263.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v263.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30]);runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 compiler=work/'compile263.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 source=(W/'luck_system_v264.lua').read_text().replace('-- RULES_GENERATED','local Rules=(function()\n'+(W/'luck_rules_v249.lua').read_text()+'\nend)()')
 src=work/'luck_system_v264_gbk.lua';src.write_bytes(source.encode('gbk'));out=W/'luck_system_v264.ljbc';subprocess.run([runtime,str(compiler),str(src),str(out)],check=True)
 helper=Dump(out.read_bytes());assert helper.protos[-1].nuv==0
 mods[14].protos[378:400]=[Proto(p.raw,378+i)for i,p in enumerate(helper.protos)]
 def compile(name):
  src=work/(name+'_gbk.lua');src.write_bytes((W/(name+'.lua')).read_text().encode('gbk'));out=W/(name+'.ljbc');subprocess.run([runtime,str(compiler),str(src),str(out)],check=True);return Dump(out.read_bytes())
 gift=compile('oil_gift_v264');assert len(gift.protos)==1 and gift.protos[0].nuv==0
 for idx in [149,180]:mods[12].protos[idx]=Proto(gift.protos[0].raw,idx)
 reset=compile('oil_reset_v264');assert len(reset.protos)==2 and reset.protos[0].uv==mods[14].protos[727].uv
 mods[14].protos[727]=Proto(reset.protos[0].raw,727)
 from patch_v181 import save_table
 # Disable oil merging in the native potion installer.
 for idx in [614]:
  p=mods[14].protos[idx];t=p.gc(0);assert ('祝福油'.encode('gbk'),True)in t[2]
  save_table(p,0,('table',t[1],[(k,v)for k,v in t[2]if k!='祝福油'.encode('gbk')]));mods[14].protos[idx]=Proto(rebuild_proto(p),idx)
 p=mods[12].protos[4091];assert p.bc[66]==ad('KSHORT',3,1);p.bc[66]=ad('KSHORT',3,0)
 t=p.gc(8);save_table(p,8,('table',t[1],[(k,('int',1)if k=='叠加上限'.encode('gbk')else v)for k,v in t[2]]));mods[12].protos[4091]=Proto(rebuild_proto(p),4091)
 # Oil must also bypass the database's same-name drag merge (including quick references).
 p=mods[12].protos[37]
 frag=[ad('ISNES',7,gcid(p,'祝福油')),0,ad('UCLO',0,32768),ad('RET0',0,1),p.bc[707]]
 raw,event_map=replace_instructions(p,{707:frag});q=Proto(raw,37);at=event_map[707];q.bc[at+1]=jump(at+1,at+4,7);mods[12].protos[37]=Proto(rebuild_proto(q),37)
 # Append a dedicated 200-tick divisor. Other users of the old 3000 remain.
 from patch_v200 import numbers
 p=mods[12].protos[20];assert p.bc[120]==abc('MODVN',1,1,8)
 slot=p.nkn;p=numbers(p,append=(200,));p.bc[120]=abc('MODVN',1,1,slot);mods[12].protos[20]=Proto(rebuild_proto(p),20)
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   p.idx=i;changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.263',b'v1.264')
    if mid==12 and i in [76,22196]:new=new.replace(b'1.263',b'1.264')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v264.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v264.res').write_bytes(data)
 report={'version':'v1.264','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'luck_helper_count':len(helper.protos),'helper_installer':420,'batch_length':[1,50],'mount_field':'附加.__gm_oil_batch_v263','gift_children':[149,180],'oil_stackable':False,'old_stack_quantities_preserved':True,'autosave_ticks':200,'timer_period_seconds':0.1,'autosave_seconds':20,'autosave_divisor_slot':slot,'event_map':event_map}
 (W/'build_v264.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items()if k!='event_map'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
