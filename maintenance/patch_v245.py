"""Companion's own equipment luck, source-aware oil and normal quickslots."""
from patch_v244 import *
BASE_SHA='0ed81db41ac778ef5b5057e79dda0eb75fb29b3ebb6e6fcd32cb2ae93582367c'

def build(runtime=None,rebuild_history=False):
 path=W/'game_v244.res'
 if rebuild_history or not path.exists():subprocess.run(['python3',str(W/'patch_v244.py')]+(['--rebuild-history']if rebuild_history else[])+(['--runtime',runtime]if runtime else[]),check=True)
 base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,30]);runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
 compiler=work/'compile245.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
 def compile(name,source):
  src=work/(name+'_gbk.lua');src.write_bytes(source.encode('gbk'));out=W/(name+'.ljbc');subprocess.run([runtime,str(compiler),str(src),str(out)],check=True);return Dump(out.read_bytes())
 helper=compile('luck_system_v245',(W/'luck_system_v245.lua').read_text().replace('-- RULES_GENERATED','local Rules=(function()\n'+(W/'luck_rules_v245.lua').read_text()+'\nend)()'))
 assert helper.protos[-1].nuv==0;count=len(helper.protos);d=mods[14];d.protos[378:395]=[Proto(p.raw,378+i)for i,p in enumerate(helper.protos)]
 for i,p in enumerate(d.protos):p.idx=i
 main=compile('oil_use_v245','return function(source)return __gm_luck_use_v244(source)end');assert len(main.protos)==1;mods[12].protos[4087]=Proto(main.protos[0].raw,4087)
 p=mods[12].protos[4089];set_string(p,27,b'Main = function(source) return __gm_luck_use_v244(source) end,')
 pc=next(i for i,x in enumerate(p.bc)if OPS[x&255]=='TSETS'and p.gc(x>>16&255)=='附加'.encode('gbk'))
 raw,mp=replace_instructions(p,{pc:[p.bc[pc],ad('KSHORT',3,0),abc('TSETS',3,2,gcid(p,'快捷物品'))]});mods[12].protos[4089]=Proto(raw,4089)
 reset=compile('oil_reset_v245',(W/'oil_reset_v245.lua').read_text());assert len(reset.protos)==2
 resetidx=685+count;assert reset.protos[0].uv==mods[14].protos[resetidx].uv;mods[14].protos[resetidx]=Proto(reset.protos[0].raw,resetidx)
 # Companion right-click originally transfers items to the hero. Only oil
 # bypasses that event, allowing the unchanged native inventory Main/consume.
 p=mods[12].protos[37];a=Asm(p);entry=a.base
 a.glob(5,'__gm_oil_event_v245');a.emit('MOV',6,0);a.emit('MOV',7,1);a.emit('CALL',5,b=2,c=3)
 a.emit('ISF',d=5);a.jmp('original',5);a.emit('RET0',5,1)
 a.mark('original');a.jmp(4367,5);a.finish();p.bc[0]=jump(0,entry,5);mods[12].protos[37]=Proto(rebuild_proto(p),37)
 # Actual mercenary attack callback already computes its own level's config.
 p=mods[12].protos[18008];repl={};ids={s:gcid(p,s)for s in ['__gm_luck_pair_v244','Ux雌','佣兵对象','属性','最小伤害','最大伤害']}
 f=[ad('GGET',21,ids['__gm_luck_pair_v244'])]
 for reg,base_reg,field in [(22,8,'最小伤害'),(23,9,'最大伤害')]:
  f +=[ad('GGET',reg,ids['Ux雌']),abc('TGETS',reg,reg,ids['佣兵对象']),abc('TGETS',reg,reg,ids['属性']),abc('TGETS',reg,reg,ids[field]),abc('ADDVV',reg,base_reg,reg)]
 f +=[ad('MOV',24,11),ad('MOV',25,12),ad('MOV',26,6),ad('GGET',27,ids['Ux雌']),abc('TGETS',27,27,ids['佣兵对象']),ad('KPRI',28,0),abc('CALL',21,3,8),ad('MOV',15,21),ad('MOV',13,22)]
 span(p,repl,417,437,f);raw,mercmap=replace_instructions(p,repl);mods[12].protos[18008]=Proto(raw,18008)
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   changed=False
   for j,v in enumerate(p.kgc):
    if not isinstance(v,bytes):continue
    new=v.replace(b'v1.244',b'v1.245')
    if mid==12 and i in [76,22194]:new=new.replace(b'1.244',b'1.245')
    if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
   if changed:d.protos[i]=Proto(rebuild_proto(p),i)
  raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v245.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9);enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v245.res').write_bytes(data)
 report={'version':'v1.245','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'helper_count':count,'helper_installer':378+count,'helper_delta':count-17,'merc_map':mercmap,'oil_map':mp,'reset_index':resetidx,'rules_file':'luck_rules_v245.lua'}
 (W/'build_v245.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items()if k not in ['merc_map','oil_map']})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--runtime');a.add_argument('--rebuild-history',action='store_true');x=a.parse_args();build(x.runtime,x.rebuild_history)
