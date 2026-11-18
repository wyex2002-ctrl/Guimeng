-- Called only after a successful role load, never on save or every frame.
return function()
 local role=Ux雌.啾啾啵啵()
 if type(role)~='table'or role.__gm_oil_welcome_v259 then return false end
 local item=Gly独.取道具信息_名称('祝福油')
 if type(item)~='table'then return false end
 local free=Gly独.取包裹空位('不限制')+Gly独.取包裹空位(item.子类)
 -- Require an empty usable slot even if an existing oil stack could accept it.
 if free<1 then return false end
 if Gly独.增加物品('祝福油',1)==true then
  role.__gm_oil_welcome_v259=true
  Gly独.提示('【系统赠送您1瓶祝福油，请查看背包】')
  return true
 end
 return false
end
