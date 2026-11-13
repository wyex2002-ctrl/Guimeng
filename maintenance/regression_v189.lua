local work,mode=arg[1],arg[2]or'normal'
if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end
local checks=0
local function eq(a,b,label)checks=checks+1;assert(a==b,(label or'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function load(name,env)local f=assert(loadfile(work..'/'..name..'.ljbc'));setfenv(f,env or _G);return f end
local function bind(name,S,env)local f=load(name,env);debug.setupvalue(f,1,S);return f end
local function copy(t)
 if type(t)~='table'then return t end
 if rawget(t,'__p')~=nil then t=t()end
 local n={};for k,v in pairs(t)do n[k]=copy(v)end;return n
end
local T={};for k,v in pairs(table)do T[k]=v end;T.copy=copy

-- Preserve the real bookstore conversion instructions as the oracle. The
-- drop event and the native 14/403 applier are both executed, not re-created.
local function book_trial(roll,price,proxied)
 local props={['商店']='书店',['技能']='测试技能',['解读']=9}
 local item={['名称']='测试技能书',['显示名']='测试技能书',['价格']=price,['数量']=1,['叠加']=1,['附加']=props,['属性']={}}
 local S={['游戏道具组']={['测试技能书']=copy(item)}}
 local proxy=bind('proxy',S);S['数据保护']=proxy;S['游戏道具组']=proxy(S['游戏道具组'],true)
 if proxied then item=proxy(item,true);props=item['附加']end
 local rng_calls=0
 local G={['事件对象']=function()return nil end,['取道具信息_名称']=bind('item_info',S,{pairs=pairs,table=T})}
 G['取随机数']=function(a,b)eq(a,1);eq(b,2);rng_calls=rng_calls+1;return roll end
 local U={['版本选择']='来世续缘'}
 local env={['Ux雌']=U,['Gly独']=G,['物品格子18']={},['是否为调试版']=function()return true end,math=math}
 eq(env.pcall,nil);eq(env._G,nil)
 local event=load('drop_event',env)
 S.tbl_qs={qs_item_drop={Main=event}}
 local calls=0
 S.fun=function(f,a)calls=calls+1;return true,f(unpack(a,1,5))end
 local drop=bind('drop',S,{type=type,table=T,pairs=pairs})
 local result,n,actual=drop(1,2,item,1,7)
 eq(result,false);eq(n,1);eq(calls,1);eq(rng_calls,1)
 local original=copy(S['游戏道具组']['测试技能书']);original['附加']['解读']=roll
 local slot={['道具']=original,['更新道具属性']=function(overrides)for k,v in pairs(overrides)do original[k]=v end end}
 load('bookstore') (nil,nil,nil,nil,nil,slot,math.ceil(price/2))
 for _,k in ipairs({'名称','显示名','价格','数量'})do eq(actual[k],original[k],'bookstore '..k)end
 for _,k in ipairs({'解读','残篇','商店','技能'})do eq(actual['附加'][k],original['附加'][k],'book props '..k)end
 eq(S['游戏道具组']['测试技能书']['附加']['解读'],9,'template untouched')
 return env,event
end
for _,proxy in ipairs({false,true})do
 for _,price in ipairs({0,1,101,10000})do
  for _,roll in ipairs({1,2})do book_trial(roll,price,proxy)end
 end
end
do
 local env,event=book_trial(1,101,false)
 local props={['商店']='书店',['强化书']=true,['解读']=8}
 eq(event(1,2,'强化书',7,props),false);eq(props['解读'],8,'enhancement books unchanged')
 props={['商店']='书店',['解读']=8,['商店目标']='existing'};eq(event(1,2,'书',0,props),false);eq(props['解读'],8,'shop creation unchanged')
 env['Ux雌']['版本选择']='前尘忆梦';eq(event(1,2,'书',7,props),nil);eq(props['解读'],8,'old story unchanged')
end
print('BOOKSTORE_DROP_PARITY_PASS',mode)

-- Invalid control snapshots reproduce the precise missing-method error in
-- the old function. The new function continues through duplicate controls.
local function control_trial(version,bad)
 local used=0;local logs={}
 local S={Game_State=1,['Hero']={['背包格子']={{32,0,true}}},['包裹物品组']={[32]={['道具']={['名称']='药水'}}}}
 local win={['名称']='背包窗口',['可视']=false,['控件组']={}}
 win['控件组'][1]={['名称']='失效格子',['类型']=6,['格子ID']=32,['对象']=bad}
 win['控件组'][2]={['名称']='有效格子',['类型']=6,['格子ID']=32,['对象']={['使用物品']=function()used=used+1;return true end}}
 S['界面_窗口_数组']={win}
 S.__gm_detail_v179=function(tag,msg,critical)logs[#logs+1]={tag,msg,critical}end
 S.run=function()end
 load('profile')(S)
 local f=bind(version,S)
 return S,f,logs,function()return used end
end
for _,bad in ipairs({{},42,false,{['使用物品']=42},{['使用物品']=false}})do
 local S,old=control_trial('use_old',bad);local ok,err=pcall(old,'药水');eq(ok,false)
 if type(bad)=='table'then eq(tostring(err):find('使用物品',1,true)~=nil,true,'old nil-method error')end
 local n,f,logs,used=control_trial('use',bad)
 eq(f('药水'),true);eq(used(),1);eq(#logs,1);eq(logs[1][1],'item.control.invalid');eq(logs[1][3],true)
 for _,text in ipairs({'actual_name=药水','slot=32','window=背包窗口','control=失效格子','control_type=6','method_type=','class_method_type=','action=skip_control'})do eq(logs[1][2]:find(text,1,true)~=nil,true,text)end
 for i=1,1000 do eq(f('药水'),true)end;eq(#logs,1,'no repeated disk logs')
 n.__gm_item_control_v189=function()error('diagnostic disk failure')end;eq(f('药水'),true)
 n.__gm_item_control_v189=nil;eq(f('药水'),true)
 local marker={};n['界面_窗口_数组'][1]['控件组'][2]['对象']['使用物品']=function()error(marker,0)end
 local good,e=pcall(f,'药水');eq(good,false);eq(e,marker,'game errors propagate')
end
do
 local S,f,logs,used=control_trial('use',nil);eq(f('药水'),true);eq(used(),1)
 S['界面_窗口_数组'][1]['控件组'][2]=nil;eq(f('药水'),false);eq(used(),1)
end
print('CONTROL_METHOD_GUARD_PASS',mode)

-- class(), text and rectangle creation are unavailable engine primitives.
-- Only these are finite facades. All game class registrations, initializer,
-- inventory use, consumption, native control construction and DB callbacks
-- below are the actual resource bytecode, not handwritten item methods.
local function inventory_trial(story,visible,mp,quick,broken)
 local id=story=='前尘忆梦'and 1 or 21
 local item={['名称']='药水',['显示名']='药水',['数量']=3,['性别要求']='不限',['职业要求']='不限',['需要等级']=1,['分类']='道具',['子类']='消耗品',['冷却时间']=0,['附加']={['加血']=not mp or nil,['加蓝']=mp or nil},['物品脚本']={Main=function()return true end},['属性']={}}
 local names={'生命值','法力值','生命值_百分比','法力值_百分比','物理伤害','魔法伤害','魔法防御','物理防御','命中','躲避','暴击','移动速度','攻击速度'}
 for _,k in ipairs(names)do item['属性'][k]=0 end
 item['属性'][mp and'法力值'or'生命值']=10
 local slots={};for i=1,150 do slots[i]={}end
 slots[32]={['道具']=item}
 if quick then
  local q=copy(item);q['附加']['快捷物品']=true;q['数量']=1
  q['物品脚本']={Main=function()return false end} -- shortcut never performs default consumption
  slots[id]={['道具']=q}
 end
 local hp,blue,hp_calls,mp_calls=5,5,0,0
 local hero={['背包格子']={},['装备格子']={},['属性']={['等级']=21,['性别']='男',['职业']='战士',maxhp=100,maxmp=100},['BUFF状态更新']=function()end,
 ['HP改变']=function(_,v)hp=hp+v;hp_calls=hp_calls+1 end,['MP改变']=function(_,v)blue=blue+v;mp_calls=mp_calls+1 end}
 local S={Game_State=1,['Hero']=hero,['包裹物品组']=slots,sid=0,shelp={},script_setting={}}
 S['数据保护']=bind('proxy',S);S['包裹物品组']=S['数据保护'](slots,true)
 slots=S['包裹物品组']
 local native_use=bind('use',S)
 local G={['取包裹空位']=function()return 100 end,['使用物品']=native_use,['从ID取格子']=function(i)return slots[i]end,['取按键状态']=function()return false end,
 ['取物品数量']=function(n)return slots[32]['道具']and slots[32]['道具']['数量']or 0 end}
 local U={['版本选择']=story,['主角HP']=hp,['主角MAXHP']=100,['主角MP']=blue,['主角MAXMP']=100,['人物选择']=1,['托管显示']={['屏幕提示']=function()error('unexpected gameplay gate')end}}
 local owner={['角色组']={['法治观念']=true},['配置']={['主角格子']=slots},['游戏格子']=slots}
 for key,name in pairs({['啾啾啵啵']=story=='前尘忆梦'and'role_a'or'role_b',['胚子考虑']=story=='前尘忆梦'and'config_a'or'config_b'})do U[key]=bind(name,owner,{['Ux雌']=U})end
 U['呦西鸽子']=bind('slots_get',owner)
 local getter=bind('public_get',S);S.get=getter
 local public=load('public_sys')(S)
 local env={type=type,['Sys']=public,['Ux雌']=U,['Gly独']=G,['物品格子18']={},['FXru胃啪']={HP=100,['取状态列表']=function()return{}end},['L常量']={},['仓库窗口2']={['可视']=false},['信息窗口2']={['可视']=false},['商店窗口2']={['可视']=false},['行会仓库2']={['可视']=false},['聊天输入框']={['焦点']=false},['英雄HP输入框']={['焦点']=false},['英雄MP输入框']={['焦点']=false}}
 for _,s in ipairs({'红','蓝'})do env['加'..s..'选择框']={['选中']=false};env['加'..s..'滑块条']={['位置']=50}end
 for _,name in ipairs({'仓库窗口','佣兵窗口','商店窗口','行会仓库','信息窗口'})do env[name]={['可视']=false}end
 local event=load('item_event',env);S.shelp[tostring(event)]={sid=5,msg='real item event'}
 local original_error;S.script_setting['Gly独']={['错误']=function(e)original_error=e end}
 local dispatch=bind('dispatch',S);S.fun=dispatch
 local aux=load('aux',env);U['窗口相关']={['辅助窗口']=aux};debug.setupvalue(aux,1,U['窗口相关'])
 local log={};S.__gm_detail_v179=function(tag,msg)log[#log+1]=tag..' '..msg end
 local cd={};local tex=function()return{}end
 local engine_run=function(action,a,b)
  if action=='qs_item_box'then
   local ok,r=dispatch(event,a,0);assert(ok,original_error or r);return ok,r
  elseif action=='fun'then return true,a(unpack(b))
  else error('unexpected engine action '..tostring(action))end
 end
 S.run=engine_run
 -- Sys.get uses the original explicit fields below, not a dynamic fake API.
 S['文字标签类']=nil
 local uiSys={get=function(key)
  if key=='hero'then return hero elseif key=='item_arr'then return slots elseif key=='item_cd_arr'then return cd elseif key=='win_tex'then return tex else error('unexpected ui engine key '..tostring(key))end
 end,run=engine_run,add=function(key,name,value)eq(key,'tbl_controls');S.tbl_controls=S.tbl_controls or{};S.tbl_controls[name]=value end}
 local ui={class=function()
  local C={};C['创建']=function(...)local o=setmetatable({},{__index=C});C['初始化'](o,...);return o end;return C
 end,math=math,table=table,select=select,setmetatable=setmetatable,['Sys']=load('public_sys')(uiSys),['Q_文字']={['取高度']=function()return 12 end},['Q_鼠标']={['格子标识']=0},['D2D_包围盒']={['创建']=function()return{}end},['Ae冻集']={['快捷事件组']={},['控件名称组']={},['包裹物品数']=150,['自定义属性表']={}}}
 setmetatable(ui,{__index=_G}) -- native module environment, not the DB sandbox
 load('inventory_class',ui)()
 local bind_control=load('bind_control',ui)
 local win={['名称']='背包窗口',['可视']=visible,['控件组']={},['坐标']={x=0,y=0},['闭包']=bind_control}
 local add=load('add_control',ui)
 if quick then add(win,6,'快捷格子',0,0,32,32,id,nil,false,false,0,false,false)end
 add(win,6,'背包格子',0,0,32,32,32,nil,false,true,0,false,false)
 local obj=win['控件组'][#win['控件组']]['对象']
 eq(type(obj['使用物品']),'function');eq(obj['标识'],32);eq(obj['格子组'],slots);eq(#hero['背包格子'],1)
 if broken then table.insert(win['控件组'],1,{['名称']='过期同ID格子',['类型']=6,['格子ID']=32,['对象']={}})end
 S['界面_窗口_数组']={win};load('profile',ui)(S)
 eq(public.get('__gm_item_control_v189'),nil);eq(public.get('__gm_item_seq_v189'),nil)
 aux('加油',mp and 1 or 0)
 eq(item['数量'],2,'exactly one genuine consumption')
 eq(hp_calls,mp and 0 or 1);eq(mp_calls,mp and 1 or 0);eq(hp,mp and 5 or 15);eq(blue,mp and 15 or 5)
 for i=1,200 do
  item['数量']=3;hp,blue=5,5
  aux('加油',mp and 1 or 0)
  eq(item['数量'],2,'repeated auxiliary consumption');eq(hp,mp and 5 or 15);eq(blue,mp and 15 or 5)
 end
 -- Manual use executes the same genuine method and consumes once.
 eq(obj['使用物品'](obj),true);eq(item['数量'],1)
 eq(obj['使用物品'](obj),true);eq(slots[32]['道具'],nil)
 eq(obj['使用物品'](obj),false,'empty cell safe');aux('加油',mp and 1 or 0)
 return checks
end
for _,story in ipairs({'前尘忆梦','来世续缘'})do
 for _,visible in ipairs({false,true})do
  for _,mp in ipairs({false,true})do
   for _,quick in ipairs({false,true})do inventory_trial(story,visible,mp,quick,true)end
  end
 end
end
print('REAL_INVENTORY_CONSTRUCTOR_USE_CONSUMPTION_PASS',mode)
print('REGRESSION_V189_PASS',mode,checks)
