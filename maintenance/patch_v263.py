"""Mount-owned lazy blessing-oil batches and native consume-point commit."""
from patch_v262 import *
BASE_SHA='a903a82701663c39bd6e685468023fe54f3e880e5489c3e4cd9acbd487525869'

def build(runtime=None,rebuild_history=False):
 path=W/'game_v262.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v262.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30,34]);runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 compiler=work/'compile263.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 source=(W/'luck_system_v263.lua').read_text().replace('-- RULES_GENERATED','local Rules=(function()\n'+(W/'luck_rules_v249.lua').read_text()+'\nend)()')
 src=work/'luck_system_v263_gbk.lua';src.write_bytes(source.encode('gbk'));out=W/'luck_system_v263.ljbc';subprocess.run([runtime,str(compiler),str(src),str(out)],check=True)
 helper=Dump(out.read_bytes());assert helper.protos[-1].nuv==0
 mods[14].protos[378:399]=[Proto(p.raw,378+i)for i,p in enumerate(helper.protos)]
 p=mods[34].protos[22];assert OPS[p.bc[41]&255]=='TSETS'and p.gc((p.bc[41]>>16)&255)=='数量'.encode('gbk')
 p.frame=12
 frag=[ad('GGET',8,gcid(p,'__gm_oil_commit_v263')),ad('MOV',9,4),ad('MOV',10,5),abc('TGETS',11,0,gcid(p,'标识')),abc('CALL',8,1,4)]
 raw,consume_map=replace_instructions(p,{41:frag});mods[34].protos[22]=Proto(raw,22)
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   p.idx=i;changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.262',b'v1.263')
    if mid==12 and i in [76,22196]:new=new.replace(b'1.262',b'1.263')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v263.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v263.res').write_bytes(data)
 report={'version':'v1.263','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'luck_helper_count':len(helper.protos),'merc_helper_at':378+len(helper.protos),'helper_installer':378+len(helper.protos)+20,'consume_map':consume_map,'rules_file':'luck_rules_v249.lua','batch_length':[5,10],'mount_field':'附加.__gm_oil_batch_v263'}
 (W/'build_v263.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items()if k!='consume_map'})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
