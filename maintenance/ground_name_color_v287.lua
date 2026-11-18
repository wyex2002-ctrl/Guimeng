-- The override belongs to the ground object and also applies when its stack shrinks.
return function(item, current, ground)
    if type(item) ~= 'table' or type(item.名称) ~= 'string' then return current end
    local name = item.名称
    local coin = item.分类 == '特殊' and (name == '金币' or name:find('金币_', 1, true) == 1)
    local sun, book = false, false
    if item.分类 == '道具' and item.子类 == '消耗品' then
        if name:sub(1, 1) == 'Q' then name = name:sub(2) end
        sun = name == '太阳水' or name == '强效太阳水' or name == '强效太阳水_包'
        local extra = item.附加
        if type(extra) == 'table' and extra.商店 == '书店' then
            local rank = tonumber(extra.强化书)
            book = rank ~= 4 and rank ~= 5
        end
        if name == '金创药' or name == '魔法药'
            or name:find('金创药_', 1, true) == 1 or name:find('魔法药_', 1, true) == 1 then
            return -1
        end
    end
    if coin or sun or book then
        ground.__gm_ground_label_color_v287 = -1
        return -1
    end
    return current
end
