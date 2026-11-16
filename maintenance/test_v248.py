from test_v225 import *
from patch_v248 import span
from patch_v201 import unpack_config

def main(runtime):
 work=W/'native_work/v248';work.mkdir(parents=True,exist_ok=True)
 a=(W/'game_v247.res').read_bytes();b=(W/'game_v248.res').read_bytes();_,old=decode(a,range(2,86,2));_,new=decode(b,range(2,86,2));current=json.loads((W/'build_v248.json').read_text());report=json.loads((W/'build_v244.json').read_text());count=current['helper_count']
 expected={12:{76,18008,22194},14:{653,689,705},30:{39,87}}
 for mid,d in new.items():
  trees(d);assert d.rebuild()==d.raw
  if mid==14:
   before=[p for p in old[mid].protos if not 378<=p.idx<399];after=[p for p in d.protos if not 378<=p.idx<378+count]
  else:before=old[mid].protos;after=d.protos
  assert len(before)==len(after);changes={p.idx for p,q in zip(before,after)if p.raw!=q.raw};assert changes==expected.get(mid,set()),(mid,changes)
  for p in d.protos:
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,p.idx,pc)
 p,q=old[12].protos[37],new[12].protos[37];assert q.bc[1:p.nbc]==p.bc[1:] and(p.params,p.frame,p.uv)==(q.params,q.frame,q.uv)
 for i in range(p.nkgc):assert p.gc(i)==q.gc(i)
 assert [p.raw for p in new[14].protos[378:399]]==[p.raw for p in old[14].protos[378:399]],'luck helper unchanged'
 for mid in [22,26,34,36,40,52]:assert new[mid].raw==old[mid].raw
 def export(mid,idx,name,patches=None,params=None):
  d=new[mid];actual=idx+(count if mid==14 and idx>=378 else 1 if mid==52 and idx>=3 else 0)
  (work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),actual,patches,params))
 for mid,idx,name in [(14,458,'proxy'),(14,13,'public_sys'),(14,224,'metadata'),(14,223,'template_info'),(14,340,'hero_api'),(12,4089,'oil_template'),(34,3,'inventory_use'),(34,22,'consume'),(14,377,'stat'),(52,3,'font')]:export(mid,idx,name)
 export(14,408,'quantity');export(14,220,'actor_api');export(14,397,'use_by_name');export(14,340,'hero_api')
 export(12,37,'item_event');export(34,1,'inventory_init');export(34,31,'inventory_class');export(48,25,'add_control');export(48,23,'bind_control');export(14,416,'public_get')
 export(14,685,'oil_reset')
 export(22,37,'merc_gear_sum',{0:ad('MOV',4,1),1:ad('MOV',5,2),2:jump(2,385,6),551:ad('RET1',4,2)},3)
 # Original mercenary merged attack span, preserving real own skill config.
 mp={int(k):v for k,v in json.loads((W/'build_v245.json').read_text())['merc_map'].items()};relocate={int(k):v for k,v in current['merc_defaults_map'].items()};mp={k:relocate[v]for k,v in mp.items()}
 export(12,18008,'merc_luck',{0:ad('MOV',8,0),1:ad('MOV',9,1),2:ad('MOV',6,2),3:ad('KSHORT',11,2),4:ad('KSHORT',12,4),5:jump(5,mp[417],21),mp[437]:ad('MOV',0,15),mp[437]+1:ad('MOV',1,13),mp[437]+2:ad('RET',0,3)},3)
 export(30,193,'table_register',{0:jump(0,33),42:jump(42,57),69:ad('RET0',0,1)})
 # Original gear aggregation loop, with a supplied initialized stat accumulator.
 export(26,38,'gear_sum',{0:ad('MOV',3,1),1:jump(1,371,4),537:ad('RET1',3,2)})
 # Exact installer insertion, retaining native S.script_setting assignment.
 mp={int(k):v for k,v in report['install_map'].items()};entry=mp[562]
 export(14,378,'install',{0:ad('UGET',11,0),1:ad('MOV',12,0),2:jump(2,entry,13),mp[563]:ad('RET0',0,1)},1)
 # Hero complete merged luck span with actual configured bounds/skill locals.
 mp={int(k):v for k,v in report['maps']['hero_attack'].items()}
 export(12,278,'hero_luck',{0:ad('MOV',8,0),1:ad('MOV',9,1),2:ad('MOV',6,2),3:ad('MOV',4,3),4:ad('KSHORT',11,2),5:ad('KSHORT',12,4),6:jump(6,mp[300],22),mp[347]:ad('MOV',0,15),mp[347]+1:ad('MOV',1,13),mp[347]+2:ad('RET',0,3)},4)
 (work/'callbacks.lua').write_text('return {'+','.join(map(str,report['generic_callbacks']))+'}')
 for idx in report['generic_callbacks']:export(12,idx,'creature'+str(idx))
 _,original=decode((W/'game_v243.res').read_bytes(),[12]);d=original[12];(work/'creature_old.ljbc').write_bytes(standalone(d,trees(d),10298))
 # Execute actual required-level branches plus the relocated luck call.
 mp={int(k):v for k,v in json.loads((W/'build_v246.json').read_text())['compact_map'].items()}
 export(12,296,'compact_tip',{0:ad('KSTR',3,0),1:jump(1,mp[798],4),mp[819]+8:ad('RET1',3,2)},2)
 export(12,296,'compact_early',{0:ad('KSTR',3,0),1:ad('MOV',4,1),2:jump(2,mp[203],5),mp[231]:ad('RET',3,3)},2)
 mp={int(k):v for k,v in json.loads((W/'build_v246.json').read_text())['detail_map'].items()}
 export(12,300,'detail_tip',{0:ad('KSTR',3,0),1:ad('MOV',4,1),2:jump(2,mp[783],6),mp[803]+8:ad('RET1',3,2)},2)
 export(12,100,'chat_message');export(12,304,'screen_message');export(52,7,'rich_register')
 export(12,179,'entry_windows',{0:jump(0,498,5),507:ad('RET0',0,1)})
 export(12,187,'chat_toggle',{0:jump(0,307,2),310:ad('RET0',0,1)})
 # Existing real skill configuration; no luck values edited in the DB.
 cfg=unpack_config(new[12].protos[6464].gc(3));(work/'skill_config.txt').write_bytes(cfg)
 # Execute the complete real mercenary callback with native public stats.
 export(12,18008,'native_merc');export(14,90,'native_random')
 d=old[12];(work/'native_merc_old.ljbc').write_bytes(standalone(d,trees(d),18008))
 p,q=old[12].protos[18008],new[12].protos[18008];mp={int(k):v for k,v in current['merc_defaults_map'].items()}
 for pc,x in enumerate(p.bc):
  at=mp[pc]+(2 if pc==385 else 0);y=q.bc[at]
  if OPS[x&255]in BRANCHES:assert x&65535==y&65535 and mp[pc+1+(x>>16)-32768]==at+1+(y>>16)-32768,pc
  else:assert x==y,pc
 assert q.bc[mp[385]:mp[385]+2]==[ad('KSHORT',11,0),ad('KSHORT',12,0)]
 runs=[]
 for suite in ['luck']:
  for mode in ['normal','hot']:
   src=work/('test.lua'if suite=='luck'else'combat.lua')
   if suite=='luck':
    code=(W/'luck_regression_v248.lua').read_text().replace('-- MERC_REGRESSION', (W/'merc_regression_v248.lua').read_text())
    src.write_bytes(code.encode('gbk'))
   r=subprocess.run([runtime,str(src),str(work),mode],capture_output=True,timeout=90);out=(r.stdout+r.stderr).decode('gbk','replace');(work/(suite+'.'+mode+'.log')).write_text(out)
   assert r.returncode==0,(suite,mode,out[-6000:]);print(out,flush=True);runs.append({'suite':suite,'mode':mode,'output':out})
 names=['patch_v248.py','test_v248.py','package_v248.py','player_changes_v248.json','luck_system_v247.lua','luck_system_v247.ljbc','luck_rules_v246.lua','luck_regression_v248.lua','merc_regression_v248.lua']
 result={'version':'v1.248','all_passed':True,'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'all_42_modules_checked':True,'creature_callbacks':247,'full_windows_game_run':False,'scope':'complete native mercenary attack callback, original public actor stats, real native random wrapper and installed luck helper; finite engine integer bridge (permissive only for old negative control); original instructions/relocations preserved, 26 unchanged from 247; native level/luck tooltip fragments, native rich formatter/layout (finite glyph metrics), native chat and transient hint, native entry window and manual info switch fragments; equipment zero and 1..7 boundaries, skill/guild independent luck; actual source-aware oil Main/native inventory consume, native hero/merc gear loops and public actor attributes; own-luck ownership, complete creature callbacks, actual merc attack span; native quickslot event->use by name->inventory chain with finite graphics/pre-use engine bridge; field roundtrip only','tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v248.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');a=p.parse_args();main(a.runtime or str(ensure_runtime()))
