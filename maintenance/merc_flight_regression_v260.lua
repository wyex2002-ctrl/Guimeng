
-- Full native skill refresh -> decorative native projectile -> native sprite
-- wrapper. The engine/texture/map sinks below are finite and explicit.
do
local mathN={};for k,v in pairs(math)do mathN[k]=v end;mathN.round=function(x)return math.floor(x+.5)end
local function split(s,sep)local out={};if not s or s==''then return out end;local start=1;while true do local a,b=s:find(sep,start,true);if not a then out[#out+1]=s:sub(start);return out end;out[#out+1]=s:sub(start,a-1);start=b+1 end end
local encoded=assert(loadfile(work..'/encoded_configs.lua'))()
local function read(s,section,key,default)s=encoded[s]or s;for line in s:gmatch('[^\r\n]+')do local a,b=line:match('^(.-)=(.*)$');if a==key then return b end end;return default end
local entries=assert(loadfile(work..'/skill_entries.lua'))()
local materials={};local assets={};local effects={};local draws={};local bullets={};local damage={};local now=0
local texture={宽度=24,高度=40,指针='weapon-ground'}
local fallback={宽度=16,高度=24,指针='weapon-bag'}
local wrappedSprite=load('sprite_factory',N)
local rawsprites={}
N.__Sprite={创建=function(pointer,x,y,w,h)local p={pointer=pointer,w=w,h=h};rawsprites[#rawsprites+1]=p;return p end,
 置参照点=function(p,x,y)p.cx=x;p.cy=y end,置混合模式=function(p,m)p.mix=m end,置渲染色=function(p,c)p.color=c end,
 显示_高级=function(p,x,y,r,sx,sy)draws[#draws+1]={sprite=p,x=x,y=y,r=r,sx=sx,sy=sy,t=now}end,
 取宽度=function(p)return p.w end,取高度=function(p)return p.h end,销毁=function(p)p.dead=true end}
N.Q__={创建精灵=wrappedSprite,创建包围盒=function()return{置宽高=noop,置位置=noop}end}
N.__ed_debug=false;N.math=mathN
N.核心={取两点间角度=function(x,y,tx,ty)return math.deg(math.atan2(ty-y,tx-x))end,
 取两点间距离=function(x,y,tx,ty)return math.sqrt((tx-x)^2+(ty-y)^2)end,
 取移动步幅=function(deg)return math.cos(math.rad(deg)),math.sin(math.rad(deg))end,
 文件是否存在=function()return true end,读配置项_内存=read}
N.核心.按方向矩阵转换=load('rotate',N)
N.分割文本=split;N.__ResPath='';N.L常量={混合_默认=0}
N.Ae冻集={游戏素材组=materials,自定义属性表={},逻辑暂停=0,屏幕偏移={x=0,y=0},画面偏移={x=0,y=0}}
N.Q_地图={坐标到逻辑格子=function(x,y)return math.floor(x/48),math.floor(y/32)end,
 逻辑格子到坐标=function(x,y)return x*48,y*32 end,取格子信息=function()return{target}end,置格子信息=noop,
 范围内对象检测=function()error('visual projectile must never acquire or damage collision targets')end}
N.__Res=function(kind,path)assets[#assets+1]={kind,path};return{宽度=24,高度=40,指针=path}end
N.D2D_精灵={创建=function(image)return{置中心点=noop,source=image}end}
local factory=load('skill_factory',N);local actual={}
-- Actual original configuration parser performs effect list parsing. Its only
-- disk reader is a bounded INI bridge, not a desired-output skill mock.
local savedSys=N.Sys
N.Sys={run=function(op,fn)eq(op,'adds');return fn()end,add=function(kind,name,cfg)eq(kind,'技能配置')end}
for name,file in pairs(entries)do
 actual[name]=load(file,N)();eq(actual[name].名称,name);eq(actual[name].脚本.getself().id,name)
 for _,fx in ipairs(actual[name].目标动画)do local base=split(fx.动画,',')[1];materials[base]={地址=base}end
end
for _,file in ipairs(assert(loadfile(work..'/fireballs.lua'))())do local cfg=load(file,N)();actual[cfg.名称]=cfg end
N.Sys=savedSys
N.引擎={取运行时间=function()return now*1000 end}
N.特效类={创建=function(...)effects[#effects+1]={t=now,args={...}};return{}end}
publicmerc.属性={攻击速度=1};publicmerc.删除状态=noop
publicmerc.播放动作=function(...)effects[#effects+1]={t=now,args={'body',...}}end
N.Ux雌={佣兵对象=publicmerc,大堵塞就=function()return{}end,游戏音效={},游戏动画={},啾啾啵啵=function()return{佣兵={性别='男'}}end}
N.Gly独={从ID取对象=function(id)return id==merc.id and merc or target end,创建音效=function()return{播放=noop}end}
N.Gly独.创建动画=function()return{播放_绑定=function(...)effects[#effects+1]={t=now,args={'attached',...}}end}end
N.FXru胃啪={取状态列表=function()return{}end}

local dispatchState={shelp={},script_setting={Gly独={错误=function(e)error(e)end}}}
local dispatch=load('script_dispatch',N);debug.setupvalue(dispatch,1,dispatchState)
local function register_functions(t,seen)
 if type(t)~='table'then return end;seen=seen or{};if seen[t]then return end;seen[t]=true
 for _,v in pairs(t)do if type(v)=='function'then dispatchState.shelp[tostring(v)]={sid='native-test',msg='skill function'}elseif type(v)=='table'then register_functions(v,seen)end end
end
for _,cfg in pairs(actual)do register_functions(cfg.脚本)end
local public=load('public_sys',N)
N.Sys=public({get=function(key,name)if key=='hero'then return merc elseif key=='skill'then return actual[name]end;error(key)end,
 add=function(kind,b)if kind=='屏幕子弹'then bullets[#bullets+1]=b elseif kind=='屏幕特效'then return else error(kind)end end,
 run=function(op,fn,args,...)if op=='fun'then return dispatch(fn,args) elseif op=='显示特效'then effects[#effects+1]={t=now,args={'hit',fn,args,...}};return true,nil end;return true,nil end})
local oldenv=setmetatable({},{__index=N});load('mode_old',oldenv)(S,E);oldenv.__gm_merc_visual_factory_v255=load('flight_old',oldenv)
local newconstruct,oldconstruct=load('skill_construct',N),load('construct_old',oldenv)
local originalconstruct=load('construct_original',N)
merc.所属阵营='友方';merc.施法速度=1;merc.属性.hp=100;merc.属性.攻击速度倍数=10
merc.属性.中心Y偏移=20;merc.属性.模型大小=1;merc.击退信息={击退中=false,冲刺模式=false}
merc.播放音效=noop;merc.改变动作_=noop;merc.增加状态=noop;merc.删除状态=noop;merc.BUFF状态更新=noop;merc.本次动作残影=false
merc.地图坐标={x=0,y=32};merc.地图格子={x=0,y=1};merc.锚点x=0;merc.锚点y=0
merc.发生伤害=function(self,t,name,ratio,extra)damage[#damage+1]={t=now,target=t,name=name,ratio=ratio,extra=extra};return{1,0}end
merc.改变动作=noop
local nativeitem=load('item_initializer',N)
-- The artwork object matches the original item initialization argument; native
-- ground sprite is a separate D2D object, never the new projectile sprite.
N.D2D_精灵={创建=function(image)return{置中心点=noop,source=image}end}
local rangeditem=T.copy(ranged,true);rangeditem.地面图标=texture;rangeditem.图标=fallback
local memento={};S.游戏道具组[rangeditem.名称]=rangeditem
-- A real class method creates the factory on actor root registration earlier.
assert(type(N.__gm_merc_visual_factory_v255)=='function')
local function setweapon(item)S.包裹物品组[397]={道具=item,拿起=false};N.物品格子397=S.包裹物品组[397];merc.绑定技能=item and E.__gm_merc_binding_v253(item)or'刺客普通攻击'end
local function reset(dist)
 now=0;effects={};draws={};bullets={};damage={};target.属性.hp=100;target.已经消失=false;target.是否有效=true;merc.属性.hp=100
 target.地图格子={x=dist,y=1};target.地图坐标={x=dist*48,y=32};target.锚点x=0;target.锚点y=0;target.属性.中心Y偏移=20;target.属性.模型大小=1
end
local function run(which,name,item,dist,delta,opts)
 opts=opts or{};reset(dist);setweapon(item);N.dt=delta;local cfg=actual[name]
 local before_mp=publicmerc.MP
 local phase=(which=='old'and oldconstruct or which=='original'and originalconstruct or newconstruct)(merc,cfg,merc,target,0,{},0,1)
 local _,state=debug.getupvalue(phase.刷新,1)
 if state.raw then state=select(2,debug.getupvalue(state.raw,1))end
 local native_child=state.子弹;eq(native_child,nil,'combat projectile state remains untouched')
 local timing={state.起手动画延迟,state.命中动画延迟,state.伤害发生延迟,state.伤害进度[1]}
 local completed
 local retired=false;local retire_time;local arrival
 for frame=1,math.ceil(3/delta)do
  now=now+delta
  if opts.swap and frame==2 then setweapon(melee)end
  if opts.move and frame==2 then target.地图坐标.y=target.地图坐标.y+16 end
  if opts.die and frame==2 then target.属性.hp=0 end
  if opts.interrupt and frame==2 then merc.击退信息.击退中=true;merc.击退信息.冲刺模式=false end
  if not retired then completed=phase.刷新();if completed then retired=true;retire_time=now end end
  for _,b in ipairs(bullets)do b.更新();b.显示()end
  local shot=state.__gm_merc_visual_v255;if shot and shot.arrived and not arrival then arrival=now end
  local drained=true;for _,b in ipairs(bullets)do if not b.已经消失()then drained=false end end
  if retired and drained and frame>math.ceil(.4/delta)then break end
 end
 merc.击退信息.击退中=false
 for _,b in ipairs(bullets)do eq(b.已经消失(),true,'visual lifetime ends');b.销毁()end
 eq(publicmerc.MP,before_mp,'visual helper never consumes MP')
 local result={damage=damage,effects=effects,draws=draws,bullets=bullets,timing=timing,state=state,completed=completed,retire_time=retire_time,arrival=arrival}
 return result
end
local function samecombat(a,b,name,cancelled)
 eq(#a.damage,#b.damage,name..' damage count');if not cancelled then eq(#a.effects,#b.effects,name..' original FX count')end
 for i,x in ipairs(a.damage)do local y=b.damage[i];if name~='刺客普通攻击'then eq(x.t,y.t,'original active/melee damage time')end;eq(x.target,y.target);eq(x.name,y.name);eq(x.ratio,y.ratio)end
 for i,x in ipairs(cancelled and{}or a.effects)do local y=b.effects[i];if x.args[1]~='hit'then eq(x.t,y.t,name..' original body FX time')end;eq(#x.args,#y.args);for j,v in ipairs(x.args)do if type(v)~='table'and type(v)~='function'then eq(v,y.args[j],name..' original FX parameters')else eq(type(v),type(y.args[j]))end end end
 eq(a.timing[1],b.timing[1],name..' original startup');if not cancelled then eq(a.retire_time,b.retire_time,name..' native retirement deadline')end
 if b.arrival and #b.damage>0 then assert(b.damage[1].t>=b.arrival and b.damage[1].t<=b.arrival+1/15+1e-8,'damage synchronized with arrival')end
end
local names={'刺客普通攻击','蝉舞','月桂','红莲','白莲','盛开'}
for _,delta in ipairs({1/60,1/15})do for _,name in ipairs(names)do
 for _,item in ipairs({rangeditem,melee})do
  local old=run(name=='刺客普通攻击'and'old'or'original',name,item,6,delta);local new=run('new',name,item,6,delta)
  if name~='刺客普通攻击'then assert(#old.effects>=2,'original active hit FX must be exercised')end
  samecombat(old,new,name);eq(#new.bullets,item==rangeditem and name=='刺客普通攻击'and 1 or 0,'exactly one visual only for ranged')
  eq(#new.damage,1,name..' original single hit')
  if item==rangeditem and name=='刺客普通攻击'then
   assert(#new.draws>0,'visible flying sprite');eq(new.draws[1].sprite.pointer,'weapon-ground','actual ground artwork preferred')
   assert(#new.draws>2,'several spinning travel frames')
   for i=2,#new.draws do local a,b=new.draws[i-1],new.draws[i]
    assert(math.abs((b.r-a.r)-delta*math.pi*24)<1e-8,'twelve full turns per second at native render boundary')
    assert(a.x~=b.x or a.y~=b.y,'translation and rotation occur together')
   end
   eq(new.draws[1].sprite.cx,12,'rotate about texture horizontal center');eq(new.draws[1].sprite.cy,20,'rotate about texture vertical center')
   eq(#old.draws,#new.draws,'same travel duration')
   for i,draw in ipairs(old.draws)do local fresh=new.draws[i]
    assert(math.abs(fresh.r-draw.r)<1e-8,'exact twelve turns per second')
    eq(fresh.x,draw.x,'same flight x');eq(fresh.y,draw.y,'same flight y');eq(fresh.t,draw.t,'same flight time')
   end
   eq(new.state.子弹,nil,'visual never becomes skill damage projectile')
  else eq(#new.draws,0,'melee adds no projectile')end
 end
end end
for _,dist in ipairs({1,3,6})do local a=run('old','刺客普通攻击',rangeditem,dist,1/60);local b=run('new','刺客普通攻击',rangeditem,dist,1/60);samecombat(a,b,'range '..dist);eq(#b.bullets,1)end
-- Fast attacks/low FPS keep an artwork frame without delaying a hit.
for _,speed in ipairs({5,25,100})do for _,delta in ipairs({1/60,1/15})do
 merc.属性.攻击速度倍数=speed
 local a=run('old','刺客普通攻击',rangeditem,6,delta);local b=run('new','刺客普通攻击',rangeditem,6,delta)
 samecombat(a,b,'speed/frame boundary');eq(#b.bullets,1);assert(#b.draws>0,'fast throw remains visible')
end end;merc.属性.攻击速度倍数=10
local genericitem=T.copy(generic,true);genericitem.地面图标=nil;genericitem.图标=nil
S.游戏道具组[genericitem.名称]={地面图标=texture}
local b=run('new','刺客普通攻击',genericitem,6,1/60);eq(#b.bullets,1);eq(b.draws[1].sprite.pointer,'weapon-ground','default companion weapon uses native template art')
local bagimage=T.copy(rangeditem,true);bagimage.地面图标=nil;S.游戏道具组[bagimage.名称]={图标=fallback}
local b=run('new','刺客普通攻击',bagimage,6,1/60);eq(#b.bullets,1);eq(b.draws[1].sprite.pointer,'weapon-bag','bag art fallback')
S.游戏道具组[rangeditem.名称]=rangeditem
for _,opts in ipairs({{move=true},{swap=true},{die=true},{interrupt=true}})do
 local a=run('original','月桂',rangeditem,6,1/60,opts);local b=run('new','月桂',rangeditem,6,1/60,opts);samecombat(a,b,'lifecycle',opts.die or opts.interrupt)
end
-- Zero artwork degrades to the original combat path; default generic weapons
-- use their own template art, while other actors receive no decorative flight.
local noimage=T.copy(rangeditem,true);noimage.地面图标=nil;noimage.图标=nil;S.游戏道具组[noimage.名称]=noimage
local a=run('old','刺客普通攻击',noimage,6,1/60);local b=run('new','刺客普通攻击',noimage,6,1/60);samecombat(a,b,'missing optional image');eq(#b.bullets,0)
S.游戏道具组[rangeditem.名称]=rangeditem
local saved=merc.id;merc.id=88;local b=run('new','刺客普通攻击',rangeditem,6,1/60);eq(#b.bullets,0,'other actor unchanged');merc.id=saved
-- Real original projectile damage method is absent in the private constructor.
-- Force its collision/arrival hooks with a throwing damage method and map query.
local stored=merc.发生伤害;merc.发生伤害=function()error('visual duplicate damage')end
target.地图坐标={x=48,y=0}
local p=N.__gm_merc_visual_factory_v255(0,0,48,0,200,merc,target,'图片',texture,false,noop,{},nil,'敌方',0,{技能名称='刺客普通攻击',穿透模式=1,渐入=0,渐出=0,子弹射程=800})
for i=1,10 do N.dt=.05;p.更新();p.显示()end;eq(p.已经消失(),true);p.销毁();merc.发生伤害=stored
-- Current story chooses its real fireball definition. Speed is not tied
-- to target distance or attack-speed multipliers anymore.
for _,story in ipairs({'归梦','前尘忆梦'})do
 E.Ux雌.版本选择=story
 local base=actual[story=='前尘忆梦'and'Q火球术'or'火球术'].子弹速度
 eq(base,story=='前尘忆梦'and 350 or 450)
 local flight=run('new','刺客普通攻击',rangeditem,6,1/60)
 eq(flight.state.__gm_merc_visual_v255.speed,base*1.2)
 assert(flight.arrival>.3,'visible slower six-cell travel')
 assert(#flight.draws>=15,'multiple visible travel frames')
end
E.Ux雌.版本选择='归梦'
-- Native continue/start/skill construction and the original actor skill loop
-- determine release admission, queue removal and cleanup. Only the engine
-- clock, body animation and outer frame collection are finite bridges.
local begin_attack=load('begin_attack',N);local begin_skill=load('begin_skill',N);local skillloop=load('skill_loop',N)
local continuation=load('attack',N)
N.核心.取两点间方向=function()return 1 end
local function continuous(which)
 reset(6);setweapon(rangeditem);N.dt=1/60
 merc.属性.攻击速度=1;merc.属性.攻击速度倍数=100;merc.属性.禁攻击=false
 merc.攻击速度_计次=0;merc.攻击来源=target;merc.临时绑定技能=nil;merc.释放技能组={};merc.BUFF组={}
 merc.当前状态=0;merc.上次状态=0;merc.抵达目标点=true;merc.剧情表={}
 merc.保持目标距离=function()return false end;merc.事件回调=function()return true,nil end
 merc.改变动作_=function(self,state)self.当前状态=state end
 merc.开始攻击=begin_attack;merc.技能开始=begin_skill
 local casttimes={};local maxactive=0;local retired={};local original=which=='old'and oldconstruct or newconstruct
 merc.技能释放=function(self,...)
  casttimes[#casttimes+1]=now
  return original(self,...)
 end
 for frame=1,1320 do
  now=now+N.dt
  if now<=20 then
   merc.攻击速度_计次=merc.攻击速度_计次+N.dt
   continuation(merc)
  end
  skillloop(merc)
  local live=0
  for i=#bullets,1,-1 do local b=bullets[i];b.更新();b.显示();if b.已经消失()then b.销毁();table.remove(bullets,i)else live=live+1 end end
  maxactive=math.max(maxactive,live)
 end
 eq(#merc.释放技能组,0,'native skill queue drained');eq(#bullets,0,'retired flight queue drained')
 eq(#damage,#casttimes,'one native damage result for every admitted attack')
 return{casts=casttimes,damage=damage,maxactive=maxactive,first=damage[1].t,last=damage[#damage].t}
end
local before=continuous('old');local after=continuous('new')
eq(#before.casts,#after.casts,'unchanged sustained release count')
for i,t in ipairs(before.casts)do eq(t,after.casts[i],'unchanged native attack admission time')end
eq(#before.damage,#after.damage,'all damage retained after draining flights')
for i,x in ipairs(before.damage)do local y=after.damage[i];eq(x.name,y.name);eq(x.ratio,y.ratio);eq(x.target,y.target)end
eq(after.first,before.first,'first hit timing preserved')
for i,x in ipairs(before.damage)do eq(x.t,after.damage[i].t,'every hit timing preserved')end
assert(after.maxactive>=3,'multiple in-flight attacks never block next cast')
local spanA=before.last-before.first;local spanB=after.last-after.first
assert(math.abs(spanA-spanB)<1/60+1e-7,'same stable damage rate after travel latency')
print('MERC_DPS_V260_PASS',mode,#after.casts,'casts',after.maxactive,'simultaneous flights','old/new damage spans',spanA,spanB)
print('MERC_VISUAL_V260_PASS',mode,'native arrival delivery and nonblocking attack pipeline')
end
