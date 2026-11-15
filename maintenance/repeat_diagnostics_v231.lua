-- Full native14/684 installer and381 dispatcher; finite in-memory disk primitives.
local work=assert(arg[1])
return function(S)
 local files,writes={},0
 local env=setmetatable({核心={读入文件=function(p)return files[p]end,写到文件=function(p,s)
  writes=writes+1;files[p]=s;return true
 end}},{__index=_G})
 local function native(name,e)local f=assert(loadfile(work..'/'..name..'.ljbc'));setfenv(f,e or env);return f end
 S.Game_State=1;S.sid=10;S.shelp={};S.save_info={};S.错误提示=function(e)return e end
 S.script_setting={Gly独={错误=function(e)return S.错误提示(e)end}}
 local dispatcher=native('dispatch',_G);debug.setupvalue(dispatcher,1,S);S.fun=dispatcher
 native('installer')(S)
 local function present(tag,run)
  for _,path in ipairs(run and {'Log/guimeng_run_latest.txt','Log/guimeng_detail_latest.txt','Log/guimeng_critical_latest.txt'} or {'Log/guimeng_critical_latest.txt'})do
   if not (files[path] and files[path]:find(tag,1,true)) then local f=assert(io.open(work..'/missing_log.txt','wb'));f:write(files[path]or'<nil>');f:close();error(path..' missing '..tag)end
  end
 end
 return {check=function(hero,e,head,fire,arm,key,pump,active)
  -- Recreate a clean session; diagnostics must survive the same real read-only getter.
  key(112,false);native('repeat_reset',e)(hero);pump(2)
  assert(type(e.Sys.get('__gm_diag_checkpoint_v159'))=='function')
  assert(not pcall(function()e.Sys.__gm_diag_checkpoint_v159=false end),'public Sys remains readonly')
  present('repeat.ready',true)
  arm();present('repeat.start',true);fire.显示(fire,nil,nil,0,0);present('repeat.border.draw',true);pump(200)
  key(112,true);pump(1);assert(not active());key(112,false);pump(2)
  for _,tag in ipairs({'repeat.ready','repeat.key','repeat.hold','repeat.start','repeat.cast','repeat.border.probe','repeat.border.draw','repeat.stop'})do present(tag)end
  assert(files['Log/guimeng_critical_latest.txt']:find('reason=skill_key',1,true))
  assert(files['Log/guimeng_critical_latest.txt']:find('ignored_hidden_children=1',1,true))
  arm();e.Ae冻集.游戏暂停=true;head(hero);assert(not active());e.Ae冻集.游戏暂停=false
  assert(files['Log/guimeng_critical_latest.txt']:find('reason=paused',1,true))
  -- Logger errors cannot change the input state machine; no engine method is replaced.
  local st=hero.__gm_repeat_skill_v229;local logger=st.logger
  st.logger=function()error('diagnostic disk failure')end
  key(112,false);pump(2);arm();assert(active());st.logger=logger
  -- Missing diagnostic callback is also supported, and recovers on a low-frequency pulse.
  st.logger=nil;key(112,true);pump(1);assert(not active());key(112,false);pump(2);arm();assert(active())
  pump(501);assert(st.logger==logger,'resolve existing logger again')
  -- Consume the per-instance cap and verify no writes after it. Ordinary rendering
  -- and idle updates do not create logs per frame; repeat requests are sampled.
  for i=1,400 do hero:__gm_repeat_control_v229('log','test.bound','sample='..i)end
  assert(st.log_left==0);key(1,true);head(hero);local before=writes
  for i=1,200 do head(hero);fire.显示(fire,nil,nil,0,0)end
  assert(writes==before,'exhausted budget writes no more records');key(1,false)
  key(112,true);head(hero);assert(not active(),'budget exhaustion does not break cancel')
  -- Shared diagnostics preserve nil/false/trailing nil and original error identity.
  local f=function(a,b,c)return a,b,c,nil end;S.shelp[tostring(f)]={sid=12,msg='repeat diagnostic ABI'}
  local function pack(...)return{n=select('#',...),...}end
  for i=1,200 do local v=pack(S.fun(f,{i,false,'ok'},-1));assert(v.n==11 and v[1]==true and v[2]==i and v[3]==false and v[4]=='ok' and v[5]==nil)end
  local v=pack(S.run('fun',f,{7,false,'ok'}));assert(v.n==5 and v[1]==true and v[2]==7 and v[3]==false and v[4]=='ok' and v[5]==nil)
  local error_object={};local ok,err=pcall(S.run,'fun',function()error(error_object)end,{})
  assert(not ok and err==error_object,'original callback error identity')
  S.错误提示('repeat regression error');assert(files['Log/guimeng_error_latest.txt']:find('repeat regression error',1,true))
  print('REPEAT_DIAGNOSTICS_V231_PASS native complete installer/read-only getter, three log streams, reason/hold/render, cap/failure/missing callback, callback ABI/error')
 end}
end
