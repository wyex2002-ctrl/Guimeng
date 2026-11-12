from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zipfile,zlib
from ljtool import Dump,Proto,rc4,uleb
from ljdis import OPS
from patch_v139 import ad,abc,jump,gcid,encstr,rebuild_dump,rebuild_proto
from bytecode_relocate import replace_instructions
from resource_tools import decode
W=Path(__file__).resolve().parent
BASE=W/'base_v176.zip'
BASE_SHA='3a726d2057af581eb0ae765448f31743739a476988a0fb4ca181a7dcd2305739'
MENUS=[7914,8361,9403,10054,10717,11127,18451]
STARTS=[7917,8364,9406,10057,10720,11130,18454]
ALLOWED=['武器','项链','戒指','头盔','手镯']

def compile_source(runtime):
 tmp=W/'compile_work';tmp.mkdir(exist_ok=True);compiler=tmp/'compile.lua'
 compiler.write_text('local f=assert(io.open(arg[2],"wb"));f:write(string.dump(assert(loadfile(arg[1]))));f:close()')
 for name in ['daily_double_v177','activate_double_v177','kill_reputation_v177']:
  src=tmp/(name+'_gbk.lua');src.write_bytes((W/(name+'.lua')).read_text().encode('gbk'))
  subprocess.run([str(runtime),str(compiler),str(src),str(W/(name+'.ljbc'))],check=True)

def equipment(d):
 # Helmets and bracelets use the defensive candidate pool. Restoring only
 # the final filter would leave both requested affixes unreachable there.
 config=d.protos[142];i=config.nkgc-1-589
 tag,values,hashed=config.kgc[i]
 assert tag=='table' and not hashed and values[0] is None
 values=values+['真伤几率'.encode('gbk'),'暴击几率'.encode('gbk')]
 config.kgc[i]=(tag,values,hashed)
 config.kraw[i]=uleb(1)+uleb(len(values))+uleb(0)+b''.join(uleb(0) if v is None else encstr(v) for v in values)
 p=d.protos[193]
 assert p.bc[1144]==ad('ISNES',10,gcid(p,'鞋子'))
 ban=next(pc for pc,i in enumerate(p.bc) if i==ad('ISEQS',11,gcid(p,'真伤几率')))
 remove=ban+2+(p.bc[ban+1]>>16)-32768
 assert OPS[p.bc[remove]&255]=='GGET' and p.gc(p.bc[remove]>>16)==b'table'
 assert OPS[p.bc[remove+4]&255]=='CALL'
 keep=remove+5
 cloth=[ad('ISNES',10,gcid(p,'衣服')),ad('JMP',12,32768)]
 for e in '火冰雷风神暗幻':cloth += [ad('ISEQS',11,gcid(p,'攻'+e+'元素')),ad('JMP',12,32768)]
 cloth.append(p.bc[1144])
 route=[ad('ISEQS',11,gcid(p,'真伤几率')),ad('JMP',12,32768),ad('ISEQS',11,gcid(p,'暴击几率')),ad('JMP',12,32768),ad('JMP',12,32768)]
 for kind in ALLOWED:route += [ad('ISEQS',10,gcid(p,kind)),ad('JMP',12,32768)]
 route += [ad('JMP',12,32768),p.bc[ban]]
 raw,mp=replace_instructions(p,{1144:cloth,ban:route});p=Proto(raw,193)
 a=mp[1144];p.bc[a+1]=jump(a+1,a+len(cloth)-1,12)
 for k in range(7):p.bc[a+3+2*k]=jump(a+3+2*k,mp[remove],12)
 a=mp[ban]
 for at in [1,3]:p.bc[a+at]=jump(a+at,a+5,12)
 p.bc[a+4]=jump(a+4,a+len(route)-1,12)
 for k in range(5):p.bc[a+6+2*k]=jump(a+6+2*k,mp[keep],12)
 p.bc[a+15]=jump(a+15,mp[remove],12)
 d.protos[193]=p
 return {str(k):v for k,v in mp.items()}

