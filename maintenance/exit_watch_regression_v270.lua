local work,mode=arg[1],arg[2]
if mode=='normal'then jit.off()else jit.opt.start('hotloop=1','hotexit=1')end
local checks=0
local function eq(a,b,msg)checks=checks+1;assert(a==b,(msg or'check')..' '..tostring(a)..' ~= '..tostring(b))end
local function pack(...)return{n=select('#',...),...}end
local function same(a,b)eq(a.n,b.n);for i=1,a.n do eq(a[i],b[i])end end
local function load(n,e)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,e);return f end
local files,writes={},0;local args,fail;local sentinel={original='exit error'}
local e=setmetatable({dt=0,os={date=os.date,time=os.time,clock=os.clock},核心={
 读入文件=function(p)return files[p]end,
 写到文件=function(p,s)files[p]=s;writes=writes+1 end}},{__index=_G})
local function original(...)
 args=pack(...)
 assert(files['Log/guimeng_exit_latest.txt']:find('exit.enter',1,true),'write before actual exit')
 if fail then error(sentinel,0)end
 return false,nil,'original',nil
end
e.os.exit=original;files['Log/guimeng_exit_latest.txt']='prior session'
local s={Game_State=1,sid=1338,__gm_native_watch_v268={frame=683,phase='hero_update'}}
local install=load('exit_watch',e);install(s)
eq(files['Log/guimeng_exit_previous.txt'],'prior session')
assert(files['Log/guimeng_exit_latest.txt']:find('stage=installed',1,true))
local wrapper=e.os.exit;assert(wrapper~=original);local before=writes
install(s);eq(e.os.exit,wrapper);eq(writes,before,'idempotent installation')
local object={};same(pack(e.os.exit(object,false,nil)),{n=4,false,nil,'original',nil});same(args,{n=3,object,false,nil})
local text=files['Log/guimeng_exit_latest.txt'];assert(text:find('argc=3',1,true));assert(text:find('arg2=false',1,true));assert(text:find('arg3=nil',1,true));assert(text:find('frame=683',1,true));assert(text:find('hero_update',1,true));assert(text:find('stack traceback:',1,true))
fail=true;local ok,err=pcall(e.os.exit);eq(ok,false);eq(err,sentinel);fail=false
-- Rebinding a freshly constructed Sys updates context, without nested wrappers.
local second={sid=42};install(second);eq(e.os.exit,wrapper);e.os.exit();assert(files['Log/guimeng_exit_latest.txt']:find('sid=42',1,true))
-- Writer failure must not suppress, duplicate, or replace the original call.
e.核心.写到文件=function()error('disk unavailable')end
same(pack(e.os.exit(false,nil)),{n=4,false,nil,'original',nil});same(args,{n=2,false,nil})
fail=true;ok,err=pcall(e.os.exit);eq(ok,false);eq(err,sentinel);fail=false
e.核心.写到文件=function(p,t)files[p]=t;writes=writes+1 end
for i=1,200 do same(pack(e.os.exit(i,nil)),{n=4,false,nil,'original',nil})end
assert(#files['Log/guimeng_exit_latest.txt']<20000,'bounded overwrite rather than append')
local nofile=setmetatable({核心=false,os={exit=original}},{__index=_G});load('exit_watch',nofile)({});eq(nofile.os.exit,original)

-- Actual original os.exit wrapper, original Gly quit function, original normal
-- save-and-quit callback, and the early native error callback share this OS table.
local requested=0;local raw=load('os_exit',e)
debug.setupvalue(raw,1,function()requested=requested+1 end)
local core_calls=0;e.核心.exit=function()
 core_calls=core_calls+1;assert(files['Log/guimeng_exit_latest.txt']:find('exit.enter',1,true));error(sentinel,0)
end
e.__SysType=1;e.os.exit=raw;e.os.__gm_exit_watch_v270=nil
local diag_calls=0;local sys={Game_State=1,__gm_diag_exit_v164=function()diag_calls=diag_calls+1 end}
install(sys)
e.Ae冻集={};local quit=load('native_quit',e);debug.setupvalue(quit,1,sys)
quit(false);eq(diag_calls,1);eq(core_calls,0);eq(e.Ae冻集.逻辑结束,true)
e.Gly独={结束游戏=quit};local saved=0;local qu=load('save_quit',e)
e.Ux雌={人物选择=2};debug.setupvalue(qu,1,{存档读档=function(cmd,slot,unused,kind)eq(cmd,'存档');eq(slot,2);eq(unused,nil);eq(kind,0);saved=saved+1 end})
ok,err=pcall(qu);eq(ok,false);eq(err,sentinel);eq(saved,1);eq(core_calls,1);eq(requested,0)
assert(files['Log/guimeng_exit_latest.txt']:find('stack traceback:',1,true))
local native_error=load('native_error',e);ok,err=pcall(native_error,'engine failure',false,nil);eq(ok,false);eq(err,sentinel);eq(core_calls,2)
-- Non-native platform branch still invokes the captured old exit exactly once.
e.__SysType=0;raw();eq(requested,1);eq(core_calls,2)

-- The current constructor registers both watches before read-only public export.
e.__SysType=1
local ctor=load('constructor',e);debug.setupvalue(ctor,5,load('readonly',e))
local runs=0;local exports={Game_State=0,run=function()runs=runs+1;return false,nil end,get=function()end,add=function()end}
local public=ctor(exports);assert(exports.__gm_exit_watch_v270);assert(exports.__gm_native_watch_v268)
same(pack(public.run()),{n=2,false,nil});eq(runs,1);eq(public.__gm_exit_watch_v270,nil)
-- Exit instrumentation adds no frame/callback wrapper, allocations or writes.
local function allocation_case(with_exit)
 local fs,wn={},0
 local env=setmetatable({dt=0,os={date=os.date,time=os.time,clock=os.clock,exit=function()end},核心={读入文件=function(p)return fs[p]end,写到文件=function(p,t)fs[p]=t;wn=wn+1 end}},{__index=_G})
 local sentinel={};local st={Game_State=1,run=function(a,...)if a=='bad'then error(sentinel,0)end;return nil,false,... end,fun=function(f,...)return f(...)end,__gm_diag_checkpoint_v159=function()return false,nil end}
 load('legacy_diag',env)(st)
 if with_exit then local run,fun=st.run,st.fun;load('exit_watch',env)(st);eq(st.run,run);eq(st.fun,fun)end
 for i=1,8 do st.run('warmup')end
 local n=wn;collectgarbage('collect');local kb=collectgarbage('count')
 for i=1,200 do same(pack(st.run('ordinary',false,nil)),{n=4,nil,false,false,nil})end
 local growth=collectgarbage('count')-kb;eq(wn,n)
 local ok,err=pcall(st.run,'bad');eq(ok,false);eq(err,sentinel)
 assert(fs['Log/guimeng_critical_latest.txt']:find('script.run.error',1,true))
 return growth
end
local old_kb,new_kb=allocation_case(false),allocation_case(true);assert(new_kb<old_kb+10)
print('EXIT_WATCH_V270_PASS '..mode..' checks='..checks..' allocation_kib='..old_kb..'/'..new_kb)
