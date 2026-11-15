return function(self, mode, tag, message)
    local state = self.__gm_repeat_skill_v229
    if mode == 'log' then
        if state and type(state.logger) == 'function' and state.log_left > 0 then
            state.log_left = state.log_left - 1
            pcall(state.logger, 'repeat.' .. tag, message)
        end
        return
    end
    if mode == 'cancel' and not state then return end
    local E = Ae冻集
    local delta = dt or 0
    local left, right = L常量.键_鼠标左, L常量.键_鼠标右
    local mouse = (left and 引擎:取按键事件(left)) or (right and 引擎:取按键事件(right))
    if not state then
        local ok, logger = pcall(Sys.get, '__gm_diag_checkpoint_v159')
        state = {logger = ok and type(logger) == 'function' and logger or nil, log_left = 240, pulse = 0, idle_reports = 0,
            down = {}, blocked = true, phase = 0, elapsed = 0,
            map = Q_地图, mapid = Ae冻 and Ae冻.地图id}
        self.__gm_repeat_skill_v229 = state
        self:__gm_repeat_control_v229('log', 'ready', 'entry=26/88 hero=' .. tostring(self.id)
            .. ' camera=' .. tostring(E.镜头ID) .. ' dt=' .. tostring(delta) .. ' slots=' .. tostring(#(E.快捷事件组 or {})))
    end
    local reason
    if mode == 'cancel' then reason = 'map_cleanup'
    elseif not E.屏幕焦点 then reason = 'screen_focus'
    elseif mouse and (E.UI焦点 or type(E.鼠标焦点事件对象) == 'table') then reason = 'mouse_interaction'
    elseif E.游戏暂停 then reason = 'paused'
    elseif E.逻辑跳过 or (E.逻辑暂停 or 0) > 0 then reason = 'logic_pause'
    elseif E.镜头ID ~= self.id then reason = 'camera'
    elseif self.已经死亡 or not self.属性 or self.属性.hp <= 0 then reason = 'dead'
    elseif self.属性.禁攻击 or (self.硬直 or 0) > 0 then reason = 'attack_disabled'
    elseif not self.剧情表 or #self.剧情表 ~= 0 then reason = 'scripted'
    elseif Q_鼠标 and Q_鼠标.被占用 then reason = 'drag_item'
    elseif state.map ~= Q_地图 or state.mapid ~= (Ae冻 and Ae冻.地图id) then reason = 'map_changed'
    elseif type(delta) ~= 'number' or delta < 0 or delta > 0.5 then reason = 'frame_delta' end
    local safe = reason == nil
    local entries = E.快捷事件组 or {}
    local any, pressed, candidate, active_entry = false, false, nil, nil
    local ignored_children = 0
    for i = 1, #entries do
        local entry = entries[i]
        local key = entry.键值
        if type(key) == 'number' and key > 0 then
            local down = 引擎:取按键事件(key) and true or false
            local previous_down = state.down[key]
            local edge = down and not previous_down
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
            if edge or (previous_down and not down) then
                self:__gm_repeat_control_v229('log', 'key', 'key=' .. key .. ' down=' .. tostring(down)
                    .. ' skill=' .. tostring(entry.绑定技能) .. ' eligible=' .. tostring(not not eligible)
                    .. ' usable=' .. tostring(info and info.可用) .. ' blocked=' .. tostring(state.blocked)
                    .. ' position=' .. tostring(skill and skill.施放位置) .. ' target=' .. tostring(skill and skill.目标类型)
                    .. ' distance=' .. tostring(skill and skill.施法距离) .. ' pierce=' .. tostring(skill and skill.穿透模式)
                    .. ' projectiles=' .. tostring(skill and skill.发射数量))
            end
            if eligible and type(entry.事件) == 'function' then
                if down then
                    if candidate and candidate ~= entry then safe = false; reason = 'multiple_keys' end
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
                -- A child opened by 12/142 remains raw-visible while its parent is closed.
                -- Match effective native visibility, including page frames, not the raw flag.
                local visible, node, depth = window.可视, window, 0
                while visible and node do
                    depth = depth + 1
                    if depth > 64 then visible = false; break end
                    if not node.可视 or (node.父外形框 and node.父外形框.可视 == false) then visible = false; break end
                    node = node.父窗口
                end
                if window.可视 and not visible then ignored_children = ignored_children + 1 end
                if visible then
                    if type(window.是否有输入框焦点) == 'function' and window:是否有输入框焦点() then safe = false; reason = 'input:' .. tostring(window.名称); break end
                    local name = window.名称 or ''
                    if string.find(name, '背包', 1, true) or string.find(name, '仓库', 1, true)
                        or string.find(name, '商店', 1, true) or string.find(name, '交易', 1, true)
                        or string.find(name, '设置', 1, true) or string.find(name, '存档', 1, true)
                        or string.find(name, '读档', 1, true) or string.find(name, '对话', 1, true)
                        or string.find(name, '菜单', 1, true) then safe = false; reason = 'window:' .. name; break end
                end
            end
        end
    end
    local lastkey = E.最后按键
    if safe and type(lastkey) == 'number' and lastkey > 0 and lastkey ~= left and lastkey ~= right and 引擎:取按键按下(lastkey) then
        local found = false
        for i = 1, #entries do if entries[i].键值 == lastkey then found = true; break end end
        if not found then safe = false; reason = 'other_key:' .. lastkey end
    end
    if state.active and pressed then safe = false; reason = 'skill_key' end
    if state.active and not active_entry then safe = false; reason = reason or 'binding_or_skill' end
    state.pulse = state.pulse + (type(delta) == 'number' and delta >= 0 and math.min(delta, 0.5) or 0)
    if state.pulse >= 5 and (any or state.active or state.idle_reports < 4) then
        state.pulse = 0; state.idle_reports = state.idle_reports + 1
        if type(state.logger) ~= 'function' then
            local ok, logger = pcall(Sys.get, '__gm_diag_checkpoint_v159')
            if ok and type(logger) == 'function' then state.logger = logger end
        end
        self:__gm_repeat_control_v229('log', 'pulse', 'active=' .. tostring(state.active) .. ' held=' .. tostring(any)
            .. ' blocked=' .. tostring(state.blocked) .. ' reason=' .. tostring(reason) .. ' dt=' .. tostring(delta)
            .. ' camera=' .. tostring(E.镜头ID) .. '/' .. tostring(self.id) .. ' slots=' .. #entries
            .. ' ignored_hidden_children=' .. ignored_children)
    end
    if not safe then
        if state.active or (any and state.reason ~= reason) then
            self:__gm_repeat_control_v229('log', state.active and 'stop' or 'blocked', 'reason=' .. tostring(reason)
                .. ' key=' .. tostring(state.key) .. ' skill=' .. tostring(state.name)
                .. ' ignored_hidden_children=' .. ignored_children)
        end
        state.reason = reason
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
    state.reason = nil
    if state.blocked then
        if not any then state.blocked = false end
        return
    end
    if state.active then
        -- A ground move may supersede our queued cast without ending repeat mode.
        if mouse or self.抵达目标点 == false then
            if state.pending and self.下次技能 == state.pending then
                self.下次技能 = nil
                if self.__gm_queued_skill_v155 == state.pending then
                    self.__gm_queued_skill_v155 = nil; self.__gm_queued_target_v155 = nil
                end
            end
            state.pending = nil
        end
        state.phase = (state.phase + (dt or 0) * 0.6) % 1
        state.elapsed = state.elapsed + (dt or 0)
        local info = self.技能信息[state.name]
        if not any and not mouse and self.抵达目标点 ~= false and state.elapsed >= 0.1 then
            state.elapsed = state.elapsed % 0.1
            if not info.开始CD效果 and info.可触发 ~= false then
                local before = self.下次技能
                state.requests = state.requests + 1
                if state.requests <= 3 or state.requests % 20 == 0 then
                    self:__gm_repeat_control_v229('log', 'cast', 'request=' .. state.requests .. ' key=' .. state.key .. ' skill=' .. tostring(state.name))
                end
                active_entry.事件(2) -- Same callback and flag as a manual skill hotkey.
                if self.下次技能 ~= before and self.下次技能 == state.name then state.pending = self.下次技能 end
            end
        end
    elseif candidate then
        if state.candidate ~= candidate then
            state.candidate = candidate; state.started = 0; state.hold_bucket = -1
            self:__gm_repeat_control_v229('log', 'hold', 'key=' .. candidate.键值 .. ' skill=' .. tostring(candidate.绑定技能) .. ' seconds=0 ignored_hidden_children=' .. ignored_children)
        else
            state.started = state.started + delta
            local bucket = math.floor(state.started * 2)
            if bucket ~= state.hold_bucket then
                state.hold_bucket = bucket
                self:__gm_repeat_control_v229('log', 'hold', 'key=' .. candidate.键值 .. ' skill=' .. tostring(candidate.绑定技能) .. ' seconds=' .. tostring(state.started))
            end
            if state.started + 1e-9 >= 2 then
                state.active = true; state.entry = candidate; state.key = candidate.键值
                state.name = candidate.绑定技能; state.phase = 0; state.elapsed = 0
                state.border_logged = false; state.border_probe = false; state.requests = 0
                self:__gm_repeat_control_v229('log', 'start', 'key=' .. state.key .. ' skill=' .. tostring(state.name) .. ' seconds=' .. tostring(state.started))
            end
        end
    else
        state.candidate = nil; state.started = nil
    end
end
