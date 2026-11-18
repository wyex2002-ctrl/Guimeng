local work, mode = arg[1], arg[2]
if mode == 'hot' then require('jit.opt').start('hotloop=1', 'hotexit=1') else jit.off() end

local function eq(actual, expected, label)
    assert(actual == expected, (label or 'check') .. ': ' .. tostring(actual) .. ' ~= ' .. tostring(expected))
end
local function load(name, env)
    return setfenv(assert(loadfile(work .. '/' .. name .. '.ljbc')), env)
end
local function bind(name, env, value, index)
    local fn = load(name, env)
    assert(debug.setupvalue(fn, index or 1, value))
    return fn
end
local function noop() end
local configs = assert(loadfile(work .. '/configs.lua'))()
local actions = {7688, 7708, 8056, 9139, 9294, 9493, 9606, 11221}
local function read(config, _, key, default)
    for line in config:gmatch('[^\r\n]+') do
        local name, value = line:match('^([^=]+)=(.*)$')
        if name == key then return value end
    end
    return default
end

local function setup(version, story)
    local hero = {id = 0, 所属阵营 = '友方', 宠物配置 = {}}
    local mercId = 200
    local state = {Hero = hero, 屏幕事件组 = {}, 事件闭包表 = {}, 事件信息组 = {},
                   shelp = {}, Game_State = 1}
    local calls, rows = {}, {}
    local N = setmetatable({
        class = function() return {} end, Ae冻 = {佣兵对象 = {id = mercId}, 版本选择 = story},
        Ae冻集 = {剧情中 = false, 自定义属性表 = {}, 游戏血条组 = {}, 掉血样式组 = {}, 新事件计次 = 3000},
        核心 = {读配置项_内存 = read, RGB2ARGB = function(color) return color end},
        Q_地图 = {置格子信息 = noop, 取范围对象组 = function(_, _, range)
            eq(range, 6)
            return rows
        end},
    }, {__index = _G})
    N.math = setmetatable({round = function(n) return math.floor(n + .5) end}, {__index = math})
    N.核心.读配置项_缓存 = bind('read_event_config', N, {})
    N.Sys = load('public_sys', N)({get = bind('public_get', N, state), add = noop})
    eq(N.Sys.Hero, nil)
    load('event_' .. version, N)()
    local class = N.类_事件
    local E = {type = type, Ux雌 = {佣兵对象 = {id = mercId}, 版本选择 = story}}
    local G = bind('gly', N, state, 2)()
    E.Gly独 = G
    state.script_setting = E
    bind('sandbox', N, state)(E)
    eq(state.script_setting, E)
    eq(E.Sys, nil)
    eq(E.pcall, nil)
    eq(E._G, nil)
    E.Ux雌.啾啾啵啵 = function() return {技能 = {超强召唤骷髅 = {0}}} end

    local function unit(id, name, config, x, y)
        local a = setmetatable({
            可视 = true, 当前状态 = 3, 目标格子 = {x = x or 1, y = y or 1}, 地图格子 = {x = x or 1, y = y or 1}, 实时移动速度 = 10,
            攻击速度 = 10, 资源动画 = {}, 剩余掉血值 = 0, BUFF组 = {},
            属性 = {名称 = name, 显示名 = name, hp = 100, maxhp = 100, 附加 = {},
                    中心Y偏移 = 0, 模型大小 = 1, 移动速度倍数 = 10, 攻击速度倍数 = 10, 经验值 = 0, 经验倍数 = 1},
        }, {__index = class})
        for _, key in ipairs({'物理伤害', '魔法伤害', '物理防御', '魔法防御', '命中', '暴击', '躲避'}) do
            a.属性[key], a.属性['附加_' .. key] = 0, 0
        end
        load('init_fields', N)(a, nil, x, y, id, config)
        a.属性更新, a.动作更新, a.继续移动, a.EXP增加, a.死亡 = noop, noop, noop, noop, noop
        a.事件回调 = function(self, name, args)
            if name == '受伤' then calls.damageTarget, calls.damageSource = self.id, args[5] end
        end
        a.播放动作 = true
        a.播放指定动作 = function(_, action, start, scale, callback)
            eq(action, '攻击')
            eq(start, 0)
            eq(scale, 1)
            calls.animation = callback
        end
        a.置位置 = function(self, x, y)
            self.地图格子 = {x = x, y = y}
            calls.moved = (calls.moved or 0) + 1
        end
        return a
    end
    local function add(a)
        state.屏幕事件组[#state.屏幕事件组 + 1] = a
        return a
    end
    class.创建 = function(_, x, y, id, config)
        local cfg = N.核心.读配置项_缓存(config)
        return unit(id, cfg.绑定属性, config, x, y)
    end
    for _, id in ipairs({1109, 1110}) do
        state.事件信息组[id] = {x = 5, y = 5, 配置项 = configs[id]}
    end
    local function summon(name)
        local id = bind('summon', E, {id = name})()
        local a = assert(N.Sys.get('obj', id))
        eq(a.宠物配置.主人, hero)
        eq(G.事件对象(id).主人id, 0)
        return a
    end

    local function guard(action)
        local config = configs[action]
        local id = tonumber(read(config, '配置', '事件标识'))
        local x = tonumber(read(config, '配置', '原始x')) + 1
        local y = tonumber(read(config, '配置', '原始y')) + 1
        local a = add(unit(id, 'NPC', config, x, y))
        eq(a.显示名称, '卫士')
        eq(a.绑定属性, 'NPC')
        eq(a.属性.名称, 'NPC')
        eq(a.所属阵营, '中立')
        local callback = load('guard_' .. version .. '_' .. action, E)()
        callback.___init(a.id)
        local dispatch = bind('dispatch', N, state)
        state.shelp[tostring(callback.动作监视)] = {sid = '卫士动作监视', msg = 'fixture'}
        local lastError
        G.错误 = function(message) lastError = message end
        local function tick(...)
            lastError = nil
            local ok, detail = dispatch(callback.动作监视, {...})
            eq(ok, true, lastError or detail)
        end
        return a, tick
    end
    return {
        guard = guard, summon = summon, hero = hero, calls = calls, gly = G,
        add = add, unit = unit, mercId = mercId,
        setRows = function(...) rows = {...} end,
    }
end

for _, story in ipairs({'前尘忆梦', '来世续缘'}) do
    for _, spell in ipairs({'召唤神兽', '召唤骷髅'}) do
        local old = setup('old', story)
        local _, tick = old.guard(9493)
        local pet = old.summon(spell)
        eq(pet.绑定属性, spell == '召唤神兽' and '神兽' or '超强骷髅')
        eq(old.gly.事件对象(pet.id).主动攻击, true)
        old.setRows(pet.id)
        tick('停止', 12)
        assert(old.calls.animation, 'v1.291 schedules attack on the pet')
        old.calls.animation('攻击', 8, 5)
        eq(old.calls.damageSource, 1017, 'old guard receives damage credit')
        eq(pet.属性.hp, 0, 'v1.291 applies lethal damage')
    end

    for _, id in ipairs(actions) do
        local s = setup('new', story)
        local guard, tick = s.guard(id)
        local beast, skeleton = s.summon('召唤神兽'), s.summon('召唤骷髅')
        eq(guard:__gm_guard_ignore_v224(beast), true)
        eq(guard:开始攻击(0, beast), false)
        -- Legacy map configuration is used for ownership and targeting,
        -- and the production callback sees the native public event proxies.
        s.setRows(beast.id, skeleton.id)
        tick('停止', 12)
        eq(s.calls.moved, nil)
        eq(s.calls.animation, nil)
        eq(beast.属性.hp, 100)
        eq(skeleton.属性.hp, 100)

        -- Exercise the ordinary monster with the same native attack fields,
        -- leaving its owner unset. Confirm the list continues past pets.
        local hostile = s.add(s.unit(201, '祖玛卫士', configs[1109], 7, 8))
        hostile.所属阵营 = '敌方'
        eq(hostile:__gm_guard_ignore_v224(beast), false)
        s.setRows(beast.id, hostile.id, skeleton.id)
        tick('停止', 12)
        eq(s.calls.moved, 1)
        assert(s.calls.animation)
        local first = s.calls.animation
        -- Binding can change after the attack animation begins.
        local bound = s.gly.主仆绑定(hostile.id, 0, nil, nil, nil, nil, nil, nil, nil, false)
        eq(bound, hostile.id)
        first('攻击', 8, 5)
        eq(hostile.属性.hp, 100)
        first('攻击', 8, 8)
        eq(s.calls.moved, 2, 'return-to-post callback remains active')

        hostile.宠物配置.主人 = nil
        tick('停止', 12)
        assert(s.calls.animation ~= first)
        s.calls.animation('攻击', 8, 5)
        eq(s.calls.damageTarget, hostile.id)
        eq(hostile.属性.hp, 0)
    end
end

do
    local s = setup('new', '来世续缘')
    local _, tick = s.guard(9493)
    local follower = s.summon('召唤神兽')
    local merc = s.add(s.unit(s.mercId, '佣兵', configs[1109]))
    local G = s.gly
    eq(G.主仆绑定(follower.id, merc.id, nil, nil, nil, nil, nil, nil, nil, false), follower.id)
    local nestedId = G.主仆绑定(1110, follower.id)
    eq(G.事件对象(follower.id).主人id, merc.id)
    eq(G.事件对象(nestedId).主人id, follower.id)
    s.setRows(follower.id, nestedId)
    for _ = 1, 200 do tick('停止', 12) end
    eq(s.calls.animation, nil)
    eq(s.calls.moved, nil)
end

print('TOWN_GUARD_V292_PASS', mode)
