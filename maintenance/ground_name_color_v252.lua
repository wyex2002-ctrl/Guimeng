-- Ground-label tint only. Never write the item/template/inventory color.
return function(item,current)
 if type(item)~='table'then return current end
 local name=item.名称
 if type(name)~='string'then return current end
 if item.分类=='特殊'and(name=='金币'or name:find('金币_',1,true)==1)then return -6240 end -- #FFE7A0
 if item.分类~='道具'or item.子类~='消耗品'then return current end
 if name:sub(1,1)=='Q'then name=name:sub(2)end
 if name=='金创药'or name=='魔法药'or name:find('金创药_',1,true)==1 or name:find('魔法药_',1,true)==1 then return -1 end -- white
 return current
end
