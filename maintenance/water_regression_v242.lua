local templates=assert(loadfile(work..'/waters.lua'))()
local bindings=assert(loadfile(work..'/bindings.lua'))()
local keys={['攻击神水']='最大破坏',['自然神水']='最大自然',['灵魂神水']='最大灵魂',['疾风神水']='攻击速度',['体力强效神水']='最大生命',['魔法强效神水']='最大法力'}
local function clone(t)if type(t)~='table'then return t end;local r={};for k,v in pairs(t)do r[k]=clone(v)end;return r end
local function water_scene(story,name,marks,companion,old,water_override)
 local s=scene(story);local env=s.env;local raw=clone(templates[name]);raw['数量']=3;if water_override then raw['附加']=clone(templates['灵魂神水_小']['附加'])end
 for _,key in ipairs(basekeys)do raw['属性'][key]=0;raw['属性'][key..'_百分比']=0 end
 for _,key in ipairs(custom)do raw['属性'][key]=0 end
 raw['属性']['生命值_百分比']=0;raw['属性']['法力值_百分比']=0
 local owner={script_setting={['Gly独']={['错误']=function(msg)error(msg)end}},['包裹物品组']={[32]={['道具']=raw}}};local proxy=load('proxy',_G);debug.setupvalue(proxy,1,owner);owner['数据保护']=proxy
 owner['包裹物品组']=proxy(owner['包裹物品组'],true);local slots=owner['包裹物品组']
 local metadata=load('slot_info',env);debug.setupvalue(metadata,1,owner);env['Gly独']['取道具信息_格子']=metadata
 env['物品格子18']={['道具']=nil};env['Ux雌']['胚子考虑']=function()return{['行会选中']=marks or{}}end
 if companion then local c=scene(story);s.companion=c;if companion=='dead'then c.h['属性'].hp=0 end;env['Ux雌']['佣兵对象']=c.env['FXru胃啪']end
 local healing={};env['Ux雌']['主角红恢复量']=0;env['Ux雌']['主角蓝恢复量']=0
 env['Ux雌']['窗口相关']={['元素图标']=noop,['加血加蓝']=function(n,red)healing[#healing+1]={n,red}end}
 local eventenv={type=type,tonumber=tonumber,math=M,table=T,pairs=pairs,unpack=unpack,['Ux雌']=env['Ux雌'],['Gly独']=env['Gly独'],['FXru胃啪']=env['FXru胃啪'],['物品格子18']=env['物品格子18'],['分割文本']=split}
 eq(eventenv.pcall,nil);eq(eventenv._G,nil);eq(eventenv.Sys,nil)
 local binding=assert(bindings[name]);local script=load((old and'old_factory'or'factory')..binding.factory,eventenv)()
 eq(script.getself().id,name,'actual registered factory identity')
 local main=script.Main;eq(type(main),'function')
 raw['物品脚本']=script;slots[32]['道具']['物品脚本']=script
 local run0=env.Sys.run
 local hooks=0;local native={get=env.Sys.get,run=function(op,f,args,...)
  if op=='qs_item_box'then hooks=hooks+1;eq(f[1],3,'native inventory pre-use callback');return true,false end
  return run0(op,f,args,...)
 end}
 env.Sys=load('public_sys',env)(native)
 env['Q_鼠标']={['格子标识']=0,['物品来源']={}};s.h['BUFF状态更新']=noop
 local control={['道具CD组']={},['可用']=true,['标识']=32,['格子组']=slots,['Hero']=s.h,['tbl']={}}
 control['消耗']=load('consume',env)
 s.use=function()return load('inventory_use',env)(control)end
 s.main=main;s.slots=slots;s.template=raw;s.healing=healing;s.hooks=function()return hooks end
 s.clean=function()
  for key in pairs(keys)do s.h['清除状态'](s.h,key);if s.companion then s.companion.h['清除状态'](s.companion.h,key)end end
 end
 return s
end
local function verify_effect(s,add,multiplier,shared)
 local key=assert(keys[add['神水位置']]);local amount=add['效果']*multiplier
 local actual=key=='最大生命'and'maxhp'or key=='最大法力'and'maxmp'or key=='攻击速度'and'攻击速度倍数'or key
 eq(s.h['属性']['附加_'..actual],amount,'actual own-factory bonus')
 eq(state(s.h['BUFF组'][1])['状态说明']:find(tostring(amount),1,true)~=nil,true,'water tooltip actual amount');eq(state(s.h['BUFF组'][1])['状态说明']:find('增加：',1,true)~=nil,true,'water tooltip stat label');eq(#s.h['BUFF组'],1);eq(state(s.h['BUFF组'][1])['持续时间'],add['时间'])
 if shared then eq(s.companion.h['属性']['附加_'..actual],amount,'native companion bonus')elseif s.companion then eq(#s.companion.h['BUFF组'],0)end
 s.clean();eq(s.h['属性']['附加_'..actual],0,'no residual bonus')
end
local water_names={};for name,t in pairs(templates)do if t['附加']['神水位置']then water_names[#water_names+1]=name end end;table.sort(water_names);eq(#water_names,24)
local cases={{marks={},companion=false},{marks={},companion=true},{marks={['酒意同辉']=1},companion=false},{marks={['酒意同辉']=1},companion=true},{marks={['同饮共战']=1},companion=true},{marks={['酒意同辉']=1,['同饮共战']=1},companion='dead'}}
for _,story in ipairs({'前尘忆梦','来世续缘'})do
 for _,name in ipairs(water_names)do
  for _,case in ipairs(cases)do
   local s=water_scene(story,name,case.marks,case.companion,false)
   eq(s.use(),true);eq(s.hooks(),1);eq(s.slots[32]['道具']['数量'],2,'one item consumed')
   if story=='来世续缘'then
    verify_effect(s,s.template['附加'],case.marks['酒意同辉']and 2 or 1,case.companion==true and(case.marks['酒意同辉']or case.marks['同饮共战']))
   else eq(#s.h['BUFF组'],0,'original early-story branch preserved')end
  end
 end
end
-- Run the water-capable branch in ALL 49 real factories with valid water
-- metadata, rather than invoking a substituted Main against every template.
-- This also covers the branch if existing consumables carry saved water tags.
do
 local count=0
 for name in pairs(bindings)do
  local s=water_scene('来世续缘',name,{},false,false,true)
  eq(s.use(),true);eq(s.slots[32]['道具']['数量'],2)
  verify_effect(s,s.template['附加'],1,false);count=count+1
 end
 eq(count,49)
end
-- The 240 release fixed precisely two real template factories, leaving 22
-- real water items broken. Include the new uploaded 61411 error explicitly.
do
 local bad,good=0,0
 for _,name in ipairs(water_names)do
  local s=water_scene('来世续缘',name,{},false,true)
  local ok,err=pcall(s.use)
  if name=='灵魂神水_小'or name=='疾风神水_小'then
   eq(ok,true);eq(err,true);eq(s.slots[32]['道具']['数量'],2);good=good+1;s.clean()
  else
   eq(ok,false);eq(tostring(err):find('arithmetic',1,true)~=nil,true);eq(s.slots[32]['道具']['数量'],3,'failed old use not consumed');bad=bad+1
   if name=='体力强效神水_小'then eq(tostring(err):find('61411',1,true)~=nil,true);print('V240_USER_ERROR_REPRODUCED',tostring(err))end
  end
 end
 eq(bad,22);eq(good,2)
end
-- Non-water healing follows the actual own factory and is compared to 240.
-- The final regeneration request is a finite interface, not a Windows HP tick.
for _,name in ipairs({'金创药_小','金创药_中','金创药_大','金创药_特','金创药_特大','魔法药_小','魔法药_中','魔法药_大','魔法药_特','魔法药_特大','太阳水','强效太阳水','万年雪霜'})do
 local a=water_scene('来世续缘',name,{},false,true);local b=water_scene('来世续缘',name,{},false,false)
 eq(a.use(),true);eq(b.use(),true);eq(#a.healing,#b.healing)
 for i,row in ipairs(a.healing)do eq(row[1],b.healing[i][1]);eq(row[2],b.healing[i][2])end
 eq(a.slots[32]['道具']['数量'],b.slots[32]['道具']['数量'])
end
-- Preserve mounted/blocked and missing-slot behavior without item consumption.
do
 local s=water_scene('来世续缘','体力强效神水_小',{},false,false)
 s.env['物品格子18']['道具']={};eq(s.use(),false);eq(s.slots[32]['道具']['数量'],3);eq(#s.h['BUFF组'],0)
 s.env['物品格子18']['道具']=nil;s.slots[32]['道具']=nil;eq(s.main(32),true)
end
-- Warm the newly reported item's actual factory/closure through its actual
-- inventory/BUFF path; no manually selected sibling Main is used.
do
 local s=water_scene('来世续缘','体力强效神水_小',{},false,false)
 for i=1,200 do s.slots[32]['道具']['数量']=3;eq(s.use(),true);eq(s.slots[32]['道具']['数量'],2);verify_effect(s,s.template['附加'],1,false)end
end
print('WATER_V242_PASS',mode,checks)
