local work,mode=arg[1],arg[2]
if mode=='normal'then jit.off()else jit.opt.start('hotloop=1','hotexit=1')end
local checks=0
local function eq(a,b,msg)checks=checks+1;assert(a==b,(msg or'check')..' '..tostring(a)..' ~= '..tostring(b))end
local function load(n,e)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,e);return f end
local function pack(...)return{n=select('#',...),...}end
local function same(a,b)eq(a.n,b.n);for i=1,a.n do eq(a[i],b[i])end end
local files,writes={},0
-- Finite screen and grid geometry only; selection/filtering is the original
-- module36/0, entered through a read-only public Sys interface.
local e=setmetatable({dt=.01,os={date=os.date,time=os.time,clock=os.clock,exit=function()end},Ae冻集={逻辑暂停=0,画面偏移={x=0,y=0},屏幕宽度=800,屏幕高度=600},核心={
 写到文件=function(p,t)files[p]=t;writes=writes+1 end,读入文件=function(p)return files[p]end}},{__index=_G})
local config={施放位置='目标',目标类型='敌方',施法距离=8,穿透模式=0,发射数量=0,作用范围={{},{},{},{},{},{},{},{}}}
local hero={id=0,属性={hp=100,mp=100},地图格子={x=0,y=0},技能信息={雷电术={对象=config,可用=true}},释放技能组={},当前状态=0}
local function enemy(id,x,hp)return{id=id,属性={hp=hp,可视=true,透明度=255},地图格子={x=x,y=0},地图坐标={x=x*48,y=40},锚点x=0,锚点y=0,可视=true,屏幕可视=true,是否有效=true,已经消失=false,所属阵营='敌方',资源动画={}}end
e.取两格子间距离=function(x,y,tx,ty)return math.sqrt((tx-x)^2+(ty-y)^2)end
e.判断是否在攻击范围=function(a,b,r)return e.取两格子间距离(a.x,a.y,b.x,b.y)<=r and 1 or -1 end
local a,b=enemy(101,2,40),enemy(102,3,60)
-- A mercenary need not carry a pet-owner field; friendly faction is enough.
local merc={id=50,所属阵营='友方',属性={hp=100},远程目标=a,当前状态=3,释放技能组={}}
local actors={a,b,merc}
local S={Hero=hero,Game_State=1,sid=11,shelp={},__gm_perf_phase_v186=function()end,__gm_perf_actor_v189=function()end}
local widget={Hero=hero,绑定技能='雷电术',控件名称='skill1'}
local releases=0;widget.释放=function(self)releases=releases+1;hero.下次技能='雷电术';return false,nil end
local selector=load('selector',e);debug.setupvalue(selector,1,widget)
local failure,actor_failure;local marker={};local sentinel=setmetatable({},{__tostring=function()return 'TARGET_TRACE_SENTINEL'end})
S.__gm_diag_checkpoint_v159=function(...)return false,nil,marker,nil end
S.__gm_detail_v179=function()end
S.fun=function(f,...)return f(...)end
S.get=function(key,value)
 if key=='__gm_diag_checkpoint_v159'then return S.__gm_diag_checkpoint_v159 end
 if key=='__gm_screen_objects_v154'then return actors end
 if key=='__gm_visible_target_v156'then return value.是否有效 and not value.已经消失 end
 error('unexpected key '..tostring(key))
end
S.run=function(action,...)
 if action=='qs_skill_drop'then return true,false end
 if action=='select'then selector(2);return false,nil end
 if action=='nested'then return S.fun(function()error(sentinel,0)end)end
 if action=='fail'then error(failure,0)end
 if action~=nil then return nil,false,... end
 S.__gm_perf_phase_v186('actors_update')
 for _,a in ipairs(actors)do
  S.__gm_perf_actor_v189(true,a)
  if actor_failure then error(sentinel,0)end
  S.__gm_perf_actor_v189(false)
 end
 S.__gm_perf_phase_v186('hero_update');S.__gm_perf_phase_v186('end')
 return nil,false,nil
