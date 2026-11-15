-- v215/v216 compare with actual hero, skill, effects and animation code.
-- Art/geometry/final damage and the flag-0 input-to-animation bridge are finite
-- fixtures, not Windows startup/rendering. Native flag-5 selector is used below.
for _,name in ipairs(names)do
 local old,new=visual_scene('old'),visual_scene('new')
 eq(old:cast(name),true,name);eq(new:cast(name),true,name)
 local a,b=upstate(old),upstate(new)
 near(a['伤害发生延迟'],b['伤害发生延迟'],'damage delay')
 near(a['命中动画延迟'],b['命中动画延迟'],'target effect delay')
 if name=='翔空剑法'then near(b['起手动画延迟'],b['伤害发生延迟']);eq(b['起手动画延迟']>a['起手动画延迟'],true)
 else near(a['起手动画延迟'],b['起手动画延迟'],name..' unchanged onset')end
 old:step(110);new:step(110)
 local x,y=effect_events(old),effect_events(new);eq(#x,#y,'effect count')
 local hit_a,hit_b=times(old,'damage'),times(new,'damage');eq(#hit_a,#hit_b)
 for i,t in ipairs(hit_a)do near(t,hit_b[i],'same damage time')end
 for i,e in ipairs(x)do
  local f=y[i];eq(e.args.n,f.args.n)
  if name=='翔空剑法'then near(f.t,hit_b[1],'jump light appears at impact');eq(f.t>e.t,true)
  else near(e.t,f.t,'other effect onset preserved')end
  for j=1,e.args.n do if j~=8 then eq(e.args[j],f.args[j],'effect arg '..j)end end
  near(e.object['播放速度'],f.object['播放速度']);near(display_until_gone(old,e),display_until_gone(new,f),'same visual duration')
 end
end
for _,opts in ipairs({{hold=true},{hold=true,speed=5},{hold=true,speed=25},{hold=true,dt=1/15}})do
 local old,new=visual_scene('old',opts),visual_scene('new',opts)
 old:cast('刺杀剑术');new:cast('刺杀剑术')
 for i=1,1200 do old:step();new:step();if #times(old,0)>=4 then break end end
 local a,b=times(old,0),times(new,0);eq(#a,#b)
 for i,t in ipairs(a)do near(t,b[i],'unchanged continuous attack cadence')end
 eq(old.hero['属性'].mp,new.hero['属性'].mp)
end
local charged={'烈火剑法','翔空剑法','莲月剑法'}
local function charge_scene(version,learned,level)
 local s=scene(version);local h,env=s.hero,s.env
 env.select=select;env.setmetatable=setmetatable;env.rawget=rawget;env.rawset=rawset
 local f=load('hero_api',env);debug.setupvalue(f,2,{Hero=h,['屏幕事件组']={s.target}})
 env['FXru胃啪']=f() -- Actual public actor API, not handwritten charge methods.
 h['主角配置']['技能']={}
 for _,name in ipairs(learned or charged)do h['主角配置']['技能'][name]={level or 0,0,5}end
 local rules=load('rules',env)()
 env['Ux雌']['大堵塞就']=function()return rules end
 env['Ux雌']['啾啾啵啵']=function()return h['主角配置']end
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
 local bufftick=load('buff_tick',env)
 local step=s.step
 s.step=function(self,n)for i=1,n or 1 do step(self);bufftick(h)end end
 -- Hero scalars touched by original BUFF creation/destruction. No combat data
 -- is synthesized in production; these are declared fixture entity fields.
 for _,key in ipairs({'附加_物理伤害','附加_魔法伤害','附加_物理防御','附加_魔法防御','附加_maxhp','附加_maxmp','附加_命中','附加_躲避','附加_暴击','附加_移动速度倍数','附加_攻击速度倍数'})do h['属性'][key]=0 end
 s.rules=rules;s.statuses=statuses;s.selector=selector
 return s
end
local function actual_name(s)return s.hero['当前技能']['对象']['名称']end
local function settle(s)for i=1,1000 do s:step();local state=s.hero['__gm_melee_state_v208'];if s.hero['当前状态']~=3 and(not state or state.ready)then s:step(2);return end end;error('native motion did not finish')end
local function selected(s,name,expected)
 local before=#times(s,0);local ok=s:cast(name);eq(ok,true,'native cast success');eq(#times(s,0),before+1,'one accepted cast')
 eq(actual_name(s),expected,'actual selected skill');s.hero['攻击目标']=nil;s.hero['远程目标']=nil;s.hero['下次技能']=nil;return s.hero['属性'].mp
end
-- Learned-level costs and successful native casting are compared to explicit
-- v215 casts, using original level refresh/setter rather than invented costs.
for level=0,5 do
 for _,name in ipairs(charged)do
  local old,new=charge_scene('old',{name},level),charge_scene('new',{name},level)
  local before=new.hero['属性'].mp
  selected(old,name,name);selected(new,'普通攻击',name)
  near(new.hero['属性'].mp,old.hero['属性'].mp,'same manual/native cost')
  near(before-new.hero['属性'].mp,new.skills[name]['消耗魔法'],'charged cost once')
  local statuses=new.hero['取状态列表'](new.hero);eq(statuses[name..'CD']['持续时间'],10,'original charge cooldown')
  old:step(110);new:step(110)
  eq(#times(old,'damage'),#times(new,'damage'),'same per-skill damage count')
  for i,t in ipairs(times(old,'damage'))do near(t,times(new,'damage')[i],'native per-skill damage time')end
 end
end
-- One, two and three learned: only available skills; no priority starvation.
for _,set in ipairs({{charged[1]},{charged[2]},{charged[3]},{charged[1],charged[2]},{charged[1],charged[3]},{charged[2],charged[3]},charged})do
 local s=charge_scene('new',set)
 for _,name in ipairs(set)do selected(s,'普通攻击',name);settle(s)end
 local before=s.hero['属性'].mp
 selected(s,'普通攻击','普通攻击');eq(before,s.hero['属性'].mp,'all charge cooldowns fall back to normal')
 s:step(1100) -- Actual native BUFF update/expiry/cleanup, not a synthetic timer.
 eq(next(s.hero['取状态列表'](s.hero)),nil,'all original cooldowns expire')
 selected(s,'普通攻击',set[1])
end
-- Input mode enables without charging mana or making temporary buffs permanent.
do
 local s=charge_scene('new');local h=s.hero;local mp=h['属性'].mp
 h['__gm_melee_timing_v208'](h,'input');eq(h['__gm_auto_charge_v216'].enabled[1],true);eq(h['属性'].mp,mp);eq(#h['BUFF组'],0)
 s:step(1300);eq(h['__gm_auto_charge_v216'].enabled[3],true,'session enable does not time out')
 load('reset_session',s.env)(h);eq(h['__gm_auto_charge_v216'],nil,'real init insertion clears per-session mode')
 eq(h['主角配置']['__gm_auto_charge_v216'],nil,'mode not saved in role data')
end
-- Boundary cases, with native selector/real public actor where applicable.
for _,kind in ipairs({'lowmp','blocked','out_of_range','native_cd','disabled','dead','ranged','unlearned','cancel'})do
 local s=charge_scene('new',{charged[1]});local h=s.hero;local mp=h['属性'].mp
 if kind=='lowmp'then h['属性'].mp=0
 elseif kind=='blocked'then s.settings['技能操作']=1
 elseif kind=='out_of_range'then s.target['地图格子'].x=20;s.target['地图坐标'].x=20;s.env['判断是否在攻击范围']=function()return -1 end
 elseif kind=='native_cd'then h['技能配置'](h,charged[1]);h['技能信息'][charged[1]]['开始CD效果']=true
 elseif kind=='disabled'then h['技能配置'](h,charged[1]);h['技能信息'][charged[1]]['可用']=false
 elseif kind=='dead'then h['属性'].hp=0;h['已经死亡']=true
 elseif kind=='unlearned'then h['主角配置']['技能']={}
 elseif kind=='cancel'then h['当前状态']=3 end
 mp=h['属性'].mp
 local ok=s:cast(kind=='ranged'and'火球术'or'普通攻击')
 if kind=='dead'then eq(#h['BUFF组'],0);eq(h['属性'].mp,mp);eq(h['__gm_auto_charge_v216'].last,0,'dead never auto charges')
 elseif kind=='out_of_range'or kind=='blocked'or kind=='cancel'then eq(ok,false,kind..' original block');eq(h['属性'].mp,mp);eq(#h['BUFF组'],0);eq(h['__gm_auto_charge_v216']and h['__gm_auto_charge_v216'].last or 0,0,'failed cast cannot rotate')
 else eq(ok,true,kind);eq(actual_name(s),kind=='ranged'and'火球术'or'普通攻击',kind..' unaffected');eq(#h['BUFF组'],0)end
end
-- New learning/forgetting is observed in this session; manual prepared buffs
-- keep original priority/consumption and don't double-add a charge cooldown.
do
 local s=charge_scene('new',{});selected(s,'普通攻击','普通攻击');settle(s)
 s.hero['主角配置']['技能'][charged[2]]={0,0,5};s.refresh(charged[2]);selected(s,'普通攻击',charged[2]);settle(s)
 s.hero['主角配置']['技能'][charged[2]]=nil;selected(s,'普通攻击','普通攻击')
end
do
 local s=charge_scene('new');local h=s.hero
 eq(h['增加状态'](h,charged[2]),true);eq(h['增加状态'](h,charged[2]..'CD'),true)
 selected(s,'普通攻击',charged[2]);eq(#h['BUFF组'],2,'manual charge no duplicate cooldown')
 settle(s);eq(h['取状态列表'](h)[charged[2]],nil,'native end consumes only actual temporary charge')
 selected(s,'普通攻击',charged[1])
end
-- Runtime cost overrides are honored, including native percentage rounding.
for _,percent in ipairs({false,true})do
 local s=charge_scene('new',{charged[1]});local h=s.hero
 local cost=percent and 1.01 or 2
 s.skills[charged[1]]['消耗魔法']=cost;s.skills[charged[1]]['消耗魔法_百分比']=percent
 local expected=percent and math.ceil(cost/100*h['属性'].maxmp)or cost
 h['属性'].mp=expected
 selected(s,'普通攻击',charged[1]);near(h['属性'].mp,0,'native runtime cost and exact mana boundary')
end
do
 local s=charge_scene('new',{charged[1]});s.hero['技能信息'][charged[1]]=nil
 selected(s,'普通攻击',charged[1]);eq(type(s.hero['技能信息'][charged[1]]),'table','original lazy skill initialization')
end
-- Representative repeated real selector -> native cast -> real BUFF updates.
do
 local s=charge_scene('new');s.hero['属性'].mp=1000000
 local last={};local counts={};local successes=0
 for i=1,200 do
  local before=#times(s,0)
  if s:cast('普通攻击')then
   successes=successes+1;eq(#times(s,0),before+1,'no duplicate cast')
   local name=actual_name(s);counts[name]=(counts[name]or 0)+1
   if name~='普通攻击'then if last[name]then eq(s.now()-last[name]>=10-1e-8,true,'native charge interval respected')end;last[name]=s.now()end
  end
  settle(s)
 end
 eq(successes,200);for _,name in ipairs(charged)do eq((counts[name]or 0)>1,true,'every learned charge keeps being selected')end
 print('AUTO_CHARGE',mode,counts[charged[1]],counts[charged[2]],counts[charged[3]],counts['普通攻击'])
end
print('EFFECT_V216_PASS',mode,checks)
