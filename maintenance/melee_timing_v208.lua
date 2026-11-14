-- Main-character instance timing only; shared skills and sprite code stay intact.
local function timing(self, mode, a, b, c)
    local state = self.__gm_melee_state_v208
    if mode == 'instance' then
        local skill = a.技能信息.对象
        local name = skill.名称
        local melee = name == '普通攻击' or name == '基本剑术' or name == '攻杀剑术'
            or name == '刺杀剑术' or name == '半月弯刀' or name == '翔空剑法'
            or name == '烈火剑法' or name == '十方斩' or name == '莲月剑法'
            or name == '快刀斩麻'
        if not melee then self.__gm_melee_state_v208 = nil; return end
        a.起手动画延迟 = a.起手动画延迟 * 0.7
        a.命中动画延迟 = a.命中动画延迟 * 0.7
        a.伤害发生延迟 = a.伤害发生延迟 * 0.7
        for i = 1, #a.伤害进度 do a.伤害进度[i] = a.伤害进度[i] * 0.7 end
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
            if state.shadow.动画帧 == state.limit then state.ready = true; state.ready_sequence = state.sequence end
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
            if #c == 0 then state.ready = true; state.ready_sequence = state.sequence end
        end
        if not state.ready and (state.last ~= state.sequence or state.initial
            or (self.当前状态 == 3 and self.动作 == state.action)) then
            local factor = first and a or (10 / self.属性.攻击速度倍数) * state.speed
            state.update(state.shadow, dt, state.frame_rate * factor, state.frames)
            state.last = state.sequence
            if state.shadow.动画帧 == state.limit then state.ready = true; state.ready_sequence = state.sequence end
        end
        local fast = state.initial or (self.当前状态 == 3 and self.动作 == state.action)
        state.initial = false
        if fast then return a * 0.7 end
        return a
    end
end
return timing
