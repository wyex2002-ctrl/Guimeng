return function(drops)
    for i = #drops, 1, -1 do
        local name = drops[i].物品道具.名称
        if type(name) == 'string' and (
            name == '回城卷' or name == '回城卷_包'
            or name:find('^Q?金创药_') or name:find('^Q?魔法药_')) then
            table.remove(drops, i)
        end
    end

    if type(Ae冻) ~= 'table' or Ae冻.版本选择 ~= '来世续缘' then
        return
    end

    local bonus = tonumber(Ae冻.主角金币掉落) or 0
    local total = 0
    local fallback = nil

    for i = #drops, 1, -1 do
        local entry = drops[i]
        local item = entry.物品道具
        local extra = type(item) == 'table' and item.附加 or nil
        if type(extra) == 'table' and extra.小金币 ~= nil and extra.大金币 ~= nil then
            fallback = item
            local count = tonumber(entry.掉落数量) or 1
            if count < 1 then
                count = 1
            end
            local pre = tonumber(extra.金币)
            if pre ~= nil then
                total = total + pre * count
            else
                local lo = tonumber(extra.小金币)
                local hi = tonumber(extra.大金币)
                if lo ~= nil and hi ~= nil then
                    for _ = 1, count do
                        local g = 引擎:取随机整数(lo, hi)
                        g = (g + math.ceil((bonus / 150) * g)) * 3
                        total = total + g
                    end
                end
            end
            table.remove(drops, i)
        end
    end

    if total <= 0 or fallback == nil then
        return
    end

    while total > 0 do
        local pile = total
        if pile > 5000 then
            pile = 5000
        end
        total = total - pile

        local tier = '金币_极大'
        if pile <= 60 then
            tier = '金币_极小'
        elseif pile <= 600 then
            tier = '金币_小'
        elseif pile <= 2400 then
            tier = '金币_中'
        elseif pile <= 4500 then
            tier = '金币_大'
        end

        local tpl = Sys.get('item', tier)
        if type(tpl) ~= 'table' then
            tpl = fallback
        end
        local copy = table.copy(tpl)
        if type(copy.附加) ~= 'table' then
            copy.附加 = {}
        end
        copy.附加.金币 = pile
        table.insert(drops, { 物品道具 = copy, 掉落数量 = 1 })
    end
end
