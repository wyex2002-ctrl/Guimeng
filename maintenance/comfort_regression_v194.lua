local work,mode=arg[1],arg[2]or'normal'
if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end
local checks=0
local function eq(a,b,label)checks=checks+1;assert(a==b,(label or'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function load(n,env)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,env or _G);return f end
local function copy(v)
 if type(v)~='table'then return v end
 if rawget(v,'__p')~=nil then v=v()end
 local t={};for k,x in pairs(v)do t[k]=copy(x)end;return t
end
local config=load('config')();eq(config['极品数值']['身体舒适'],0.2,'existing coefficient')
local configs=assert(loadfile(work..'/shoes.lua'))()
local function setup(raw)
 local base=copy(raw);base['附加']={['等级']=40,['商店']='防具店'};base['属性']={}
 -- These are the engine's numeric equipment fields, explicitly initialized;
 -- there is no catch-all metatable returning zero for arbitrary lookups.
 for k in pairs(config['极品数值'])do base[k]=base[k]or 0;base['属性'][k]=base[k]end
 for _,k in ipairs({'身体舒适','物品腕力','物品重量','穿戴肩力','武器腕力'})do base['属性'][k]=0 end
 local S={};local proxy=load('proxy');debug.setupvalue(proxy,1,S);S['数据保护']=proxy;S['游戏道具组']=proxy({[base['名称']]=base},true)
 local info=load('item_info',{table={copy=copy},pairs=pairs});debug.setupvalue(info,1,S)
 local U={['独角兽下']=function()return config end,['胚子考虑']=function()return{['装备操作']=0}end,['啾啾啵啵']=function()return{['职业']='战士',['等级']=100,['性别']='男',['人物选择']=1}end}
 local env={type=type,tonumber=tonumber,tostring=tostring,pairs=pairs,ipairs=ipairs,math=math,string=string,table={copy=copy,remove=table.remove},['Ux雌']=U,['Gly独']={['取道具信息_名称']=info,['取随机数']=function(a,b)return math.random(a,b)end},['物品格子18']={},['商店窗口']={['可视']=false},['商店窗口2']={['可视']=false},['格式化数值']=tostring,['L常量']={},['FXru胃啪']={['职业']='战士',['性别']='男',['等级']=100}}
 return base,info,load('gen',env),load('tip_old',env),load('tip',env)
end
math.randomseed(194);local generated=0;local representative
for index,raw in ipairs(configs)do
 local base,info,gen,old,new=setup(raw);local example
 local limit=index==1 and 200 or 1
 for i=1,limit do
  local item=copy(info(base['名称']));gen(item,40,3)
  eq(item['自动回血']or 0,base['自动回血']or 0,'no random HP regen');eq(item['自动回蓝']or 0,base['自动回蓝']or 0,'no random MP regen')
  if(item['身体舒适']or 0)>0 then
   generated=generated+1;example=item
   local before=item['身体舒适'];local text=new(item,1,32)
   eq(text:find('舒适:'..before,1,true)~=nil,true,'generated comfort visible');eq(item['身体舒适'],before,'render is read-only')
  end
 end
 if index==1 then
  assert(example,'comfort must actually be generated in bounded sample')
  eq(old(example,1,32):find('舒适:',1,true),nil,'old full tooltip omits generated stat')
  representative={example,new}
 end
 -- Existing equipment values, base contribution, zero/absent and identification.
 local item=copy(info(base['名称']));item['身体舒适']=6;item['附加']['条数']=3
 eq(new(item,1,32):find('舒适:6',1,true)~=nil,true,'existing item visible')
 item['身体舒适']=0;eq(new(item,1,32):find('舒适:',1,true),nil,'no zero placeholder')
 item['身体舒适']=nil;eq(new(item,1,32):find('舒适:',1,true),nil,'missing stat safe')
 item['身体舒适']=6;item['附加']['鉴定']=1;eq(new(item,1,32):find('舒适:6',1,true),nil,'old identification gate retained')
 item['附加']['鉴定']=nil;base['属性']['身体舒适']=2;item['身体舒适']=5
 local text=new(item,1,32);eq(text:find('舒适:5',1,true)~=nil,true);eq(text:find('(+3)',1,true)~=nil,true,'base/bonus split')
end
-- Bounded repeated render stresses the changed display path only.
local item,new=unpack(representative)
for i=1,200 do eq(new(item,1,32):find('舒适:',1,true)~=nil,true)end
print('COMFORT_V194_PASS',mode,'checks',checks,'generated_comfort',generated)
