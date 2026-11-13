local work,mode=assert(arg[1]),arg[2] or 'normal'
if mode=='hot' then require('jit.opt').start('hotloop=1','hotexit=1') end
local count=0
local function eq(a,b,msg)count=count+1;assert(a==b,(msg or 'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function load(name,env)local f=assert(loadfile(work..'/'..name..'.ljbc'));setfenv(f,setmetatable(env or {},{__index=_G}));return f end
local function fail()error('unexpected exit or destructive mutation')end
-- Read and write the actual data wrapper, including direct changes through its
-- callable underlying-table interface (normal saves and engine callbacks use it).
for _,version in ipairs({'old','new'})do
 local checks=0;local env={Sys={run=function(name,code)eq(name,'debug_msg');eq(code,1);checks=checks+1 end}}
 local wrap=load('proxy_'..version,env);local sys={script_setting={}};sys['数据保护']=wrap;debug.setupvalue(wrap,1,sys)
 local source={level=21,nested={hp=40}};local p=wrap(source,true)
 eq(p.level,21);eq(p(),source);p.level=22;eq(source.level,22);eq(p.level,22)
 source.level=999;eq(p.level,999);eq(checks,version=='old' and 1 or 0,'mirror comparison removed')
 p.nested().hp=777;eq(p.nested.hp,777);eq(checks,version=='old' and 2 or 0)
 p.level=nil;eq(p.level,nil);p.level=25;eq(p.level,25)
end
-- Explicit menu exit must still save and quit for both game branches.
for _,idx in ipairs({153,188})do
 local saves,quits=0,0;local U={['人物选择']=2};local G={['结束游戏']=function(flag)eq(flag,true);quits=quits+1 end,['增加物品']=fail}
 local f=load('quit'..idx,{['Ux雌']=U,['Gly独']=G});debug.setupvalue(f,1,{['存档读档']=function(command,slot,_,kind)eq(command,'存档');eq(slot,2);eq(kind,0);saves=saves+1 end})
 for i=1,100 do f()end;eq(saves,100);eq(quits,100)
end
-- The settings menu must bind the real retained exit callback, not just a mock.
do
 local U={};local f=load('settings',{['Ux雌']=U});local saves,quits=0,0
 local owner={['信息窗口']=function(msg)assert(msg:find('退出',1,true));count=count+1 end,['存档读档']=function()saves=saves+1 end}
 debug.setupvalue(f,1,owner);local env=getfenv(f);env['Gly独']={['结束游戏']=function()quits=quits+1 end};U['人物选择']=1
 f('退出游戏');eq(type(U['信息按钮']),'function');U['信息按钮']();eq(saves,1);eq(quits,1)
end
-- Whole alternate-backpack withdrawal: old data exceeds the historic cap, but
-- the requested withdrawal remains valid. Verify the old destructive branch is
-- reproducible, and the new code actually delivers the item and keeps capacity gates.
local function withdraw(version,space,input,total)
 local state={saves=0,quits=0,delivered=0,cleared=0,messages=0}
 local stock={['药品']=total,['超人']=100,['前线']=1};local hero={['灵魂贝贝']=stock}
 local env={['购买输入框']={['内容']=input},['到数值']=tonumber,['Ux雌']={['人物选择']=1,['啾啾啵啵']=function()return hero end,
  ['托管显示']={['屏幕提示']=function()state.messages=state.messages+1 end},['窗口相关']={['存档读档']=function()state.saves=state.saves+1 end,['窗口开关']=function()end}},
  ['L常量']={['颜色_红']=1},['物品格子18']={['重置道具']=function()state.cleared=state.cleared+1 end},['调试输出']=function()end,['调试输出2']=function()end,['写配置项']=function()end,['远程调试']=function()end}
 env['Gly独']={['取包裹空位']=function()return space end,['结束游戏']=function()state.quits=state.quits+1;error('old anti-cheat withdrawal')end,
 ['增加物品']=function(name,n)eq(name,'药品');state.delivered=state.delivered+n end}
 local f=load('withdraw_'..version,env);debug.setupvalue(f,1,0);debug.setupvalue(f,2,'药品')
 state.ok,state.error=pcall(f);state.stock=stock;return state
end
do
 local old=withdraw('old',10,'1',10000);eq(old.ok,false);eq(old.quits,1);eq(old.cleared,1);eq(old.delivered,0)
 for i=1,200 do
  local s=withdraw('new',10,'1',10000);eq(s.ok,true);eq(s.quits,0);eq(s.cleared,0);eq(s.saves,0);eq(s.delivered,1);eq(s.stock['药品'],9900)
 end
 for _,case in ipairs({{0,'1',10000},{10,'-1',10000},{10,'2',100}})do
  local s=withdraw('new',unpack(case));eq(s.ok,true);eq(s.delivered,0);eq(s.quits,0);eq(s.cleared,0);eq(s.messages,1)
 end
end
-- Compatibility no-op checker APIs do not touch files, memory, HTTP or saves.
local poison=setmetatable({},{__index=function(_,key)error('checker accessed '..tostring(key))end})
for _,name in ipairs({'item_copy','hack_zb','hack_js','script_check','timer_check','resource_check','character_check','item_check'})do
 local f=load(name,{});for i=1,200 do f(poison,poison)end;count=count+200
end
-- Native debug dispatcher ignores removed checker codes even when an old
-- engine call arrives; genuine read errors retain the old callback contract.
do
 local calls=0;local f=load('debug_dispatch',{['核心']={['远程错误']=function()end}})
 debug.setupvalue(f,1,{save_info={uid='test'},debug_msg_callback=function(code,payload)calls=calls+1;eq(code,6);assert(payload['错误信息']);count=count+1 end})
 for i=1,200 do for _,code in ipairs({1,2,3,5})do f(code,{'key','value'})end end;eq(calls,0)
 f(6,{-2});eq(calls,1)
end
-- Native initialization still imports/sets identifiers, but does not reject
-- a changed UUID or account flags before installing the database environment.
for _,login in ipairs({0,1})do
 for _,version in ipairs({'old','new'})do
  local ended=false;local env={__SysType=1,['Ae冻集']={},os={exit=function()ended=true;error('old identifier enforcement')end},['核心']={get_info=function()return 'name','short-id',1,2 end,set_info=function()return 1,2,9,9 end}}
  local sys={user_info={},save_info={uid='save-id'},op_login=login,op_qudong=0}
  local f=load('native_init_'..version,env);debug.setupvalue(f,1,sys)
  local ok=pcall(f);eq(ok,version=='new');eq(ended,version=='old')
  eq(env['Ae冻集'].UID,1);eq(env['Ae冻集'].GID,2)
 end
end
-- Exercise the real inventory dispatcher through its entry trampoline.
-- These events have no item to manipulate, and must return normally in either
-- story branch after deleting the template/shop-token detector block.
for _,story in ipairs({'前尘忆梦','来世续缘'})do
 local slots={};for i=1,450 do slots[i]={id=i}end
 local U={['版本选择']=story,['呦西鸽子']=function()return slots end,['胚子考虑']=function()return {['主角格子']=slots}end,
 ['啾啾啵啵']=function()return {['技能']={},['属性']={}}end,['窗口相关']={['套装属性']=function()end,['宝石属性']=function()end,['内观显示']=function()end,['王二狗水']=function()end,['元素图标']=function()end}}
 local env={['Ux雌']=U,['Gly独']={['从ID取格子']=function(i)return slots[i]end,['取控件对象']=function(i)return slots[i]end},
 ['宝石窗口']={['关闭']=function()end},['商店窗口']={['可视']=false},['仓库窗口']={['可视']=false},['信息窗口']={['可视']=false}}
 local f=load('item_event',env)
 for _,slot in ipairs({1,21,26,31,126})do for event=0,2 do
  local ok,why=pcall(f,event,slot,nil,0,{});assert(ok,tostring(story)..' event='..event..' slot='..slot..' '..tostring(why));count=count+1
 end end
end
do
 local f=load('currency_new',{['Ux雌']={['啾啾啵啵']=function()return {}end}})
 eq(f('烤鸡'),'可乐','legacy currency checker mode returns without touching gameplay data')
end
print('CHECK_REMOVAL_PASS',mode,count)
