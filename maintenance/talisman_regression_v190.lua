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
 opts=opts or{};local merc_active=opts.merc~=false
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
 local owner={['角色组']={['爽不精英']={0,0,0,0,0,0,0,0,0}},['配置']={['主角格子']=slots},['游戏格子']=slots}
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
 return {f=f,slots=slots,hero=hero,merc=merc,native_merc=native_merc,U=U,S=S,env=env,owner=owner,messages=messages,native_env=native_env,T=T,
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
-- The supplied PC diagnosis is reproduced using the actual v189 closure.
for _,kind in ipairs({'小','中','大','特'})do
 for _,id in ipairs({12,408})do
  local old=make('old',id==12 and kind or nil,id==408 and kind or nil);old:storage(137)
  eq(old.slots[id]['道具']['附加']['最小储存'],0,'old legacy bug')
  local n=make('new',id==12 and kind or nil,id==408 and kind or nil);n:storage(137)
  eq(n.slots[id]['道具']['附加']['最小储存'],137);eq(n.hero['经验'],0);eq(n.merc['经验'],0)
 end
end
print('OLD_LEGACY_RETURN_REPRODUCED',mode)
for _,amount in ipairs({0,-1,math.huge,-math.huge,0/0,'5',false,'nil'})do
 local s=make('new','小','灵');local old=s:state();if amount=='nil'then s:storage(nil)else s:storage(amount)end;same(s:state(),old,'invalid storage XP ignored')
end
-- The one-jump correction restores the ORIGINAL single-owner legacy rules.
-- Compare all capacities, final use removal, fullness, old restrictions and
-- normal XP recursion against this independent, unrewritten reference.
for _,story in ipairs({'前尘忆梦','来世续缘'})do
 for _,kind in ipairs({'小','中','大','特'})do
  for _,id in ipairs({12,408})do
   for _,uses in ipairs({0,1,10})do
    for _,near in ipairs({false,true})do
     local a=make('new',id==12 and kind or nil,id==408 and kind or nil,{story=story})
     local b=make('reference',id==12 and kind or nil,id==408 and kind or nil,{story=story})
     for _,s in ipairs({a,b})do local v=s.slots[id]['道具']['附加'];v['最小次数']=uses;v['最小储存']=near and capacities[kind]-5 or 0;s:storage(17)end
     same(a:state(),b:state(),'original storage parity')
     for _,s in ipairs({a,b})do s:gain(31)end
     same(a:state(),b:state(),'normal XP and recursive storage parity')
    end
   end
  end
 end
end
-- Both legacy talismans retain hero-first selection, never a duplicated
-- legacy storage grant. The same applies with a dead/inactive owner.
for _,opts in ipairs({{}, {hero_dead=true}, {merc_dead=true}, {hero_dead=true,merc_dead=true},{merc=false}})do
 local a=make('new','小','大',opts);local b=make('reference','小','大',opts)
 a:storage(123);b:storage(123);same(a:state(),b:state(),'two legacy owners')
end
local a=make('new','小','大');a:storage(123);eq(a.slots[12]['道具']['附加']['最小储存'],123);eq(a.slots[408]['道具']['附加']['最小储存'],0)
-- Fullness releases one capacity and uses one charge; the existing original
-- overflow/no-carry rule is intentional here, not silently changed.
for _,kind in ipairs({'小','中','大','特'})do
 local s=make('new',kind,nil,{merc=false});local a=s.slots[12]['道具']['附加'];a['最小储存']=capacities[kind]-1
 s:storage(10);eq(a['最小储存'],0);eq(a['最小次数'],9);eq(s.hero['经验'],capacities[kind])
 s:storage(10);eq(a['最小储存'],10);eq(s.hero['经验'],capacities[kind],'no repeated release')
end
do
 local s=make('new','小',nil,{merc=false});local a=s.slots[12]['道具']['附加']
 local spare=rawcopy(s.slots[12]['道具']);spare['附加']['最小次数']=4;spare['附加']['最小储存']=123
 s.slots[31]['道具']=spare;a['最小次数']=1;a['最小储存']=499999
 s:storage(10);eq(s.slots[31]['道具'],nil);eq(s.slots[12]['道具']['附加']['最小次数'],4)
 eq(s.slots[12]['道具']['附加']['最小储存'],123);eq(s.hero['经验'],500000)
 s:storage(10);eq(s.slots[12]['道具']['附加']['最小储存'],133)
end
print('LEGACY_CAPACITY_CHARGES_FULLNESS_PRIORITY_PASS',mode)
-- Ling helpers and item-event code are byte-identical. Compare outcomes for
-- both owners, mixed equipment, fullness and the real manual item event.
for _,h in ipairs({'灵','none'})do for _,m in ipairs({'灵','none'})do
 local hk=h~='none'and h or nil;local mk=m~='none'and m or nil
 for _,near in ipairs({false,true})do
  local a=make('new',hk,mk);local b=make('old',hk,mk)
  for _,s in ipairs({a,b})do
   for _,id in ipairs({12,408})do local t=s.slots[id]['道具'];if t then t['附加']['最小储存']=near and 1999995 or 0 end end
   s:gain(11)
  end
  same(a:state(),b:state(),'Ling accumulation unchanged')
 end
end end
for _,kind in ipairs({'小','中','大','特'})do
 for _,hero_ling in ipairs({false,true})do
  local s=make('new',hero_ling and'灵'or kind,hero_ling and kind or'灵');s:storage(71)
  eq(s.slots[12]['道具']['附加']['最小储存'],71);eq(s.slots[408]['道具']['附加']['最小储存'],71)
  eq(s.hero['经验'],0);eq(s.merc['经验'],0,'mixed partial storage does not award XP')
 end
end
for _,hero_ling in ipairs({false,true})do
 local s=make('new',hero_ling and'灵'or'小',hero_ling and'小'or'灵')
 for _,id in ipairs({12,408})do local a=s.slots[id]['道具']['附加'];a['最小储存']=a['最大储存']-1 end
 s:storage(17);eq(s.hero['经验']+s.merc['经验'],2500000,'mixed full releases each capacity once')
 for _,id in ipairs({12,408})do eq(s.slots[id]['道具']['附加']['最小储存'],0)end
 s:storage(17);eq(s.hero['经验']+s.merc['经验'],2500000,'mixed no repeated full grant')
end
for _,id in ipairs({12,408})do
 local s=make('new',id==12 and'灵'or'小',id==408 and'灵'or'大')
 s:storage(51);local t=s.slots[id]['道具'];local before=s.hero['经验']+s.merc['经验']
 local event=load('item_event',s.env);event(3,id,t['名称'])
 local after=s.hero['经验']+s.merc['经验'];eq(after-before,50,'Ling split claim actual XP')
 eq(t['附加']['最小储存'],1,'odd XP remains');event(3,id,t['名称']);eq(s.hero['经验']+s.merc['经验'],after,'no duplicate claim')
end
print('LING_INDEPENDENT_MIXED_AND_MANUAL_CLAIM_PASS',mode)
-- Actual native item export preserves the existing storage/count fields.
-- This is a data round trip, explicitly not a full Windows save/load test.
for _,kind in ipairs({'小','中','大','特'})do
 local s=make('new',kind,nil);s.slots[12]['道具']['附加']['最小次数']=7;s:storage(246);local export=bind('export_item',s.S,s.native_env)
 local saved=s.T.copy(export(12),true);eq(saved['附加']['最小储存'],246);eq(saved['附加']['最小次数'],7)
 local next_session=make('new',kind,nil);next_session.slots[12]['道具']=saved;next_session:storage(10)
 eq(next_session.slots[12]['道具']['附加']['最小储存'],256);eq(saved['附加']['最小次数'],7)
end
-- Repeated real normal-XP -> recursive storage, switching equipment and empty
-- cells during trace side exits; verify exactly-once storage and normal XP.
for _,mixed in ipairs({false,true})do
 local s=make('new',mixed and'灵'or'特',mixed and'特'or'灵',{merc=false})
 for i=1,1000 do s:gain(3)end
 eq(s.hero['经验'],6000,'normal XP multiplier unchanged');eq(s.slots[12]['道具']['附加']['最小储存'],6000)
end
print('TALISMAN_V190_PASS',mode,count)
