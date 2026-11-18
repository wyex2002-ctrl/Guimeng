return function(drops)
    for i = #drops, 1, -1 do
        local name = drops[i].物品道具.名称
        if type(name) == 'string' and (
            name == '回城卷' or name == '回城卷_包'
            or name:find('^Q?金创药_') or name:find('^Q?魔法药_')) then
            table.remove(drops, i)
        end
    end
end
