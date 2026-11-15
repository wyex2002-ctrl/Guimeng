-- Actual sprite update and native effect constructor/display; file/image/map
-- primitives are finite, explicit fixtures (not complete Windows resources).
local names={'普通攻击','基本剑术','攻杀剑术','刺杀剑术','半月弯刀','翔空剑法','烈火剑法','十方斩','莲月剑法','快刀斩麻'}
local function visual_scene(version,opts)
 opts=opts or{};opts.effects=true
 local s=scene(version,opts);local env,h=s.env,s.hero
 -- The standalone database factory precedes the game's startup conversion.
 -- Supply finite startup visual metadata decoded from its actual config text;
 -- don't pretend that the complete game registration/assets were executed.
 for _,skill in pairs(s.skills)do
  for _,key in ipairs({'起手动画','目标动画'})do
   local converted={}
   for _,row in ipairs(split(skill[key],'*'))do
    if row~=''then
     local values=split(row,'|')
     converted[#converted+1]={['动画']=values[1],['位置']=tonumber(values[2])or 0,['跟随']=tonumber(values[3])or 0,['层次']=tonumber(values[4])or 0,['延迟']=tonumber(values[5])or 0}
    end
   end
   skill[key]=converted
  end
 end
 env['Ae冻集']['新动画计次']=0
 env['是否为调试版']=function()return false end
 env['Q_temp_spr']={['显示']=noop}
 local frames={1,2,3,4,5,6,7,8};local acts={}
 for _,name in ipairs(names)do
  for _,suffix in ipairs({'_起手','_命中'})do
   local dirs={};for i=1,8 do dirs[i]=frames end
   acts[name..suffix]={['帧率']=10,['帧数组']=dirs,['中心x']=0,['中心y']=0,['锚点x']=0,['锚点y']=0,['翻转组']={},['混合组']={}}
  end
 end
 acts['火球术_起手']=acts['攻杀剑术_起手'];acts['火球术_命中']=acts['攻杀剑术_命中']
 env['D2D_资源包']={['创建']=function(path)
  return {['取动作组']=function()return acts end,['更新']=load('animation',env),['反向更新']=load('reverse',env),['重置']=load('reset',env),['停止']=false,['可视']=false,['总帧数']=100,['全局计次']=0,['时间累积']=0,['动画帧']=0,['动作结束']=false,['置中心点']=noop,['置颜色']=noop,['置混合模式']=noop,['显示']=noop}
 end}
 env.class=function()
  local methods={};local class={}
  class['创建']=function(...)local obj=setmetatable({},{__index=methods});methods['初始化'](obj,...);return obj end
  return setmetatable(class,{__newindex=function(_,k,v)methods[k]=v end})
 end
 load('effect_class',env)()
 local effects={};local owner={Hero=h,add=function(kind,obj)eq(kind,'屏幕特效');effects[#effects+1]=obj end}
 local factory=load('effect_factory',env);debug.setupvalue(factory,1,owner)
 local original=env.Sys.run
 env.Sys.run=function(op,...)
  if op=='显示特效'then
   local args={n=select('#',...),...};local effect=factory(...)
   s.events[#s.events+1]={op='effect',args=args,object=effect,t=s.now()}
   return effect
  end
  return original(op,...)
 end
 env['Q_地图']['置格子信息']=noop
 h['绑定特效']=function(_,effect)effects[#effects+1]=effect end
 s.target['绑定特效']=h['绑定特效']
 s.target['BUFF状态更新']=noop
 s.target['被击中']=function(target,attacker,damage)target['属性'].hp=target['属性'].hp-damage end
 -- Re-enter the original damage method so target sword effects (快刀) aren't
 -- omitted by the finite final-damage boundary in the reused timing fixture.
 h['回调脚本']['发生伤害']=function()return{1,0,0}end
 h['发生伤害']=function(self,target,skill,...)
  s.events[#s.events+1]={op='damage',t=s.now(),name=skill['名称']}
  return s.methods['发生伤害'](self,target,skill['名称'],...)
 end
 s.effects=effects;s.make_effect=factory
 return s
end
local function effect_events(s)local t={};for _,e in ipairs(s.events)do if e.op=='effect'then t[#t+1]=e end end;return t end
local function display_until_gone(s,e)
 local count=0
 while not e.object['已经消失']and count<300 do e.object['显示'](e.object);count=count+1 end
 eq(e.object['已经消失'],true,'native effect ends and cleans up')
 return count*s.env.dt
end
for _,name in ipairs(names)do
 local old,new=visual_scene('old'),visual_scene('new')
 eq(old:cast(name),true);eq(new:cast(name),true)
 old:step(110);new:step(110)
 local a,b=effect_events(old),effect_events(new)
 eq(#a,#b,'effect count');eq(#times(old,'damage'),#times(new,'damage'),'damage count')
 for i,t in ipairs(times(old,'damage'))do near(t,times(new,'damage')[i],'damage time preserved')end
 for i,e in ipairs(a)do
  local f=b[i];near(e.t,f.t,'effect onset unchanged');eq(e.args.n,f.args.n,'nil argument count')
  for j=1,e.args.n do if j~=13 and j~=8 then eq(e.args[j],f.args[j],'effect arg '..j)end end
  near(f.object['播放速度'],e.object['播放速度']*.5,'native interval halves')
  local duration_old,duration_new=display_until_gone(old,e),display_until_gone(new,f)
  eq(duration_new<duration_old,true,'effect plays faster')
  if name=='刺杀剑术'then print('SWORD_EFFECT',duration_old,duration_new,'onset',e.t,'damage',times(new,'damage')[1])end
 end
 if name~='普通攻击'and name~='基本剑术'then eq(#a>0,true,name..' real configured visual not empty')end
end
-- Stable attack schedules, costs and damage callbacks across representative
-- speed/frame-rate cases, with real effects enabled during attacks.
for _,opts in ipairs({{hold=true},{hold=true,speed=5},{hold=true,speed=25},{hold=true,dt=1/60},{hold=true,dt=1/15}})do
 local old,new=visual_scene('old',opts),visual_scene('new',opts)
 old:cast('刺杀剑术');new:cast('刺杀剑术')
 for i=1,1000 do old:step();new:step();if #times(old,0)>=4 then break end end
 local a,b=times(old,0),times(new,0);eq(#a,#b)
 for i,t in ipairs(a)do near(t,b[i],'accepted attack timing')end
 eq(old.hero['属性'].mp,new.hero['属性'].mp)
end
-- Non-warrior visuals keep their exact call arguments, including nil speed.
do
 local old,new=visual_scene('old'),visual_scene('new')
 for _,s in ipairs({old,new})do
  -- Probe the unchanged non-warrior target-visual branch with finite art.
  s.skills['火球术']['目标动画']=s.skills['快刀斩麻']['目标动画']
  s.hero['发生伤害'](s.hero,s.target,s.skills['火球术'],1,0,false,true)
 end
 local a,b=effect_events(old),effect_events(new);eq(#a>0,true);eq(#a,#b)
 for i,e in ipairs(a)do for j=1,e.args.n do if j~=8 then eq(e.args[j],b[i].args[j],'unrelated visual args')end end;near(e.object['播放速度'],b[i].object['播放速度'])end
end
-- Roughly 200 representative effect lifecycles, no multiplied stress matrix.
do
 local old,new=visual_scene('old'),visual_scene('new')
 for i=1,200 do
  local a=old.hero['__gm_melee_timing_v208'](old.hero,'effect',1,'半月弯刀')
  local b=new.hero['__gm_melee_timing_v208'](new.hero,'effect',1,'半月弯刀')
  eq(a,1);eq(b,.5)
  local path='fixture.empak,半月弯刀_起手'
  local x={object=old.make_effect(path,0,0,1,'默认位置',1,1,old.hero,0,0,nil,1,a,0,0,0)}
  local y={object=new.make_effect(path,0,0,1,'默认位置',1,1,new.hero,0,0,nil,1,b,0,0,0)}
  eq(display_until_gone(new,y)<display_until_gone(old,x),true,'representative native effect lifecycle')
 end
end
print('EFFECT_V211_PASS',mode,checks,'native dispatch/factory/effect class/update; finite image/map/final damage primitives; no Windows test')
