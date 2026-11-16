-- Native event environment: use only existing public Sys operations.
return function(victim,killer,former_owner)
 if type(victim)~='table'or victim.所属阵营~='敌方'or victim.__gm_oil_done_v242 then return end
 if former_owner~=nil and former_owner~=-1 then return end
 local stats=victim.属性
 if type(stats)~='table'or type(stats.hp)~='number'or stats.hp~=stats.hp or stats.hp>0 then return end
 killer=tonumber(killer);if not killer or killer<0 or killer%1~=0 then return end
 local hero=Sys.get('hero');if type(hero)~='table'then return end
 local U=Ae冻
 local merc=type(U)=='table'and U.佣兵对象 or nil
 if type(merc)=='function'then merc=merc()end
 local mercid=type(merc)=='table'and tonumber(merc.id)or tonumber(merc)
 local credited,current=killer==0,killer
 for depth=1,8 do
  if credited then break end
  if mercid and mercid>0 and current==mercid then credited=true;break end
  local actor=Sys.get('obj',current);if type(actor)~='table'then break end
  local owner=tonumber(actor.主人id)
  if not owner then
   local pet=actor.宠物配置;owner=type(pet)=='table'and pet.主人 or nil
   if type(owner)=='table'then owner=owner.id end
   owner=tonumber(owner)
  end
  if not owner or owner<0 or owner%1~=0 then break end
  if owner==0 then credited=true;break end
  current=owner
 end
 if not credited then return end
 local at=victim.地图格子;if type(at)~='table'then return end
 local template=Sys.get('item','祝福油');if type(template)~='table'then return end
 local item=table.copy(template,true)
 item.附加=Sys.run('数据保护',item.附加,true)
 item.属性=Sys.run('数据保护',item.属性,true)
 item=Sys.run('数据保护',item)
 -- Extra test drop is one item, independent of normal drop multipliers.
 Sys.run('掉落物品',true,item,1,at.x,at.y,at.x,at.y)
 victim.__gm_oil_done_v242=true
end
