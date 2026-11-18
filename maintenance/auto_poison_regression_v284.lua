-- Two separate releases in the same tick can apply both colors.
for level = 0, 5 do
    local s = setup('new', {level = level})
    chargeBoth(s)
    local mp = s.hero.属性.mp
    local first = direct(s)
    s.damageResult = {10, 1, 100}
    first.发生伤害()
    assert(s.status(green))
    eq(s.charges(31), 3)
    first.发生伤害()
    eq(s.charges(126), 4, 'same release cannot apply both colors')
    direct(s).发生伤害()
    assert(s.status(red))
    eq(s.charges(126), 3)
    eq(s.now(), 0)
    direct(s).发生伤害()
    eq(s.charges(31), 3)
    eq(s.charges(126), 3)
    eq(s.hero.属性.mp, mp - 2 * s.rank.消耗魔法)
    eq(s.hero.技能信息[poison], nil, 'auto must not initialize manual cooldown')
    eq(s.poses(), 0)
end

local function manualControl(s)
    s.hero.当前状态, s.hero.硬直 = 0, 0
    s.hero.释放技能组 = {}
    s.hero.__gm_melee_state_v208 = nil
end

for level = 0, 5 do
    local s, original = setup('new', {level = level}), setup('old', {level = level})
    chargeBoth(s)
    chargeBoth(original)
    direct(s).发生伤害()
    manualControl(s)
    attack(s, poison)
    attack(original, poison)
    local info = assert(s.hero.技能信息[poison])
    local baseline = original.hero.技能信息[poison]
    local keys = {'开始CD效果', '技能延时', 'dt', 'CD倍数', '技能延时计次', '当前帧'}
    eq(info.开始CD效果, true)
    eq(info.技能延时, 1.5)
    for _, key in ipairs(keys) do eq(info[key], baseline[key], key) end

    manualControl(s)
    eq(s:cast(poison), false, 'manual cooldown still blocks manual recast')

    s.env.dt = .025
    s:step(40)
    eq(info.开始CD效果, true)
    s:step(20)
    eq(info.开始CD效果, false)
    manualControl(s)
    attack(s, poison)
    eq(info.开始CD效果, true, 'manual cast starts its own cooldown again')
end

do
    local s = setup('new')
    chargeBoth(s)
    attack(s, poison)
    for _ = 1, 130 do
        if s.status(green) then break end
        s:step(1)
    end
    assert(s.status(green), 'actual manual poison effect')
    local info = s.hero.技能信息[poison]
    eq(info.开始CD效果, true)
    local snapshot = {}
    for _, key in ipairs({'开始CD效果', '技能延时', 'dt', 'CD倍数', '技能延时计次', '当前帧'}) do
        snapshot[key] = info[key]
    end
    direct(s).发生伤害()
    assert(s.status(red))
    eq(s.charges(126), 3, 'manual cooldown cannot stop automatic red poison')
    eq(s.hero.技能信息[poison], info)
    for key, value in pairs(snapshot) do eq(info[key], value, key) end
end

print('AUTO_POISON_V284_PASS', mode, checks)
