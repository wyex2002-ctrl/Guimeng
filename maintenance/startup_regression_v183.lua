local work,mode=assert(arg[1]),arg[2] or 'normal'
if mode=='hot' then require('jit.opt').start('hotloop=1','hotexit=1') end
local count=0
local function eq(a,b,msg)count=count+1;assert(a==b,(msg or 'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function load(name,env)local f=assert(loadfile(work..'/'..name..'.ljbc'));setfenv(f,env);return f end
local function fail()error('unexpected native primitive, network report or exit')end
local function setup(version,story,difficulty,debugging)
 local U=load('ux_init',_G)()
 local errors,registered,callbacks={},{},{}
 local disk={Ver=story,GuimengDifficulty=tostring(difficulty)}
 local env={['Ux雌']=U,['Ae冻']=U,['Gly独']={['鼠标指针动画']=function()end,['错误']=function(e)errors[#errors+1]=e end,['结束游戏']=fail},
 ['是否为调试版']=function()return debugging end,
 ['读配置项']=function(path,section,key)eq(path,'Dat/Options.ini');eq(section,'Main');return disk[key]end,
 ['写配置项']=function(path,section,key,value)eq(path,'Dat/Options.ini');eq(section,'Main');disk[key]=tostring(value)end}
 local export=load('builtin_exports',_G);eq(export(nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,env),env)
 local G=env['Gly独']
 G['创建音乐']=function()return {['播放']=function()end}end
 G['创建音效']=function()return {['播放']=function()end}end
 G['创建动画']=function()return {}end
 G['取随机数']=load('rng_original',{['引擎']={['取随机整数']=function(_,lo,hi)eq(type(lo),'number');eq(type(hi),'number');return lo end}})
 local sys={script_setting=env,tbl_controls={},shelp={},sid=-1}
 for _,name in ipairs({'选择框4','选择框5','选择框6','启动图片','来世续缘','前尘忆梦','动画框4','登录按钮','登录按钮2','版本号标签','数据按钮','测试按钮','人物外形框','佣兵属性','佣兵属性外形框','佣兵技能','佣兵技能外形框','佣兵窗口','佣兵装备','佣兵装备外形框','佣兵设置','佣兵设置外形框','冰_外形框','属性外形框','幻影_外形框','技能_冰','技能_幻','技能_暗','技能_火','技能_物','技能_神','技能_雷','技能_风','技能外形框','技能窗口','暗黑_外形框','火_外形框','物理_外形框','状态外形框','登录按钮','登录按钮2','神圣_外形框','背包子夹','背包格子','背包窗口','英雄人物外形框','英雄属性外形框','英雄技能外形框','英雄状态外形框','英雄窗口2','英雄窗口2_英雄人物','英雄窗口2_英雄属性','英雄窗口2_英雄技能','英雄窗口2_英雄状态','角色窗口2','角色窗口2_人物','角色窗口2_属性','角色窗口2_技能','角色窗口2_状态','连接动画框','雷_外形框','风_外形框'})do
  sys.tbl_controls[name]={tbl={['播放']=function()end,['置父']=function()end,['打开']=function()end}}
 end
 -- A native primitive facade is deliberately finite. Missing game functions
 -- stay nil, and neither _G nor a generic function fallback is available.
 local native={}
 native.add=function(kind,name,f,msg)
  eq(kind=='qs_update' or kind=='qs_update_other',true)
  eq(type(f),'function');registered[#registered+1]={kind=kind,name=name,f=f,msg=msg}
 end
 local public=load('public_sys',_G);env.Sys=public(native)
 local install=load('sandbox_install',_G);debug.setupvalue(install,1,sys);install()
 eq(env.pcall,nil);eq(env.xpcall,nil);eq(env._G,nil)
 local dispatch=load('dispatch',_G);debug.setupvalue(dispatch,1,sys)
 -- Execute the entire real database constructor and its public interface.
 local db=load('database_'..version,{setmetatable=setmetatable})();eq(type(db['接口']),'function')
 -- No UI resources exist on the Linux host. Execute the original contiguous
 -- registration block (all 19 events/pages) and all page factories unchanged.
 load('register_'..version,env)();eq(#registered,19)
 for i,r in ipairs(registered)do
  if r.kind=='qs_update_other' then
   local page=r.f();eq(type(page.Main),'function');eq(type(page.getself),'function')
   callbacks[r.name]=page
   sys.shelp[tostring(page.Main)]={sid=i,msg=r.msg}
  end
 end
 local function run(name)
  local p=assert(callbacks[name],name);local n=#errors
  local ok=dispatch(p.Main,{},-1);eq(sys.sid,-1)
  return ok,errors[n+1]
 end
 return {U=U,env=env,sys=sys,db=db,callbacks=callbacks,run=run,errors=errors,disk=disk}
end
local timer=load('item_timer',setmetatable({},{__index=fail}))
for i=1,1000 do eq(timer(),true) end
-- Reproduce the user's precise next failure, with the old original installer.
for _,story in ipairs({'前尘忆梦','来世续缘'})do
 local s=setup('old',story,0,false)
 eq(s.run('版本选择'),true)
 eq(s.U['金轮法王'],nil);eq(s.U['游戏检查'],nil)
 local ok,err=s.run('频道相关');eq(ok,false)
 eq(type(err),'string');eq(err:find('nil value',1,true)~=nil,true)
 eq(#s.errors,1)
end
print('V182_MISSING_API_REPRODUCED',mode,count)
-- Real registration produces the getter and the complete disabled API table.
-- Run both story branches, every difficulty and release/debug UI paths.
for iteration=1,10 do
 for _,story in ipairs({'前尘忆梦','来世续缘'})do
  for difficulty=0,2 do
   for _,debugging in ipairs({false,true})do
    local s=setup('new',story,difficulty,debugging)
    eq(s.U['金轮法王'],nil,'must be registered by production code')
    eq(s.run('版本选择'),true)
    eq(type(s.U['金轮法王']),'function');eq(s.U['金轮法王'](),1)
    eq(s.callbacks['版本选择'].getself()['金轮法王'],1)
    eq(s.U['版本选择'],story);eq(s.U['__gm_difficulty_v175'],difficulty)
    eq(s.disk.GuimengDifficulty,tostring(difficulty))
    eq(type(s.U['游戏检查']),'table')
    local total=0
    for name,f in pairs(s.U['游戏检查'])do
     eq(type(f),'function');eq(f(setmetatable({},{__index=fail})),nil);total=total+1
    end
    eq(total,9)
    eq(s.run('频道相关'),true);eq(#s.errors,0)
    eq(type(s.U['开挖机的']),'table')
    local n=0;for _,f in pairs(s.U['开挖机的'])do eq(type(f),'function');n=n+1 end;eq(n,5)
    if story=='来世续缘' then
     eq(type(s.U['震爆山巅']),'function');eq(type(s.U['震爆山巅']()['声望']),'table')
    end
    -- Subsequent pages must also initialize without synthesizing functions.
    for _,name in ipairs({'游戏配置','窗口相关','托管显示','地图刷怪'})do
     local ok,err=s.run(name);assert(ok,err);eq(ok,true)
    end
    eq(#s.errors,0)
    s.env['UNREGISTERED_v183']=true
    eq(s.env['UNREGISTERED_v183'],nil);eq(#s.errors,1)
    eq(s.errors[1]:find('不安全的变量',1,true)~=nil,true)
   end
  end
 end
end
print('PAGE_STARTUP_PASS',mode,count)
