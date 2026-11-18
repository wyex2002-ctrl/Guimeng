local work, mode = arg[1], arg[2]
if mode == 'hot' then require('jit.opt').start('hotloop=1', 'hotexit=1') else jit.off() end

local function eq(actual, expected, label)
    assert(actual == expected, (label or 'check') .. ': ' .. tostring(actual) .. ' ~= ' .. tostring(expected))
end
local function load(name, env)
    local fn = assert(loadfile(work .. '/' .. name .. '.ljbc'))
    return setfenv(fn, env or _G)
end

local function setup(version, story)
    local hero, merc = {id = 0}, {id = 80}
    local state = {Hero = hero, 屏幕事件组 = {merc}, 游戏技能组 = {弓箭 = {击退距离 = 0, 状态变化_删除_目标 = {}, 状态变化_增加_目标 = {}}}}
    local rows, calls = {}, {spell = 0, damage = 0}
    local env = setmetatable({
        class = function() return {} end,
        Ae冻 = {佣兵对象 = {id = 80}, 版本选择 = story},
        Ae冻集 = {剧情中 = false},
        核心 = {取指定范围指定方向格子 = function(_, _, _, out) out[1] = {1, 1} end},
        Q_地图 = {
            取指定范围内对象 = function(_, _, _, _, _, filter)
                for _, unit in ipairs(rows) do if filter(unit) then return unit end end
            end,
            取格子信息 = function() return rows end,
        },
    }, {__index = _G})
    local get = load('public_get', env)
    assert(debug.setupvalue(get, 1, state))
    env.Sys = load('public_sys', env)({get = get, add = function() end})
    eq(env.Sys.Hero, nil)
    load('event_' .. version, env)()
    local cls = env.类_事件
    local function unit(id, name, owner, ownerId)
        local actor = setmetatable({
            id = id, 主人id = ownerId, 绑定属性 = name, 所属阵营 = '友方',
            宠物配置 = {主人 = owner}, 地图格子 = {x = 1, y = 1},
            属性 = {名称 = name, hp = 100, 视野范围 = 10,
                    禁攻击 = false, 禁移动 = false, 混乱 = false},
            攻击方向限制 = 0, 绑定技能 = '无',
        }, {__index = cls})
        load('assign_hero', env)(actor)
        eq(actor.Hero, hero)
        eq(actor.Hero.主角, nil)
        eq(actor.Hero.佣兵, nil)
        actor.停止 = function(self) self.stopped = (self.stopped or 0) + 1 end
        actor.事件回调 = function(_, name)
            eq(name, '发生伤害')
            calls.damage = calls.damage + 1
            return true, {10, 0, 100}
        end
        actor.技能开始 = function() calls.spell = calls.spell + 1 end
        actor.被击中 = function(self, _, damage) self.属性.hp = self.属性.hp - damage end
        state.屏幕事件组[#state.屏幕事件组 + 1] = actor
        return actor
    end
    local function hit(guard, targets)
        local hits = {}
        for i, target in ipairs(targets) do hits[i] = {target, 100} end
        local skill = {对象 = {位移距离 = 0, 名称 = '弓箭', 类型 = 1},
                       施法者 = guard, 命中目标组 = hits, 伤害进度 = {0}}
        local update = load('hit_' .. version, env)
        assert(debug.setupvalue(update, 1, skill))
        assert(update())
        eq(skill.伤害产生_已结束, true)
        return skill.命中目标组
    end
    return {
        env = env, hero = hero, merc = merc, unit = unit, calls = calls, hit = hit,
        setRows = function(list) rows = list end,
    }
end

-- v1.289 with the actual Hero field layout selects and damages a pet.
do
    local s = setup('old', '来世续缘')
    local guard = s.unit(1, '大刀卫士')
    local pet = s.unit(2, '骷髅', s.hero)
    s.setRows({pet})
    eq(guard:寻找目标(), pet, 'v1.289 wrongly picks the summon')
    s.hit(guard, {pet})
    eq(pet.属性.hp, 90, 'v1.289 hits the summon')
end

for _, story in ipairs({'前尘忆梦', '来世续缘'}) do
    local s = setup('new', story)
    local sword = s.unit(1, '大刀卫士')
    local bow = s.unit(2, '弓箭守卫')
    bow.属性.名称 = nil
    local skeleton = s.unit(3, '骷髅', s.hero)
    local beast = s.unit(4, '神兽', nil, 0)
    local mercPet = s.unit(5, '神兽', {id = s.merc.id})
    local nested = s.unit(6, '超强神兽', nil, mercPet.id)
    local wild = s.unit(7, '野怪')
    local foreign = s.unit(8, '野怪', {id = 1234})
    local cyclic = s.unit(9, '神兽', nil, 9)

    for _, guard in ipairs({sword, bow}) do
        s.setRows({skeleton, beast, mercPet, nested, wild})
        eq(guard:寻找目标(), wild)
        guard.攻击方向限制, guard.攻击方向配置 = 1, {1}
        eq(guard:寻找目标(), wild)
        guard.攻击方向限制 = 0
        s.setRows({skeleton, beast, mercPet, nested})
        eq(guard:寻找目标(), nil)
        for _, pet in ipairs({skeleton, beast, mercPet, nested}) do
            eq(guard:开始攻击(0, pet), false)
            eq(guard:释放技能_API('弓箭', pet), false)
            eq(guard:发生伤害(pet, '弓箭', 1), false)
            eq(pet.属性.hp, 100)
        end
        guard.攻击来源 = skeleton
        guard:继续攻击()
        eq(guard.攻击来源, nil)
        guard.攻击来源 = beast
        guard:继续追击()
        eq(guard.攻击来源, nil)
        eq(guard.stopped, 2)
        eq(guard:__gm_guard_ignore_v224(foreign), false)
        eq(guard:__gm_guard_ignore_v224(cyclic), false)
        eq(guard:__gm_guard_ignore_v224(s.hero), false)

        local before = s.calls.damage
        local hits = s.hit(guard, {skeleton, wild, beast, mercPet, nested})
        eq(#hits, 1); eq(hits[1][1], wild)
        eq(s.calls.damage, before + 1)
        eq(guard:释放技能_API('弓箭', wild), true)
    end
    eq(wild.属性.hp, 80)
    eq(s.calls.spell, 2)
    local monster = s.unit(10, '祖玛卫士')
    s.setRows({skeleton})
    eq(monster:寻找目标(), skeleton)
    eq(#s.hit(monster, {skeleton}), 1)
    eq(skeleton.属性.hp, 90)
    local ownedGuard = s.unit(11, '大刀卫士', s.hero)
    eq(ownedGuard:__gm_guard_ignore_v224(skeleton), false)
    local public = load('entity_api', s.env)
    assert(debug.setupvalue(public, 1, {对象 = sword}))
    eq(public({}, '__gm_guard_ignore_v224'), nil)

    for i = 1, 200 do
        s.setRows({i % 2 == 0 and skeleton or mercPet, wild})
        eq(sword:寻找目标(), wild)
    end
end
print('TOWN_GUARD_V290_PASS', mode)
