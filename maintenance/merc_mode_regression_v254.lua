local work,mode=arg[1],arg[2]
if mode=='normal'then jit.off()else jit.opt.start('hotloop=1','hotexit=1')end
local checks=0
local function eq(a,b,label)checks=checks+1;assert(a==b,(label or'')..' expected '..tostring(b)..' got '..tostring(a))end
local function noop()end
local function load(name,env)local f=assert(loadfile(work..'/'..name..'.ljbc'));setfenv(f,env);return f end
local N=setmetatable({},{__index=_G});local E={};local S={屏幕事件组={},包裹物品组={}}
local merc={id=7,属性={hp=100,禁攻击=false,攻击速度=1,攻击速度倍数=100,禁移动=false,视野范围=8},是否有效=true,绑定技能='刺客普通攻击',当前状态=0,地图格子={x=0,y=0},地图坐标={x=0,y=0},锚点x=0,锚点y=0,方向=1}
local target={id=9,属性={hp=100},是否有效=true,地图格子={x=3,y=0},地图坐标={x=30,y=0},锚点x=0,锚点y=0}
S.屏幕事件组[1]=merc;S.包裹物品组[397]={拿起=false,道具=nil}
local messages={};local publicmerc={id=7,MP=100,地图格子=merc.地图格子}
E.Ux雌={佣兵对象=publicmerc,开挖机的={孔爱琴泥=function(t)messages[#messages+1]=t end},托管显示={屏幕提示=noop}}
E.Gly独={事件对象=function(id)if id==9 then return{HP=target.属性.hp,地图格子=target.地图格子,方向=1}end end}
-- Use the native 399 installer segment, including existing luck and sandbox
-- assignment, rather than directly loading the new source helper.
local install=load('install',N);debug.setupvalue(install,1,S);install(E)
eq(S.script_setting,E);eq(E.Sys,nil);eq(E.pcall,nil);eq(E._G,nil)
local weapons=assert(loadfile(work..'/weapons.lua'))();local melee=weapons['初级暗杀剑'];local ranged=weapons['潜行之刃'];local generic
for _,it in pairs(weapons)do if it.附加.绑定技能==nil then generic=it;break end end
assert(generic)
local function equip(it)S.包裹物品组[397].道具=it;merc.绑定技能=it and E.__gm_merc_binding_v253(it)or'刺客普通攻击'end
local counts={melee=0,ranged=0}
for _,it in pairs(weapons)do
 equip(it);local isrange=E.__gm_merc_binding_v253(it)=='刺客普通攻击';counts[isrange and'ranged'or'melee']=counts[isrange and'ranged'or'melee']+1
 for _,skill in ipairs({'刺客普通攻击','蝉舞','月桂','红莲','白莲','盛开'})do eq(N.__gm_merc_range_v253(merc,1,skill),isrange and 8 or 1)end
 local name=N.__gm_merc_name_v253(it,it.显示名,397);eq(name,it.显示名..(isrange and'（远程）'or''));eq(N.__gm_merc_name_v253(it,name,397),name)
 eq(it.显示名:find('（远程）',1,true),nil,'never mutate name')
 if it.附加.绑定技能==nil then eq(N.__gm_merc_name_v253(it,it.显示名),it.显示名,'generic neutral shop/ground')end
end
eq(counts.melee,16);eq(counts.ranged,126)
-- Native equipment callback resets default binding after a two-hand weapon.
local binding=load('binding_update',E);equip(melee);binding({道具=generic});eq(publicmerc.绑定技能,'刺客普通攻击');binding({道具=melee});eq(publicmerc.绑定技能,'刺客双手攻击')
-- Register the original class method trees without executing engine constructors.
N.class=function()return{}end;load('slot_class',N)();load('actor_class',N)()
local slotclass=N.格子_包裹格子;local actorclass=N.类_事件
assert(type(slotclass.拿起物品)=='function'and type(actorclass.继续攻击)=='function')
-- Withdrawn guards and all associated private exports are absent.
eq(N.__gm_merc_block_v253,nil);eq(N.__gm_merc_request_v253,nil)
local request=load('request',N);local calls=0
S.fun=function(fn,args)calls=calls+1;return true,fn(unpack(args))end
S.tbl_qs={qs_item_box={Main=function(...)return 'allowed',... end}}
debug.setupvalue(request,1,S)
merc.攻击来源=target;merc.当前状态=3;merc.本次目标=target;equip(ranged)
for k=1,6 do local a,b=request({k,397,'weapon',333});eq(a,true);eq(b,'allowed')end
eq(calls,6,'all native requests still forward while fighting')
N.Sys=load('public_sys',N)({run=function(key,args)eq(key,'qs_item_box');return request(args)end})
local paper={}
local box={标识=397,格子组=S.包裹物品组,可用=true,弹簧效果刷新=noop,主角纸娃娃更新=function(_,op)paper[#paper+1]=op end}
N.Q_鼠标={格子标识=333,被占用=false}
slotclass.拿起物品(box);eq(box.拿起,true);eq(N.Q_鼠标.格子标识,397);eq(paper[#paper],'拿起')
box.能否放下=function()return true end
slotclass.放下物品(box);eq(box.拿起,false);eq(N.Q_鼠标.被占用,false);eq(N.Q_鼠标.格子标识,0);eq(paper[#paper],'放下')
eq(#messages,0,'no removed combat-lock messages')
-- The complete original predicates still enforce ordinary item restrictions.
local seen=0
N.Sys=load('public_sys',N)({run=function(key,args)eq(key,'qs_item_box');seen=seen+1;return true,true end})
local function predicate(box)N.Q_鼠标={格子标识=397};return slotclass.能否放下(box)end
local okbox={标识=397,格子组=S.包裹物品组,包含子类=function()return true end,限制类型={'武器'},Hero={属性={}}}
-- Further native class methods are byte-identical to v252, including the
-- exchange trampoline and quick-equip. No replacement method mocks are used.
-- Here the real final request rejects with its original false contract.
N.Sys=load('public_sys',N)({run=function(key,args)eq(key,'qs_item_box');seen=seen+1;return true,true end})
eq(predicate(okbox),false);eq(seen,1)
local usebox={标识=397,格子组=S.包裹物品组,可用=true}
eq(slotclass.使用物品(usebox),false);eq(seen,2)
S.包裹物品组[333]={道具=melee};N.Q_鼠标={格子标识=333,被占用=true,占用类型='道具'}
okbox.能否放下=slotclass.能否放下
slotclass.交换物品(okbox);eq(seen,3,'native exchange reaches original predicate')
local quick={标识=333,格子组=S.包裹物品组,可用=true}
eq(slotclass.使用物品(quick),false);eq(seen,4,'companion quick equip reaches original callback')
-- Original full native AI methods with finite map/path and action sinks. In
-- range no FindPath/LOS callback is needed even when walls block all paths.
local paths,attacks,moves=0,0,0
N.Ae冻集={剧情中=false};N.核心={取两点间方向=function()return 1 end}
N.取两格子间距离=function(x,y,a,b)return math.max(math.abs(x-a),math.abs(y-b))end
N.判断是否在攻击范围=function(p,q,r)return math.max(math.abs(p.x-q.x),math.abs(p.y-q.y))<=r and 0 or -1 end
N.Q_地图={FindPath=function()paths=paths+1;return 0,{speed=1}end}
N.Sys=load('public_sys',N)({get=function(key,name)if key=='skill'then return{施法距离=1}end;error('unexpected get '..key)end})
merc.__gm_guard_ignore_v224=function()return false end;merc.控制托管=true;merc.攻击速度_计次=10;merc.移动类型='移动';merc.巡逻动作='走';merc.跑动动作='跑'
merc.开始攻击=function()attacks=attacks+1 end;merc.开始移动=function()moves=moves+1 end;merc.停止=noop;merc.改变动作_=noop
local attack,pursue=load('attack',N),load('pursue',N);merc.继续追击=pursue
for _,it in ipairs({ranged,melee,generic})do for _,dist in ipairs({1,3,8,9})do
 equip(it);target.地图格子.x=dist;merc.攻击来源=target;merc.临时绑定技能=nil;merc.攻击速度_计次=10
 local a,p,m=attacks,paths,moves;attack(merc);eq(merc.本次攻击距离,it==melee and 1 or 8)
 if dist<=(it==melee and 1 or 8)then eq(attacks,a+1);eq(paths,p,'no path request in attack range')else assert(paths>p)end
end end
equip(ranged);target.地图格子.x=8;merc.攻击来源=target;local before=paths;pursue(merc);eq(paths,before,'already pursuing within range bypasses wall path query')
for _,skill in ipairs({'蝉舞','月桂','红莲','白莲','盛开'})do for _,d in ipairs({1,3,8,9})do equip(ranged);merc.临时绑定技能=skill;merc.攻击来源=target;target.地图格子.x=d;merc.攻击速度_计次=10;attack(merc);eq(merc.本次攻击距离,8)end end;merc.临时绑定技能=nil
for i=1,200 do equip(ranged);merc.攻击来源=target;target.地图格子.x=(i%2==0)and 8 or 9;merc.攻击速度_计次=10;attack(merc)end
-- Monster and hero IDs never receive a ranged distance, even with same binding.
eq(N.__gm_merc_range_v253({id=8,绑定技能='刺客普通攻击'},1,'蝉舞'),1);local savedbox=S.包裹物品组[397];S.包裹物品组[397]=17;eq(N.__gm_merc_range_v253(merc,1,'蝉舞'),1,'invalid weapon entry');S.包裹物品组[397]=savedbox;equip(nil);eq(N.__gm_merc_range_v253(merc,1,'蝉舞'),1);equip(ranged)
-- Full original Chant script: ranged never searches adjacent cells or teleports.
local casts,teleports,positions,states=0,0,0,0
E.Ux雌.胚子考虑=function()return{佣兵操作=0}end;E.Ux雌.啾啾啵啵=function()return{佣兵={技能={蝉舞=1}}}end
publicmerc.取状态列表=function()return{}end;publicmerc.增加状态=function()states=states+1 end;publicmerc.瞬移=function()teleports=teleports+1 end;publicmerc.释放技能=function(s,id)eq(s,'蝉舞');eq(id,9);casts=casts+1 end
E.Gly独.取出技能信息=function()return{消耗魔法=5}end;E.Gly独.取有效位置=function()positions=positions+1;return 2,3 end;E.Gly独.取随机数=function(a)return a end;E.取两点间方向=function()return 1 end;E.FXru胃啪={目标=0}
local chant=load('chant',E)
for _,it in ipairs({ranged,melee,generic})do for _,dist in ipairs({1,3,8,9})do
 equip(it);target.地图格子.x=dist;merc.攻击来源=target;publicmerc.MP=100;local c,t,p,s=casts,teleports,positions,states;chant(9)
 if it~=melee and dist>8 then eq(casts,c);eq(publicmerc.MP,100);eq(states,s)
 else eq(casts,c+1);eq(publicmerc.MP,95);eq(states,s+1);eq(teleports,t+(it==melee and 1 or 0));eq(positions,p+(it==melee and 1 or 0))end
end end
-- Native locked-target selection and delayed hit callback for all six ranged
-- skills, using the actual DB configuration. The update selection fragment
-- excludes animation and phase scheduling; the damage closure is complete.
local configs=assert(loadfile(work..'/skills.lua'))()
N.引擎={取运行时间=function()return 0 end}
local oldsys=N.Sys
N.Sys=load('public_sys',N)({get=function(key,name)if key=='skill'then return configs[name]end;error(key)end,run=function(key,fn,args)if key=='fun'then if type(fn)=='function'then return true,fn(unpack(args))end;return true end;error(key)end})
local construct=load('skill_construct',N);local select_targets=load('skill_targets',N);local damage=load('skill_damage',N)
merc.施法速度=1;merc.所属阵营='友方';target.所属阵营='敌方'
local hits=0
merc.发生伤害=function(self,t,skill,ratio)eq(t,target);eq(ratio,1);hits=hits+1;return{5,0}end
for name,cfg in pairs(configs)do
 cfg.脚本={Main=noop};cfg.子弹形态=nil;cfg.起手动画=nil;cfg.目标动画=nil
 for _,dist in ipairs({1,3,8})do
  target.地图格子.x=dist;target.属性.hp=100
  local phase=construct(merc,cfg,merc,target,0,{},0,1)
  local _,state=debug.getupvalue(phase.刷新,1);assert(type(state)=='table')
  debug.setupvalue(select_targets,1,state);select_targets();eq(#state.命中目标组,1);eq(state.命中目标组[1][1],target)
  local before=hits;debug.setupvalue(damage,1,state);debug.setupvalue(damage,2,0);damage();eq(hits,before+1)
  target.属性.hp=0;state.伤害进度={1};damage();eq(hits,before+1,'dead target never hit');target.属性.hp=100
 end
end
N.Sys=oldsys
-- Returned display metadata and public read-only Sys boundary.
local T={};for k,v in pairs(table)do T[k]=v end;N.table=T;load('table_register',N)();S.游戏道具组=weapons
local template=load('template_info',N);debug.setupvalue(template,1,S)
local metadata=load('metadata',N);debug.setupvalue(metadata,1,S)
local function withattrs(it)local v=T.copy(it);v.属性=function()return{}end;v.数量=1;v.风格提示={宽度=0,高度=0};return v end
for _,it in ipairs({ranged,melee,generic})do
 local v=withattrs(it);S.游戏道具组[v.名称]=v;S.包裹物品组[397].道具=v
 local a=template(v.名称);local b=metadata(397);eq(b.显示名,v.显示名..(it==melee and''or'（远程）'));eq(a.名称,v.名称);eq(v.显示名,it.显示名)
end
-- Complete original tooltip, its real metadata lookup and name formatter.
-- All numeric fields come from native template/configuration data. Finite
-- formatting/player settings below only bridge the surrounding engine.
local proxy=load('proxy',N);debug.setupvalue(proxy,1,S);S.数据保护=proxy
local config=load('equipment_config',N)()
local suitfactory=load('suit_config',N);debug.setupvalue(suitfactory,1,{});local suits=suitfactory()
local U={天竺葵家=function()return suits end,独角兽下=function()return config end,胚子考虑=function()return{装备操作=0}end,啾啾啵啵=function()return{职业='刺客',等级=100,性别='男',人物选择=1}end}
local TE={type=type,tonumber=tonumber,tostring=tostring,pairs=pairs,ipairs=ipairs,math=math,string=string,table=N.table,Ux雌=U,Gly独={取道具信息_名称=template},物品格子18={},物品格子14={},物品格子410={},商店窗口={可视=false},商店窗口2={可视=false},格式化数值=tostring,L常量={},FXru胃啪={职业='刺客',性别='男',等级=100},__gm_merc_name_v253=E.__gm_merc_name_v253,__gm_luck_line_v244=E.__gm_luck_line_v244}
local tip,oldtip=load('tooltip',TE),load('tooltip_old',TE)
local nameformat=load('name_format',TE);U.化肥化挥发会=nameformat
local function itemcopy(it)
 local v=T.copy(it);v.附加=T.copy(it.附加);v.数量=1;v.风格提示={宽度=0,高度=0};v.属性={}
 for k in pairs(config.极品数值)do v[k]=v[k]or 0;v.属性[k]=v[k]end
 for _,k in ipairs({'身体舒适','物品腕力','物品重量','穿戴肩力','武器腕力'})do v.属性[k]=0;v[k]=v[k]or 0 end
 return v
end
local function checktip(it,slot,illusion,tier)
 local v=itemcopy(it);v.附加.条数=tier;v.附加.幻化=illusion and'武器'or nil;v.附加.位置=3
 local base=T.copy(v,true);base.属性=proxy(base.属性,true);base.附加=proxy(base.附加,true);S.游戏道具组[v.名称]=proxy(base)
 local before=oldtip(v,1,slot);local after=tip(v,1,slot)
 if it==weapons['实战杀伤刀']then eq(before:find('（远程）',1,true),nil,'v253 missing tooltip suffix negative control')end
 local expected=N.__gm_merc_name_v253(v,v.显示名,slot)
 eq(after:find(expected,1,true)~=nil,true,'full tooltip title')
 local suffix=expected~=v.显示名
 local _,n=after:gsub('（远程）','');eq(n,suffix and 1 or 0,'one title suffix')
 eq(v.显示名,it.显示名,'never overwrite original name')
 if suffix then eq(after:gsub('（远程）',''),before,'all original rich text, font/color and attributes preserved')else eq(after,before,'non-target full tooltip unchanged')end
 return after
end
for _,it in pairs(weapons)do checktip(it,32,false,3)end
for _,tier in ipairs({0,3,4,5,6,7})do
 for _,it in ipairs({weapons['实战杀伤刀'],ranged,melee,generic})do
  for _,illusion in ipairs({false,true})do checktip(it,32,illusion,tier);checktip(it,397,illusion,tier)end
 end
end
for i=1,200 do checktip(weapons['实战杀伤刀'],32,i%2==0,3+i%5)end
print('TOOLTIP_V254_PASS',mode)
-- Full ground construction uses shared name classifier; coins change only tint.
local label;local G=setmetatable({table=N.table,Ae冻集={默认文字_间距=0,默认文字_行距=0,地面道具描边=false},Q__={创建动画=function()return{置中心点=noop}end},Q_公用图片库={地面物品闪烁序列图={}},Q_地图={逻辑格子到坐标=function(x,y)return x*10,y*10 end,坐标到逻辑格子=function(x,y)return x/10,y/10 end,取地图信息_总=function()return{宽度=1000,高度=1000}end,置格子信息=noop},Q_文字={取宽度=function(t)return #t*6 end,取高度=function()return 12 end},ARGB=function(a,r,g,b)return a*16777216+r*65536+g*256+b end,引擎={取随机整数=function(_,lo)return lo end,取随机小数=function(_,lo)return lo end,取运行时间=function()return 0 end}},{__index=N})
G.Sys=load('public_sys',N)({get=function(key)if key=='hero'then return{}elseif key=='win_tex'then return function()return{置标题=function(...)label={...}end}end end;error(key)end})
local ground=load('ground_new',G)
for _,it in ipairs({ranged,melee,generic,{名称='金币_100',显示名='金币',分类='特殊',子类='特殊',颜色值=-6240}})do
 local v=T.copy(it);v.附加=T.copy(it.附加 or{});local o={};ground(o,v,5,7,2,0);eq(v.显示名,it.显示名);if it.分类=='特殊'then eq(label[3],-2612)else eq(o.显示内容:find('（远程）',1,true)~=nil,it==ranged)end
end
print('MERC_V254_PASS',mode,checks,'checks',counts.melee,'melee',counts.ranged,'ranged')

local h={}
do
 -- Real full constructor. Only engine/graphics/map and window primitives are
 -- finite. Original public Sys wrapper remains in the path.
 local label
 local GE=setmetatable({table=T,Ae冻集={默认文字_间距=0,默认文字_行距=0,地面道具描边=false},
  Q__={创建动画=function()return{置中心点=noop}end},Q_公用图片库={地面物品闪烁序列图={}},
  Q_地图={逻辑格子到坐标=function(x,y)return x*10,y*10 end,坐标到逻辑格子=function(x,y)return x/10,y/10 end,
   取地图信息_总=function()return{宽度=1000,高度=1000}end,置格子信息=noop},
  Q_文字={取宽度=function(t)return #t*6 end,取高度=function()return 12 end},
  ARGB=function(a,r,g,b)return a*16777216+r*65536+g*256+b end,
  引擎={取随机整数=function(_,lo,hi)return lo end,取随机小数=function(_,lo,hi)return lo end,取运行时间=function()return 0 end}}, {__index=N})
 GE.Sys=load('public_sys',N)({get=function(key)
  if key=='hero'then return h elseif key=='win_tex'then return function()return{置标题=function(...)label={...}end}end end
  error('unexpected native constructor get '..tostring(key))
 end})
 local old,new=load('ground_old',GE),load('ground_new',GE)
 local templates=assert(loadfile(work..'/ground_templates.lua'))()
 local function run(fn,item,qty,outline)
  GE.Ae冻集.地面道具描边=outline;label=nil;local object={};fn(object,item,5,7,qty,0);assert(label);return object,label
 end
 local med,gold=0,0
 for _,item in pairs(templates)do
  local before=item.颜色值
  if item.kind=='medicine'then med=med+1 else gold=gold+1 end
  for _,qty in ipairs({1,9})do for _,outline in ipairs({false,true})do
   local a,x=run(old,item,qty,outline);local b,y=run(new,item,qty,outline)
   eq(y[3],item.kind=='medicine'and -1 or -2612,'ground-only tint')
   for k=1,7 do if k~=3 then eq(y[k],x[k],'ground title/outline/size unchanged')end end
   eq(item.颜色值,before,'item/template tint is never overwritten');eq(b.物品,item);eq(b.数量,a.数量);eq(b.显示内容,a.显示内容)
  end end
 end
 eq(med,22);eq(gold,5)
 for _,item in ipairs({
  {名称='祝福油',显示名='祝福油',分类='道具',子类='消耗品',颜色值=-65536},
  {名称='灵魂神水_小',显示名='灵魂神水',分类='道具',子类='消耗品',颜色值=-26368},
  {名称='疗伤药',显示名='疗伤药',分类='道具',子类='消耗品',颜色值=-5592406},
  {名称='金币卷',显示名='金币卷',分类='特殊',子类='特殊',颜色值=-65536},
  {名称='魔法药_装备',显示名='特殊装备',分类='装备',子类='武器',颜色值=-26368,附加={条数=7}},
  {名称='金创药材',显示名='药材',分类='道具',子类='消耗品',颜色值=-26368},
 })do
  for _,outline in ipairs({false,true})do
   local _,x=run(old,item,1,outline);local _,y=run(new,item,1,outline)
   for k=1,7 do eq(y[k],x[k],'non-target name/rarity remains native')end
  end
 end
 -- R15 native rarity is live after our call. All existing qualities and both
 -- outline modes must retain the exact original tint/outline selection.
 for tier=0,7 do for _,outline in ipairs({false,true})do
  local item={名称='测试装备',显示名='测试装备',分类='装备',子类='武器',颜色值=-26368,附加={条数=tier}}
  local _,x=run(old,item,1,outline);local _,y=run(new,item,1,outline)
  for k=1,7 do eq(y[k],x[k],'live rarity register survived new helper')end
 end end
 local rows={};for _,item in pairs(templates)do rows[#rows+1]=item end
 for i=1,200 do local item=rows[i%#rows+1];local _,label=run(new,item,i%5+1,i%2==0);eq(label[3],item.kind=='medicine'and -1 or -2612)end
 print('GROUND_V254_PASS',mode,med,'medicine variants',gold,'coin variants')
end

