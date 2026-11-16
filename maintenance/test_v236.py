"""Execute real slot constructor/display and animation wrapper, with finite graphics."""
from test_v225 import *
def main(runtime):
 work=W/'native_work/v236';work.mkdir(parents=True,exist_ok=True)
 _,old=decode((W/'game_v235.res').read_bytes(),range(2,86,2));_,new=decode((W/'game_v236.res').read_bytes(),range(2,86,2))
 build=json.loads((W/'build_v236.json').read_text());expected={int(k):v for k,v in build['changed_prototypes'].items()}
 assert expected=={12:[76,22194],14:[632,668,684],26:[88],30:[39,87],36:[]}
 for mid,d in new.items():
  trees(d)
  for i,p in enumerate(d.protos):
   assert (p.raw!=old[mid].protos[i].raw)==(i in expected.get(mid,[])),(mid,i)
   for pc,x in enumerate(p.bc):
    if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc
 assert old[26].protos[3].bc[4:]==new[26].protos[3].bc[4:],'native update instructions preserved after entry'
 assert old[26].protos[54].raw==new[26].protos[54].raw,'retain229 constructor fix'
 from patch_v201 import unpack_config
 from test_v192 import lua
 import re
 cfg={};p=new[12].protos[6464];name=None;rows=[]
 for x in p.bc:
  if OPS[x&255]=='KSTR':
   a=(x>>8)&255;v=p.gc(x>>16)
   if a==4:name=v
   if a==7 and isinstance(v,bytes)and v.endswith(b'*'):
    cfg[name]=unpack_config(v)
    cd=re.search(rb'^'+ '冷却时间'.encode('gbk')+rb'=(.*)',cfg[name],re.M)
    rows.append({'name':name.decode('gbk'),'base_cd':cd[1].strip().decode()if cd else None})
 assert rows==json.loads((W/'cooldown_audit_v227.json').read_text()),'base CD templates unchanged'
 (work/'configs.lua').write_bytes(('return '+lua(cfg)).encode('gbk'));(work/'scripts.lua').write_bytes(b'return {}')
 for mid,idx,name in [(26,89,'class_new'),(20,8,'animation'),(20,6,'reverse'),(20,21,'reset'),(12,4091,'skill_factory'),(30,43,'rotate'),(36,13,'slot_class'),(16,39,'cd_factory'),(16,73,'sprite_factory'),(14,416,'getter'),(14,13,'readonly')]:
  d=new[mid];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx))
 d=new[26];(work/'tick_new.ljbc').write_bytes(standalone(d,trees(d),3,{0:jump(0,843,3),852:ad('RET0',0,1)}))
 # Execute real rule rows, status insertion/timing, native selector and public lookup.
 for mid,i,n in [(12,46,'selector'),(14,222,'skill_info'),(40,20,'buff_class'),(14,340,'hero_api'),(12,165,'refresh_skills'),(14,221,'skill_set'),(12,126,'role_a'),(12,132,'role_b'),(12,204,'shift')]:
  d=new[mid];(work/f'{n}.ljbc').write_bytes(standalone(d,trees(d),i))
 d=new[12];(work/'shift_registration.ljbc').write_bytes(standalone(d,trees(d),292,{0:jump(0,63,0),66:jump(66,240,0),241:jump(241,301,1),304:jump(304,472,1)}))
 d=new[12];p=d.protos[142];assert OPS[p.bc[2972]&255]=='TNEW'
 (work/'rules.ljbc').write_bytes(standalone(d,trees(d),142,{0:ad('TNEW',1,0),1:jump(1,2972,4),3032:ad('RET1',1,2)}))
 d=new[26];stop=3
 (work/'reset_session.ljbc').write_bytes(standalone(d,trees(d),0,{stop:ad('RET0',0,1)}))
 d=new[26];(work/'buff_tick.ljbc').write_bytes(standalone(d,trees(d),3,{0:jump(0,91,3),145:ad('RET0',0,1)}))
 # Exact status template data; scripts are the real child factories.
 from portal_routes_v213 import child_refs
 from ljtool import Proto
 p=new[12].protos[725];refs=child_refs(new[12]);status={}
 wanted={'烈火剑法','翔空剑法','莲月剑法','烈火剑法CD','翔空剑法CD','莲月剑法CD'}
 for pc,x in enumerate(p.bc):
  if OPS[x&255]!='TDUP':continue
  t=p.gc(x>>16)
  if not isinstance(t,tuple)or t[0]!='table':continue
  fields=dict(t[2]);name=fields.get('标识'.encode('gbk'))
  if name is None or name.decode('gbk')not in wanted:continue
  fields.pop('配置项文本'.encode('gbk'),None);fields['属性'.encode('gbk')]={}
  status[name]=fields
  site=next(j for j in range(pc,pc+15)if OPS[p.bc[j]&255]=='FNEW')
  idx=refs[725,p.bc[site]>>16]
  (work/('status_'+name.hex()+'.ljbc')).write_bytes(standalone(new[12],trees(new[12]),idx))
 assert len(status)==6
 (work/'statuses.lua').write_bytes(('return '+lua(status)).encode('gbk'))
 d=new[26];(work/'repeat_head.ljbc').write_bytes(standalone(d,trees(d),3,{4:ad('RET0',0,1)}))
 d=new[26];(work/'repeat_reset.ljbc').write_bytes(standalone(d,trees(d),0,{3:ad('RET0',0,1)}))
 d=new[14];(work/'map_cleanup.ljbc').write_bytes(standalone(d,trees(d),391))
 _,legacy=decode((W/'game_v229.res').read_bytes(),[26]);d=legacy[26];(work/'repeat_legacy.ljbc').write_bytes(standalone(d,trees(d),88))
 d=new[14];(work/'input_focus.ljbc').write_bytes(standalone(d,trees(d),385,{0:jump(0,19,34),22:jump(22,336,34),426:ad('RET0',0,1)}))
 for mid,i,name in [(48,44,'window_class'),(14,684,'installer'),(14,381,'dispatch')]:
  d=new[mid];(work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),i))
 d=new[12];(work/'parent_setup.ljbc').write_bytes(standalone(d,trees(d),142,{0:jump(0,355,0),364:ad('RET0',0,1)}))
 _,old231=decode((W/'game_v231.res').read_bytes(),[26]);d=old231[26];(work/'repeat231.ljbc').write_bytes(standalone(d,trees(d),88))
 d=old[26];(work/'repeat235.ljbc').write_bytes(standalone(d,trees(d),88))
 _,old232=decode((W/'game_v232.res').read_bytes(),[26]);d=old232[26];(work/'repeat232.ljbc').write_bytes(standalone(d,trees(d),88))
 d=new[12];(work/'cast_recovery.ljbc').write_bytes(standalone(d,trees(d),45))
 d=new[26];(work/'stiff_tick.ljbc').write_bytes(standalone(d,trees(d),3,{0:jump(0,145,3),159:ad('RET0',0,1),163:ad('RET0',0,1)}))
 _,v230=decode((W/'game_v230.res').read_bytes(),[26]);d=v230[26];(work/'repeat230.ljbc').write_bytes(standalone(d,trees(d),88))
 # Assert constructor inputs against the real UI factory, rather than invent visibility.
 p=new[12].protos[22194]
 for at,values in [(1653,[539,'背包窗口',657,22,282,484,1,0,0,0]),(1712,[540,'背包格子',0,0,243,625,1,0,0,0])]:
  for j,value in enumerate(values):
   x=p.bc[at+j];assert ((x>>8)&255)==j
   assert (p.gc(x>>16).decode('gbk') if isinstance(value,str) else (x>>16))==value
 (work/'repeat_diagnostics.lua').write_bytes((W/'repeat_diagnostics_v235.lua').read_text().encode('gbk'))
 prefix=(W/'melee_regression_v210.lua').read_text().split("local melee={'普通攻击'")[0]
 charge=(W/'combat_regression_v218.lua').read_text();charge=charge[charge.index("local charged="):charge.index('\n\n-- Shared skill')]
 (work/'test.lua').write_bytes(("io.stdout:setvbuf('no')\n"+prefix+charge+(W/'cooldown_regression_v227.lua').read_text()+(W/'cooldown_regression_v228.lua').read_text()+(W/'repeat_regression_v236.lua').read_text()).encode('gbk'))
 runs=[]
 d=old[14];(work/'installer_old.ljbc').write_bytes(standalone(d,trees(d),684))
 d=new[14];(work/'installer_new.ljbc').write_bytes(standalone(d,trees(d),684))
 (work/'logger_test.lua').write_bytes((W/'repeat_log_regression_v231.lua').read_text().encode('gbk'))
 for mode in ['normal','hot']:
  r=subprocess.run([runtime,str(work/'test.lua'),str(work),mode],capture_output=True,timeout=90);out=(r.stdout+r.stderr).decode('gbk','replace');assert r.returncode==0,out;print(out);runs.append(out)
  q=subprocess.run([runtime,str(work/'logger_test.lua'),str(work),mode],capture_output=True,timeout=90);out=(q.stdout+q.stderr).decode('gbk','replace');assert q.returncode==0,out;print(out);runs.append(out)
 names=['repeat_log_regression_v231.lua','patch_v236.py','test_v236.py','cooldown_regression_v227.lua','package_v236.py','player_changes_v236.json','cooldown_mask_v228.lua','cooldown_mask_v228.ljbc','cooldown_audit_v227.json','cooldown_regression_v228.lua','combat_regression_v218.lua','cooldown_regression_v228.lua','repeat_skill_v236.lua','repeat_skill_v236.ljbc','repeat_border_v231.lua','repeat_border_v231.ljbc','diagnostics_v231.lua','diagnostics_v231.ljbc','repeat_diagnostics_v235.lua','repeat_regression_v236.lua']
 result={'focus_loss_preserves_mode':True,'foreign_input_and_return_edges_ignored':True,'background_native_release_checked':True,'alt_tab_foreground_transition_checked':True,'diagnostic_only':False,'manual_probe_budget_per_30_seconds':12,'native_cast_recovery_negative_control':True,'stiffness_fragment_jit':False,'stiffness_fragment_hot_limitation':'Hot intermittently exited -11, including after interpreting the truncated countdown. Native update entry changed from high R20 call across uninitialized slots to contiguous R1/R2; subsequent five hot checks passed. Countdown fragment remains interpreted, complete helper/callback integration hot. Limited verification, not full native frame/Windows JIT testing.','native_hidden_parent_negative_control':True,'complete_native_diagnostic_installer':True,'log_budget_per_hero':240,'unrelated_ordinary_trace_performance_compared':True,'version':'v1.236','all_passed':True,'sha256':build['sha256'],'runs':runs,'all_42_modules_checked':True,'full_windows_game_run':False,'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
 (W/'validation_v236.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');a=p.parse_args();main(a.runtime or str(ensure_runtime()))
