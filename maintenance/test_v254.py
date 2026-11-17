from test_v225 import *
from patch_v254 import BASE_SHA
from test_v192 import lua

def main(runtime):
 work=W/'native_work/v254';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v253.res').read_bytes();b=(W/'game_v254.res').read_bytes();assert hashlib.sha256(a).hexdigest()==BASE_SHA
 _,old=decode(a,range(2,86,2));_,new=decode(b,range(2,86,2));report=json.loads((W/'build_v254.json').read_text());cnt=report['merc_helper_count'];maps=json.loads((W/'build_v253.json').read_text())['maps']
 expected={12:{76,300,22194},14:{449,653,689,705},30:{39,87},34:{3,4,11,16,18}}
 for mid,d in new.items():
  trees(d);assert d.rebuild()==d.raw
  before=[p for p in old[mid].protos if mid!=14 or not 399<=p.idx<414];after=[p for p in d.protos if mid!=14 or not 399<=p.idx<399+cnt]
  assert len(before)==len(after);changes={i for i,(p,q)in enumerate(zip(before,after))if p.raw!=q.raw};assert changes==expected.get(mid,set()),(mid,changes)
  for p in d.protos:
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,p.idx,pc)
 # Entire DB skill and damage factories, hit/mana/passive logic are untouched.
 for idx in [6464,18007,18008,5275,5285,5310,5320,5335,5345,5380,729,4090]:assert new[12].protos[idx].raw==old[12].protos[idx].raw
 def export(mid,idx,name,patches=None,params=None,legacy=False):
  d=old[mid]if legacy else new[mid];actual=idx+(cnt if mid==14 and idx>=399 and not legacy else 0)
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
 # Original tooltip instructions, branch A/live boundary and numeric/debug pool.
 p,q=old[12].protos[300],new[12].protos[300];mp={int(k):v for k,v in report['tooltip_map'].items()}
 from bytecode_relocate import numeric_and_debug
 from bytecode_relocate import relocated_debug
 owners=[pc for pc in range(p.nbc)for _ in range(mp[pc+1]-mp[pc])]
 assert numeric_and_debug(p)[0]==numeric_and_debug(q)[0] and p.uv==q.uv
 assert relocated_debug(p,mp,owners)==numeric_and_debug(q)
 assert q.kgc[-p.nkgc:]==p.kgc
 for pc,x in enumerate(p.bc):
  y=q.bc[mp[pc]]
  if OPS[x&255]in BRANCHES:
   assert y&65535==x&65535
   assert mp[pc]+1+(y>>16)-32768==mp[pc+1+(x>>16)-32768]
  else:assert x==y,(pc,x,y)
 assert {pc for pc in range(p.nbc)if (mp.get(pc+1,q.nbc)-mp[pc])!=1}=={524,536}
 # No compiled detection, exports or combat-lock text remains.
 forbidden=['__gm_merc_block_v253','__gm_merc_request_v253','佣兵战斗中，无法更换武器']
 for d in new.values():
  for p in d.protos:
   for v in p.kgc:
    if isinstance(v,bytes):assert all(x.encode('gbk')not in v for x in forbidden)
 # Native skill construction, original target selection and delayed damage.
 export(22,53,'skill_construct');export(22,50,'skill_damage')
 export(22,52,'skill_targets',{0:jump(0,1034,1),1290:ad('RET0',0,1)})
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
 (work/'merc_weapon_audit_v254.json').write_text(json.dumps({'version':'v1.254','count':len(rows),'weapons':rows},ensure_ascii=False,indent=2)+'\n')
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
 src=work/'test.lua';src.write_bytes((W/'merc_mode_regression_v254.lua').read_text().encode('gbk'));runs=[]
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(src),str(work),mode],capture_output=True,timeout=90);out=(r.stdout+r.stderr).decode('gbk','replace');(work/(mode+'.log')).write_text(out);print(out,flush=True);assert r.returncode==0,(mode,out[-5000:]);runs.append({'mode':mode,'output':out})
 names=['patch_v254.py','test_v254.py','package_v254.py','player_changes_v254.json','merc_mode_v254.lua','merc_mode_v254.ljbc','merc_mode_regression_v254.lua']
 result={'version':'v1.254','all_passed':True,'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'all_42_modules_checked':True,'full_windows_game_run':False,'scope':'native sandbox install, native class registration, restored pre-v253 UI mutation entrances, complete tooltip title and rich-text comparison, full AI attack/pursuit and Chant callback with finite engine/map/actor/graphics; metadata and full ground constructor; weapon DB field audit; unchanged skill/damage factories byte-for-byte; no full Windows client/save/load run','tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v254.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');a=p.parse_args();main(a.runtime or str(ensure_runtime()))
