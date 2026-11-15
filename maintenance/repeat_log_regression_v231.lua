local work,mode=assert(arg[1]),arg[2] or 'normal'
if mode=='hot' then require('jit.opt').start('hotloop=1','hotexit=1')end
local count=0
local function eq(a,b,msg)count=count+1;assert(a==b,(msg or 'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function pack(...)return {n=select('#',...),...}end
local function load(name,env)local f=assert(loadfile(work..'/'..name..'.ljbc'));setfenv(f,env);return f end
local function make(version,disk_failure)
 local writes,bytes,native_calls=0,0,0
 local files={};local S={Game_State=1,sid=10,shelp={},save_info={}}
 local E={tag='original error'}
 local env=setmetatable({['核心']={['读入文件']=function(p)return files[p]end,['写到文件']=function(p,s)
  writes=writes+1;bytes=bytes+#s;if disk_failure then error('disk unavailable')end;files[p]=s;return true
 end}}, {__index=_G})
 S['错误提示']=function(e)return e end
 S.script_setting={['Gly独']={['错误']=function(e)return S['错误提示'](e)end}}
 local dispatcher=load('dispatch',_G);debug.setupvalue(dispatcher,1,S);S.fun=dispatcher
 S.run=function(action,...)
  native_calls=native_calls+1
  if action=='failure' then error(E)end
  if action=='fun' then return S.fun(...)end
  if action=='hot' then return nil,false,1,2,3,4,5,6,nil end
  return nil,select('#',...),...
 end
 local f=load('installer_'..version,env);f(S)
 return {S=S,files=files,E=E,stats=function()return writes,bytes,native_calls end}
end

local baseline={}
for _,version in ipairs({'old','new'})do
 for _,failure in ipairs({false,true})do
  local s=make(version,failure);local S=s.S
  for i=1,200 do
   local r=pack(S.run('echo',i,nil,false,nil))
   eq(r.n,6);eq(r[1],nil);eq(r[2],4);eq(r[3],i);eq(r[4],nil);eq(r[5],false);eq(r[6],nil)
  end
  local ok,err=pcall(S.run,'failure');eq(ok,false);eq(err,s.E)
  if not failure then
   eq(s.files['Log/guimeng_critical_latest.txt']:find('script.run.error',1,true)~=nil,true)
   eq(s.files['Log/guimeng_critical_latest.txt']:find('stack traceback',1,true)~=nil,true)
   S.__gm_diag_exit_v164(true)
   eq(s.files['Log/guimeng_critical_latest.txt']:find('exit.requested',1,true)~=nil,true)
  end
 end
 local s=make(version);for i=1,200 do s.S.run('hot',i)end
 collectgarbage();local memory=collectgarbage('count');collectgarbage('stop');local before=s.stats()
 for i=1,200 do
  local r=pack(s.S.run('hot',i));eq(r.n,9);eq(r[1],nil);eq(r[2],false);eq(r[9],nil)
  s.S.__gm_diag_checkpoint_v159('skill.hero.enter','ordinary sample')
 end
 local allocated=collectgarbage('count')-memory;collectgarbage('restart')
 baseline[version]={writes=s.stats()-before,kib=allocated}
end
eq(baseline.old.writes,baseline.new.writes,'unrelated trace disk writes unchanged')
eq(baseline.new.kib<=baseline.old.kib+16,true,'no material ordinary trace allocation increase')
print('REPEAT_LOG_ABI_PERF_V231_PASS',mode,'old/new ordinary writes',baseline.old.writes,baseline.new.writes,'KiB',baseline.old.kib,baseline.new.kib)