def build():
 with zipfile.ZipFile(BASE) as z:base=z.read('Lib/game.res')
 assert hashlib.sha256(base).hexdigest()==BASE_SHA
 outer,mods=decode(base,[12,14,22]);root=outer.protos[0];d=mods[12]
 daily=Dump((W/'daily_double_v177.ljbc').read_bytes()).protos[:-1]
 assert len(daily)==1 and daily[0].nuv==0 and daily[0].params==2;d.protos[109]=daily[0]
 activation=Dump((W/'activate_double_v177.ljbc').read_bytes()).protos[:-1]
 assert len(activation)==1 and activation[0].nuv==1 and activation[0].params==0
 for idx in STARTS:
  previous=d.protos[idx];p=Proto(activation[0].raw,idx)
  assert previous.nuv==1 and previous.uv==bytes.fromhex('01c0')
  p.uv=previous.uv;p.raw=rebuild_proto(p);d.protos[idx]=Proto(p.raw,idx)
 for idx in MENUS:
  p=d.protos[idx];hits=0
  for i,s in enumerate(p.kgc):
   if isinstance(s,bytes):
    new=s.replace('每天零时后登录或领取时增加两小时双倍时间，可叠加，'.encode('gbk'),'每天增加两小时双倍时间；玛法名俊为四小时。'.encode('gbk'))
    new=new.replace('最多储存二十四小时。活跃卷轴可补满双倍时间。'.encode('gbk'),'新增时间直接累加到剩余余额，上限二十四小时。'.encode('gbk'))
    new=new.replace('双倍时间： #G'.encode('gbk'),'剩余可用双倍： #G'.encode('gbk')).replace('开启双倍@开启双倍经验'.encode('gbk'),'开启双倍@开启或查看双倍'.encode('gbk'))
    if new!=s:p.kgc[i]=new;p.kraw[i]=encstr(new);hits+=1
  assert hits>=3,(idx,hits)
 mp=equipment(d)
 rep=Dump((W/'kill_reputation_v177.ljbc').read_bytes()).protos[:-1]
 assert len(rep)==4 and rep[-1].params==3 and rep[-1].nuv==0
 changed22=[]
 for idx,p in enumerate(rep,60):
  if mods[22].protos[idx].raw!=p.raw:changed22.append(idx)
  mods[22].protos[idx]=p
 p=mods[14].protos[645];hits=[i for i,s in enumerate(p.kgc) if isinstance(s,bytes) and b'Guimeng patch v1.176 | local diagnostic log' in s]
 assert len(hits)==1;i=hits[0];p.kgc[i]=p.kgc[i].replace(b'v1.176',b'v1.177');p.kraw[i]=encstr(p.kgc[i])
 changes={12:sorted([109,142,193]+MENUS+STARTS),14:[645],22:changed22}
 for m,d in mods.items():
  rebuild=set(changes[m])-set([109]+STARTS) if m==12 else {645} if m==14 else set()
  raw=rebuild_dump(d,rebuild);assert Dump(raw).rebuild()==raw
  (W/f'module_{m}_v177.ljbc').write_bytes(raw)
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
  enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));v=enc if m==12 else enc.hex().upper().encode()
  i=root.nkgc-1-m;root.kgc[i]=v;root.kraw[i]=encstr(v)
 data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v177.res').write_bytes(data)
 result={'version':'v1.177','base':'v1.176','base_sha256':BASE_SHA,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'delta_bytes':len(data)-len(base),
  'changed_prototypes':{str(m):v for m,v in changes.items()},'generator_relocations':mp,
  'restored_affixes':['暴击几率','真伤几率'],'allowed_slots':ALLOWED,'clothes_attack_element_cap':0,
  'daily_seconds':{'normal':7200,'active_premium':14400,'cap':86400,'same_day_premium_topup':True},
  'double_activation':'already active shows live balance; no duplicate buff or repeated grant of same daily time',
  'reputation':'numeric-string compatibility; use actual Sys.__gm_diag_checkpoint_v159 receiver; 10% per eligible ordinary kill and Boss ceil(level/3) unchanged; client kill log required to establish remaining cause'}
 (W/'build_v177.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='generator_relocations'},ensure_ascii=False,indent=2))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--runtime');a=ap.parse_args()
 if a.runtime:compile_source(Path(a.runtime).resolve())
 build()
