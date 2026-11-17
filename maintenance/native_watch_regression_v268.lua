local work,mode=arg[1],arg[2]
if mode=='normal'then jit.off()else jit.opt.start('hotloop=1','hotexit=1')end
local checks=0
local function eq(a,b,msg)checks=checks+1;assert(a==b,(msg or'')..' '..tostring(a)..' ~= '..tostring(b))end
local function load(n,e)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,e);return f end
local function pack(...)return{n=select('#',...),...}end
local function same(a,b)
 eq(a.n,b.n,'return count');for i=1,a.n do eq(a[i],b[i],'return/argument identity')end
end
local files,writes,logs={},0,{}
local env=setmetatable({dt=.01,核心={写到文件=function(path,data)files[path]=data;writes=writes+1 end,读入文件=function(path)return files[path]end}},{__index=_G})
local original_frames=0;local frame_args;local save_args;local fail_frame,fail_save,fail_fun
local sentinel={message='original error object'}
local function saving(...)
 save_args=pack(...);if fail_save then error(sentinel,0)end
 return false,nil,'saved',nil
end
local function frame(action,...)
 frame_args=pack(action,...)
 if fail_frame then error(sentinel,0)end
 if action=='init'then return nil,false,nil end
 if action~=nil then return 'action',nil end
 original_frames=original_frames+1
 S.__gm_perf_phase_v186('actors_update')
 for i=1,3 do S.__gm_perf_actor_v189(true,S.屏幕事件组[i]);S.fun(function()return false,nil end);S.__gm_perf_actor_v189(false)end
 S.__gm_perf_phase_v186('timers')
 return nil,false,'frame',nil
end
S={Game_State=1,sid=11,Hero={id=0,属性={hp=50,mp=10,等级=36},当前状态=1,动作='移动',地图格子={x=5,y=6},释放技能组={}},
 屏幕事件组={},script_setting={Gly独={存档=saving}},__gm_detail_v179=function(stage,msg)logs[#logs+1]=stage..' '..msg end,
 __gm_perf_phase_v186=function()end,__gm_perf_actor_v189=function()end,
 run=frame,fun=function(f,...)if fail_fun then error(sentinel,0)end;return f(...)end}
for i=1,3 do S.屏幕事件组[i]={id=i,属性={hp=50,mp=10},当前状态=3,动作='攻击',释放技能组={}}end
files['Log/guimeng_native_watch_latest.txt']='old attempt'
load('watch',env)(S)
eq(files['Log/guimeng_native_watch_previous.txt'],'old attempt','rotate prior attempt')
assert(files['Log/guimeng_native_watch_latest.txt']:find('v1.268',1,true))
same(pack(S.run('init','x',nil)),{n=3,nil,false,nil});same(frame_args,{n=3,'init','x',nil})
same(pack(S.run('other',false,nil)),{n=2,'action',nil});same(frame_args,{n=3,'other',false,nil})
local api=S.script_setting.Gly独.存档;assert(api~=saving,'actual save API attached')
same(pack(api('path',false,nil)),{n=4,false,nil,'saved',nil});same(save_args,{n=3,'path',false,nil})
assert(files['Log/guimeng_native_watch_latest.txt']:find('save.returned',1,true))
local w0=writes
for i=1,200 do same(pack(S.run()),{n=4,nil,false,'frame',nil})end
eq(original_frames,200);assert(writes-w0<=20,'bounded disk writes, never per actor/callback')
local data=files['Log/guimeng_native_watch_latest.txt'];assert(data:find('actor.return',1,true));assert(data:find('hero id=0',1,true));assert(#data<40000)
-- Nil/false and tail nil callback ABI is untouched; no table packing in wrapper.
local object={};local f=function(...)same(pack(...),{n=3,object,false,nil});return nil,object,false,nil end
same(pack(S.fun(f,object,false,nil)),{n=4,nil,object,false,nil})
fail_save=true;local ok,err=pcall(api,'path');eq(ok,false);eq(err,sentinel);assert(table.concat(logs,'\n'):find('native.save.error',1,true));fail_save=false
fail_frame=true;ok,err=pcall(S.run);eq(ok,false);eq(err,sentinel);assert(table.concat(logs,'\n'):find('native.frame.error',1,true));fail_frame=false
-- Diagnostic writer failures cannot change gameplay return or errors.
env.核心.写到文件=function()error('disk unavailable')end
same(pack(api('path')), {n=4,false,nil,'saved',nil});same(pack(S.run()),{n=4,nil,false,'frame',nil})
fail_frame=true;ok,err=pcall(S.run);eq(ok,false);eq(err,sentinel);fail_frame=false
-- Original hooks still execute; missing optional diagnostic hooks remain usable.
local calls=0;local plain={run=function()calls=calls+1;return false,nil end,Game_State=1}
load('watch',env)(plain);same(pack(plain.run()),{n=2,false,nil});eq(calls,1)
local nofile={run=frame};load('watch',setmetatable({核心=false},{__index=_G}))(nofile);eq(nofile.run,frame)
-- The real native constructor tail calls the compiled child before read-only export.
local exports={run=function()return false,nil end,get=function()end,add=function()end}
local ctor=load('constructor',env);debug.setupvalue(ctor,5,load('readonly',env))
local public=ctor(exports);same(pack(public.run()),{n=2,false,nil});eq(public.Hero,nil);eq(public.__gm_native_watch_v268,nil)
print('NATIVE_WATCH_V268_PASS '..mode..' checks='..checks..'; bounded writes, actual constructor/public export, original varargs/returns/errors, finite file sink')
-- Full original diagnostic installer, compared with/without the new native
-- wrapper; no manual replacement of its handlers or file buffering logic.
local function original_logger_case(with_watch)
 local fs,wn={},0;local nowrites
 local e=setmetatable({dt=0,核心={读入文件=function(p)return fs[p]end,写到文件=function(p,s)fs[p]=s;wn=wn+1 end}},{__index=_G})
 local error_object={};local function original(a,...)if a=='bad'then error(error_object,0)end;return nil,false,... end
 local sys={Game_State=1,run=original,fun=function(f,...)return f(...)end,__gm_diag_checkpoint_v159=function()return false,nil end}
 load('legacy_diag',e)(sys)
 if with_watch then load('watch',e)(sys)end
 for i=1,8 do sys.run('warmup')end
 local before=wn;collectgarbage('collect');local kb=collectgarbage('count')
 for i=1,200 do same(pack(sys.run('ordinary',false,nil)),{n=4,nil,false,false,nil})end
 local growth=collectgarbage('count')-kb;eq(wn,before,'ordinary dispatch keeps original low-frequency disk behavior')
 local ok,err=pcall(sys.run,'bad');eq(ok,false);eq(err,error_object,'original diagnostic error object')
 assert(fs['Log/guimeng_critical_latest.txt']:find('script.run.error',1,true),'original error stack still reaches original sink')
 return growth
end
local old_kb,new_kb=original_logger_case(false),original_logger_case(true)
assert(new_kb<old_kb+100,'bounded additional diagnostic allocation')
print('NATIVE_WATCH_ORIGINAL_LOGGER_V268_PASS '..mode..' allocation_kib='..old_kb..'/'..new_kb)
