-- Native event instances, not the public read-only entity proxy.
return function(self,target)
 if type(target)~='table' or type(self.属性)~='table' then return false end
 local name=self.属性.名称
 local guard=name=='卫士' or name=='大刀卫士' or name=='弓箭卫士'
  or name=='大刀守卫' or name=='弓箭守卫' or name=='城镇卫士'
  or name=='守卫' or name=='弓箭手' or name=='大刀'
 if not guard then return false end
 if self.宠物配置 and self.宠物配置.主人 then return false end
 local hero=self.Hero
 if type(hero)~='table' then return false end
 local pet=target.宠物配置
 local owner=type(pet)=='table' and pet.主人
 -- Bound the owner chain; ignore unowned monsters and cyclic/broken ownership.
 for i=1,8 do
  if type(owner)~='table' then return false end
  if owner==hero.主角 or owner==hero.佣兵 then return true end
  pet=owner.宠物配置
  owner=type(pet)=='table' and pet.主人
 end
 return false
end
