return function(windows)
    local red, blue, compound = 1, 2, 3
    local specs = {小 = 0.2, 中 = 0.5, 大 = 1, 特 = 1.5, 特大 = 2}
    local groups = {
        金创药_小 = red, 金创药_中 = red, 金创药_大 = red, 金创药_特 = red,
        金创药_特大 = red, Q金创药_小 = red,
        魔法药_小 = blue, 魔法药_中 = blue, 魔法药_大 = blue, 魔法药_特 = blue,
        魔法药_特大 = blue, Q魔法药_小 = blue,
        太阳水 = compound, 强效太阳水 = compound, 万年雪霜 = compound,
    }
    local packTypes = {'加血', '加蓝', '加血蓝'}
    local actors = {}
    local autoItem
    local lastNoticeName, lastNoticeTime

    local function state(actor)
        local entry = actors[actor]
        if not entry then
            entry = {ready = {}, rescue = {}}
            actors[actor] = entry
        end
        return entry
    end

    local function warn(item)
        if not item or autoItem == item.名称 then return end
        local name = item.显示名 or item.名称
        local now = Gly独.__gm_potion_ms_v294()
        if lastNoticeName ~= name or now - lastNoticeTime >= 500 then
            lastNoticeName, lastNoticeTime = name, now
            -- Mode 0 is the same lower-left message feed as kill experience.
            Ux雌.托管显示.屏幕提示('冷却中，请稍后再使用【' .. name .. '】', L常量.颜色_红, 0)
        end
    end

    local function available(entry, group, now)
        return now >= (entry.ready[group] or 0)
    end

    local function effects(item, merc)
        local extra = item.附加
        local hp, mp = extra.加血 or 0, extra.加蓝 or 0
        local spec = 分割文本(item.名称, '_')[2]
        local factor = specs[spec] or 1
        if merc then
            local attrs = merc.属性
            if hp > 0 then hp = hp + math.ceil(attrs.红恢复量 * factor) end
            if mp > 0 then mp = mp + math.ceil(attrs.蓝恢复量 * factor) end
        else
            local qi = Ux雌.啾啾啵啵().技能.运气术
            if qi then
                local rate = (qi[1] + 2) / 10
                hp, mp = hp + math.ceil(hp * rate), mp + math.ceil(mp * rate)
            end
            if hp > 0 then hp = hp + math.ceil(Ux雌.主角红恢复量 * factor) end
            if mp > 0 then mp = mp + math.ceil(Ux雌.主角蓝恢复量 * factor) end
        end
        return hp, mp
    end

    local function collect(group, merc)
        local quick, bag, byName = {}, {}, {}
        local function offer(target, slot, item, order)
            if not item or groups[item.名称] ~= group or item.子类 ~= '消耗品'
                or not item.附加 or (item.数量 or 0) < 1 then return end
            local hp, mp = effects(item, merc)
            local amount = hp + mp
            if amount <= 0 then return end
            local candidate = {slot = slot, item = item, order = order, hp = hp, mp = mp, amount = amount}
            target[#target + 1] = candidate
            return candidate
        end

        if merc then
            local slots = Ux雌.佣兵背包
            for i = 1, #slots do
                local slot = slots[i]
                if slot then offer(bag, i, slot.道具, i) end
            end
        else
            for id = 31, 126 do
                local slot = Gly独.取控件对象('物品格子' .. id)
                local item = slot and slot.道具
                local candidate = offer(bag, id, item, id)
                if candidate and not byName[item.名称] then byName[item.名称] = candidate end
            end
            for id = 21, 26 do
                local slot = Gly独.取控件对象('物品格子' .. id)
                local item = slot and slot.道具
                if item and item.附加 and item.附加.快捷物品 ~= nil then
                    local stock = byName[item.名称]
                    if stock then
                        offer(quick, stock.slot, stock.item, id)
                    else
                        offer(quick, id, item, id)
                    end
                else
                    offer(quick, id, item, id)
                end
            end
        end

        local function weakest(a, b)
            if a.amount == b.amount then return a.order < b.order end
            return a.amount < b.amount
        end
        table.sort(quick, weakest)
        table.sort(bag, weakest)
        return quick, bag
    end

    local function use(group, merc, entry)
        local function trySources(quick, bag)
            local tried = {}
            local function try(source)
                for i = 1, #source do
                    local candidate = source[i]
                    local slot, item = candidate.slot, candidate.item
                    if not tried[slot] then
                        tried[slot] = true
                        if merc then
                            if Ux雌.佣兵对象 ~= merc or merc.HP <= 0 then return false end
                            if windows.佣兵窗口('补丁扣除药品', slot, item.名称) then
                                if candidate.hp > 0 then windows.佣兵窗口('恢复', 0, candidate.hp) end
                                if candidate.mp > 0 then windows.佣兵窗口('恢复', 1, candidate.mp) end
                                entry.ready[group] = Gly独.__gm_potion_ms_v294() + 3000
                                return true
                            end
                        else
                            local before = entry.ready[group]
                            autoItem = item.名称
                            Gly独.使用物品(autoItem, {__gm_autopotion_slot_v142 = slot})
                            autoItem = nil
                            if entry.ready[group] ~= before then return true end
                        end
                    end
                end
            end
            return try(quick) or try(bag)
        end

        local quick, bag = collect(group, merc)
        if trySources(quick, bag) then return true end
        if #quick + #bag > 0 then return false end

        -- Use the existing unpackers, which enforce six open slots and consume one pack.
        if merc then
            windows.佣兵窗口('背包检测', '解包', packTypes[group])
        else
            windows.辅助窗口('背包检测', nil, packTypes[group])
        end
        return trySources(collect(group, merc))
    end

    local function needs(check, slider, value, maximum)
        local enabled = check and check.选中 == false and slider and slider.位置 > 0
        return enabled, enabled and maximum > 0 and value * 100 <= maximum * slider.位置
    end

    local function threshold(group, merc)
        if merc then
            local p = merc.属性
            if group == red then
                return needs(佣兵加红选择框, 佣兵加红滑块条, p.当前生命值, p.最大生命值)
            end
            return needs(佣兵加蓝选择框, 佣兵加蓝滑块条, p.当前法力值, p.最大法力值)
        end
        if group == red then
            return needs(加红选择框, 加红滑块条, Ux雌.主角HP, Ux雌.主角MAXHP)
        end
        return needs(加蓝选择框, 加蓝滑块条, Ux雌.主角MP, Ux雌.主角MAXMP)
    end

    local function checkActor(actor, merc, safe, now)
        if not actor then return end
        local entry = actors[actor]
        if not safe or actor.HP <= 0 then
            if entry then entry.rescue = {} end
            return
        end
        local needsCompound = false
        for group = red, blue do
            local enabled, low = threshold(group, merc)
            local due = entry and entry.rescue[group]
            if not enabled then
                if entry then entry.rescue[group] = nil end
            elseif due then
                if now >= due then
                    entry.rescue[group] = nil
                    needsCompound = needsCompound or low
                end
            elseif low then
                entry = entry or state(actor)
                if available(entry, group, now) and use(group, merc, entry) then
                    entry.rescue[group] = Gly独.__gm_potion_ms_v294() + 1000
                else
                    needsCompound = true
                end
            end
        end
        if needsCompound and available(entry, compound, now) then
            use(compound, merc, entry)
        end
    end

    local function visible(window)
        return window and window.可视 == true
    end

    local function tick()
        local hero, merc = FXru胃啪, Ux雌.佣兵对象
        local now = Gly独.__gm_potion_ms_v294()
        -- A detached actor's pending work is canceled. A live cooldown is
        -- retained briefly if the very same instance is reattached.
        for actor, entry in pairs(actors) do
            if actor ~= hero and actor ~= merc then
                entry.rescue = {}
                if now >= math.max(entry.ready[red] or 0, entry.ready[blue] or 0,
                                   entry.ready[compound] or 0) then actors[actor] = nil end
            end
        end
        local safe = 物品格子18 and not 物品格子18.道具
            and not (visible(仓库窗口) or visible(佣兵窗口) or visible(商店窗口) or visible(行会仓库))
            and Ux雌.啾啾啵啵().法治观念 ~= nil
        checkActor(hero, nil, safe, now)
        checkActor(merc, merc, true, now)
    end

    windows.__gm_potions_v293 = function(action, item, states)
        if Ux雌.版本选择 ~= '来世续缘' then return end
        if action == 'tick' then tick(); return true end
        if action == 'notice' then warn(item); return true end
        local group = item and groups[item.名称]
        if action == 'group' then return group ~= nil end
        if action == 'gate' and group then
            local entry = FXru胃啪 and actors[FXru胃啪]
            if entry and not available(entry, group, Gly独.__gm_potion_ms_v294()) then
                warn(item)
                return -1
            end
            return 1
        end
        if action == 'used' then
            if group and FXru胃啪 then
                state(FXru胃啪).ready[group] = Gly独.__gm_potion_ms_v294() + 3000
            end
            return
        end
        if action == 'script' then
            if group then return 1 end
            if states.道具CD ~= nil then warn(item); return -1 end
        end
        return false
    end
end
