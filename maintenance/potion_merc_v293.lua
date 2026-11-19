return function(index, name, decrement)
    local merc = Ux雌.佣兵对象
    local slot = Ux雌.佣兵背包[index]
    if not merc or merc.HP <= 0 or not slot or not slot.道具
        or slot.道具.名称 ~= name or (slot.道具.数量 or 0) < 1 then return false end
    if not decrement(slot) then slot.重置道具(nil) end
    return true
end
