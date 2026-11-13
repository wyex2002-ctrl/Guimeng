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
-- The actual complete native installer (legacy plus detail layers), not a
-- hand-written replacement logger. Validate argument/return counts and identity.
for _,version in ipairs({'old','new'})do
 for _,failure in ipairs({false,true})do
  local s=make(version,failure);local S=s.S
  for i=1,1100 do
   local r=pack(S.run('echo',i,nil,false,nil));eq(r.n,6);eq(r[1],nil);eq(r[2],4);eq(r[3],i);eq(r[4],nil);eq(r[5],false);eq(r[6],nil)
  end
  local ok,err=pcall(S.run,'failure');eq(ok,false);eq(err,s.E)
  if not failure then
   eq(s.files['Log/guimeng_critical_latest.txt']:find('script.run.error',1,true)~=nil,true)
   eq(s.files['Log/guimeng_critical_latest.txt']:find('stack traceback',1,true)~=nil,true)
  end
 end
end
-- All dispatches stay in memory; routine writes are batched. A real error/exit
-- checkpoint flushes pending context immediately, even before a batch is full.
local trace={}
for _,version in ipairs({'old','new'})do
 local s=make(version);local S=s.S;S.__gm_diag_checkpoint_v159('load.return')
 local before=s.stats()
 for i=1,15 do S.__gm_diag_checkpoint_v159('script.dispatch','pending-'..i)end
 -- Direct checkpoints do not increment the dispatch wrapper's shared budget;
 -- exercise the actual wrapped native dispatcher for the real batch boundary.
 local f=function(x)return x,nil,false end;S.shelp[tostring(f)]={sid=13,msg='perf dispatch'}
 for i=1,320 do local r=pack(S.fun(f,{i},-1));eq(r[1],true);eq(r[2],i);eq(r[3],nil);eq(r[4],false)end
 local after=s.stats();trace[version]=after-before
 S.__gm_diag_checkpoint_v159('load.return')
 for i=1,3 do S.fun(f,{i},-1)end
 S['错误提示']('original failure')
 local log=s.files['Log/guimeng_error_latest.txt'];eq(type(log),'string')
 eq(log:find('script.dispatch',1,true)~=nil,true);eq(log:find('perf dispatch',1,true)~=nil,true)
 local run=s.files['Log/guimeng_run_latest.txt'];eq(run:find('error.format',1,true)~=nil,true)
 -- Exit logger must flush the pending trace before writing its error report.
 S.__gm_diag_exit_v164(true);eq(s.files['Log/guimeng_critical_latest.txt']:find('exit.requested',1,true)~=nil,true)
end
eq(trace.new<trace.old/8,true,'dispatch write reduction')
print('TRACE_WRITES',mode,trace.old,trace.new)
-- Allocation measurement is deterministic enough for a regression gate. CPU
-- timing is evidence only: a shared CI host cannot establish Windows FPS.
local perf={}
for _,version in ipairs({'old','new'})do
 local s=make(version);for i=1,5000 do s.S.run('hot',i)end
 collectgarbage();local memory=collectgarbage('count');local start=os.clock();collectgarbage('stop')
 local sink=0
 for i=1,50000 do local a,b,c,d,e,f,g,h,j=s.S.run('hot',i);sink=sink+c+h end
 local elapsed=os.clock()-start;local allocated=collectgarbage('count')-memory;collectgarbage('restart')
 eq(sink,350000);perf[version]={seconds=elapsed,kib=allocated}
 print('PERF',mode,version,elapsed,allocated)
end
eq(perf.new.kib<perf.old.kib/3,true,'temporary allocation reduction')
print('PERFORMANCE_PASS',mode,count)
