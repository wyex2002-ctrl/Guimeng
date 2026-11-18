return function(self, target, hits)
    local attrs = self.属性
    if type(attrs) ~= 'table' then return false end
    local guard = false
    for field = 1, 2 do
        local name = field == 1 and attrs.名称 or self.绑定属性
        if name == '卫士' or name == '大刀卫士' or name == '弓箭卫士'
            or name == '大刀守卫' or name == '弓箭守卫' or name == '城镇卫士'
            or name == '守卫' or name == '弓箭手' or name == '大刀' then
            guard = true
            break
        end
    end
    if not guard then return false end

    local pet = self.宠物配置
    local owner = self.主人id
    if (type(pet) == 'table' and pet.主人)
        or (type(owner) == 'number' and owner >= 0) then return false end

    if hits then
        for i = #hits, 1, -1 do
            if self:__gm_guard_ignore_v224(hits[i][1]) then table.remove(hits, i) end
        end
        return false
    end
    if type(target) ~= 'table' then return false end

    local hero = self.Hero
    if type(hero) ~= 'table' or hero.id ~= 0 then hero = Sys.get('hero') end
    if type(hero) ~= 'table' or hero.id ~= 0 or target.id == hero.id then return false end
    local merc = Ae冻 and Ae冻.佣兵对象
    local mercId = type(merc) == 'table' and merc.id
    local actor = target
    for _ = 1, 8 do
        pet = actor.宠物配置
        owner = type(pet) == 'table' and pet.主人
        if not owner then owner = actor.主人id end
        local id = type(owner) == 'table' and owner.id or owner
        if type(id) == 'number' and id >= 0 and id % 1 == 0 then
            if id == hero.id or (mercId and mercId > 0 and id == mercId) then return true end
            if type(owner) == 'table' and rawget(owner, '宠物配置') then
                actor = owner
            else
                actor = Sys.get('obj', id)
            end
        elseif type(owner) == 'table' then
            actor = owner
        else
            return false
        end
        if type(actor) ~= 'table' then return false end
    end
    return false
end
