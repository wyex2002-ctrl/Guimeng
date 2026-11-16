local templates=assert(loadfile(work..'/waters.lua'))()
local keys={['攻击神水']='最大破坏',['自然神水']='最大自然',['灵魂神水']='最大灵魂',['疾风神水']='攻击速度',['体力强效神水']='最大生命',['魔法强效神水']='最大法力'}
local function clone(t)if type(t)~='table'then return t end;local r={};for k,v in pairs(t)do r[k]=clone(v)end;return r end
local function water_scene(story,name,marks,companion,old,script_idx)
 local s=scene(story);local env=s.env;local raw=clone(templates[name]);raw['数量']=3
 for _,key in ipairs(basekeys)do raw['属性'][key]=0;raw['属性'][key..'_百分比']=0 end
 for _,key in ipairs(custom)do raw['属性'][key]=0 end
 raw['属性']['生命值_百分比']=0;raw['属性']['法力值_百分比']=0
 local owner={script_setting={['Gly独']={['错误']=function(msg)error(msg)end}},['包裹物品组']={[32]={['道具']=raw}}};local proxy=load('proxy',_G);debug.setupvalue(proxy,1,owner);owner['数据保护']=proxy
 owner['包裹物品组']=proxy(owner['包裹物品组'],true);local slots=owner['包裹物品组']
 local metadata=load('slot_info',env);debug.setupvalue(metadata,1,owner);env['Gly独']['取道具信息_格子']=metadata
 env['物品格子18']={['道具']=nil};env['Ux雌']['胚子考虑']=function()return{['行会选中']=marks or{}}end
 if companion then local c=scene(story);s.companion=c;env['Ux雌']['佣兵对象']=c.env['FXru胃啪']end
 env['Ux雌']['窗口相关']={['元素图标']=noop}
 local eventenv={type=type,tonumber=tonumber,math=M,table=T,pairs=pairs,unpack=unpack,['Ux雌']=env['Ux雌'],['Gly独']=env['Gly独'],['FXru胃啪']=env['FXru胃啪'],['物品格子18']=env['物品格子18']}
 eq(eventenv.pcall,nil);eq(eventenv._G,nil);eq(eventenv.Sys,nil)
 local idx=script_idx or 1259
 local main=load((old and'water_old'or'water')..idx,eventenv);debug.setupvalue(main,1,{})
 raw['物品脚本']={Main=main};slots[32]['道具']['物品脚本']={Main=main}
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
 s.main=main;s.slots=slots;s.template=raw;s.hooks=function()return hooks end
 s.clean=function()
  for key in pairs(keys)do s.h['清除状态'](s.h,key);if s.companion then s.companion.h['清除状态'](s.companion.h,key)end end
 end
 return s
end
for _,script_idx in ipairs({1256,1259})do
for _,story in ipairs({'前尘忆梦','来世续缘'})do
 for name,template in pairs(templates)do
  for _,marks in ipairs({{}, {['酒意同辉']=1}})do
   local s=water_scene(story,name,marks,true,false,script_idx)
   local before=s.slots[32]['道具']['数量'];eq(s.use(),true,'real native inventory use succeeds');eq(s.hooks(),1);eq(s.slots[32]['道具']['数量'],before-1,'consume once')
   local add=template['附加'];local key=keys[add['神水位置']];local expected=add['效果']*(marks['酒意同辉']and 2 or 1)
   local actual=key=='最大生命'and'maxhp'or key=='最大法力'and'maxmp'or key=='攻击速度'and'攻击速度倍数'or key
   if story=='来世续缘'then
   eq(s.h['属性']['附加_'..actual],expected,'native correct effect and multiplier')
   eq(#s.h['BUFF组'],1);local info=state(s.h['BUFF组'][1]);eq(info['持续时间'],add['时间'],'original duration preserved')
   if marks['酒意同辉']then eq(s.companion.h['属性']['附加_'..actual],expected,'existing companion guild effect')else eq(#s.companion.h['BUFF组'],0)end
   s.clean();eq(s.h['属性']['附加_'..actual],0,'native cleanup removes amount')
   else eq(#s.h['BUFF组'],0,'original early-story no-op retained')end
  end
 end
 -- Invalid slot and cooldown keep original false/nil conventions, no consume.
 local s=water_scene(story,'灵魂神水_小',{},false);s.slots[32]['道具']=nil;eq(s.main(32),true)
end
end
-- Old bytecode reproduces an arithmetic failure with the original valid
-- template/proxy and default guild state. Numeric x2 path was already valid.
do
 for _,idx in ipairs({1256,1259})do
 local s=water_scene('来世续缘','灵魂神水_小',{},false,true,idx)
 local ok,err=pcall(s.use);eq(ok,false,'old missing multiplier reproduces');eq(tostring(err):find('arithmetic',1,true)~=nil,true);eq(s.slots[32]['道具']['数量'],3,'failed use not consumed')
 print('OLD_WATER_ERROR_REPRODUCED',tostring(err))
end
end
-- One representative path repeatedly applies, consumes and clears through
-- the native APIs; hot-loop repetition does not leave old state increments.
do
 local s=water_scene('来世续缘','灵魂神水_小',{},false)
 for i=1,200 do s.slots[32]['道具']['数量']=3;eq(s.use(),true);eq(s.slots[32]['道具']['数量'],2);eq(s.h['属性']['附加_最大灵魂'],s.template['附加']['效果']);s.clean()end
end
print('WATER_V240_PASS',mode,checks)
