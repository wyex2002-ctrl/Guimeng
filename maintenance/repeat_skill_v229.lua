return function(self, mode)
    local state = self.__gm_repeat_skill_v229
    if mode == 'cancel' and not state then return end
    local E = Ae冻集
    local now = 引擎:取运行时间()
    if not state then
        state = {down = {}, blocked = true, phase = 0, last = now, elapsed = 0,
            map = Q_地图, mapid = Ae冻 and Ae冻.地图id}
        self.__gm_repeat_skill_v229 = state
    end
    local safe = mode ~= 'cancel' and E.屏幕焦点 and not E.UI焦点
        and not E.游戏暂停 and not E.逻辑跳过 and (E.逻辑暂停 or 0) <= 0
        and E.遮罩信息 and E.遮罩信息.触发 and E.镜头ID == self.id
        and not self.已经死亡 and self.属性 and self.属性.hp > 0
        and not self.属性.禁攻击 and (self.硬直 or 0) <= 0
        and self.剧情表 and #self.剧情表 == 0
        and not (Q_提示框 and Q_提示框.可视)
        and not (Q_鼠标 and Q_鼠标.被占用)
        and state.map == Q_地图 and state.mapid == (Ae冻 and Ae冻.地图id)
        and now >= state.last and now - state.last <= 500
    state.last = now
    if safe then
        local left, right = L常量.键_鼠标左, L常量.键_鼠标右
        if (left and 引擎:取按键事件(left)) or (right and 引擎:取按键事件(right)) then safe = false end
    end
    local entries = E.快捷事件组 or {}
    local any, pressed, candidate, active_entry = false, false, nil, nil
    for i = 1, #entries do
        local entry = entries[i]
        local key = entry.键值
        if type(key) == 'number' and key > 0 then
            local down = 引擎:取按键事件(key) and true or false
            local edge = down and not state.down[key]
            state.down[key] = down
            any = any or down
            if edge then pressed = true end
            local info = self.技能信息[entry.绑定技能]
            local skill = info and info.对象
            local eligible = (down or state.entry == entry) and skill and info.可用 ~= false and skill.施放位置 == '目标'
                and skill.目标类型 == '敌方' and type(skill.穿透模式) == 'number' and skill.穿透模式 <= 0
                and type(skill.施法距离) == 'number' and skill.施法距离 > 1
            if eligible then
                if type(skill.发射数量) ~= 'number' or skill.发射数量 > 1
                    or type(skill.作用范围) ~= 'table' then eligible = false end
                if eligible then
                    for direction = 1, 8 do
                        local range = skill.作用范围[direction]
                        if type(range) ~= 'table' or #range > 1 then eligible = false; break end
                    end
                end
            end
            if eligible and type(entry.事件) == 'function' then
                if down then
                    if candidate and candidate ~= entry then safe = false end
                    candidate = entry
                end
                if state.entry == entry and state.key == key and state.name == entry.绑定技能 then active_entry = entry end
            end
        end
    end
    -- The existing public item_box getter returns the native window array (14/416).
    if safe and (state.active or state.candidate or any) then
        local windows = Sys.get('item_box')
        if windows then
            for i = 1, #windows do
                local window = windows[i]
                if window.可视 then
                    if type(window.是否有输入框焦点) == 'function' and window:是否有输入框焦点() then safe = false; break end
                    local name = window.名称 or ''
                    if string.find(name, '背包', 1, true) or string.find(name, '仓库', 1, true)
                        or string.find(name, '商店', 1, true) or string.find(name, '交易', 1, true)
                        or string.find(name, '设置', 1, true) or string.find(name, '存档', 1, true)
                        or string.find(name, '读档', 1, true) then safe = false; break end
                end
            end
        end
    end
    local lastkey = E.最后按键
    if safe and type(lastkey) == 'number' and lastkey > 0 and 引擎:取按键按下(lastkey) then
        local found = false
        for i = 1, #entries do if entries[i].键值 == lastkey then found = true; break end end
        if not found then safe = false end
    end
    if not safe or (state.active and (pressed or not active_entry)) then
        if state.pending and self.下次技能 == state.pending then
            self.下次技能 = nil
            if self.__gm_queued_skill_v155 == state.pending then
                self.__gm_queued_skill_v155 = nil; self.__gm_queued_target_v155 = nil
            end
        end
        state.pending = nil; state.active = false; state.entry = nil
        state.candidate = nil; state.started = nil; state.blocked = true
        state.map = Q_地图; state.mapid = Ae冻 and Ae冻.地图id
        return
    end
    if state.blocked then
        if not any then state.blocked = false end
        return
    end
    if state.active then
        state.phase = (state.phase + (dt or 0) * 0.6) % 1
        state.elapsed = state.elapsed + (dt or 0)
        local info = self.技能信息[state.name]
        if not any and state.elapsed >= 0.1 then
            state.elapsed = state.elapsed % 0.1
            if not info.开始CD效果 and info.可触发 ~= false then
                local before = self.下次技能
                active_entry.事件(2) -- Same callback and flag as a manual skill hotkey.
                if self.下次技能 ~= before and self.下次技能 == state.name then state.pending = self.下次技能 end
            end
        end
    elseif candidate then
        if state.candidate ~= candidate then
            state.candidate = candidate; state.started = now
        elseif now - state.started >= 2000 then
            state.active = true; state.entry = candidate; state.key = candidate.键值
            state.name = candidate.绑定技能; state.phase = 0; state.elapsed = 0
        end
    else
        state.candidate = nil; state.started = nil
    end
end
