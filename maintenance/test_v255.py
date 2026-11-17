from test_v225 import *
from patch_v255 import BASE_SHA
from test_v192 import lua

def main(runtime):
 work=W/'native_work/v255';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v254.res').read_bytes();b=(W/'game_v255.res').read_bytes();assert hashlib.sha256(a).hexdigest()==BASE_SHA
 _,old=decode(a,range(2,86,2));_,new=decode(b,range(2,86,2));report=json.loads((W/'build_v255.json').read_text());cnt=report['merc_helper_count'];maps=json.loads((W/'build_v253.json').read_text())['maps']
 expected={12:{76,22194},14:{653,689,705},22:{52,53,73,113},30:{39,87}}
 for mid,d in new.items():
  trees(d);assert d.rebuild()==d.raw
  before=[p for p in old[mid].protos if mid!=14 or not 399<=p.idx<409];after=[p for p in d.protos if mid!=14 or not 399<=p.idx<399+cnt]
  if mid==22:after=[p for p in after if not 113<=p.idx<121]
  assert len(before)==len(after);changes={i for i,(p,q)in enumerate(zip(before,after))if p.raw!=q.raw};assert changes==expected.get(mid,set()),(mid,changes)
  for p in d.protos:
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,p.idx,pc)
 # Entire DB skill and damage factories, hit/mana/passive logic are untouched.
 for idx in [6464,18007,18008,5275,5285,5310,5320,5335,5345,5380,729,4090]:assert new[12].protos[idx].raw==old[12].protos[idx].raw
 def export(mid,idx,name,patches=None,params=None,legacy=False):
  d=old[mid]if legacy else new[mid];actual=idx+(cnt if mid==14 and idx>=399 and not legacy else 8 if mid==22 and idx==113 and not legacy else 0)
  (work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),actual,patches,params))
 mp={int(k):v for k,v in maps['14/399'].items()}
 export(14,399,'install',{0:ad('UGET',11,0),1:ad('MOV',12,0),2:jump(2,562,13),mp[567]:ad('RET0',0,1)},1)
 for mid,idx,name in [(14,13,'public_sys'),(14,223,'template_info'),(14,224,'metadata'),(14,449,'request'),(22,72,'attack'),(22,73,'pursue'),(12,18009,'chant'),(12,262,'weapon_update'),(34,3,'use'),(34,4,'place_test'),(34,11,'swap'),(34,16,'take'),(34,18,'place'),(76,1,'ground_new')]:export(mid,idx,name)
 export(76,1,'ground_old',legacy=True)
 export(12,300,'tooltip');export(12,300,'tooltip_old',legacy=True)
 export(12,299,'name_format')
 export(12,142,'suit_config',{0:jump(0,979),1183:ad('MOV',0,2),1184:ad('RET1',0,2)})
 export(14,479,'proxy')
 export(30,193,'table_register',{0:jump(0,33),42:jump(42,57),69:ad('RET0',0,1)})
 export(12,142,'equipment_config',{0:jump(0,1238),1248:ad('RET1',2,2)})
 _,pre=decode((W/'game_v252.res').read_bytes(),[14,34])
 for idx in [3,4,11,16,18]:assert new[34].protos[idx].raw==pre[34].protos[idx].raw
 assert new[14].protos[449+cnt].raw==pre[14].protos[449].raw
 assert new[52].raw==old[52].raw and new[76].raw==old[76].raw
 # All unrelated actor instructions and native FX/damage remain unchanged.
 for idx in [52,53]:
  p,q=old[22].protos[idx],new[22].protos[idx];mp={int(k):v for k,v in report['maps'][f'22/{idx}'].items()}
  for pc,x in enumerate(p.bc):
   at=mp[pc]+(3 if pc==(29 if idx==52 else 399)else 0);y=q.bc[at]
   if OPS[x&255]in BRANCHES:
    assert y&65535==x&65535 and at+1+(y>>16)-32768==mp[pc+1+(x>>16)-32768]
   else:assert x==y,(idx,pc,x,y)
 assert new[46].raw==old[46].raw
 private=new[22].protos[113:121]
 assert private[1].bc==[ad('RET0',0,1)]and private[1].nkgc==0
 for p in private:
  assert '发生伤害'.encode('gbk')not in p.kgc
 for idx in [0,2,3,5,6]:assert private[idx].raw==old[46].protos[idx].raw
 # Root line metadata is repaired from its pristine table; bytecode except
 # the final private factory registration remains exact.
 assert new[22].protos[121].bc[:-3]==old[22].protos[113].bc[:-1]
 export(46,7,'monster_flight')
 (work/'visual_flight.ljbc').write_bytes((W/'merc_flight_native_v255.ljbc').read_bytes())
 export(22,53,'construct_old',legacy=True)
  # No compiled detection, exports or combat-lock text remains.
 forbidden=['__gm_merc_block_v253','__gm_merc_request_v253','佣兵战斗中，无法更换武器']
 for d in new.values():
  for p in d.protos:
   for v in p.kgc:
    if isinstance(v,bytes):assert all(x.encode('gbk')not in v for x in forbidden)
 # Native skill construction, original target selection and delayed damage.
 export(22,53,'skill_construct');export(22,50,'skill_damage')
 export(22,52,'skill_targets',{0:jump(0,int(report['maps']['22/52']['1034']),1),int(report['maps']['22/52']['1290']):ad('RET0',0,1)})
 from patch_v201 import unpack_config
 import configparser
 p=new[12].protos[6464];configs={}
 wanted=['刺客普通攻击','刺客双手攻击','蝉舞','月桂','红莲','白莲','盛开']
 for pc,x in enumerate(p.bc[:-2]):
  if OPS[x&255]!='KSTR'or p.gc(x>>16)not in[k.encode('gbk')for k in wanted]:continue
  y=p.bc[pc+2]
  if OPS[y&255]!='KSTR'or len(p.gc(y>>16))<500:continue
  cfg=configparser.RawConfigParser();cfg.read_string(unpack_config(p.gc(y>>16)).decode('gbk'))
  row={}
  for k,v in cfg['配置'].items():
   if v=='':continue
   try:v=float(v)if'.'in v else int(v)
   except ValueError:v=v.encode('gbk')
   row[k.encode('gbk')]=v
  row['名称'.encode('gbk')]=p.gc(x>>16);row['作用范围'.encode('gbk')]={i:{}for i in range(1,9)};configs[p.gc(x>>16)]=row
 assert len(configs)==7
 (work/'skills.lua').write_bytes(('return '+lua(configs)).encode('gbk'))
 # Native configuration factory is the exact database parser used by skills.
 export(12,4091,'skill_factory')
 export(30,43,'rotate')
 export(16,73,'sprite_factory')
 export(12,729,'item_initializer')
 raw_configs={};encoded={};entries={}
 for pc,x in enumerate(p.bc[:-2]):
  if OPS[x&255]=='KSTR'and p.gc(x>>16)in configs:
   y=p.bc[pc+2]
   if OPS[y&255]=='KSTR'and len(p.gc(y>>16))>500:
    key=p.gc(x>>16);raw_configs[key]=unpack_config(p.gc(y>>16));encoded[p.gc(y>>16)]=raw_configs[key]
 (work/'configs.lua').write_bytes(('return '+lua(raw_configs)).encode('gbk'))
 (work/'encoded_configs.lua').write_bytes(('return '+lua(encoded)).encode('gbk'))
 for key in configs:
  label='【数据库/技能脚本/'.encode('gbk')+key+'】'.encode('gbk')
  at=next(i for i,x in enumerate(p.bc)if OPS[x&255]=='KSTR'and p.gc(x>>16)==label)
  start=max(i for i,x in enumerate(p.bc[:at])if OPS[x&255]=='KSTR'and x>>8&255==4 and p.gc(x>>16)==key)-1
  end=next(i for i in range(at,p.nbc)if p.bc[i]==__import__('patch_v139').abc('CALL',10,1,4))
  name='native_skill_'+str(start);entries[key]=name.encode()
  export(12,6464,name,{4:jump(4,start,10),end+1:ad('RET1',1,2)})
 (work/'skill_entries.lua').write_bytes(('return '+lua(entries)).encode('gbk'))
 # Entry-only weapon binding update exercises original script branch and helper.
 mp={int(k):v for k,v in maps['12/262'].items()}
 export(12,262,'binding_update',{0:ad('MOV',4,0),1:jump(1,mp[68],5),mp[79]:ad('RET0',0,1)},1)
 # Root registration covers original methods, including the preexisting swap guard.
 export(34,31,'slot_class');export(22,113,'actor_class')
 # Audit every native weapon template plus its preceding original extra string.
 p=new[12].protos[4090];extra='';rows=[];items={}
 def cv(v):
  if isinstance(v,bytes):return v
  if isinstance(v,tuple)and v[0]=='int':return v[1]
  return v
 for pc,x in enumerate(p.bc):
  if OPS[x&255]=='KSTR'and x>>8&255==4:extra=p.gc(x>>16).decode('gbk')
  if OPS[x&255]!='TDUP':continue
  t=p.gc(x>>16)
  if not isinstance(t,tuple)or t[0]!='table':continue
  f={k:cv(v)for k,v in t[2]};name=f.get('名称'.encode('gbk'),b'').decode('gbk')
  if f.get('子类'.encode('gbk'))!='武器'.encode('gbk'):continue
  attr={k.encode('gbk'):v.encode('gbk')for k,v in(v.split('ぅ',1)for v in extra.split('ぃ')if 'ぅ'in v)}
  f['附加'.encode('gbk')]=attr;items[name.encode('gbk')]=f
  bind=attr.get('绑定技能'.encode('gbk'));bind=bind.decode('gbk')if bind else None
  rows.append({'id':f[b'id'],'name':name,'class':f['职业要求'.encode('gbk')].decode('gbk'),'explicit_binding':bind,'default_binding':'刺客普通攻击'if bind is None else None,'effective_binding':bind or'刺客普通攻击','mode':'melee'if bind=='刺客双手攻击'else'ranged','name_scope':'all explicit binding labels'if bind=='刺客普通攻击'else'companion inventory/equipment only'if bind is None else'unchanged'})
 assert len(rows)==142 and all(r['effective_binding']in['刺客普通攻击','刺客双手攻击']for r in rows)
 (work/'weapons.lua').write_bytes(('return '+lua(items)).encode('gbk'))
 (work/'merc_weapon_audit_v255.json').write_text(json.dumps({'version':'v1.255','count':len(rows),'weapons':rows},ensure_ascii=False,indent=2)+'\n')
 # All medicine/coin variants and original rarity/outline comparison.
 selected={}
 for x in new[12].protos[4090].bc:
  if OPS[x&255]!='TDUP':continue
  t=new[12].protos[4090].gc(x>>16)
  if not isinstance(t,tuple)or t[0]!='table':continue
  f={k:cv(v)for k,v in t[2]};name=f.get('名称'.encode('gbk'),b'').decode('gbk')
  if name.startswith(('金创药_','魔法药_','Q金创药_','Q魔法药_')):kind='medicine'
  elif name.startswith('金币_'):kind='gold'
  else:continue
  selected[name.encode('gbk')]={k:f[k]for k in[s.encode('gbk')for s in ['名称','显示名','分类','子类','颜色值']]};selected[name.encode('gbk')][b'kind']=kind.encode()
 (work/'ground_templates.lua').write_bytes(('return '+lua(selected)).encode('gbk'))
 src=work/'test.lua';src.write_bytes(((W/'merc_mode_regression_v255.lua').read_text()+(W/'merc_flight_regression_v255.lua').read_text()).encode('gbk'));runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(src),str(work),mode],capture_output=True,timeout=90);out=(r.stdout+r.stderr).decode('gbk','replace');(work/(mode+'.log')).write_text(out);print(out,flush=True);assert r.returncode==0,(mode,out[-5000:]);runs.append({'mode':mode,'output':out})
 names=['patch_v255.py','test_v255.py','package_v255.py','player_changes_v255.json','merc_mode_v255.lua','merc_mode_v255.ljbc','merc_flight_native_v255.ljbc','merc_mode_regression_v255.lua','merc_flight_regression_v255.lua']
 result={'version':'v1.255','all_passed':True,'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'all_42_modules_checked':True,'full_windows_game_run':False,'scope':'native sandbox installation and original class registration; six-cell native AI/Chant and unchanged damage/passive factories; complete native skill DB entry factories, actual Main/stage scripts, full original skill construct/refresh and damage scheduling; private native projectile lifecycle and original sprite wrapper; original hit/body FX request comparison and one-hit timing comparison; optional-art fallback, swaps/moving/dead targets and interruption; complete tooltip/ground regression; finite texture/map/FX sinks and public animation/stat bridge, not full Windows combat/render/save validation','tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v255.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');a=p.parse_args();main(a.runtime or str(ensure_runtime()))
