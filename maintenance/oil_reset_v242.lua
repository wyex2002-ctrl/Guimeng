return function(S,original)
 return function(id,change,mode)
  local box=S.包裹物品组[id];local item=box and box.道具
  local incoming=type(change)=='table'and change.名称 or nil
  local oil=incoming=='祝福油'or(incoming==nil and item and item.名称=='祝福油')
  if oil and type(change)=='table'then
   local raw=type(change.__数据)=='table'and change.__数据 or change
   local copy={}
   for k,v in pairs(raw)do if k~='__数据'and k~='__p'and k~='__c'then copy[k]=v end end
   local image=copy.格子底图
   if image=='道具|祝福油|包裹图标'or type(image)=='number'or(type(image)=='string'and image:find('gm_blessing_oil_v',1,true)==1)then copy.格子底图=''end
   copy.颜色值=-65536
   copy.道具说明='蕴含神秘祝福的油剂，使用后有机会提升已装备坐骑的幸运。'
   change=copy
  end
  return original(id,change,mode)
 end
end
