local work,mode=assert(arg[1]),arg[2] or 'normal'
if mode=='hot' then require('jit.opt').start('hotloop=1','hotexit=1')end
local count=0
local function eq(a,b,msg)assert(a==b,(msg or 'check')..': '..tostring(a)..' ~= '..tostring(b));count=count+1 end
local function load(name,env)local f=assert(loadfile(work..'/'..name..'.ljbc'));setfenv(f,env);return f end
local function clone(v)if type(v)~='table' then return v end;local r={};for k,x in pairs(v)do r[k]=clone(x)end;return r end
local MARK='__gm_double_day_v173'
local REFRESH='__gm_daily_refresh_v173'
local function make(version)
 local s={version=version,day='2026-11-13',errors={},logs={},timers=0,drivers=0,enabled=0,dialogs=0,date_calls=0,
  hero={['爽不精英']={0,123,0},['迟则生变']='2026-12-02 16:52:29'},engine_time='2026-12-02 16:52:29'}
 local U=load('ux_init',_G)();s.U=U
 U['啾啾啵啵']=function()return s.hero end
 U['窗口相关']={['定时检测']=function(kind,stamp)eq(kind,3);eq(stamp,s.engine_time);s.timers=s.timers+1 end}
 U['游戏音效']=setmetatable({},{__index=function()return {['播放']=function()end}end})
 local env={['Ux雌']=U,['Gly独']={['错误']=function(msg)s.errors[#s.errors+1]=msg;error(msg)end},
  ['取系统时间']=function(kind)eq(kind,1);return s.engine_time end,
  ['调试输出2']=function(msg)s.logs[#s.logs+1]=msg end,['格式化数值']=tostring,
  ['FXru胃啪']={['增加状态']=function(name)eq(name,'双倍经验');s.hero['爽不精英'][3]=1;s.enabled=s.enabled+1 end}}
 s.env=env
 -- Execute the ORIGINAL explicit whitelist export instructions, rather than
 -- manually copying Lua globals (which previously smuggled pcall into tests).
 local native=setmetatable({os={date=function(fmt)
  eq(fmt,'%Y-%m-%d');s.date_calls=s.date_calls+1;return s.day
 end}},{__index=_G})
 local export=load('builtin_exports',native)
 eq(export(nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,env),env)
 eq(rawget(env,'pcall'),nil);eq(rawget(env,'xpcall'),nil)
 local sys={script_setting=env,tbl_controls={['对话窗口']={tbl={['对话']=function(a,b,c,d,msg,z,owner)s.dialogs=s.dialogs+1;s.lastdialog=msg;s.lastowner=owner end,['关闭']=function()end}}}}
 local install=load('sandbox_install',_G);debug.setupvalue(install,1,sys);install()
 eq(env.pcall,nil,'actual protected environment does not provide pcall')
 eq(env.xpcall,nil,'xpcall is also absent')
 -- Execute the real original daily-function binding; the newly created child
 -- inherits this restricted environment, just as it does in the game.
 local owner={['驱蚊水点']=function()s.drivers=s.drivers+1 end}
 U['开挖机的']=owner
 local register=load('register_daily_'..version,env);debug.setupvalue(register,1,owner)
 s.daily=register();eq(type(s.daily),'function');eq(owner['可激动了'],s.daily);eq(getfenv(s.daily),env)
 s.login=load('load_daily_'..version,env);s.create=load('create_daily_'..version,env)
 return s
end
local REFRESH='__gm_daily_refresh_v173'
local GRANTED='__gm_double_granted_v177'
do
 local old=make('old');old.hero['爽不精英'][9]=1;old.login();eq(old.hero['爽不精英'][1],7200,'v176 ignores membership for daily grant')
 local s=make('new');s.hero['爽不精英'][9]=1;s.login();eq(s.hero['爽不精英'][1],14400);eq(s.hero[GRANTED],14400)
 eq(s.timers,1);eq(s.drivers,1)
 for i=1,1000 do s.daily(REFRESH);eq(s.hero['爽不精英'][1],14400)end
end
do
 local s=make('new');s.login();eq(s.hero['爽不精英'][1],7200)
 local begin=load('buff_begin_new',s.env);debug.setupvalue(begin,1,{id='玛法名俊'});eq(begin(),true)
 eq(s.hero['爽不精英'][9],1);s.daily(REFRESH);eq(s.hero['爽不精英'][1],14400,'same-day premium upgrade tops up missing 2h')
 local stop=load('buff_end_new',s.env);debug.setupvalue(stop,1,{id='玛法名俊'});stop();eq(s.hero['爽不精英'][9],0)
 begin();s.daily(REFRESH);eq(s.hero['爽不精英'][1],14400,'toggling membership never regrants time')
 s.hero['爽不精英'][1]=0;s.daily(REFRESH);eq(s.hero['爽不精英'][1],0,'spent same-day time not repeated')
 s.day='2026-11-14';s.daily(REFRESH);eq(s.hero['爽不精英'][1],14400,'next day grants four hours')
 s.hero=clone(s.hero);s.daily(REFRESH);eq(s.hero['爽不精英'][1],14400,'saved entitlement survives reload')
end
do
 -- Migration from v173..v176: today's marker meant exactly a base2h grant.
 local s=make('new');s.hero[MARK]=s.day;s.hero['爽不精英'][1]=7200;s.hero['爽不精英'][9]=1
 s.daily(REFRESH);eq(s.hero['爽不精英'][1],14400);eq(s.hero[GRANTED],14400)
 for i=1,1000 do s.daily(REFRESH);eq(s.hero['爽不精英'][1],14400)end
 s.day='2026-11-14';s.daily(REFRESH);eq(s.hero['爽不精英'][1],28800,'new daily credits stack while XP already enabled')
 s.hero['爽不精英'][1]=86000;s.day='2026-11-15';s.daily(REFRESH);eq(s.hero['爽不精英'][1],86400)
 s.hero['爽不精英'][1]=80000;s.daily(REFRESH);eq(s.hero['爽不精英'][1],80000,'cap does not become an unlimited refill')
end
for _,idx in ipairs({7914,8361,9403,10054,10717,11127,18451})do
 local s=make('new');s.hero['爽不精英'][9]=1;s.hero['爽不精英'][3]=1
 local menu=load('menu'..idx..'_new',s.env);debug.setupvalue(menu,1,{})
 menu();eq(s.hero['爽不精英'][1],14400);assert(s.lastdialog:find('四小时',1,true));count=count+1
 s.day='2026-11-14';menu();eq(s.hero['爽不精英'][1],28800)
end
for _,idx in ipairs({7917,8364,9406,10057,10720,11130,18454})do
 local s=make('new');s.hero['爽不精英'][9]=1;s.hero['爽不精英'][3]=1;s.hero[MARK]=s.day;s.hero['爽不精英'][1]=7200
 local npc={name='NPC'};local start=load('menu'..idx..'_new',s.env);debug.setupvalue(start,1,npc)
 start();eq(s.hero['爽不精英'][1],14400);eq(s.enabled,0,'active effect is not applied twice');eq(s.lastowner,npc,'original owner upvalue preserved')
 assert(s.lastdialog:find('240',1,true));assert(not s.lastdialog:find('失败',1,true));count=count+2
 start();eq(s.hero['爽不精英'][1],14400);eq(s.enabled,0)
 s.hero['爽不精英'][3]=0;start();eq(s.enabled,1,'inactive effect can start normally')
 local tick=load('buff_tick_new',s.env);debug.setupvalue(tick,1,{id='双倍经验'});tick();eq(s.hero['爽不精英'][1],14399,'original tick consumes shared remaining balance')
 s.hero['爽不精英'][1]=0;start();eq(s.enabled,1,'zero balance does not start an effect')
 eq(#s.errors,0)
end
print('DAILY_AND_BUFF_PASS',mode,count)
math.randomseed(177)
local config=load('affix_config_new',_G)()
local env={table={copy=clone,remove=table.remove},['Ux雌']={['独角兽下']=function()return config end},
 ['Gly独']={['取随机数']=function(lo,hi)assert(lo<=hi);return math.random(lo,hi)end}}
setmetatable(env,{__index=_G});local gen=load('generator_new',env)
local allowed={['武器']=true,['项链']=true,['戒指']=true,['头盔']=true,['手镯']=true};local seen={}
for _,kind in ipairs({'武器','项链','戒指','头盔','手镯','衣服','鞋子','腰带','勋章','饰品'})do
 seen[kind]={}
 for tier=3,7 do for i=1,250 do
  local t=setmetatable({['子类']=kind,['分类']='装备',['职业要求']='战士',['附加']={},['价格']=100},{__index=function()return 0 end})
  eq(gen(t,40,tier),t);eq(t['附加']['条数'],tier)
  for _,key in ipairs({'暴击几率','真伤几率'})do
   if rawget(t,key) then assert(allowed[kind],'affix on excluded slot');seen[kind][key]=true;count=count+1 end
  end
  if kind=='衣服' or kind=='鞋子' then for _,e in ipairs({'火','冰','雷','风','神','暗','幻'})do eq(rawget(t,'攻'..e..'元素'),nil)end end
  if kind=='鞋子' then for _,key in ipairs({'最大破坏','最大自然','最大灵魂'})do eq(rawget(t,key),nil)end end
  for _,key in ipairs({'抵抗暴击','抵抗几率','抵抗真伤','暴击伤害'})do eq(rawget(t,key),nil)end
  local n=0;for key in pairs(config['极品数值'])do if rawget(t,key)then n=n+1 end end;eq(n,tier,'unique affix count retained')
 end end
 if allowed[kind] then eq(seen[kind]['暴击几率'],true,kind..' critical affix actually generated');eq(seen[kind]['真伤几率'],true,kind..' penetration affix actually generated')end
end
print('AFFIX_PASS',mode,count)
print('PASS',mode,count)
