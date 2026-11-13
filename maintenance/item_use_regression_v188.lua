local work,mode=arg[1],arg[2]or 'normal'
if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end
local count=0
local function eq(a,b,msg)count=count+1;assert(a==b,(msg or'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function load(name,env)local f=assert(loadfile(work..'/'..name..'.ljbc'));setfenv(f,env or _G);return f end
local function make(version,kind,result,proxy)
 local logs,hooks={},{};local consumed=0
 local bad={['道具']={['名称']='药水'}}
 if kind=='entry'then bad=42 elseif kind=='item'then bad['道具']=42 elseif kind=='empty'then bad=nil end
 local slots={[31]=bad,[32]={['道具']={['名称']='药水',['任务关联']=true,['剧情关联']=true,['数量']=10}}}
 local S={['Hero']={['背包格子']={{31,0,true},{32,0,true}}},['包裹物品组']=slots,script_setting={}}
 if proxy then local wrap=load('proxy');debug.setupvalue(wrap,1,S);S['数据保护']=wrap;S['包裹物品组']=wrap(slots,true)end
 S.__gm_detail_v179=function(stage,msg,critical)logs[#logs+1]={stage,msg,critical}end
 local controls={}
 for _,id in ipairs({31,32})do
  local c={['类型']=6,['对象']={['使用物品']=function()consumed=consumed+1;return result end}}
  if kind=='cleared'and id==31 then setmetatable(c,{__index=function(_,key)if key=='格子ID'then slots[31]['道具']=42;return 31 end end})else c['格子ID']=id end
  controls[#controls+1]=c
 end
 S['界面_窗口_数组']={{['控件组']=controls}}
 S['脚本关联处理']=function(...)hooks[#hooks+1]={...}end
 local f=load('use_'..version);debug.setupvalue(f,1,S)
 local getter=load('public_get');debug.setupvalue(getter,1,S);S.get=getter
 local public=load('public_sys')(S)
 return {S=S,slots=slots,f=f,logs=logs,hooks=hooks,public=public,consumed=function()return consumed end}
end
for _,kind in ipairs({'entry','item','cleared'})do
 local s=make('old',kind,true);local ok,err=pcall(s.f,'药水');eq(ok,false);eq(type(err),'string');eq(err:find('number value',1,true)~=nil,true)
 print('OLD_ITEM_ERROR_REPRODUCED',mode,kind,err)
 for _,proxy in ipairs({false,true})do
  local n=make('new',kind,true,proxy);eq(n.f('药水'),true);eq(n.consumed(),1);eq(#n.logs,1)
  eq(n.logs[1][1],'item.use.invalid');eq(n.logs[1][2]:find('type=number',1,true)~=nil,true);eq(n.logs[1][3],true)
  eq(n.S.get('__gm_item_invalid_v188'),nil,'private diagnostic state remains hidden')
  for i=1,50 do n.f('药水')end;eq(#n.logs,1,'bounded invalid log')
 end
end
for _,value in ipairs({true,false,'nil'})do
 for _,version in ipairs({'old','new'})do
  local expected=value;if value=='nil'then expected=nil end
  local s=make(version,'empty',expected,true);eq(s.f('药水'),expected);eq(s.consumed(),1);eq(#s.logs,0)
  eq(#s.hooks,value==true and 2 or 0)
  if value==true then eq(s.hooks[1][1],'物品使用_脚本');eq(s.hooks[2][2],1)end
  eq(s.f('不存在的药'),false);eq(s.consumed(),1)
  local err={tag='original control failure'};s.S['界面_窗口_数组'][1]['控件组'][2]['对象']['使用物品']=function()error(err,0)end
  local ok,e=pcall(s.f,'药水');eq(ok,false);eq(e,err,'original errors propagate')
 end
end
-- Reproduce the complete auxiliary -> selected quick slot -> original database
-- quick-item event -> native inventory lookup chain, including both stories.
local function nested(version,story,broken)
 local consumed=0;local id=story=='前尘忆梦'and 1 or 21
 local quick={['道具']={['名称']='药水',['附加']={['加血']=true,['快捷物品']=true}}}
 local real={['道具']={['名称']='药水',['数量']=5,['附加']={}}}
 local slots={[id]=quick,[31]=broken and 42 or nil,[32]=real}
 local S={sid=0,shelp={},script_setting={},['包裹物品组']=slots,['Hero']={['背包格子']={{31,0,true},{32,0,true}}}}
 local logs={};S.__gm_detail_v179=function(tag,msg)logs[#logs+1]=tag..' '..msg end
 local f=load('use_'..version);debug.setupvalue(f,1,S)
 local U={['版本选择']=story,['主角HP']=5,['主角MAXHP']=100,['人物选择']=1,['托管显示']={['屏幕提示']=function()error('unexpected gameplay gate')end}}
 local owner={['角色组']={['法治观念']=true},['配置']={['主角格子']=slots},['游戏格子']=slots}
 for key,name in pairs({['啾啾啵啵']=story=='前尘忆梦'and'role_a'or'role_b',['胚子考虑']=story=='前尘忆梦'and'config_a'or'config_b'})do
  local g=load(name,{['Ux雌']=U});debug.setupvalue(g,1,owner);U[key]=g
 end
 local slots_get=load('slots_get');debug.setupvalue(slots_get,1,owner);U['呦西鸽子']=slots_get
 local G={['使用物品']=f,['从ID取格子']=function(i)return slots[i]end,['取按键状态']=function()return false end,
 ['取物品数量']=function(name)if name=='药水'then return real['道具']['数量']end;return 0 end}
 local getter=load('public_get');debug.setupvalue(getter,1,S);S.get=getter
 local public=load('public_sys')(S)
 local env={type=type,['Sys']=public,['Ux雌']=U,['Gly独']=G,['物品格子18']={['道具']=nil},['FXru胃啪']={HP=100,['取状态列表']=function()return{}end},['加红选择框']={['选中']=false},['加红滑块条']={['位置']=50},['L常量']={},['仓库窗口2']={['可视']=false},['信息窗口2']={['可视']=false},['聊天输入框']={['焦点']=false},['英雄HP输入框']={['焦点']=false},['英雄MP输入框']={['焦点']=false}}
 for _,name in ipairs({'仓库窗口','佣兵窗口','商店窗口','行会仓库','信息窗口'})do env[name]={['可视']=false}end
 eq(env.pcall,nil);eq(env.xpcall,nil);eq(env._G,nil)
 local event=load('item_event',env);S.shelp[tostring(event)]={sid=5,msg='actual item event'}
 local event_error;S.script_setting['Gly独']={['错误']=function(e)event_error=e end}
 local dispatch=load('dispatch');debug.setupvalue(dispatch,1,S);S.fun=dispatch
 local aux=load('aux',env);U['窗口相关']={['辅助窗口']=aux};debug.setupvalue(aux,1,U['窗口相关'])
 local controls={}
 controls[1]={['类型']=6,['格子ID']=id,['对象']={['使用物品']=function()
  local ok,r=dispatch(event,{3,id,nil,0,{}},0);if not ok then error(event_error or r,0)end;eq(ok,true,'real dispatcher');return r
 end}}
 controls[2]={['类型']=6,['格子ID']=32,['对象']={['使用物品']=function()consumed=consumed+1;real['道具']['数量']=real['道具']['数量']-1;return true end}}
 S['界面_窗口_数组']={{['控件组']=controls}}
 local ok,err=pcall(aux,'加油',0)
 return ok,err,consumed,real['道具']['数量'],logs
end
for _,story in ipairs({'前尘忆梦','来世续缘'})do
 for _,version in ipairs({'old','new'})do
  local ok,e,n,q=nested(version,story,false);assert(ok,e);eq(n,1);eq(q,4)
 end
 local old_ok,old_error=nested('old',story,true);eq(old_ok,false);eq(tostring(old_error):find('number value',1,true)~=nil,true)
 local ok,e,n,q,logs=nested('new',story,true);assert(ok,e);eq(n,1);eq(q,4);eq(#logs,1)
end
-- A broken diagnostic writer cannot make a bad slot terminate item use.
do local s=make('new','entry',true);s.S.__gm_detail_v179=function()error('disk unavailable')end;eq(s.f('药水'),true)end
-- Fixed-arity native calls must not format unused extra-argument registers.
do
 local s=make('new','cleared',true);s.slots[1]=s.slots[31]
 local c=s.S['界面_窗口_数组'][1]['控件组'][1]
 setmetatable(c,{__index=function(_,k)if k=='格子ID'then s.slots[1]['道具']=42;return 1 end end})
 local poison=setmetatable({},{__tostring=function()error('unused argument stringification')end})
 local ok,r=pcall(s.f,'药水',{__gm_autopotion_slot_v142=1},nil,nil,nil,poison)
 eq(ok,true);eq(r,false);eq(#s.logs,1);eq(s.logs[1][2]:find('requested_slot=1',1,true)~=nil,true)
end
print('ITEM_USE_REGRESSION_PASS',mode,count)
