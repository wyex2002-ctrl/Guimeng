return function(S,E)
 -- RULES_GENERATED
 local function finite(v)local n=tonumber(v);if n and n==n and n~=math.huge and n~=-math.huge then return n end end
 local function bounded(v,lo,hi)local n=finite(v)or lo;return math.max(lo,math.min(hi,n))end
 local function random()
  local n=引擎:取随机小数(0,1)
  assert(type(n)=='number'and n==n,'invalid luck random value')
  return math.max(0,math.min(1-2^-53,n))
 end
 local function lookup(id)
  if id==0 then return E.FXru胃啪 end
  if E.Gly独 then return E.Gly独.事件对象(id)end
 end
 local function owned(actor)
  if type(actor)~='table'then return false end
  local hero=E.FXru胃啪
  if actor==hero or actor==S.Hero then return true end
  local id=finite(actor.id)
  local merc=E.Ux雌 and E.Ux雌.佣兵对象
  if type(merc)=='function'then merc=merc()end
  local mercid=finite(type(merc)=='table'and merc.id or merc)
  if mercid and mercid>0 and id==mercid then return false end
  if id==0 then return hero~=nil end
  local seen={}
  for depth=1,8 do
   if not id or id<=0 or id%1~=0 or seen[id]then return false end;seen[id]=true
   local owner=finite(actor.主人id)
   if not owner then
    local pet=actor.宠物配置;local who=type(pet)=='table'and pet.主人 or nil
    owner=finite(type(who)=='table'and who.id or who)
   end
   if mercid and mercid>0 and owner==mercid then return false end
   if owner==0 then return true end
   if not owner or owner<0 or owner%1~=0 then return false end
   actor=lookup(owner);if type(actor)~='table'then return false end;id=owner
  end
  return false
 end
 local function probability(actor,skill,guild,kind)
  if not owned(actor)then return nil end
  local hero=E.FXru胃啪;local attrs=hero and hero.属性
  local luck=bounded(attrs and attrs.幸运,0,7)
  local context={luck=luck,actor=actor,owner=hero,skill=skill,kind=kind}
  local p=bounded(Rules.equipment(context),0,1)
  if kind=='attack'then
   p=p+bounded(type(skill)=='table'and skill.幸运属性,0,100)/100
   if guild then p=p+bounded(Rules.guild_attack,0,1) end -- Original integer roll >=90 on 1..100.
  end
  return math.min(1,p)
 end
 local function lucky(actor,skill,guild,kind)
  local p=probability(actor,skill,guild,kind)
  return p~=nil and random()<p
 end
 local function attack_pair(lo,hi,sl,sh,skill,actor,guild)
  local a=E.Gly独.取随机数(lo,hi);local b=E.Gly独.取随机数(sl,sh)
  local marks=type(guild)=='table'and guild.行会选中 or nil
  if lucky(actor,skill,type(marks)=='table'and marks.幸运加持~=nil,'attack')then return math.max(lo,hi),math.max(sl,sh)end
  return a,b
 end
 local function attack(lo,hi,skill,actor)
  local n=E.Gly独.取随机数(lo,hi)
  if lucky(actor,skill,false,'attack')then return math.max(lo,hi)end
  return n
 end
 local function defense(actor,is_hero)
  local lo,hi,ml,mh
  if is_hero then
   local u=E.Ux雌
   lo=math.floor(bounded((finite(u.主角最小防御)or 0)+(finite(u.主角最小魔防)or 0),0,2147483647))
   hi=math.floor(bounded((finite(u.主角最大防御)or 0)+(finite(u.主角最大魔防)or 0),lo,2147483647))
   ml,mh=lo,hi
  else
   local a=actor.属性;local stat=E.__gm_stat_v162;local u=E.Ux雌
   lo=stat(1,actor,a,'最小防御',u);hi=stat(1,actor,a,'最大防御',u)
   ml=stat(1,actor,a,'最小魔防',u);mh=stat(1,actor,a,'最大魔防',u)
  end
  local a=E.Gly独.取随机数(lo,hi);local b=E.Gly独.取随机数(ml,mh)
  if lucky(actor,nil,false,'defense')then return math.max(lo,hi),math.max(ml,mh)end
  return a,b
 end
 local function message(text,color)
  local u=E.Ux雌;local out=u and u.开挖机的
  if color then text='#c('..color..')'..text..'#W'end
  if out and type(out.孔爱琴泥)=='function'then out.孔爱琴泥(text,1)end
 end
 local function use()
  local hero=S.Hero;local bag=S.包裹物品组;local mount
  if hero and bag then
   for _,slot in ipairs(hero.装备格子 or{})do
    local box=slot.拿起==false and bag[slot.标识]or nil
    local it=box and box.道具
    if type(it)=='table'and it.子类=='坐骑'then mount=it;break end
   end
  end
  if not mount then message('请先装备坐骑后再使用祝福油。');return false end
  if S.游戏道具组 and mount==S.游戏道具组[mount.名称]then return false end
  local attrs=mount.属性;if type(attrs)~='table'then return false end
  local value=attrs.幸运;local luck=value==nil and 0 or finite(value)
  if not luck or luck%1~=0 then return false end
  if luck>=7 then message('坐骑幸运已达到上限 +7。');return false end
  luck=math.max(0,luck)
  local result,new='success',1
  if luck>0 then
   local a,b,c=Rules.enhancement({luck=luck,item=mount,owner=E.FXru胃啪,kind='enhancement'})
   a,b,c=finite(a),finite(b),finite(c)
   if not a or not b or not c or a<0 or b<0 or c<0 or a+b+c<=0 then return false end
   local roll=random()*(a+b+c)
   if roll<a then new=luck+1 elseif roll<a+b then result='loss';new=luck-1 else result='same';new=luck end
  end
  -- Copy nested attributes before editing: never mutate a public item template.
  local updated=table.copy(attrs,true);updated.幸运=math.max(0,math.min(7,new))
  mount.属性=S.数据保护(updated,true)
  hero:属性更新()
  if result=='success'then message('祝福油使用成功，坐骑幸运提升至 +'..new..'！',-13465000)
  elseif result=='loss'then message('祝福油使用失败，坐骑幸运下降至 +'..new..'。',-5026736)
  else message('祝福油使用后，坐骑幸运没有变化。',-13465000)end
  return true -- Original inventory consumes exactly one, for every valid result.
 end
 local function line(item,base)
  if type(item)~='table'or item.子类~='坐骑'then return ''end
  local n=finite(item.幸运)or 0;if n<=0 then return ''end
  local original=finite(type(base)=='table'and base.幸运)or 0
  local bonus=n-original
  local suffix=bonus==0 and ''or('（'..(bonus>=0 and'+'or'')..bonus..'）')
  return '\n#md#f(宋_9_幸运,#c(-1720246)幸运：'..n..suffix..')#W'
 end
 E.__gm_luck_attack_v244=attack;E.__gm_luck_pair_v244=attack_pair
 E.__gm_luck_defense_v244=defense;E.__gm_luck_use_v244=use;E.__gm_luck_line_v244=line
end
