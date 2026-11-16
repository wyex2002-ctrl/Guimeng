"""Lucky stat placement, zero equipment luck, oil feedback and closed chat."""
from patch_v245 import *
BASE_SHA='7e017fe828d14865adb17edbb5e277130a680e4c04e8c816d5f4567deed5c859'

def build(runtime=None,rebuild_history=False):
 path=W/'game_v245.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v245.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30]);runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 compiler=work/'compile246.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 src=work/'luck_system_v246_gbk.lua';src.write_bytes((W/'luck_system_v246.lua').read_text().replace('-- RULES_GENERATED','local Rules=(function()\n'+(W/'luck_rules_v246.lua').read_text()+'\nend)()').encode('gbk'))
 out=W/'luck_system_v246.ljbc';subprocess.run([runtime,str(compiler),str(src),str(out)],check=True);helper=Dump(out.read_bytes());count=len(helper.protos);assert helper.protos[-1].nuv==0
 d=mods[14];d.protos[378:399]=[Proto(p.raw,378+i)for i,p in enumerate(helper.protos)]
 for i,p in enumerate(d.protos):p.idx=i
 # Only the chat window defaults closed; bottom/quick windows still open.
 p=mods[12].protos[179];assert OPS[p.bc[505]&255]=='TGETS'and p.gc(p.bc[505]>>16&255)=='打开'.encode('gbk')
 close=gcid(p,'关闭');assert close<256;p.bc[505]=abc('TGETS',5,5,close);mods[12].protos[179]=Proto(rebuild_proto(p),179)
 # Detailed view: move the existing helper call after either required-level branch.
 p=mods[12].protos[300];repl={i:[]for i in range(742,749)}
 repl[803]=[ad('GGET',6,gcid(p,'__gm_luck_line_v244')),ad('MOV',7,0),ad('MOV',8,4),abc('CALL',6,2,3),ad('MOV',7,3),ad('MOV',8,6),abc('CAT',3,7,8),p.bc[803]]
 raw,detailmap=replace_instructions(p,repl);mods[12].protos[300]=Proto(raw,300)
 # Compact view: preserve non-mount native luck, skip its mount duplication.
 _,original=decode((W/'game_v243.res').read_bytes(),[12]);p=original[12].protos[296];a=Asm(p);entry=a.base
 a.get(5,0,'子类');a.emit('ISNES',5,d=gcid(p,'坐骑'));a.jmp('legacy',5);a.jmp(231,5)
 a.mark('legacy');a.ins.append(p.bc[203]);a.jmp(204,6);a.finish();p.bc[203]=jump(203,entry,5)
 repl={819:[ad('GGET',4,gcid(p,'__gm_luck_line_v244')),ad('MOV',5,0),ad('KPRI',6,0),abc('CALL',4,2,3),ad('MOV',5,3),ad('MOV',6,4),abc('CAT',3,5,6),p.bc[819]]}
 raw,compactmap=replace_instructions(p,repl);mods[12].protos[296]=Proto(raw,296)
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.245',b'v1.246')
    if mid==12 and i in [76,22194]:new=new.replace(b'1.245',b'1.246')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v246.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v246.res').write_bytes(data)
 report={'version':'v1.246','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'helper_count':count,'helper_installer':378+count,'detail_map':detailmap,'compact_map':compactmap,'rules_file':'luck_rules_v246.lua'}
 (W/'build_v246.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items()if not k.endswith('_map')})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
