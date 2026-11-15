-- Compare v216/v217 visuals; native callback arguments remain unchanged.
for _,name in ipairs(names)do
 local old,new=visual_scene('old'),visual_scene('new')
 eq(old:cast(name),true);eq(new:cast(name),true)
 local a,b=upstate(old),upstate(new)
 near(a['伤害发生延迟'],b['伤害发生延迟']);near(a['起手动画延迟'],b['起手动画延迟'])
 old:step(110);new:step(110)
 local x,y=effect_events(old),effect_events(new);eq(#x,#y)
 for i,t in ipairs(times(old,'damage'))do near(t,times(new,'damage')[i],'unchanged hit time')end
 for i,e in ipairs(x)do
  local f=y[i];near(e.t,f.t,'unchanged sword-light onset');eq(e.args.n,f.args.n)
  for j=1,e.args.n do if j~=8 and j~=13 then eq(e.args[j],f.args[j],'effect arg '..j)end end
  if name=='翔空剑法'then
   near(f.object['播放速度'],e.object['播放速度']/.7,'30 percent lower playback rate')
   eq(display_until_gone(new,f)>display_until_gone(old,e),true,'longer sword-light animation only')
  else
   near(f.object['播放速度'],e.object['播放速度']);near(display_until_gone(new,f),display_until_gone(old,e))
  end
 end
end
for _,opts in ipairs({{hold=true},{hold=true,speed=5},{hold=true,speed=25},{hold=true,dt=1/15}})do
 local old,new=visual_scene('old',opts),visual_scene('new',opts)
 old:cast('刺杀剑术');new:cast('刺杀剑术')
 for i=1,1200 do old:step();new:step();if #times(old,0)>=4 then break end end
 local a,b=times(old,0),times(new,0);eq(#a,#b)
 for i,t in ipairs(a)do near(t,b[i],'unchanged attack cadence')end
end
local charged={'烈火剑法','翔空剑法','莲月剑法'}
local function charge_scene(version,learned,level)
 local s=scene(version);local h,env=s.hero,s.env
 env.select=select;env.setmetatable=setmetatable;env.rawget=rawget;env.rawset=rawset
 local f=load('hero_api',env);debug.setupvalue(f,2,{Hero=h,['屏幕事件组']={s.target}})
 env['FXru胃啪']=f() -- Actual public actor API, not handwritten charge methods.
 s.role={['技能']={}};eq(h['主角配置']['技能'],nil,'real hero operation config has no learned skills')
 for _,name in ipairs(learned or charged)do s.role['技能'][name]={level or 0,0,5}end
 local rules=load('rules',env)()
 env['Ux雌']['大堵塞就']=function()return rules end
 local role_owner={['角色组']=s.role};s.role_owner=role_owner;local getrole=load('role_b',env);debug.setupvalue(getrole,1,role_owner);env['Ux雌']['啾啾啵啵']=getrole
 env['Ux雌']['版本选择']='来世续缘'
 s.settings={['技能操作']=0};env['Ux雌']['胚子考虑']=function()return s.settings end
 env['Ux雌']['窗口相关']={['命中状态']=noop}
 env['Ux雌']['托管显示']={['屏幕提示']=noop}
 env['Ae冻']=env['Ux雌']
 local owner={Hero=h,['游戏技能组']=s.skills,['格式化技能属性']=function()return'finite tooltip'end}
 env['丰富文本_解析']=function()return{},0,0 end
 env['Ae冻集']['技能提示宽度']=200
 local set=load('skill_set',env);debug.setupvalue(set,1,owner)
 local get=load('skill_info',env);debug.setupvalue(get,1,owner)
 env['Gly独']['修改技能信息']=set;env['Gly独']['取出技能信息']=get
 for name in pairs(s.skills)do h['技能配置'](h,name)end
 s.refresh=load('refresh_skills',env)
 s.refresh() -- Real learned-level refresh -> original skill setter -> real cost.
 for _,name in ipairs(learned or charged)do near(s.skills[name]['消耗魔法'],rules[name][(level or 0)+1]['消耗魔法'],'native configured cost')end
 local T={};for k,v in pairs(table)do T[k]=v end
 -- Only finite raw status template attributes, never the game database proxy.
 T.copy=function(t)local out={};for k,v in pairs(t)do out[k]=v end;return out end
 env.table=T
 local statuses=assert(loadfile(work..'/statuses.lua'))()
 for name,status in pairs(statuses)do
  status['脚本']=load('status_'..(string.gsub(name,'.',function(c)return string.format('%02x',string.byte(c))end)),env)()
  -- Zero-valued non-combat status attribute fixture for native BUFF arithmetic.
  for _,key in ipairs({'物理伤害','魔法伤害','物理防御','魔法防御','最大生命','最大法力','生命值','法力值','命中','躲避','暴击','移动速度','攻击速度'})do status['属性'][key]=0;status['属性'][key..'_百分比']=0;if h['属性'][key]==nil then h['属性'][key]=0 end end
  status['资源表']={};status['动作转移']={};status['图标']=nil;status['动画']=nil
 end
 h['属性更新']=noop -- Zero-attribute status fixture: final entity recomputation boundary.
 h['属性']['移动速度倍数']=10
 env['Ae冻集']['自定义属性表']={}
 env['Ae冻集']['状态图标显示模式']=0
 env['Q__']={['创建精灵']=function()return{['置中心点']=noop}end}
 load('buff_class',env)()
 local get0=env.Sys.get
 env.Sys.get=function(kind,name)if kind=='status'then return statuses[name]end;return get0(kind,name)end
 local selector=load('selector',env);local run=env.Sys.run
 env.Sys.run=function(op,args,...)
  if op=='qs_skill_drop'and args[1]==5 then return true,selector(unpack(args))end
  return run(op,args,...)
 end
 env['引擎']['取按键按下']=function()return false end
 h['快捷事件组']={};env['Ae冻集']['快捷事件组']={}
 env['Ae冻集']['镜头ID']=h.id;env['Ae冻集']['遮罩信息']['触发']=true
 local bufftick=load('buff_tick',env)
 local step=s.step
 s.step=function(self,n)for i=1,n or 1 do step(self);bufftick(h);h['输入控制'](h)end end
 -- Hero scalars touched by original BUFF creation/destruction. No combat data
 -- is synthesized in production; these are declared fixture entity fields.
 for _,key in ipairs({'附加_物理伤害','附加_魔法伤害','附加_物理防御','附加_魔法防御','附加_maxhp','附加_maxmp','附加_命中','附加_躲避','附加_暴击','附加_移动速度倍数','附加_攻击速度倍数'})do h['属性'][key]=0 end
 s.rules=rules;s.statuses=statuses;s.selector=selector
 return s
end
local function actual_name(s)return s.hero['当前技能']['对象']['名称']end
local function settle(s)for i=1,1000 do s:step();local state=s.hero['__gm_melee_state_v208'];if s.hero['当前状态']~=3 and #s.hero['释放技能组']==0 and(not state or state.ready) and(not s.hero['当前技能']or not s.hero['当前技能']['开始CD效果'])then s:step(2);return end end;error('native motion did not finish')end
local function selected(s,name,expected)
 local before=#times(s,0);local ok=s:cast(name);eq(ok,true,'native cast success');eq(#times(s,0),before+1,'one accepted cast')
 eq(actual_name(s),expected,'actual selected skill');s.hero['攻击目标']=nil;s.hero['远程目标']=nil;s.hero['下次技能']=nil;return s.hero['属性'].mp
end

-- Previous fixture incorrectly merged operation config and role skills.
-- Real getter + separate operation config reproduces the v216 failure.
do
 local old,new=charge_scene('old'),charge_scene('new')
 old:step(20);new:step(20)
 eq(old.hero['__gm_auto_charge_v216'],nil,'old automatic activation never starts')
 for i=1,3 do eq(new.hero['__gm_auto_charge_v216'].ready[i],true,'zero-input actual activation')end
 eq(new.hero['属性'].mp,1000,'activation itself has original zero cost')
end
-- Stored reserve lasts past its original 12s timeout; native 10s CD expires
-- while the reserve stays full, permitting two rounds without a cooldown reset.
for _,set in ipairs({{charged[1]},{charged[2]},{charged[3]},{charged[1],charged[2]},{charged[1],charged[3]},{charged[2],charged[3]},charged})do
 local s=charge_scene('new',set);s:step(1500)
 local h=s.hero;local states=h['取状态列表'](h)
 for _,name in ipairs(set)do eq(states[name]~=nil,true,'stored ready status persists');eq(states[name..'CD'],nil,'activation CD expired while stored')end
 for round=1,2 do
  for _,name in ipairs(set)do
   selected(s,'普通攻击',name);settle(s)
  end
 end
 local before=h['属性'].mp;selected(s,'普通攻击','普通攻击');eq(h['属性'].mp,before,'no third stored attack')
 s:step(1300);selected(s,'普通攻击',set[1])
end
-- Actual level refresh, native fee deduction and percentage rounding.
for level=0,5 do
 for _,name in ipairs(charged)do
  local old,new=charge_scene('old',{name},level),charge_scene('new',{name},level)
  selected(old,name,name);selected(new,'普通攻击',name)
  near(new.hero['属性'].mp,old.hero['属性'].mp,'original skill cost paid once')
 end
end
for _,percent in ipairs({false,true})do
 local s=charge_scene('new',{charged[1]});local h=s.hero
 local cost=percent and 1.01 or 2;s.skills[charged[1]]['消耗魔法']=cost;s.skills[charged[1]]['消耗魔法_百分比']=percent
 local expected=percent and math.ceil(cost/100*h['属性'].maxmp)or cost;h['属性'].mp=expected
 selected(s,'普通攻击',charged[1]);near(h['属性'].mp,0,'native exact MP boundary')
end
for _,kind in ipairs({'blocked','out_of_range','native_cd','disabled','dead','lowmp','ranged','cancel'})do
 local s=charge_scene('new',{charged[1]});s:step(20);local h=s.hero;local mp=h['属性'].mp
 if kind=='blocked'then s.settings['技能操作']=1
 elseif kind=='out_of_range'then s.target['地图格子'].x=20;s.env['判断是否在攻击范围']=function()return -1 end
 elseif kind=='native_cd'then h['技能信息'][charged[1]]['开始CD效果']=true
 elseif kind=='disabled'then h['技能信息'][charged[1]]['可用']=false
 elseif kind=='dead'then h['属性'].hp=0;h['已经死亡']=true
 elseif kind=='lowmp'then h['属性'].mp=0;mp=0
 elseif kind=='cancel'then h['当前状态']=3 end
 local ok=s:cast(kind=='ranged'and'火球术'or'普通攻击')
 eq(h['__gm_auto_charge_v216'].ready[1],true,kind..' cannot consume reserve')
 eq(h['__gm_auto_charge_v216'].last,0,kind..' cannot rotate')
 eq(h['属性'].mp,mp,kind..' no extra MP charge')
 if kind=='ranged'then eq(actual_name(s),'火球术','permanent reserves do not hijack a spell')end
end
-- Forgetting/new learning observes actual role; session init clears private data.
do
 local s=charge_scene('new',{});s:step(20);eq(s.hero['__gm_auto_charge_v216'],nil)
 s.role['技能'][charged[2]]={0,0,5};s.refresh(charged[2]);s:step(20)
 eq(s.hero['__gm_auto_charge_v216'].ready[2],true)
 s.role['技能'][charged[2]]=nil;s:step(20);eq(s.hero['__gm_auto_charge_v216'].ready[2],false)
 load('reset_session',s.env)(s.hero);eq(s.hero['__gm_auto_charge_v216'],nil)
 eq(s.role['__gm_auto_charge_v216'],nil,'not a savegame field')
end
-- Both native story role getters expose the same independent role contract.
do
 local s=charge_scene('new',{charged[1]});local getter=load('role_a',s.env);debug.setupvalue(getter,1,s.role_owner)
 s.env['Ux雌']['啾啾啵啵']=getter;s.env['Ux雌']['版本选择']='前尘忆梦'
 s:step(20);eq(s.hero['__gm_auto_charge_v216'].ready[1],true,'first-story zero-input activation')
 selected(s,'普通攻击',charged[1])
end
-- Actual Shift callback registration -> public release -> real selector.
-- Stored buffs still have native priority, so this tests the override too.
for _,distance in ipairs({1,2})do
 local s=charge_scene('new');s:step(1500);local h,env=s.hero,s.env
 s.role['技能']['刺杀剑术']={0,0,5}
 s.target['地图格子'].x=0;s.target['地图格子'].y=-distance
 s.target['地图坐标'].x=0;s.target['地图坐标'].y=-distance
 env['Ae冻集']['鼠标_地图格子']={x=0,y=-distance};env['Ae冻集']['鼠标_地图坐标']={x=0,y=-distance}
 env['L常量']['键_SHIFT']=16;env['L常量']['键_鼠标左']=1
 local keys={[16]=true,[1]=true};env['引擎']['取按键事件']=function(a,b)return keys[b or a]or false end
 local register=load('shift_registration',env);debug.setupvalue(register,1,{})
 local window=register();window['命中状态']=env['Ux雌']['窗口相关']['命中状态'];env['Ux雌']['窗口相关']=window
 h['输入控制'](h)
 eq(actual_name(s),'刺杀剑术','Shift always thrusts at distance '..distance)
 for i=1,3 do eq(h['__gm_auto_charge_v216'].ready[i],true,'Shift preserves every reserve')end
 eq(h['__gm_auto_charge_v216'].last,0,'Shift never advances rotation')
 keys[16]=false;keys[1]=false;h['攻击目标']=nil;h['远程目标']=nil;h['下次技能']=nil;settle(s)
 selected(s,'普通攻击',charged[1])
end
-- Native status lookup still contains a removed buff before its next cleanup.
-- Such a stale entry must not become a fresh reserve or bypass its charge CD.
do
 local s=charge_scene('new',{charged[1]});s:step(20);local h=s.hero
 for _,buff in ipairs(h['BUFF组'])do if buff['取标识']()==charged[1]then buff['已经消失'](true)end end;h['__gm_auto_charge_v216'].ready[1]=false
 eq(h['取状态列表'](h)[charged[1]]~=nil,true,'native stale lookup before cleanup')
 selected(s,'普通攻击','普通攻击');eq(h['__gm_auto_charge_v216'].ready[1],false,'no stale re-arm')
end
-- Native continuous target attack. Geometry/path progress is finite: move
-- the fixture target into range after a real rejected far release; invoke the
-- native attack method and original state updates, not a hand-written attack loop.
for _,far in ipairs({false,true})do
 local s=charge_scene('new');s:step(1500)
 if far then
  s.env['判断是否在攻击范围']=function()return -1 end;s.target['地图格子'].x=20
  eq(s:cast('普通攻击'),false,'real pursuit queues without spending reserve')
  for i=1,3 do eq(s.hero['__gm_auto_charge_v216'].ready[i],true,'out-of-range request preserves reserves')end
  s.env['判断是否在攻击范围']=function()return 1 end;s.target['地图格子'].x=1
 end
 if not far then eq(s:cast('普通攻击'),true)else s.hero['开始物理攻击动作'](s.hero,true,true)end
 for i=1,2500 do s:step();if #times(s,0)>=7 then break end end
 local casts={};for _,e in ipairs(s.events)do if e.op==0 then casts[#casts+1]=e.name end end
 eq(#casts>=7,true,'native continuous attack keeps going')
 for i=1,6 do eq(casts[i],charged[(i-1)%3+1],'continuous two rounds '..i)end
 eq(casts[7],'普通攻击','no third stored round')
end
-- Bounded representative casting: original instance end cannot erase a newly
-- prepared reserve; no stacking above one, no duplicate successful casts.
do
 local s=charge_scene('new');s.hero['属性'].mp=100000;s:step(1500)
 local counts={};local successes=0
 for i=1,200 do
  local n=#times(s,0)
  if s:cast('普通攻击')then
   successes=successes+1;eq(#times(s,0),n+1,'one accepted cast')
   local name=actual_name(s);counts[name]=(counts[name]or 0)+1
   s.hero['攻击目标']=nil;s.hero['远程目标']=nil;s.hero['下次技能']=nil
  end
  settle(s)
  for _,v in pairs(s.hero['__gm_auto_charge_v216'].ready)do eq(type(v),'boolean','one reserve only')end
 end
 eq(successes,200);for _,name in ipairs(charged)do eq((counts[name]or 0)>2,true,'all learned skills keep working')end
 print('RESERVES',mode,counts[charged[1]],counts[charged[2]],counts[charged[3]],counts['普通攻击'])
end
print('EFFECT_V217_PASS',mode,checks)
