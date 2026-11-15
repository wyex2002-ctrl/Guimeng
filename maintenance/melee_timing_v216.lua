-- Main-character instance timing only; shared skills and sprite code stay intact.
local function timing(self, mode, a, b, c)
    -- Auto-enable only the three native charged melee skills. This is a
    -- per-hero session mode, not a permanent damage buff or saved setting.
    if mode == 'input' or mode == 'charge_select' or mode == 'charge_commit' then
        local runtime = self.__gm_auto_charge_v216
        local role = self.主角配置
        local learned = role and role.技能
        if type(learned) == 'table' then
            if not runtime and (learned.烈火剑法 or learned.翔空剑法 or learned.莲月剑法) then
                runtime = {last = 0, names = {'烈火剑法', '翔空剑法', '莲月剑法'}, enabled = {}}
                self.__gm_auto_charge_v216 = runtime
            end
            if runtime then
                for i = 1, 3 do
                    local entry = learned[runtime.names[i]]
                    local level = type(entry) == 'table' and tonumber(entry[1])
                    runtime.enabled[i] = type(level) == 'number' and level >= 0 and level <= 5
                end
            end
        elseif runtime then
            for i = 1, 3 do runtime.enabled[i] = false end
        end
        if mode == 'charge_select' then
            if not runtime then return b end
            runtime.pending = nil
            if b == true or self.已经死亡 or self.属性.hp <= 0 then return b end
            -- Only replace an ordinary melee request. Ranged spells, explicit
            -- charged casts and manual prepared charges retain native behavior.
            local melee = a == '普通攻击' or a == '基本剑术' or a == '攻杀剑术'
                or a == '刺杀剑术' or a == '半月弯刀' or a == '十方斩'
            if not melee then return b end
            local statuses = self:取状态列表()
            if (b == '烈火剑法' or b == '翔空剑法' or b == '莲月剑法')
                and statuses[b] ~= nil then return b end
            if type(b) == 'string' and b ~= '普通攻击' and b ~= '基本剑术'
                and b ~= '攻杀剑术' and b ~= '刺杀剑术' and b ~= '半月弯刀'
                and b ~= '十方斩' then return b end
            local getter = Ae冻 and Ae冻.大堵塞就
            if type(getter) ~= 'function' then return b end
            local rules = getter()
            if type(rules) ~= 'table' then return b end
            for offset = 1, 3 do
                local index = (runtime.last + offset - 1) % 3 + 1
                local name = runtime.names[index]
                local entry = self.技能信息[name]
                local level = runtime.enabled[index] and tonumber(learned[name][1])
                local row = level and rules[name] and rules[name][level + 1]
                local skill = entry and entry.对象 or Sys.get('skill', name)
                local cost = skill and tonumber(skill.消耗魔法)
                if cost and cost > 0 and skill.消耗魔法_百分比 then
                    cost = math.ceil(cost / 100 * self.属性.maxmp)
                end
                if runtime.enabled[index] and row and cost and cost >= 0
                    and self.属性.mp >= cost and statuses[name .. 'CD'] == nil
                    and (not entry or (entry.对象 and entry.开始CD效果 ~= true
                    and entry.可用 ~= false)) then
                    runtime.pending = name
                    return name
                end
            end
            return b
        elseif mode == 'charge_commit' then
            if runtime and runtime.pending == a then
                runtime.pending = nil
                -- Commit only after the real cast succeeds. Original status
                -- config supplies the charge cooldown; never fake a timer.
                local statuses = self:取状态列表()
                if statuses[a .. 'CD'] == nil then self:增加状态(a .. 'CD') end
                for i = 1, 3 do if runtime.names[i] == a then runtime.last = i; break end end
            end
            return
        end
    end
    if mode == 'effect' then
        -- Native effect speed is an interval multiplier (smaller = faster).
        -- Use the final skill, not the current hero animation/last attack.
        local name = b
        if name == '普通攻击' or name == '基本剑术' or name == '攻杀剑术'
            or name == '刺杀剑术' or name == '半月弯刀' or name == '翔空剑法'
            or name == '烈火剑法' or name == '十方斩' or name == '莲月剑法'
            or name == '快刀斩麻' then return (a or 1) * 0.5 end
        return a
    end
    if mode == 'input' then
        -- Runs only after the native input/focus/pause/UI guards. Keep the
        -- original 100ms held-input retry cadence; don't speed up other jobs.
        if self.已经死亡 or self.属性.hp <= 0 then self.__gm_shift_input_v210 = nil; return end
        local input = self.__gm_shift_input_v210
        if not input then input = {elapsed = 0, held = false}; self.__gm_shift_input_v210 = input end
        local shift = 引擎:取按键事件(L常量.键_SHIFT)
        local right = shift and 引擎:取按键事件(L常量.键_鼠标右) or false
        local left = shift and not right and 引擎:取按键事件(L常量.键_鼠标左) or false
        local held = shift and not right
        local pressed = held and left
        input.elapsed = input.elapsed + dt
        local previous = self.__gm_melee_state_v208
        local rested = not previous or (previous.ready and previous.ready_elapsed
            and previous.elapsed >= previous.ready_elapsed + 0.1)
        local immediate = rested and held and (not input.held or (pressed and not input.pressed))
        local due = input.elapsed >= 0.1
        input.held, input.pressed = held, pressed
        if due then input.elapsed = input.elapsed - 0.1 end
        if not held then return end
        if not immediate and not due then return end
        if immediate then input.elapsed = 0 end
        local window = Ae冻 and Ae冻.窗口相关
        local callback = window and window.刺杀剑术
        if type(callback) == 'function' then callback() end
        return
    end
    local state = self.__gm_melee_state_v208
    if mode == 'instance' then
        local skill = a.技能信息.对象
        local name = skill.名称
        local melee = name == '普通攻击' or name == '基本剑术' or name == '攻杀剑术'
            or name == '刺杀剑术' or name == '半月弯刀' or name == '翔空剑法'
            or name == '烈火剑法' or name == '十方斩' or name == '莲月剑法'
            or name == '快刀斩麻'
        if not melee then self.__gm_melee_state_v208 = nil; return end
        a.起手动画延迟 = a.起手动画延迟 * 0.5
        a.命中动画延迟 = a.命中动画延迟 * 0.5
        a.伤害发生延迟 = a.伤害发生延迟 * 0.5
        -- 翔空 is a jumping slash: release its blade light at the existing
        -- impact phase, instead of during the very early jump preparation.
        if name == '翔空剑法' then
            a.起手动画延迟 = math.max(a.起手动画延迟, a.伤害发生延迟)
        end
        for i = 1, #a.伤害进度 do a.伤害进度[i] = a.伤害进度[i] * 0.5 end
        self.__gm_melee_state_v208 = {elapsed = 0, sequence = 0, last = -1,
            initial = self.本次攻击动作 ~= '无', speed = self.施法速度,
            ready = self.本次攻击动作 == '无', ready_sequence = -1,
            no_animation = self.本次攻击动作 == '无'}
        return
    end
    if not state then return (mode == 'gate' or mode == 'direct_gate') and true or a end
    if self.属性.hp <= 0 then self.__gm_melee_state_v208 = nil; return (mode == 'gate' or mode == 'direct_gate') and true or a end
    local knockback = self.击退信息
    if self.当前状态 == 4 or (knockback and knockback.击退中 and not knockback.冲刺模式) then
        self.__gm_melee_state_v208 = nil
        return (mode == 'gate' or mode == 'direct_gate') and true or a
    end
    if mode == 'tick' then
        state.elapsed = state.elapsed + a
        state.sequence = state.sequence + 1
        if state.reset_pending and state.ready then
            state.reset_pending = false
            state.recovery = 0
            self.攻击速度_计次 = 0
        elseif state.recovery then state.recovery = state.recovery + a end
    elseif mode == 'end_reset' then
        if state.ready then state.recovery = 0 else state.reset_pending = true end
    elseif mode == 'direct_gate' then
        return state.ready and state.sequence > state.ready_sequence
    elseif mode == 'gate' then
        -- Original counter can be cleared by movement/target cancellation. Keep
        -- the elapsed part of this attack, without starting another full wait.
        local elapsed = state.recovery or state.elapsed
        if self.攻击速度_计次 < elapsed then self.攻击速度_计次 = elapsed end
        local period = self.属性.攻击速度 * (10 / self.属性.攻击速度倍数) * state.speed
        if not state.ready or elapsed < period then return false end
        self.__gm_melee_state_v208 = nil
        return true
    elseif mode == 'advance' then
        -- After early recovery the real actor may be in paused idle (99) or
        -- moving. The original attack would still animate; advance only that
        -- original timing copy, including its native one-step-per-call rule.
        if self.当前状态 ~= 3 and state.shadow and not state.ready and state.last ~= state.sequence then
            local factor = (10 / self.属性.攻击速度倍数) * state.speed
            state.update(state.shadow, dt, state.frame_rate * factor, state.frames)
            state.last = state.sequence
            if state.shadow.动画帧 == state.limit then state.ready = true; state.ready_sequence = state.sequence; state.ready_elapsed = state.elapsed end
        end
    elseif mode == 'motion' then
        -- a = original animation speed factor; b = resolved action; c = frames.
        -- Called once for the first body layer, using existing public Lua methods.
        if state.no_animation then return a end
        local layer = self.动画组[1]
        local anim = layer.动画
        local first = not state.shadow
        if first then
            state.shadow = {停止 = false, 可视 = false, 时间累积 = anim.时间累积,
                全局计次 = anim.全局计次, 动画帧 = anim.动画帧,
                总帧数 = anim.总帧数, 动作结束 = anim.动作结束}
            state.frames = c
            state.action = self.动作
            state.frame_rate = layer.动作组[b].帧率
            state.reverse = self.动作反向播放
            state.update = state.reverse and anim.反向更新 or anim.更新
            state.limit = #c + ((self.僵直效果 and not state.reverse) and 0 or -1)
            if #c == 0 then state.ready = true; state.ready_sequence = state.sequence; state.ready_elapsed = state.elapsed end
        end
        if not state.ready and (state.last ~= state.sequence or state.initial
            or (self.当前状态 == 3 and self.动作 == state.action)) then
            local factor = first and a or (10 / self.属性.攻击速度倍数) * state.speed
            state.update(state.shadow, dt, state.frame_rate * factor, state.frames)
            state.last = state.sequence
            if state.shadow.动画帧 == state.limit then state.ready = true; state.ready_sequence = state.sequence; state.ready_elapsed = state.elapsed end
        end
        if first and #c > 1 then
            -- Advance the visible start pose during the accepted attack's
            -- first update, not after a whole sprite interval. Capture the
            -- original shadow above FIRST; recovery/attack gates stay native.
            for i = 1, #self.动画组 do
                local part = self.动画组[i]
                local action = part.动作组[b]
                if action then
                    local interval = action.帧率 * a * 0.5 / 100
                    if part.动画.时间累积 < interval then part.动画.时间累积 = interval end
                end
            end
        end
        local fast = state.initial or (self.当前状态 == 3 and self.动作 == state.action)
        state.initial = false
        if fast then return a * 0.5 end
        return a
    end
end
return timing
