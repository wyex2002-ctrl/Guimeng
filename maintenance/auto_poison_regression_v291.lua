    local originalTable = N.table
    N.table = setmetatable({copy = function(t)
        local out = {}
        for k, v in pairs(t) do out[k] = v end
        return out
    end}, {__index = originalTable})
    local ini = assert(loadfile(work .. '/poison_cfg.lua'))()
    N.核心.读配置项_内存 = function(s, section, key, default)
        return read(assert(ini[s]), section, key, default)
    end
    N.核心.ARGB分解 = function() return 255, 0, 0, 0 end
    N.ARGB = function(a,r,g,b) return a*16777216+r*65536+g*256+b end
    N.__Res = function() return nil end
    N.L常量.颜色_红, N.L常量.颜色_绿 = 11, 22
    N.Sys = load('public_sys', N)({
        get = function(kind, ...)
            if kind == '__gm_diag_checkpoint_v159' then
                return function(point, message)
                    if point == 'skill.auto_poison.error' then print(point, message) end
                end
            end
            return lookup(kind, ...)
        end,
        run = run,
        add = function(kind, name, config)
            if kind == '屏幕子弹' then return end -- The fixture advances created projectiles.
            eq(kind, '状态配置')
            owner.游戏状态组[name] = config
        end,
    })
    N.Ae冻集.自定义属性表 = {'最大防御','最大魔防'}
    t.属性.属性集 = {成长='怪物',附加={血条=-18},最大防御=0,最大魔防=0}
    t.属性.最大防御, t.属性.最大魔防 = 0, 0
    load('poison_statuses', N)()
    for _, name in ipairs({green, red, green .. '图标', red .. '图标'}) do
        assert(owner.游戏状态组[name], name)
    end
    load('buff_class', N)()
    t.属性.maxhp, t.属性.maxmp, t.属性.可视 = 100000, 1000, true
    t.HP改变, t.MP改变, t.属性更新 = noop, noop, noop
    for key, value in pairs(owner.游戏状态组[red].属性) do
        t.属性['附加_' .. key] = 0
    end
    t.属性.附加_maxhp, t.属性.附加_maxmp = 0, 0
    t.属性.附加_移动速度倍数, t.属性.附加_攻击速度倍数 = 0, 0
    t.动作转移 = {}
    t.事件回调, t.跳跃信息, t.剩余掉血值 = noop, {}, 0
    t.被击中 = load('monster_damage', N)
    N.特效类 = {创建=function() return {} end}; t.绑定特效 = noop
-- Regression cases
local function poisonScene(version, story, level, skill)
    local s = setup(version, {story = story, level = level, skill = skill})
    s.hero.属性.属性集 = {}
    for i, element in ipairs({'火', '冰', '雷', '风', '神', '暗', '幻'}) do
        local key = '攻' .. element .. '元素'
        s.hero.自定义属性表[key] = true
        s.hero.属性.属性集[key], s.hero.属性['附加_' .. key] = i, 0
    end
    return s
end

local function misplaced(version, story, color, both)
    local s = poisonScene(version, story, 0)
    local other = color == red and green or red
    local cost = s.rank.数量
    if both then s.stock(70, color, 4 * cost) end
    s.stock(31, other, 4 * cost)
    direct(s).发生伤害()
    direct(s).发生伤害()
    eq(s.charges(31), 4 * cost, 'old code skips early slot')
    assert(not s.status(other) and not s.status(other .. '图标'))
    if both then
        assert(s.status(color) and s.status(color .. '图标'), version .. ' ' .. story .. ' missing poison or icon, ' .. s.charges(70))
        eq(s.charges(70), 3 * cost, 'only the later powder can be used')
    else
        assert(not s.status(color))
    end
end

for _, story in ipairs({'前尘忆梦', '来世续缘'}) do
    misplaced('old', story, red, true)
    misplaced('old', story, red, false)
    if arg[3] == 'legacy' then misplaced('legacy', story, green, true) end
    for level = 0, 5 do
        for _, slot in ipairs({31, 32, 80, 126}) do
            for colorIndex, color in ipairs({green, red}) do
                local s = poisonScene('new', story, level)
                local cost, mana = s.rank.数量, s.rank.消耗魔法
                local mp = s.hero.属性.mp
                s.rank.位置 = 3 - colorIndex
                s.stock(slot, color, cost)
                local cast = direct(s)
                cast.发生伤害()
                assert(s.status(color) and s.status(color .. '图标'))
                eq(s.charges(slot), 0)
                cast.发生伤害()
                eq(s.hero.属性.mp, mp - mana, 'one application per release')
            end
        end

        local s = poisonScene('new', story, level)
        local cost, mana = s.rank.数量, s.rank.消耗魔法
        local mp = s.hero.属性.mp
        s.rank.位置 = 2
        s.stock(31, green, 3 * cost)
        s.stock(32, red, 3 * cost)
        direct(s).发生伤害()
        assert(s.status(red) and not s.status(green))
        direct(s).发生伤害()
        assert(s.status(green .. '图标') and s.status(red .. '图标'))
        local greenExtra, greenBuff = s.status(green)
        local redExtra, redBuff = s.status(red)
        assert(greenBuff and redBuff)
        local greenDamage = s.rank.减少生命 + math.ceil(28 * 2 / 5)
        local reduction = -(s.rank.削弱防御 + 28)
        eq(greenExtra.生命值, -greenDamage)
        eq(redExtra.最大防御, reduction)
        eq(s.target.属性.附加_最大防御, reduction)
        eq(s.target.属性.附加_最大魔防, reduction)
        direct(s).发生伤害()
        eq(s.charges(31), 2 * cost)
        eq(s.charges(32), 2 * cost)
        eq(s.hero.属性.mp, mp - 2 * mana)
        eq(s.hero.技能信息[poison], nil, 'automatic hits leave manual cooldown untouched')
        local hp = s.target.属性.hp
        s.env.dt = 1.89
        greenBuff.更新()
        eq(s.target.属性.hp, hp)
        s.env.dt = .02
        greenBuff.更新()
        eq(s.target.属性.hp, hp - greenDamage)
    end

    -- Ranged release travels through the actual projectile before spending.
    local ranged = poisonScene('new', story, 0, '火球术')
    local cost = ranged.rank.数量
    ranged.stock(31, green, 2 * cost)
    ranged.hero.远程目标 = ranged.target
    attack(ranged, '火球术')
    eq(ranged.charges(31), 2 * cost)
    ranged:step(170)
    assert(#ranged.projectiles > 0 and ranged.status(green))
    eq(ranged.charges(31), cost)
end

do
    local s = poisonScene('new', '来世续缘', 5)
    local cost = s.rank.数量
    s.stock(31, green, cost - 1)
    s.stock(126, green, cost)
    local mp = s.hero.属性.mp
    s.hero.属性.mp = s.rank.消耗魔法 - 1
    direct(s).发生伤害()
    assert(not s.status(green))
    eq(s.charges(126), cost)
    s.hero.属性.mp = mp
    direct(s).发生伤害()
    assert(s.status(green))
    eq(s.charges(31), cost - 1)
    eq(s.charges(126), 0)
end

print('AUTO_POISON_V291_PASS', mode)
