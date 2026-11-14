local work,mode=arg[1],arg[2]or'normal'
if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end
local count=0
local function eq(a,b,why)count=count+1;assert(a==b,(why or'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function load(name,env)local f=assert(loadfile(work..'/'..name..'.ljbc'));setfenv(f,env or _G);return f end
local function bind(name,S,env)local f=load(name,env);debug.setupvalue(f,1,S);return f end
local configs=assert(loadfile(work..'/configs.lua'))()
local capacities={['小']=500000,['中']=2000000,['大']=5000000,['特']=10000000,['灵']=2000000}
local function rawcopy(t)
 if type(t)~='table'then return t end
 if rawget(t,'__p')~=nil then t=t()end
 local n={};for k,v in pairs(t)do n[k]=rawcopy(v)end;return n
end
local function make(which,hkind,mkind,opts)
 opts=opts or{};local merc_active=opts.merc~=false and not opts.gone
 local S={['script_setting']={},['屏幕事件组']={}}
 local proxy=bind('proxy',S);S['数据保护']=proxy
 local T={};for k,v in pairs(table)do T[k]=v end
 S.run=function(op,v,deep)assert(op=='数据保护',tostring(op));return proxy(v,deep)end
 local native_env=setmetatable({table=T,Sys=S},{__index=_G})
 load('table_register',native_env)()
 local function item(kind)
  if not kind then return nil end
  local a={}
  if kind=='灵'then a={['最小储存']=0,['最大储存']=2000000,['最小次数']=10,['最大次数']=10,['聚灵符咒']=2}
  else
   for k,v in configs[kind]:gmatch('([^ぃ]+)ぅ([^ぃ]+)ぃ')do a[k]=tonumber(v)or v end
   eq(a['最大储存'],capacities[kind]);eq(a['最小次数'],10);eq(a['最大次数'],10)
  end
  return {['名称']='聚灵符咒_'..kind,['显示名']='聚灵符咒('..kind..')',['数量']=1,['附加']=a,['属性']={},['分类']='装备',['子类']='符咒',['价格']=1000,['叠加']=0,['风格提示']={['宽度']=0,['高度']=0}}
 end
 local slots={};for i=1,500 do slots[i]={['拿起']=false}end
 slots[12]['道具']=item(hkind);slots[408]['道具']=item(mkind)
 slots=proxy(slots,true);S['包裹物品组']=slots
 local native_merc={id=50001,['属性']={['当前经验值']=0,['下级所需经验']=100000000,['等级']=21,hp=opts.merc_dead and 0 or 100},['宠物配置']={}}
 native_merc['事件回调']=function()return true,nil end -- engine callback boundary
 native_merc['EXP增加']=load('merc_exp')
 S['屏幕事件组']={native_merc}
 local hero={HP=opts.hero_dead and 0 or 100,['等级']=21,['经验']=0}
 local merc=bind('entity',S)(native_merc)
 S.get=bind('public_get',S);local public=load('public_sys')(S)
 local U={['版本选择']=opts.story or'来世续缘',['佣兵对象']=merc_active and merc or nil,['主角死亡惩罚']=0,['主角击杀经验']=0,['人物选择']=1}
 local owner={['角色组']=proxy({['爽不精英']={0,0,0,0,0,0,0,0,0},['佣兵']=opts.saved or {['生命值']=opts.merc_dead and 0 or 41,['法力值']=34,['经验值']=0,['等级']=21}},true),['配置']={['主角格子']=slots},['游戏格子']=slots}
 for key,name in pairs({['啾啾啵啵']=U['版本选择']=='前尘忆梦'and'role_a'or'role_b',['胚子考虑']=U['版本选择']=='前尘忆梦'and'config_a'or'config_b'})do U[key]=bind(name,owner,{['Ux雌']=U})end
 U['呦西鸽子']=bind('slots_get',owner);U['窗口相关']=owner
 local messages={};U['托管显示']={['屏幕提示']=function(s)messages[#messages+1]=s end}
 local G={['从ID取格子']=function(i)return slots[i]end,['取物品数量']=function(name)
  local n=0;for i=31,126 do local t=slots[i]['道具'];if t and t['名称']==name then n=n+t['数量']end end;return n
 end,['取按键状态']=function()return false end}
 local env={type=type,tonumber=tonumber,tostring=tostring,math=math,unpack=unpack,pairs=pairs,ipairs=ipairs,
 ['Sys']=public,['Ux雌']=U,['Gly独']=G,['FXru胃啪']=hero,['物品格子12']=slots[12],['物品格子408']=slots[408],['物品格子18']={},
 ['佣兵头像']={['可视']=merc_active},['佣兵经验选择框']={['选中']=true},['佣兵经验滑块条']={['位置']=50},['L常量']={['颜色_绿']=1}}
 eq(env.pcall,nil);eq(env.xpcall,nil);eq(env._G,nil)
 local register=bind('register_'..which,owner,env);register()
 local f=owner['经验获得'];eq(type(f),'function')
 for _,id in ipairs({12,408,31,32})do
  slots[id]['重置道具']=function(name,qty,flag,original)
   if name==nil then slots[id]['道具']=nil
   else assert(original,'unexpected item creation');local t=rawcopy(original);t['名称']=name;t['数量']=qty;slots[id]['道具']=proxy(t,true)end
  end
 end
 return {which=which,f=f,slots=slots,hero=hero,merc=merc,native_merc=native_merc,U=U,S=S,env=env,owner=owner,messages=messages,native_env=native_env,T=T,
 record=U['啾啾啵啵']()['佣兵'],
 storage=function(self,n)self.f(21,n,1,'聚灵符咒')end,
 gain=function(self,n)self.f(21,n,1)end,
 state=function(self)
  local a={hero=self.hero['经验'],merc=self.merc['经验']}
  for _,id in ipairs({12,408})do local t=self.slots[id]['道具'];a[id]=t and rawcopy(t['附加'])or false end
  return a
 end}
end
local function same(a,b,why)
 if type(a)~='table'then eq(a,b,why);return end
 eq(type(b),'table',why)
 for k,v in pairs(a)do same(v,b[k],(why or'')..'/'..tostring(k))end
 for k in pairs(b)do eq(a[k]~=nil,true,'extra '..tostring(k))end
end
local function click(s,id)
 local item=s.slots[id]['道具'];local event=load('item_event_'..s.which,s.env)
 local native={run=function(op,args)eq(op,'qs_item_box');return true,event(unpack(args))end}
 local use=load('grid_use',{Sys=native})
 local obj={['可用']=true,['格子组']=s.slots,['标识']=id,tbl={}}
 local q=item['数量'];eq(use(obj),false,'handled talisman event prevents default consumption');eq(item['数量'],q)
end
local function resume(s)
 s.native_merc['属性'].hp=100;s.U['佣兵对象']=s.merc;s.record['生命值']=41
 bind('mark_deployed',s.owner,s.env)(nil,nil,nil,s.U['啾啾啵啵']())
 bind('restore_flush',s.owner,s.env)(nil,nil,nil,s.U['啾啾啵啵']())
end
-- Previous v206 halves dead storage and splits/defer claims; reproduce first.
do
 local s=make('old',nil,'灵',{merc_dead=true,gone=true});s:gain(100)
 eq(s.slots[408]['道具']['附加']['最小储存'],100);eq(s.hero['经验'],200)
 s.slots[408]['道具']['附加']['最小储存']=101;click(s,408)
 eq(s.slots[408]['道具']['附加']['最小储存'],1);eq(s.hero['经验'],250);eq(s.record.__gm_talisman_pending_v206,50)
end
for _,story in ipairs({'前尘忆梦','来世续缘'})do
 for _,gone in ipairs({false,true})do
  for _,kind in ipairs({'灵','小','中','大','特'})do
   local s=make('new',nil,kind,{merc_dead=true,gone=gone,story=story});s:storage(100)
   eq(s.slots[408]['道具']['附加']['最小储存'],100,'dead owner gets full storage')
   eq(s.hero['经验'],0);eq(s.merc['经验'],0)
  end
 end
 for _,id in ipairs({12,408})do
  local s=make('new',id==12 and'灵'or nil,id==408 and'灵'or nil,{merc_dead=true,gone=true,story=story})
  local a=s.slots[id]['道具']['附加'];a['最小储存']=101;click(s,id)
  eq(s.hero['经验'],101);eq(a['最小储存'],0);eq(s.record.__gm_talisman_pending_v206,nil)
  click(s,id);eq(s.hero['经验'],101);eq(s.merc['经验'],0,'no repeat claim')
  resume(s);eq(s.hero['经验'],101);eq(s.merc['经验'],0,'no dead claim reserved for merc')
  resume(s);eq(s.hero['经验'],101);eq(s.merc['经验'],0)

 end
end
-- No deployment and positive-HP recruit record: storage stays disabled.
for _,kind in ipairs({'灵','小','中','大','特'})do
 local s=make('new',nil,kind,{merc=false});s:storage(100)
 eq(s.slots[408]['道具']['附加']['最小储存'],0);eq(s.record.__gm_talisman_pending_v206,nil)
end
-- Actual post-deployment marker enables later dead/offline accounting.
do
 local s=make('new',nil,'灵',{merc=false});bind('mark_deployed',s.owner,s.env)(nil,nil,nil,s.U['啾啾啵啵']())
 eq(s.record.__gm_talisman_summoned_v206,true)
 s.U['佣兵对象']=nil;s:storage(100);eq(s.slots[408]['道具']['附加']['最小储存'],100)
end
-- Preserve live behavior, XP distribution and independent Ling storage.
for _,h in ipairs({'none','灵','小'})do
 for _,m in ipairs({'灵','特'})do
  local old=make('old',h~='none'and h or nil,m);local new=make('new',h~='none'and h or nil,m)
  old:gain(100);new:gain(100)
  same(new:state(),old:state(),'live outcome parity')
 end
end
-- Legacy capacity/charges and hero-first selection retain their original rules.
for _,kind in ipairs({'小','中','大','特'})do
 local s=make('new',nil,kind,{merc_dead=true,gone=true})
 local a=s.slots[408]['道具']['附加'];a['最小储存']=capacities[kind]-1;s:storage(10)
 eq(a['最小储存'],0);eq(a['最小次数'],9);eq(s.hero['经验'],capacities[kind])
 local p=make('new','小',kind,{merc_dead=true,gone=true});p:storage(100)
 eq(p.slots[12]['道具']['附加']['最小储存'],100);eq(p.slots[408]['道具']['附加']['最小储存'],0,'legacy hero-first unchanged')
end
-- Both equipped Ling talismans auto-grant their full capacity to the hero
-- while the merc is dead; preserve the original one-capacity overflow rule.
for _,gone in ipairs({false,true})do
 local s=make('new','灵','灵',{merc_dead=true,gone=gone})
 for _,id in ipairs({12,408})do s.slots[id]['道具']['附加']['最小储存']=1999999 end
 s:storage(10);eq(s.hero['经验'],4000000);eq(s.merc['经验'],0)
 for _,id in ipairs({12,408})do eq(s.slots[id]['道具']['附加']['最小储存'],0)end
 eq(s.record.__gm_talisman_pending_v206,nil);resume(s);eq(s.merc['经验'],0)
end
-- Actual deep proxy export/recreation of a v206 balance; migrate once to hero,
-- whether first used while dead or during the original restore hook alive.
for _,dead in ipairs({false,true})do
 local s=make('new',nil,'灵',{merc_dead=true,gone=true})
 s.record.__gm_talisman_pending_v206=73
 local saved=s.T.copy(s.record,true)
 local restored=make('new',nil,'灵',{saved=saved,merc_dead=dead,gone=dead})
 if dead then restored:storage(1)else resume(restored)end
 eq(restored.hero['经验'],73);eq(restored.merc['经验'],0);eq(restored.record.__gm_talisman_pending_v206,0)
 resume(restored);eq(restored.hero['经验'],73);eq(restored.merc['经验'],0)
end
-- Hero talisman storage is identical with a living/dead merc in both versions.
for _,which in ipairs({'old','new'})do
 for _,kind in ipairs({'灵','小','中','大','特'})do
  local live=make(which,kind,'灵');local dead=make(which,kind,'灵',{merc_dead=true,gone=true})
  live:gain(100);dead:gain(100)
  eq(live.slots[12]['道具']['附加']['最小储存'],200)
  eq(dead.slots[12]['道具']['附加']['最小储存'],200)
 end
end
-- Death -> full claim -> revival -> original live split -> death again.
do
 local s=make('new','灵','灵',{merc_dead=true,gone=true})
 s.slots[12]['道具']['附加']['最小储存']=1;click(s,12);eq(s.hero['经验'],1)
 resume(s);s.slots[408]['道具']['附加']['最小储存']=101;click(s,408)
 eq(s.hero['经验'],51);eq(s.merc['经验'],50);eq(s.slots[408]['道具']['附加']['最小储存'],1)
 s.native_merc['属性'].hp=0;click(s,408)
 eq(s.hero['经验'],52);eq(s.merc['经验'],50);eq(s.slots[408]['道具']['附加']['最小储存'],0)
end
-- Original private setter acknowledgement: a refused grant keeps every balance.
do
 local s=make('new','灵','灵');local a=s.slots[12]['道具']['附加'];a['最小储存']=100
 local callback=s.native_merc['事件回调'];s.native_merc['事件回调']=function()return true,0 end
 click(s,12);eq(a['最小储存'],100);eq(s.hero['经验'],0);eq(s.merc['经验'],0)
 s.native_merc['事件回调']=callback;click(s,12);eq(a['最小储存'],0);eq(s.hero['经验'],50);eq(s.merc['经验'],50)
 local b=s.slots[408]['道具']['附加'];b['最小储存']=100;click(s,408);eq(s.hero['经验'],100);eq(s.merc['经验'],100)
 s.record.__gm_talisman_pending_v206=100;s.native_merc['事件回调']=function()return true,0 end
 resume(s);eq(s.record.__gm_talisman_pending_v206,0);eq(s.hero['经验'],200);eq(s.merc['经验'],100)
 resume(s);eq(s.hero['经验'],200);eq(s.merc['经验'],100)

end
-- One representative 200-call XP/claim/restore chain, not a Cartesian stress test.
do
 local s=make('new',nil,'灵',{merc_dead=true,gone=true});local a=s.slots[408]['道具']['附加']
 for i=1,200 do s:gain(3);if i%5==0 then click(s,408)end end
 eq(a['最小储存'],0);eq(s.record.__gm_talisman_pending_v206,nil);eq(s.hero['经验'],2400)
 resume(s);eq(s.merc['经验'],0);eq(s.hero['经验'],2400)
end
for _,v in ipairs({0,-1,math.huge,-math.huge,0/0,'10',false})do
 local s=make('new',nil,'灵',{merc_dead=true,gone=true});s:storage(v);eq(s.slots[408]['道具']['附加']['最小储存'],0)
end
print('TALISMAN_V207_PASS',mode,count,'full dead storage/hero claims, live parity and native proxy pending migration; no Windows save/load test')

