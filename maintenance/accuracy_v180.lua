-- Database environment: use only the original explicit API whitelist.
return function(_)
  local role=Ux雌.啾啾啵啵()
  local skills=role.技能
  local base=0
  if skills.基本剑术~=nil then base=skills.基本剑术[1]+2 end
  if skills.精神力战法~=nil then base=skills.精神力战法[1]+1 end
  local amount=0
  if base>0 then amount=base*4+2 end
  local attack=skills.攻杀剑术
  if type(attack)=='table' then
    local level=tonumber(attack[1])
    if type(level)=='number' and level==level and level>=0 and level<math.huge and level%1==0 then
      amount=amount+level+1
    end
  end
  if amount>0 then
    FXru胃啪.增加状态('增加命中',0,{准确几率=amount})
  else
    FXru胃啪.删除状态('增加命中')
  end
end
