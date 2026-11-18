-- Database skill callback. Use the same bag slots, refill check and charge
-- fields as the original hand-cast event. The request already passed the
-- original skill-rank and target guard.
return function(rank, needed)
    local mana, charges = rank.消耗魔法, rank.数量
    if type(mana) ~= 'number' or mana < 0 or not (FXru胃啪.MP >= mana)
        or type(charges) ~= 'number' or charges <= 0 then return end
    local powders = 分割文本(rank.物品, '_')
    local first = needed ~= 0 and needed or rank.位置
    local alternate = needed == 0 and 3 - first or nil
    local chosen, slot, id
    -- Prefer the first usable stack of the required color. With neither
    -- poison present, use the manual cast's current preference and fallback.
    for index = 31, 126 do
        -- 主角格子 is a compact list of registered controls, not a slot-ID map.
        local cell = Gly独.取控件对象('物品格子' .. index)
        local item = cell and cell.道具
        local extra = item and item.附加
        if extra and type(extra.最小次数) == 'number' and extra.最小次数 >= charges then
            if item.名称 == powders[first] then
                chosen, slot, id = first, cell, index
                break
            end
            if not slot and alternate and item.名称 == powders[alternate] then
                chosen, slot, id = alternate, cell, index
            end
        end
    end
    if not slot then return 'missing' end

    Ux雌.窗口相关.抗菌药物(id, 1000, 1)
    local extra = slot.道具.附加
    extra.最小次数 = extra.最小次数 - charges
    if extra.最小次数 <= 0 then slot.重置道具(nil) end
    if needed == 0 then rank.位置 = 3 - chosen end
    return {chosen, mana}
end
