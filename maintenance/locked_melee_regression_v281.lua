local function actor(id, x, y)
 return {id=id, 地图格子={x=x,y=y}, 地图坐标={x=x,y=y}, 属性={hp=100000},
  所属阵营='敌方', 是否有效=true, 锚点x=0, 锚点y=0}
end

local function setup(version, skill, direction)
 direction = direction or 1
 local s = scene(version, {bound=skill, convert=skill})
 s.hero.方向 = direction
 s.env.核心.取两点间方向 = function() return direction end
 s.actors, s.lookups = {s.target}, {}
 s.env.Q_地图.取格子信息 = function(x, y, faction)
  s.lookups[#s.lookups+1] = {x,y,faction}
  local out = {}
  for _, a in ipairs(s.actors) do
   if a.所属阵营 == faction and a.地图格子.x == x and a.地图格子.y == y then
    out[#out+1] = a
   end
  end
  return out
 end
 s.hero.发生伤害 = function(_, target, _, power)
  s.events[#s.events+1] = {op='damage',t=s.now(),target=target,power=power}
  return {true,1,0}
 end
 return s
end

local function launch(s, skill)
 s.hero.开始物理攻击动作(s.hero, true, true)
 eq(#s.hero.释放技能组, 1, 'one native skill instance')
 local state = upstate(s)
 eq(state.技能信息.对象.名称, skill)
 eq(#state.伤害进度, 1, 'one native damage phase')
 return state
end

local function endInput(s)
 s.hero.攻击目标, s.hero.远程目标, s.hero.下次技能 = nil, nil, nil
end

local function damage(s, target)
 local out = {}
 for _, e in ipairs(s.events) do
  if e.op == 'damage' and (not target or e.target == target) then out[#out+1] = e end
 end
 return out
end

local function move(a, x, y)
 a.地图格子, a.地图坐标 = {x=x,y=y}, {x=x,y=y}
end

local added = {'半月弯刀', '十方斩'}
for which, name in ipairs(added) do
 for direction = 1, 8 do
  local old, new = setup('old',name,direction), setup('new',name,direction)
  for i, s in ipairs({old,new}) do
   local state = launch(s,name)
   eq(state.__gm_cisha_target_v139, i == 2 and s.target or nil)
   s:step(1)
   move(s.target,20,20)
   endInput(s)
   local cells = s.skills[name].作用范围[direction]
   eq(#cells, which == 1 and 5 or 8)
   for j, cell in ipairs(cells) do s.actors[#s.actors+1] = actor(100+j,cell.x,cell.y) end
   s:step(110)
  end
  local a,b = damage(old),damage(new)
  eq(#a, which == 1 and 5 or 8)
  eq(#b,#a+1); eq(#damage(old,old.target),0); eq(#damage(new,new.target),1)
  near(b[#b].power,1)
  for j,e in ipairs(a) do
   eq(b[j].target.id,e.target.id)
   near(b[j].power,e.power)
   near(b[j].t,e.t)
   near(b[#b].t,e.t)
  end
  eq(#old.lookups,#new.lookups)
  for j,cell in ipairs(old.lookups) do
   for k=1,3 do eq(new.lookups[j][k],cell[k],'native map query') end
  end
  eq(new.hero.属性.mp,old.hero.属性.mp)
 end

 for _,kind in ipairs({'in_cell','duplicate','retarget','no_lock','dead','removed','invalid','untargetable','friendly','bad_hp','nan_hp'}) do
  local old, new = setup('old',name), setup('new',name)
  for _, s in ipairs({old,new}) do
   if kind=='no_lock' then
    endInput(s)
    eq(s.hero.技能释放(s.hero,name,true,nil,nil,false),true)
    eq(upstate(s).__gm_cisha_target_v139,nil)
   else
    launch(s,name)
   end
   s:step(1)
   endInput(s)
   local cell = s.skills[name].作用范围[1][1]
   s.other = actor(77,cell.x,cell.y)
   s.actors = {s.target,s.other}
   move(s.target,20,20)
   if kind=='in_cell' or kind=='duplicate' then
    move(s.target,cell.x,cell.y)
    if kind=='duplicate' then s.actors = {s.target,s.other,s.target,s.other} end
   elseif kind=='retarget' then
    s.next = actor(88,30,30)
    s.actors[#s.actors+1] = s.next
    s.hero.攻击目标,s.hero.远程目标 = s.next,s.next
   elseif kind=='dead' then s.target.属性.hp=0
   elseif kind=='removed' then s.target.已经消失=true
   elseif kind=='invalid' then s.target.是否有效=false
   elseif kind=='untargetable' then s.target.不可选中=true
   elseif kind=='friendly' then s.target.所属阵营='友方'
   elseif kind=='bad_hp' then s.target.属性.hp='bad'
   elseif kind=='nan_hp' then s.target.属性.hp=0/0
   end
   s:step(39)
   endInput(s)
   s:step(72)
  end
  local a,b = damage(old,old.target),damage(new,new.target)
  eq(#b,(kind=='in_cell' or kind=='duplicate' or kind=='retarget') and 1 or 0,kind)
  if kind=='in_cell' or kind=='duplicate' then near(b[1].power,a[1].power) end
  if kind=='duplicate' then eq(#a,2);eq(#damage(new,new.other),2) end
  if kind=='retarget' then eq(#damage(new,new.next),0) end
  local ao,bo=damage(old,old.other),damage(new,new.other)
  eq(#ao,#bo)
  for i,e in ipairs(ao) do near(e.power,bo[i].power);near(e.t,bo[i].t) end
 end
end

for _, name in ipairs({'刺杀剑术','翔空剑法','烈火剑法','莲月剑法','普通攻击'}) do
 local old,new=setup('old',name),setup('new',name)
 for _,s in ipairs({old,new}) do
  launch(s,name); s:step(1); endInput(s); move(s.target,20,20); s:step(110)
 end
 local a,b=damage(old),damage(new)
 eq(#a,#b,name)
 for i,e in ipairs(a)do near(e.t,b[i].t);near(e.power,b[i].power)end
end

for i=1,200 do
 local name=added[(i-1)%2+1]
 local s=setup('new',name)
 launch(s,name);s:step(1);endInput(s)
 local cell=s.skills[name].作用范围[1][1]
 if i%3==0 then move(s.target,cell.x,cell.y) else move(s.target,20,20) end
 s:step(100)
 eq(#damage(s,s.target),1,'single original-target judgement per strike')
end
print('LOCKED_MELEE_V281_PASS',mode,checks)
