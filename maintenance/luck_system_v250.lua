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
 local function mercenary()
  local merc=E.Ux雌 and E.Ux雌.佣兵对象
  if type(merc)=='function'then merc=merc()end
  return type(merc)=='table'and merc or nil
 end
 local function luck_owner(actor)
  if type(actor)~='table'then return nil end
  local hero=E.FXru胃啪;local merc=mercenary();local mercid=merc and finite(merc.id)
  if actor==hero or actor==S.Hero then return hero end
  local seen={}
  for depth=1,8 do
   local id=finite(actor.id)
   if id==0 then return hero end
   if not id or id<=0 or id%1~=0 or seen[id]then return nil end;seen[id]=true
   if mercid and mercid>0 and id==mercid then return merc end
   local owner=finite(actor.主人id)
   if not owner then
    local pet=actor.宠物配置;local who=type(pet)=='table'and pet.主人 or nil
    owner=finite(type(who)=='table'and who.id or who)
   end
   if owner==0 then return hero end
   if mercid and mercid>0 and owner==mercid then return merc end
   if not owner or owner<0 or owner%1~=0 then return nil end
   actor=lookup(owner);if type(actor)~='table'then return nil end
  end
  return nil
 end
 local function probability(actor,skill,guild,kind)
  local hero=luck_owner(actor);if not hero then return nil end
  local attrs=hero.属性
  local companion=hero~=E.FXru胃啪
  local luck=bounded(attrs and attrs.幸运,0,companion and 7 or 9)
  local context={luck=luck,actor=actor,owner=hero,skill=skill,kind=kind,companion=companion}
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
  local plain=text
  if color then text='#c('..color..')'..text..'#W'end
  if out and type(out.孔爱琴泥)=='function'then out.孔爱琴泥(text,1)end
  local hints=u and u.托管显示
  if hints and type(hints.屏幕提示)=='function'then hints.屏幕提示(plain,color or -1,true)end
 end
 local function raw_merc(merc)
  if not merc then return nil end
  local id=finite(merc.id);if not id or id<=0 then return nil end
  for _,actor in pairs(S.屏幕事件组 or{})do if type(actor)=='table'and actor.id==id then return actor end end
 end
 local function use(source)
  source=finite(source)
  if not source or source%1~=0 then return false end
  local story=E.Ux雌 and E.Ux雌.版本选择
  if(story=='前尘忆梦'and source>=1 and source<=6)or(story=='来世续缘'and source>=21 and source<=26)then return false end
  local sourcebox=S.包裹物品组 and S.包裹物品组[source]
  local oil=sourcebox and sourcebox.道具
  if not oil or oil.名称~='祝福油'or(finite(oil.数量)or 0)<1 then return false end
  -- Original item-event routes companion consumables to slots 333..396.
  local is_merc=source>=333 and source<=396
  local target,hero=E.FXru胃啪,S.Hero
  -- Do not fall back to the hero if the companion actor is absent.
  if is_merc then target=mercenary();hero=raw_merc(target)end
  local bag=S.包裹物品组;local mount
  local function candidate(slot)
   local box=slot and slot.拿起==false and bag and bag[slot.标识]or nil
   local it=box and box.道具
   if type(it)=='table'and it.子类=='坐骑'then return it end
  end
  if hero then
   for _,slot in ipairs(hero.装备格子 or{})do mount=candidate(slot);if mount then break end end
  elseif is_merc then
   -- Persistent companion equipment controls exist even when not summoned.
   for _,win in ipairs(S.界面_窗口_数组 or{})do
    if win.名称=='佣兵窗口'or win.名称=='佣兵窗口2'then
     for _,c in ipairs(win.控件组 or{})do
      if c.类型==6 and c.格子ID and c.格子ID>396 and not c.背包格子 then
       mount=candidate(c.对象)
       if mount and target then
        for _,bound in ipairs(c.对象.绑定事件 or{})do if bound.id==target.id then hero=bound;break end end
       end
       if mount then break end
      end
     end
    end
    if mount then break end
   end
  end
  local prefix=is_merc and '佣兵'or ''
  if not mount then message(is_merc and '请先为佣兵装备坐骑后再使用祝福油。'or'请先装备坐骑后再使用祝福油。');return false end
  if S.游戏道具组 and mount==S.游戏道具组[mount.名称]then return false end
  local attrs=mount.属性;if type(attrs)~='table'then return false end
  local value=attrs.幸运;local luck=value==nil and 0 or finite(value)
  if not luck or luck%1~=0 then return false end
  if luck>=7 then message(prefix..'坐骑幸运已达到上限 +7。');return false end
  luck=math.max(0,luck)
  local result,new='success',1
  if luck>0 then
   local a,b,c=Rules.enhancement({luck=luck,item=mount,owner=target,source=source,companion=is_merc,kind='enhancement'})
   a,b,c=finite(a),finite(b),finite(c)
   if not a or not b or not c or a<0 or b<0 or c<0 or a+b+c<=0 then return false end
   local roll=random()*(a+b+c)
   if roll<a then new=luck+1 elseif roll<a+b then result='loss';new=luck-1 else result='same';new=luck end
  end
  -- Copy nested attributes before editing: never mutate a public item template.
  local updated=table.copy(attrs,true);updated.幸运=math.max(0,math.min(7,new))
  mount.属性=S.数据保护(updated,true)
  if hero then hero:属性更新()end
  if result=='success'then message('祝福油使用成功，'..prefix..'幸运提升至 +'..new..'！',-8726117)
  elseif result=='loss'then message('祝福油使用失败，'..prefix..'幸运下降至 +'..new..'。',-880748)
  else message('祝福油使用无效'..(is_merc and'（佣兵）'or'')..'。',-8726117)end
  return true -- Original inventory consumes exactly one, for every valid result.
 end
 local function line(item,base)
  if type(item)~='table'or item.子类~='坐骑'then return ''end
  local n=finite(item.幸运)or 0;if n<=0 then return ''end
  if type(base)~='table'then base=E.Gly独.取道具信息_名称(item.名称)end
  local original=finite(type(base)=='table'and base.幸运)or 0
  local bonus=n-original
  local suffix=bonus==0 and ''or('（'..(bonus>=0 and'+'or'')..bonus..'）')
  local style='宋_9_幸运'
  if item.分类=='装备'and finite(type(item.附加)=='table'and item.附加.条数)==7 then style='宋_9_鎏金'end
  return '\n#md#f('..style..',#c(-1720246)幸运：'..n..suffix..')#W'
 end
 local function oil_event(kind,source)
  if kind~=3 or type(source)~='number'or source<333 or source>396 then return false end
  local box=S.包裹物品组 and S.包裹物品组[source];local item=box and box.道具
  return type(item)=='table'and item.名称=='祝福油'
 end
 E.__gm_oil_event_v245=oil_event
 E.__gm_luck_attack_v244=attack;E.__gm_luck_pair_v244=attack_pair
 E.__gm_luck_defense_v244=defense;E.__gm_luck_use_v244=use;E.__gm_luck_line_v244=line
end
