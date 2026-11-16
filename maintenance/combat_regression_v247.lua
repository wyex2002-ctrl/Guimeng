-- Complete native hero attack / skill-instance / area collection / final damage
-- dispatch. Map lookup, attack conversion and final combat outcome are finite.
local function actor(id,x,y)
 return {id=id,地图格子={x=x,y=y},地图坐标={x=x,y=y},属性={hp=100000},所属阵营='敌方',是否有效=true,锚点x=0,锚点y=0}
end
local function setup(version,name,direction)
 local s=scene(version,{bound=name,convert=name});local h=s.hero
 h.方向=direction or 1;s.env.核心.取两点间方向=function()return direction or 1 end
 s.actors={s.target};s.lookups={}
 s.env.Q_地图.取格子信息=function(x,y,faction)
  s.lookups[#s.lookups+1]={x,y,faction};local out={}
  for _,a in ipairs(s.actors)do if faction==a.所属阵营 and a.地图格子.x==x and a.地图格子.y==y then out[#out+1]=a end end
  return out
 end
 -- Explicit boundary: preserve native skill dispatch and record its final
 -- target/skill/power; damage, evasion and health formulas are not mocked as hits.
 h.发生伤害=function(_,target,skill,power)
  s.events[#s.events+1]={op='damage',t=s.now(),target=target,name=skill.名称,power=power};return {true,1,0}
 end
 return s
end
local function launch(s,auto)
 if auto then s.hero.开始物理攻击动作(s.hero,true,true)else eq(s:cast('翔空剑法'),true)end
 eq(#s.hero.释放技能组,1,'one native skill instance')
 local state=upstate(s);eq(state.技能信息.对象.名称,'翔空剑法')
 return state
end
local function stop(s)s.hero.攻击目标=nil;s.hero.远程目标=nil;s.hero.下次技能=nil end
local function damage(s,target)
 local out={};for _,e in ipairs(s.events)do if e.op=='damage'and(not target or e.target==target)then out[#out+1]=e end end;return out
end
local function move(a,x,y)a.地图格子={x=x,y=y};a.地图坐标={x=x,y=y}end
-- Reproduce the reported gap via the real automatic melee entry, not a direct
-- call to the new merge helper. The old version must miss this moved target.
for _,version in ipairs({'old','new'})do
 local s=setup(version,'翔空剑法');local state=launch(s,true)
 if version=='new'then eq(state.__gm_cisha_target_v139,s.target,'capture original launch target')end
 s:step(1);move(s.target,20,20);stop(s);s:step(110)
 eq(#damage(s,s.target),version=='old'and 0 or 1,'moving lock fallback')
 if version=='new'then near(damage(s)[1].power,1);near(damage(s)[1].t,.35)end
end
-- All eight original 5-cell directions and 50/80/100 ratios remain intact.
for direction=1,8 do
 local old,new=setup('old','翔空剑法',direction),setup('new','翔空剑法',direction)
 local pair={old,new};local states={}
 for i,s in ipairs(pair)do
  states[i]=launch(s,true);s:step(1);move(s.target,20,20);stop(s)
  local cells=s.skills.翔空剑法.作用范围[direction];eq(#cells,5)
  for j,cell in ipairs(cells)do s.actors[#s.actors+1]=actor(100+j,cell.x,cell.y)end
  s:step(110)
 end
 local a,b=damage(old),damage(new);eq(#a,5);eq(#b,6)
 for j,e in ipairs(a)do
  eq(e.target.id,b[j].target.id,'other cells keep original order');near(e.power,b[j].power,'native cell ratio');near(e.t,b[j].t,'native damage delay')
 end
 for j,lookup in ipairs(old.lookups)do local current=new.lookups[j];eq(lookup[1],current[1]);eq(lookup[2],current[2]);eq(lookup[3],current[3])end
 eq(#old.lookups,#new.lookups,'no extra map cell query');eq(#damage(new,new.target),1)
 eq(new.hero.属性.mp,old.hero.属性.mp,'cost unchanged');eq(states[1].伤害产生_已结束,states[2].伤害产生_已结束)
end
-- If the original lock is already in any native cell, retain that ratio and
-- damage it only once. Unrelated duplicate rows also retain native behavior.
for cell=1,5 do
 local old,new=setup('old','翔空剑法'),setup('new','翔空剑法')
 for _,s in ipairs({old,new})do
  launch(s,true);s:step(1);stop(s);local pos=s.skills.翔空剑法.作用范围[1][cell];move(s.target,pos.x,pos.y);s:step(110)
 end
 eq(#damage(old),1);eq(#damage(new),1);near(damage(old)[1].power,damage(new)[1].power)
end
-- A primary returned twice is judged once, but unrelated duplicate native
-- rows are deliberately left alone so only the requested target rule changes.
do
 local old,new=setup('old','翔空剑法'),setup('new','翔空剑法')
 for _,s in ipairs({old,new})do
  launch(s,true);s:step(1);stop(s)
  local cell=s.skills.翔空剑法.作用范围[1][3];move(s.target,cell.x,cell.y)
  local other=actor(88,cell.x,cell.y);s.other=other;s.actors={s.target,s.target,other,other};s:step(110)
 end
 eq(#damage(old,old.target),2);eq(#damage(new,new.target),1)
 eq(#damage(old,old.other),2);eq(#damage(new,new.other),2)
end
-- Selection changes after launch cannot redirect the committed strike.
do
 local s=setup('new','翔空剑法');launch(s,true);s:step(1);move(s.target,20,20)
 local other=actor(77,30,30);s.actors[#s.actors+1]=other;s.hero.攻击目标=other;s.hero.远程目标=other
 s:step(39);eq(#damage(s,s.target),1);eq(#damage(s,other),0);stop(s)
end
-- Do not add dead, removed, invalid, untargetable, friendly or absent locks.
for _,kind in ipairs({'dead','removed','invalid','untargetable','friendly','no_id','no_attributes','bad_hp','nan_hp'})do
 local s=setup('new','翔空剑法');launch(s,true);s:step(1);move(s.target,20,20);stop(s)
 if kind=='dead'then s.target.属性.hp=0
 elseif kind=='removed'then s.target.已经消失=true
 elseif kind=='invalid'then s.target.是否有效=false
 elseif kind=='untargetable'then s.target.不可选中=true
 elseif kind=='friendly'then s.target.所属阵营='友方'
 elseif kind=='no_id'then s.target.id=nil
 elseif kind=='no_attributes'then s.target.属性=nil
 elseif kind=='bad_hp'then s.target.属性.hp='bad'
 elseif kind=='nan_hp'then s.target.属性.hp=0/0 end
 s:step(110);eq(#damage(s),0,kind..' is not a forced target')
end
-- Real no-target (ground) skill construction: no fallback and native area only.
do
 local s=setup('new','翔空剑法');s.hero.攻击目标=nil
 eq(s.hero.技能释放(s.hero,'翔空剑法',true,nil,nil,false),true)
 local state=upstate(s);eq(state.__gm_cisha_target_v139,nil);s.actors={};stop(s);s:step(110);eq(#damage(s),0)
end
-- Existing thrust fallback and other melee behavior compare against 246.
for _,name in ipairs({'刺杀剑术','烈火剑法','莲月剑法','半月弯刀','十方斩','普通攻击'})do
 local a,b=setup('old',name),setup('new',name)
 eq(a:cast(name),true);eq(b:cast(name),true);a:step(1);b:step(1)
 move(a.target,20,20);move(b.target,20,20);stop(a);stop(b);a:step(110);b:step(110)
 eq(#damage(a),#damage(b),name..' moving lock unchanged')
 for i,e in ipairs(damage(a))do near(e.t,damage(b)[i].t);near(e.power,damage(b)[i].power)end
end
-- Representative mixed calls stress the captured instance under hot traces.
for i=1,200 do
 local s=setup('new','翔空剑法');launch(s,i%2==0);s:step(1);stop(s)
 if i%3==0 then move(s.target,20,20)else local cell=s.skills.翔空剑法.作用范围[1][i%5+1];move(s.target,cell.x,cell.y)end
 s:step(60);eq(#damage(s,s.target),1,'one judgement per committed skill')
end
print('COMBAT_V247_PASS',mode,checks)
