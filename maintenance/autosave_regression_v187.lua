local work,mode=assert(arg[1]),arg[2]or 'normal'
if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end
local count=0
local function eq(a,b,msg)count=count+1;assert(a==b,(msg or 'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function load(name,env)local f=assert(loadfile(work..'/'..name..'.ljbc'));setfenv(f,env or _G);return f end
local function setup(version,story,enabled,debugging,cost)
 local saves,quits,steps,elapsed=0,0,0,0
 local owner={['角色组']={hp=100},['配置']={['征集死亡']=0},['金轮法王']=1}
 local U={['人物选择']=2,['开挖机的']={['正弦函数']=function(t)steps=steps+1 end}}
 for key,name in pairs({['啾啾啵啵']='role_'..story,['胚子考虑']='config_'..story,['金轮法王']='mode_get'})do
  local f=load(name,{['Ux雌']=U});debug.setupvalue(f,1,owner);U[key]=f
 end
 U['窗口相关']={['存档读档']=function(command,slot,unused,kind)
  eq(command,'存档');eq(slot,2);eq(unused,nil);eq(kind,0)
  saves=saves+1;elapsed=elapsed+0.270;if cost then cost(0.270)end
 end}
 local env={['Ux雌']=U,['镜头选择框']={['选中']=enabled},['是否为调试版']=function()return debugging end}
 local f=load('timer_'..version,env)
 return {f=f,t={},U=U,owner=owner,stats=function()return saves,steps,elapsed end}
end
for _,story in ipairs({'a','b'})do
 for _,enabled in ipairs({true,false,'nil'})do
  for _,debugging in ipairs({false,true})do
   local selected=enabled;if enabled=='nil'then selected=nil end
   local old=setup('old',story,selected,debugging);local new=setup('new',story,selected,debugging)
   for i=1,6005 do old.f(old.t);new.f(new.t)end
   local a,asteps=old.stats();local b,bsteps=new.stats()
   eq(a,selected==false and 6005 or 0,'reproduce runaway saves')
   eq(b,selected==false and not debugging and 2 or 0,'original periodic gate')
   eq(asteps,6005);eq(bsteps,asteps);eq(old.t['时间'],new.t['时间'])
   eq(old.owner['配置']['征集死亡'],new.owner['配置']['征集死亡'])
   eq(new.t['啾啾啵啵'],new.owner['角色组'],'actual role getter preserved')
  end
 end
end
-- Exact boundary and wrap behavior, including the original mode condition.
do
 local s=setup('new','a',false,false);s.t['时间']=2998;s.t['咯是']=0
 s.f(s.t);eq(s.stats(),0);s.f(s.t);eq(s.stats(),1);s.f(s.t);eq(s.stats(),1)
 s.t['时间']=5999;s.f(s.t);eq(s.stats(),2)
end
-- Actual native timer factory + complete real native frame + constructor's
-- public.run export. Only the timer callback is explicitly bounded at the
-- autosave region; unrelated later gameplay work is unchanged byte-for-byte.
local costs={}
for _,version in ipairs({'old','new'})do
 local events,logs={},{};local tick,elapsed=0,0
 local function op(name)return function(...)events[#events+1]=name end end
local E={['游戏进度']=1,['逻辑暂停']=0,['屏幕焦点']=true,['最后按键']=0,['界面可视']=true,['游戏暂停']=false,
 ['屏幕震动时间']=0,['屏幕宽度']=800,['屏幕高度']=600,['屏幕缩放']=1,['画面偏移']={x=0,y=0},
 ['鼠标_屏幕坐标']={x=0,y=0},['鼠标_地图坐标']={x=0,y=0},['鼠标_地图格子']={x=0,y=0},['遮罩信息']={['启动']=false}}
local S={Game_State=1,['控制对象']={},['Hero']={['更新']=op('hero.update'),['属性']={hp=100}},['script_setting']={['Ux雌']={},['Gly独']={}}}
for _,name in ipairs({'游戏技能组','道具CD信息组','屏幕特效组','屏幕锁链组','屏幕粒子组','屏幕事件组','屏幕子弹组','界面_窗口_数组','屏幕提示组','屏幕气泡组','Plug','动画精灵组','剧情对话框','剧情资源表','time_table','创建窗口组'})do S[name]={}end
for _,name in ipairs({'取鼠标所在窗口','状态图标显示控制','状态图标显示提示','焦点触发'})do S[name]=op(name)end
S.temp_spr={['置混合模式']=op('composite.blend'),['显示_范围缩放']=op('composite.draw')}
S['banner']={show=op('banner')};S['黑边特效']={show=op('letterbox')}
S.get=function(key)if key=='item_box'then return{}end end
S.Hero['焦点触发']=op('hero.focus')
S['中间提示组']={};S['中间遮罩']={['可视']=false};S['气泡提示组']={}
for i=0,9 do S['气泡提示组'][i]={['可视']=false}end
local env={['Ae冻']={},['Ae冻集']=E,dt=0.1,Sys=S,['丰富文本_动画更新显示']=op('richtext'),['Q_公用动画库']={},['Q_提示框']={['可视']=false},
 ['Q_鼠标']={},['Q_地图']={['更新']=op('map.update'),['显示']=op('map.draw')},['Q_文字']={['显示']=op('text')},
 ['引擎']={['取按键按下']=function()return false end,['取按键弹起']=function()return false end,['调整屏幕']=op('camera')},
 ['L常量']={},['核心']={http_url_get=function()return {['总数']=0}end}}
env._G=env;env.loadstring=function(src)local f,e=loadstring(src);if f then setfenv(f,env)end;return f,e end
env.os={clock=function()return tick end,time=function()return math.floor(elapsed)end};S.__gm_detail_v179=function(tag,msg) logs[#logs+1]=tag..' '..msg;tick=tick+0.007 end
setmetatable(env,{__index=function(_,k)if k=='__gm_bulk_sale_tick_v177' or k=='__gm_info_tick_v137' then return nil end;if _G[k]~=nil then return _G[k]end;error('MISSING GLOBAL '..tostring(k))end})


 E['新时钟计次']=0
 local t=setup(version,'a',false,false,function(v)tick=tick+v end)
 local create=load('timer_factory',env);debug.setupvalue(create,1,S)
 local control=create(100,t.f);eq(type(control['暂停']),'function');eq(#S.time_table,1);eq(S.time_table[1].time,0.1)
 S.time_table[1].tbl=t.t
 local frame=load('native_frame',env);debug.setupvalue(frame,1,S);debug.setupvalue(frame,2,{})
 S.run=frame;load('profile_only',env)(S)
 local exporter=load('native_exports',env);debug.setupvalue(exporter,5,load('public_sys',_G))
 local public=exporter(S);eq(public.run,S.run)
 for i=1,3001 do public.run();elapsed=elapsed+0.1 end
 local n,steps,modeled=t.stats();eq(steps,3001);eq(n,version=='old'and 3001 or 1)
 costs[version]={saves=n,modeled_seconds=modeled}
 eq(t.t['时间'],3001);eq(#S.time_table,1)
 local before=steps;env.dt=0;public.run();local _,after=t.stats();eq(before,after,'zero dt skips timers')
 if version=='old'then eq(table.concat(logs,'\n'):find('phase_peak=timers',1,true)~=nil,true)end
end
print('NATIVE_AUTOSAVE_IO',mode,costs.old.saves,costs.new.saves,costs.old.modeled_seconds,costs.new.modeled_seconds)
-- Manual/exit saving retains the real existing quit callbacks, unchanged.
for _,idx in ipairs({153,188})do
 local saves,quits=0,0;local U={['人物选择']=2}
 local env={['Ux雌']=U,['Gly独']={['结束游戏']=function(flag)eq(flag,true);quits=quits+1 end}}
 local f=load('quit'..idx,env);debug.setupvalue(f,1,{['存档读档']=function(command,slot,unused,kind)eq(command,'存档');eq(slot,2);eq(kind,0);saves=saves+1 end})
 for i=1,10 do f()end;eq(saves,10);eq(quits,10)
end
print('AUTOSAVE_REGRESSION_PASS',mode,count)