end
load('watch',e)(S);e.Sys=load('readonly',e)({get=S.get,run=S.run})
same(pack(S.__gm_diag_checkpoint_v159('abi',false,nil)),{n=4,false,nil,marker,nil})
S.run('select');eq(hero.远程目标,a,'actual selector chooses nearest living target');S.run()
a.属性.hp=0;a.已经消失=true;S.run();S.run('select');eq(hero.远程目标,b,'actual selector replaces dead target');S.run()
b.是否有效=false;S.run();S.run('select');eq(hero.远程目标,nil,'actual selector rejects invalid target');S.run()
local c=enemy(101,1,80);actors[3]=c;S.run('select');eq(hero.远程目标,c,'new object may reuse old ID');S.run()
c.属性.hp=0;S.run();c.属性.hp=80;S.run()
local n=writes;for i=1,200 do S.run()end;assert(writes-n<=12,'no per-target/actor writes')
local text=files['Log/guimeng_native_watch_latest.txt']
for _,key in ipairs({'FROZEN_EVENTS','target.change','actor=50 field=远程目标','old_id=101 old_hp=0','new_id=102 new_hp=60','new_id=101 new_hp=80','skill.selector.target','old_hp=40','new_gone=true'})do assert(text:find(key,1,true),key..' missing')end
-- Formatting reads cannot mutate the old event after the entity changes again.
c.属性.hp=777;for i=1,60 do S.run()end
assert(files['Log/guimeng_native_watch_latest.txt']:find('new_hp=80',1,true),'old event is frozen')
-- Catch the innermost Lua fault, preserve its identity through action layers.
local ok,err=pcall(S.run,'nested');eq(ok,false);eq(err,sentinel)
text=files['Log/guimeng_native_watch_latest.txt'];assert(text:find('FIRST_LUA_FAULT native.callback.error',1,true));assert(text:find('TARGET_TRACE_SENTINEL',1,true));assert(text:find('stack traceback:',1,true));eq(S.__gm_native_watch_v268.depth,0)
for _,value in ipairs({false,sentinel})do failure=value;ok,err=pcall(S.run,'fail');eq(ok,false);eq(err,value)end
failure=nil;ok,err=pcall(S.run,'fail');eq(ok,false);eq(err,nil)
actor_failure=true;ok,err=pcall(S.run);eq(ok,false);eq(err,sentinel);assert(files['Log/guimeng_native_watch_latest.txt']:find('id=101',1,true));actor_failure=false
-- Unreadable diagnostic properties cannot become gameplay failures.
actors[4]=setmetatable({},{__index=function()error('no diagnostic access')end})
same(pack(S.run()),{n=3,nil,false,nil})
S.__gm_detail_v179('diagnostic.error','unreadable entity stays isolated')
text=files['Log/guimeng_native_watch_latest.txt'];assert(text:find('<entity context unavailable:',1,true));assert(text:find('unreadable entity stays isolated',1,true));assert(S.__gm_native_watch_v268.observation_failures>0)
e.核心.写到文件=function()error('disk unavailable')end
same(pack(S.run('ordinary',false,nil)),{n=4,nil,false,false,nil});failure=sentinel;ok,err=pcall(S.run,'fail');eq(ok,false);eq(err,sentinel)
-- Real init order: optional sinks become available only after an action.
local late=setmetatable({dt=0,os=e.os,核心={写到文件=function(p,t)files[p]=t end}},{__index=_G})
local L={};L.run=function(action)if action=='init'then L.__gm_diag_checkpoint_v159=function()return nil,false,nil end;L.__gm_detail_v179=function()end end;return false,nil end
load('watch',late)(L);assert(not L.__gm_native_watch_v268.checkpoint_attached)
same(pack(L.run('init')),{n=2,false,nil});assert(L.__gm_native_watch_v268.checkpoint_attached);assert(L.__gm_native_watch_v268.detail_attached)
same(pack(L.__gm_diag_checkpoint_v159('skill.selector.target',42)),{n=3,nil,false,nil})
print('TARGET_TRACE_V274_PASS '..mode..' checks='..checks..'; actual selector and frozen changes, nested error identity, late sinks')
