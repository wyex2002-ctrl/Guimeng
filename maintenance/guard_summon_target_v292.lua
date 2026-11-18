-- Database event proxy. 主人id is resolved by the original native entity API.
return function(target)
    local merc = Ux雌.佣兵对象
    local mercId = merc and merc.id
    for _ = 1, 8 do
        local owner = target.主人id
        if type(owner) ~= 'number' or owner < 0 then return false end
        if owner == 0 or (mercId and mercId > 0 and owner == mercId) then return true end
        target = Gly独.事件对象(owner)
        if not target then return false end
    end
    return false
end
