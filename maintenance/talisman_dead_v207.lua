-- One existing child getter plus one processor: preserve the module's closure tree.
local function process(mode, amount, slot)
    local function context(id)
        local actor, cell, record, dead
        if id == 12 then
            actor, cell = FXru胃啪, 物品格子12
        elseif id == 408 then
            actor, cell = Ux雌.佣兵对象, 物品格子408
            local role = Ux雌.啾啾啵啵()
            if type(role) == 'table' and type(role.佣兵) == 'table' then record = role.佣兵 end
            local known = record and record.__gm_talisman_summoned_v206 == true
            if type(actor) == 'table' and type(actor.HP) == 'number' then
                known = true
                if record then record.__gm_talisman_summoned_v206 = true end
                dead = actor.HP <= 0
            else
                actor = nil
                -- Migration: original recruited-but-never-deployed templates have
                -- positive HP (41); a saved dead record proves prior deployment.
                if record and type(record.生命值) == 'number' and record.生命值 <= 0 then known = true end
                dead = known
            end
            if not known then return nil, nil, record, false end
        else return end
        if not cell or type(cell.道具) ~= 'table' then return nil, actor, record, dead end
        local item = cell.道具
        if item.名称 ~= '聚灵符咒_灵' or type(item.附加) ~= 'table' then return nil, actor, record, dead end
        local a = item.附加
        if type(a.最小储存) ~= 'number' or a.最小储存 ~= a.最小储存 or a.最小储存 == math.huge or a.最小储存 == -math.huge then return nil, actor, record, dead end
        if type(a.最大储存) ~= 'number' or a.最大储存 ~= a.最大储存 or a.最大储存 == math.huge or a.最大储存 <= 0 then return nil, actor, record, dead end
        return a, actor, record, dead
    end
    -- v206 balances were earned while dead. Transfer them to the hero once,
    -- including when the next call is the original post-revival restore hook.
    local _, merc, record, dead = context(408)
    local hero = FXru胃啪
    local pending = record and record.__gm_talisman_pending_v206
    local heroexp = type(hero) == 'table' and hero.经验
    if type(pending) == 'number' and pending == pending and pending > 0 and pending < math.huge
        and type(heroexp) == 'number' and heroexp == heroexp and heroexp > -math.huge
        and heroexp < math.huge and heroexp + pending < math.huge then
        hero.经验 = heroexp + pending
        record.__gm_talisman_pending_v206 = 0
    end
    if mode == 2 then return end
    if mode == 0 then
        if type(amount) ~= 'number' or amount ~= amount or amount <= 0 or amount == math.huge then return false end
        local deadmerc = dead == true
        for i = 1, 2 do
            local id = i == 1 and 12 or 408
            local attrs, owner, saved, isdead = context(id)
            local active = owner and type(owner.HP) == 'number' and owner.HP > 0
            if attrs and (active or (id == 408 and isdead and saved)) then
                local gain = amount
                local stored = math.max(0, attrs.最小储存) + gain
                if stored < attrs.最大储存 then
                    attrs.最小储存 = stored
                elseif id == 12 then
                    if type(owner.经验) == 'number' then
                        owner.经验 = owner.经验 + attrs.最大储存
                        attrs.最小储存 = 0
                    end
                elseif isdead then
                    if type(hero.经验) == 'number' and hero.经验 == hero.经验
                        and hero.经验 > -math.huge and hero.经验 + attrs.最大储存 < math.huge then
                        hero.经验 = hero.经验 + attrs.最大储存
                        attrs.最小储存 = 0
                    end
                else
                    attrs.最小储存 = attrs.最大储存
                    owner.__gm_claim_exp_v148 = attrs
                end
            end
        end
        return deadmerc
    elseif mode == 1 then
        local attrs = context(slot)
        if not attrs or attrs.最小储存 <= 0 then return false end
        local _, merc, record, dead = context(408)
        if not merc and not dead then return false end
        local hero = FXru胃啪
        if type(hero) ~= 'table' or type(hero.经验) ~= 'number' or hero.经验 ~= hero.经验 or hero.经验 == math.huge or hero.经验 == -math.huge then return false end
        if dead then
            local stored = attrs.最小储存
            if hero.经验 + stored == math.huge then return false end
            hero.经验 = hero.经验 + stored
            attrs.最小储存 = 0
            return true
        end
        local half = math.floor(attrs.最小储存 / 2)
        if half <= 0 or hero.经验 + half == math.huge then return false end
        local accepted = 0
        local request = {最小储存 = half}
        merc.__gm_claim_exp_v148 = request
        local rest = request.最小储存
        if type(rest) == 'number' and rest == rest and rest >= 0 and rest <= half then accepted = half - rest end
        if accepted <= 0 then return false end
        hero.经验 = hero.经验 + accepted
        attrs.最小储存 = attrs.最小储存 - accepted * 2
        return true
    end
end
return process
