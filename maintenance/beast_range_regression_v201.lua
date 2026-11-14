local work,mode=arg[1],arg[2]or'normal'
if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end
local checks=0
local function eq(a,b,label)checks=checks+1;assert(a==b,(label or'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function load(n,env)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,env or _G);return f end
local function bind(n,owner,env)local f=load(n,env);debug.setupvalue(f,1,owner);return f end
local function copy(t)local o={};for k,v in pairs(t)do o[k]=type(v)=='table'and copy(v)or v end;return o end
local function split(s,sep)
 local t={};local at=1;s=s or'';if s==''then return t end
 while true do local a,b=string.find(s,sep,at,true);if not a then t[#t+1]=string.sub(s,at);return t end;t[#t+1]=string.sub(s,at,a-1);at=b+1 end
end
local cfg=assert(loadfile(work..'/configs.lua'))()
local function read(s,section,key,default)
 eq(section,'配置');for line in string.gmatch(s,'[^\r\n]+')do local a,b=string.match(line,'^(.-)=(.*)$');if a==key then return b end end;return default
end
local captured={};local sprite={['置中心点']=function()end}
local factory_env={tonumber=tonumber,math=math,table=table,string=string,['分割文本']=split,['核心']={['读配置项_内存']=read},['Ae冻集']={['自定义属性表']={},['游戏素材组']={}},['D2D_精灵']={['创建']=function()return sprite end},['Sys']={add=function(kind,name,value)captured[name]=value end}}
factory_env['核心']['按方向矩阵转换']=load('rotate',factory_env)
local sf=load('skill_factory',factory_env);local af=load('attr_factory',factory_env)
local attacks={};local beast_attributes={}
for name,c in pairs(cfg)do
 if string.find(name,'攻击',1,true)then
  local before=sf(0,0,nil,nil,name,'魔法','',c.old);local after=sf(0,0,nil,nil,name,'魔法','',c.new)
  eq(before['施法距离'],1);eq(after['施法距离'],2);eq(before['冷却时间'],after['冷却时间']);eq(before['伤害延迟'],after['伤害延迟']);eq(#before['状态变化_增加_目标'],#after['状态变化_增加_目标']);attacks[name]=after
 else
  af(name,name,c.old,{});local before=captured[name];af(name,name,c.new,{});local after=captured[name]
  eq(before['攻击距离'],1);eq(after['攻击距离'],2);eq(before['攻击速度'],after['攻击速度']);eq(before.hp,after.hp);beast_attributes[name]=after
 end
end
-- Actual grid algorithms: square/Chebyshev geometry, no replacement distance formula.
local ai_env={math=math,max=math.max,type=type,['Ae冻集']={['剧情中']=false},['核心']={['取两点间方向']=function()return 0 end},['Sys']={get=function(kind,name)eq(kind,'skill');return assert(attacks[name])end}}
ai_env.lookupHelixNumber=load('helix',ai_env)
ai_env['取两格子间距离']=load('distance',ai_env)
ai_env['判断是否在攻击范围']=load('range',ai_env)
local attack=load('attack_ai',ai_env);local pursue=load('pursue',ai_env);local start=load('start_attack',ai_env);local formula=load('formula',{})
local hits,moves,stops,finds=0,0,0,0;local blocked=false;local lastskill
ai_env['Q_地图']={FindPath=function()finds=finds+1;if blocked then return -1,{}end;return 1,{speed=2}end}
local target={id=10,['属性']={hp=100},['地图格子']={x=1,y=0},['地图坐标']={x=1,y=0},['锚点x']=0,['锚点y']=0,['是否有效']=true}
local pet={['属性']={['禁攻击']=false,['禁移动']=false,['攻击距离']=2,['视野范围']=7,['攻击速度']=100,['攻击速度倍数']=10},['攻击来源']=target,['控制托管']=false,['地图格子']={x=0,y=0},['地图坐标']={x=0,y=0},['锚点x']=0,['锚点y']=0,['攻击速度_计次']=999,['移动类型']='随机',['巡逻动作']='移动',['跑动动作']='跑动'}
pet['改变动作_']=function()end;pet['停止']=function()stops=stops+1 end
pet['开始移动']=function()moves=moves+1 end
pet['继续追击']=function(self)return pursue(self)end
pet['事件回调']=function()return nil,nil end
pet['开始攻击']=start
pet['技能开始']=function(self,skill,owner,victim)
 eq(owner,self);eq(victim,target);eq(skill['施法距离'],2);hits=hits+1;lastskill=skill
 -- Execute the original damage formula; engine hit/delay/effect ticks are outside this fixture.
 eq(formula({['物理伤害']=20,['魔法伤害']=30},{['物理防御']=5,['魔法防御']=10}),35)
end
for name in pairs(attacks)do
 pet['绑定技能']=name
 for _,xy in ipairs({{1,0},{2,0},{2,2},{-2,-1}})do
  target['地图格子'].x=xy[1];target['地图格子'].y=xy[2];target['地图坐标']=target['地图格子'];pet['攻击速度_计次']=999
  local h=hits;attack(pet);eq(hits,h+1,'in-range attack accepted');eq(pet['本次攻击距离'],2);eq(lastskill,attacks[name])
 end
 target['地图格子']={x=3,y=0};target['地图坐标']=target['地图格子'];pet['攻击速度_计次']=999
 local h,m=hits,moves;attack(pet);eq(hits,h,'outside range no attack');eq(moves,m+1,'outside range pursues')
 -- Pursuit itself also attacks at two tiles; unreachable native FindPath result stops.
 target['地图格子'].x=2;pet['攻击速度_计次']=999;h=hits;pursue(pet);eq(hits,h+1)
 blocked=true;local s=stops;h=hits;pursue(pet);eq(stops,s+1);eq(hits,h);blocked=false
 -- Cooldown remains enforced.
 pet['攻击速度_计次']=0;h=hits;attack(pet);eq(hits,h)
end
pet['绑定技能']='神兽攻击';pet['临时绑定技能']='超强神兽攻击1';pet['攻击速度_计次']=999;attack(pet);eq(pet['本次攻击距离'],2);eq(lastskill,attacks['神兽攻击'])
pet['绑定技能']='无';pet['临时绑定技能']=nil;target['地图格子'].x=3;local m=moves;attack(pet);eq(pet['本次攻击距离'],2);eq(moves,m+1)
-- Legacy cached entity distance cannot override the bound skill's new cast range.
pet['绑定技能']='神兽攻击';pet['属性']['攻击距离']=1;target['地图格子'].x=2;pet['攻击速度_计次']=999
local h=hits;attack(pet);eq(pet['本次攻击距离'],2);eq(hits,h+1);pet['属性']['攻击距离']=2
-- One representative hot/cold repeated path (200 total, not per variant).
pet['绑定技能']='神兽攻击';target['地图格子'].x=2
for i=1,200 do pet['攻击速度_计次']=999;local h=hits;attack(pet);eq(hits,h+1)end
-- INSERT_SUMMON_SCENE
-- Actual summon dispatcher and original restore transform: finite engine entity primitives.
for _,enhanced in ipairs({false,0,1,2,3,4,5})do
 local s=scene('new',4498,enhanced);s.cast(skeleton);s.cast(beast);local _,p=s.live(beast)
 eq(p['属性']['攻击距离'],2,'spawn range');eq(s.live(skeleton),1)
 for lv=1,8 do
  s.C['宝宝颜色'][lv]=1;p['属性']['最大生命值']=1200;p['移动间隔']=1000
  bind('upgrade',{},s.env)(p,lv,1);eq(p['属性']['攻击距离'],2,'all pet levels retain range')
 end
 p['附加']['变身']=1;bind('transform',{},s.env)(p.id);eq(p['附加']['变身'],0);eq(p['属性']['攻击距离'],2)
 local n=s.count();s.cast(beast);eq(s.count(),n,'same-kind recall remains');eq(p['属性']['攻击距离'],2)
 p.HP=0;s.flush();s.cast(beast);local _,fresh=s.live(beast);eq(fresh['属性']['攻击距离'],2,'resummon range');eq(s.live(skeleton),1);s.verify()
end
print('BEAST_RANGE_V201_PASS',mode,'checks',checks,'real_map_and_full_damage_tick_not_tested')
