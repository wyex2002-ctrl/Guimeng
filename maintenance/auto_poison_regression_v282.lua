local poison, green, red = '施毒术', '灰色药粉', '黄色药粉'
local tokenKey = '__gm_poison_token_v282'
local function bound(name, env, owner, index)
    local f = load(name, env)
    assert(debug.setupvalue(f, index or 1, owner))
    return f
end

local function setup(version, options)
    options = options or {}
    local s = scene(version, {bound = options.skill})
    local h, t, N = s.hero, s.target, s.env
    setmetatable(N, {__index = _G})
    N.丰富文本_解析 = function() return {}, 0, 0 end
    N.Ae冻集.自定义属性表 = {}
    local notices, failures, hits, effects = {}, {}, {}, {}
    local bag = {}
    for i = 31, 126 do
        local cell = {}
        cell.重置道具 = function(item) cell.道具 = item end
        bag[i] = cell
    end
    local E = {
        type = type, math = M, tonumber = tonumber, tostring = tostring, pairs = pairs,
        ipairs = ipairs, table = table, string = string, 分割文本 = split,
        是否为调试版 = function() return false end,
    }
    local U = {
        版本选择 = '来世续缘', 主角攻暗元素 = 20, 主角攻击速度 = 10,
        主角最小破坏 = 5, 主角最大破坏 = 5, 主角最小自然 = 6, 主角最大自然 = 6,
        主角最小灵魂 = 7, 主角最大灵魂 = 7, 窗口相关 = {}, 游戏音效 = {},
    }
    local ranks = load('ranks', E)()
    local learned = options.unlearned and {} or {[poison] = {options.level or 0}, 施毒大法 = {0}}
    U.啾啾啵啵 = function() return {技能 = learned} end
    U.大堵塞就 = function() return ranks end
    U.胚子考虑 = function() return {主角格子 = bag, 主角攻击速度 = 10} end
    U.窗口相关.抗菌药物 = load('powder_refill', E)
    U.窗口相关.元素窗口 = noop
    E.Ux雌 = U
    N.Ux雌 = U
    local owner = {Hero = h, Game_State = 1, shelp = {}, script_setting = E,
                   屏幕事件组 = {t}, 事件闭包表 = {}, 游戏技能组 = s.skills, 游戏状态组 = {}}
    local controls = {}
    owner.tbl_controls, owner.界面_窗口_数组 = {}, {{控件组 = controls}}
    for i = 31, 126 do
        local name = '物品格子' .. i
        controls[#controls + 1] = {名称 = name, 类型 = 6, 格子ID = i}
        owner.tbl_controls[name] = {tbl = bag[i]}
    end
    owner.取包裹指定物品个数 = function(name)
        local count = 0
        for _, cell in pairs(bag) do
            if cell.道具 and cell.道具.名称 == name then count = count + cell.道具.数量 end
        end
        return count
    end
    owner.格式化技能属性 = function() return '' end
    local G = bound('gly_class', N, owner, 2)()
    G.错误 = function(err) failures[#failures + 1] = debug.traceback(tostring(err), 2) end
    local heroProxy = bound('hero_api', N, owner, 2)()
    owner.FXru胃啪 = heroProxy
    E.Gly独, E.FXru胃啪 = G, heroProxy
    N.FXru胃啪 = heroProxy
    local install = bound('sandbox', N, owner)
    install(E)
    eq(owner.script_setting, E, 'actual sandbox installation')
    eq(E.Sys, nil); eq(E.pcall, nil); eq(E._G, nil)

    local baseRun = N.Sys.run
    local dispatch = bound('dispatch', N, owner)
    local lookup = bound('public_get', N, owner)
    local function register(fn)
        owner.shelp[tostring(fn)] = {sid = 'poison-test', msg = 'original event'}
        return fn
    end
    local manual = register(load('manual_event', E))
    local function run(op, first, ...)
        if op == 'fun' then
            if first == nil then return end
            if not owner.shelp[tostring(first)] then register(first) end
            local ok, a, b = dispatch(first, ...)
            assert(#failures == 0, table.concat(failures, '\n'))
            return ok, a, b
        end
        if op == 'qs_skill_drop' and (first[4] == poison or first[4] == '施毒大法') and first[1] == 0 then
            return run('fun', manual, first)
        end
        if op == '屏幕提示' then
            notices[#notices + 1] = {first, s.now()}
            return true
        end
        return baseRun(op, first, ...)
    end
    N.Sys = load('public_sys', N)({get = lookup, run = run, add = noop})
    eq(N.Sys.get('hero'), h)
    eq(N.Sys.get('obj', t.id), t)

    local poseCalls = 0
    h.播放指定动作 = function() poseCalls = poseCalls + 1 end
    -- Keep the lock selected while testing a single release.
    h.开始物理攻击动作 = function() return false end
    for _, name in ipairs({'物理伤害', '魔法伤害', '物理防御', '魔法防御', '命中', '暴击', '躲避'}) do
        h.属性[name], h.属性['附加_' .. name] = 0, 0
    end
    h.自定义属性表, h.实时移动速度 = {}, 10
    h.取状态列表 = load('list_status', N)
    h.清除状态 = noop
    h.id = 0
    h.发生伤害 = s.methods.发生伤害
    h.回调脚本.发生伤害 = register(function(id, skill, power)
        local result = s.damageResult or {10, 0, 100}
        hits[#hits + 1] = {id = id, name = skill, power = power, at = s.now()}
        if skill == poison or skill == '施毒大法' then return {-1, 6, 0} end
        return result
    end)
    local function addActor(a)
        a.可视 = true
        a.属性.附加 = {血条 = -18}
        a.属性.成长 = '怪物'
        a.属性.经验值, a.属性.经验倍数 = 0, 1
        for _, name in ipairs({'物理伤害', '魔法伤害', '物理防御', '魔法防御', '命中', '暴击', '躲避'}) do
            a.属性[name], a.属性['附加_' .. name] = 0, 0
        end
        a.自定义属性表, a.实时移动速度, a.本次移动速度倍数 = {}, 10, 10
        a.属性.攻击速度倍数, a.属性.移动速度倍数 = 10, 10
        a.属性.模型大小, a.属性.中心Y偏移 = 1, 0
        a.BUFF组 = {}
        a.增加状态 = load('add_status', N)
        a.取状态列表 = load('list_status', N)
        a.清除状态 = function(self, name)
            for i = #self.BUFF组, 1, -1 do
                if self.BUFF组[i].取信息() == name then table.remove(self.BUFF组, i) end
            end
        end
        a.BUFF状态更新 = noop
        a.被击中 = function(self, _, damage)
            if damage > 0 and not s.blockDamage then self.属性.hp = math.max(self.属性.hp - damage, 0) end
        end
        return a
    end
    addActor(t)
    N.类_BUFF图标类 = function(config, target, _, _, extra)
        local buf = {}
        buf.取信息 = function() return config.name, '', extra.持续时间 or 0, extra.持续时间 or 0, extra end
        buf.已经消失 = function() return buf.gone == true end
        buf.解除判断 = noop
        effects[#effects + 1] = {name = config.name, who = target.id, extra = extra, at = s.now()}
        return buf
    end
    for name, file in pairs({[green] = 'green_status', [red] = 'red_status'}) do
        owner.游戏状态组[name] = {name = name, 不可叠加 = true, 脚本 = load(file, E)()}
        owner.游戏状态组[name .. '图标'] = {name = name .. '图标', 不可叠加 = true}
    end
    s.skills[poison].脚本 = load('poison_' .. version, E)()
    s.skills.施毒大法.脚本 = load('area_poison_' .. version, E)()
    if not options.unlearned then load('rank_update', E)(poison) end
    local grid = N.Q_地图
    grid.取格子信息 = function(x, y, faction)
        local found = {}
        for _, actor in ipairs(owner.屏幕事件组) do
            if actor.所属阵营 == faction and actor.地图格子.x == x and actor.地图格子.y == y then
                found[#found + 1] = actor
            end
        end
        return found
    end
    grid.范围内对象检测 = function(x, y, _, faction, _, _, multiple)
        local found = grid.取格子信息(x, y, faction)
        return multiple and found or found[1]
    end
    grid.坐标到逻辑格子 = function(x, y) return math.floor(x / 48), math.floor(y / 32) end
    grid.逻辑格子到坐标 = function(x, y) return x * 48, y * 32 end
    local function move(a, x, y)
        a.地图格子, a.地图坐标 = {x = x, y = y}, {x = x * 48, y = y * 32}
    end
    move(t, 1, 0)
    N.核心.取两点间角度 = function(x, y, tx, ty) return math.deg(math.atan2(ty - y, tx - x)) end
    N.核心.取两点间距离 = function(x, y, tx, ty) return math.sqrt((tx - x)^2 + (ty - y)^2) end
    N.核心.取移动步幅 = function(deg) return math.cos(math.rad(deg)), math.sin(math.rad(deg)) end
    local function visual()
        return {置中心点 = noop, 置混合模式 = noop, 置颜色 = noop, 显示 = noop,
                显示_高级 = noop, 销毁 = noop, 更新 = noop}
    end
    N.__Res = function() return {宽度 = 24, 高度 = 32} end
    N.ARGB = function(a, r, g, b) return a * 16777216 + r * 65536 + g * 256 + b end
    N.__ResPath = ''
    N.类_轻动画 = {创建 = visual}
    N.Q__ = {创建精灵 = visual}
    N.L常量.混合_默认 = 0
    N.引擎.取随机小数 = function(_, low) return low end
    N.Ae冻集.屏幕偏移 = {x = 0, y = 0}
    local projectiles = {}
    local projectile = load('projectile', N)
    N.子弹类 = function(...)
        local p = projectile(...)
        projectiles[#projectiles + 1] = p
        return p
    end
    local step = s.step
    s.step = function(self, steps)
        for i = 1, steps do
            for _, p in ipairs(projectiles) do
                if not p.已经消失() then p.更新() end
            end
            step(self, 1)
        end
        assert(#failures == 0, table.concat(failures, '\n'))
    end
    s.stock = function(id, name, count)
        bag[id].道具 = count and {名称 = name, 数量 = 1, 附加 = {最小次数 = count, 最大次数 = 50}} or nil
    end
    s.charges = function(id)
        return bag[id].道具 and bag[id].道具.附加.最小次数 or 0
    end
    s.status = function(name)
        for _, buf in ipairs(t.BUFF组) do
            local kind, _, _, _, extra = buf.取信息()
            if kind == name and not buf.已经消失() then return extra, buf end
        end
    end
    s.add = function(id, x, y)
        local a = addActor({id = id, 属性 = {hp = 10000}, 所属阵营 = '敌方',
                            是否有效 = true, 锚点x = 0, 锚点y = 0})
        move(a, x, y)
        owner.屏幕事件组[#owner.屏幕事件组 + 1] = a
        return a
    end
    s.poses = function() return poseCalls end
    s.rank, s.hits, s.effects, s.notices, s.move = ranks[poison][(options.level or 0) + 1], hits, effects, notices, move
    s.projectiles, s.owner, s.db = projectiles, owner, E
    return s
end

local function attack(s, name)
    eq(s:cast(name or '普通攻击'), true, name or '普通攻击')
    local instance = upstate(s)
    assert(instance)
    return instance
end

local function chargeBoth(s)
    s.stock(31, green, 4)
    s.stock(126, red, 4)
end

-- Every supported melee release and every base single-target ranged skill
-- runs through the actual instance, update, damage and target status calls.
for _, name in ipairs({'普通攻击', '攻杀剑术', '刺杀剑术', '烈火剑法', '翔空剑法', '莲月剑法',
    '半月弯刀', '十方斩', '基本剑术', '精神力战法', '火球术', '大火球', '冰月神掌', '冰月震天',
    '霹雳掌', '雷电术', '风掌', '击风', '月魂断玉', '月魂灵波', '灵魂火符', '灭魂火符'}) do
    local old, new = setup('old', {skill = name}), setup('new', {skill = name})
    for _, s in ipairs({old, new}) do
        chargeBoth(s)
        local state = attack(s, name)
        eq(s.charges(31), 4, 'no powder at release')
        eq(s.poses(), 0)
        if s.skills[name].类型 == 1 then
            local i = 0
            repeat i = i + 1; s:step(1) until #s.projectiles > 0 or i > 200
            assert(#s.projectiles > 0, name)
            eq(s.charges(31), 4, 'no powder at projectile launch')
        end
        s:step(170)
        eq(s.poses(), 0, 'no added caster pose')
        eq(s.hero.攻击目标, s.target, 'lock intact')
        assert(#s.hits > 0, name)
        eq(state.施法者, s.hero)
    end
    eq(new.charges(31), 3, name)
    eq(new.charges(126), 4)
    assert(new.status(green) and new.status(green .. '图标'), name)
    eq(new.hero.属性.mp, old.hero.属性.mp - new.rank.消耗魔法)
    eq(#new.hits, #old.hits, 'original damage count')
    for i, hit in ipairs(old.hits) do
        eq(new.hits[i].name, hit.name); near(new.hits[i].power, hit.power); near(new.hits[i].at, hit.at)
    end
    eq(new.hero.动作, old.hero.动作)
    eq(new.hero.硬直, old.hero.硬直)
end

local function direct(s, name)
    name = name or '普通攻击'
    s.hero.当前状态, s.hero.硬直 = 0, 0
    s.hero.释放技能组 = {}
    s.hero.__gm_melee_state_v208 = nil
    local info = s.hero.技能信息[name]
    if info and name ~= poison then info.开始CD效果 = false end
    local instance = attack(s, name)
    instance.命中目标组 = {{s.target, 100}}
    return instance
end

-- Isolate native cooldown initialization from frame advancement and compare
-- the entire shared state with a real manual release.
for level = 0, 5 do
    local manual, auto = setup('old', {level = level}), setup('new', {level = level})
    chargeBoth(manual); chargeBoth(auto)
    attack(manual, poison)
    direct(auto).发生伤害()
    eq(auto.charges(31), manual.charges(31))
    eq(auto.hero.属性.mp, manual.hero.属性.mp)
    local automatic, hand = auto.hero.技能信息[poison], manual.hero.技能信息[poison]
    for _, key in ipairs({'开始CD效果', '技能延时', 'dt', 'CD倍数', '技能延时计次', '当前帧'}) do
        near(type(hand[key]) == 'number' and hand[key] or (hand[key] and 1 or 0),
             type(automatic[key]) == 'number' and automatic[key] or (automatic[key] and 1 or 0), key)
    end
    eq(automatic.技能延时, 1.5)
    eq(auto:cast(poison), false, 'auto -> manual shared lockout')
    manual:step(130)
    for key, value in pairs(manual.status(green)) do eq(auto.status(green)[key], value) end
    eq(auto.poses(), 0)
end

do
    local s = setup('new')
    chargeBoth(s)
    attack(s, poison)
    direct(s).发生伤害()
    eq(s.charges(31), 3, 'manual -> auto shared lockout')
    eq(s.charges(126), 4)
end

do
    local s = setup('new')
    chargeBoth(s)
    s.damageResult = {10, 1, 100}
    direct(s).发生伤害()
    eq(s.charges(31), 3, 'critical hits count')
    s.hero.释放技能组 = {}
    s.env.dt = .025
    s:step(40)
    eq(s.hero.技能信息[poison].开始CD效果, true)
    s:step(20)
    eq(s.hero.技能信息[poison].开始CD效果, false)
    direct(s).发生伤害()
    eq(s.charges(126), 3, 'native cooldown expires for the next attack')
end

do
    local s = setup('new')
    chargeBoth(s)
    local spell = s.skills.火球术
    spell.发射数量, spell.发射间隔, spell.发射方向 = 2, 0, 0
    attack(s, '火球术')
    eq(#s.hero.释放技能组, 3, 'native multishot constructor')
    local entries = s.hero.释放技能组
    local function stateAt(i) return select(2, debug.getupvalue(entries[i].刷新, 1)) end
    local firstToken = stateAt(1)[tokenKey]
    assert(firstToken, 'one token for three projectiles')
    for i = 2, 3 do eq(stateAt(i)[tokenKey], firstToken) end
    for i = 1, 3 do
        local state = stateAt(i)
        state.命中目标组 = {{s.target, 100}}
        if i == 1 then s.damageResult = {-1, -1, 0}
        else s.damageResult = nil end
        state.发生伤害()
        if i == 2 then s.hero.技能信息[poison].开始CD效果 = false end
    end
    eq(s.charges(31), 3, 'second projectile can trigger after the first misses')
    eq(s.charges(126), 4, 'third projectile uses the same attempt')
end

for _, existing in ipairs({green, red, 'both', 'expired', 'fallback'}) do
    local s = setup('new')
    chargeBoth(s)
    if existing == 'both' then
        s.target:增加状态(green, 0, {}); s.target:增加状态(red, 0, {})
    elseif existing == 'expired' then
        s.target:增加状态(green, 0, {})
        local _, buf = s.status(green)
        buf.gone = true
    elseif existing == 'fallback' then
        s.stock(31, green, nil)
    else
        s.target:增加状态(existing, 0, {})
    end
    direct(s).发生伤害()
    if existing == 'both' then
        eq(s.charges(31), 4); eq(s.charges(126), 4)
        eq(s.hero.技能信息[poison], nil)
    elseif existing == green or existing == 'fallback' then
        eq(s.charges(126), 3); assert(s.status(red))
    else
        eq(s.charges(31), 3); assert(s.status(green))
    end
end

for _, scenario in ipairs({'miss', 'zero', 'veto', 'unlearned', 'low_mana', 'dead', 'locked_other',
    'removed', 'invalid', 'new_map', 'friendly', 'foreign_caster'}) do
    local s = setup('new', {unlearned = scenario == 'unlearned'})
    chargeBoth(s)
    local instance = direct(s)
    if scenario == 'miss' then s.damageResult = {-1, -1, 0}
    elseif scenario == 'zero' then s.damageResult = {0, 0, 0}
    elseif scenario == 'veto' then s.blockDamage = true
    elseif scenario == 'low_mana' then s.hero.属性.mp = s.rank.消耗魔法 - 1
    elseif scenario == 'dead' then s.target.属性.hp = 1
    elseif scenario == 'locked_other' then s.hero.攻击目标 = s.add(33, 2, 0)
    elseif scenario == 'removed' then table.remove(s.owner.屏幕事件组, 1)
    elseif scenario == 'invalid' then s.target.是否有效 = false
    elseif scenario == 'new_map' then s.env.Ae冻.地图id = 'new'
    elseif scenario == 'friendly' then s.target.所属阵营 = '友方'
    elseif scenario == 'foreign_caster' then s.owner.Hero = {} end
    instance.发生伤害()
    eq(s.charges(31), 4, scenario)
    eq(s.hero.技能信息[poison], nil)
end

do
    local s = setup('new')
    chargeBoth(s)
    local nearby = s.add(28, 2, 0)
    local area = direct(s, '半月弯刀')
    area.命中目标组 = {{nearby, 50}, {s.target, 80}, {s.target, 100}}
    area.发生伤害()
    assert(s.status(green))
    eq(#nearby.BUFF组, 0, 'splash does not poison')
    s.hero.技能信息[poison].开始CD效果 = false
    area.发生伤害()
    eq(s.charges(126), 4, 'one attempt even on later damage of the same release')
    s.hero:发生伤害(s.target, '普通攻击', 1, {})
    eq(s.charges(126), 4, 'damage outside the release, including status ticks')
end

do
    local s = setup('new')
    s.stock(31, green, 2)
    s.target:增加状态(green, 0, {})
    local first = direct(s)
    first.发生伤害()
    eq(#s.notices, 1)
    eq(s.charges(31), 2, 'no fallback when a specific color is missing')
    s.stock(126, red, 1)
    first.发生伤害()
    eq(s.charges(126), 1, 'failed attempt also spends the one attempt')
    s.stock(126, red, nil)
    s.env.引擎.取运行时间 = function() return 9999 end
    direct(s).发生伤害()
    eq(#s.notices, 1)
    s.env.引擎.取运行时间 = function() return 10000 end
    direct(s).发生伤害()
    eq(#s.notices, 2)
    s.stock(126, red, 1)
    direct(s).发生伤害()
    eq(s.charges(126), 0, 'last charge clears cell')
    assert(s.status(red))
end

for _, name in ipairs({'炎天火雨', '炎天火雨_引导', '地狱火', '爆裂火焰', '诱惑之光', '乾坤大挪移', '斗转星移'}) do
    local s = setup('new')
    local instance = direct(s, name)
    eq(instance[tokenKey], nil, name)
end

for _, change in ipairs({'lock', 'gone', 'id_reused'}) do
    local s = setup('new')
    chargeBoth(s)
    s.move(s.target, 5, 0)
    attack(s, '火球术')
    for i = 1, 180 do
        if #s.projectiles > 0 then break end
        s:step(1)
    end
    eq(#s.projectiles, 1)
    if change == 'lock' then s.hero.攻击目标 = s.add(33, 1, 1)
    elseif change == 'gone' then s.target.已经消失 = true
    else s.owner.屏幕事件组[1] = s.add(s.target.id, 5, 0) end
    s:step(200)
    eq(s.charges(31), 4, 'projectile target ' .. change)
end

do
    local s = setup('new')
    chargeBoth(s)
    s.owner.游戏状态组[green].脚本.Main = function() return false end
    direct(s).发生伤害()
    eq(s.status(green), nil, 'native status veto still applies')
    eq(s.charges(31), 3)
    eq(#s.effects, 0)
end

do
    local s = setup('new')
    s.stock(31, green, 400)
    s.stock(126, red, 400)
    for i = 1, 200 do
        s.hero.技能信息[poison] = nil
        s.hero.属性.mp = 100
        s.hero.硬直, s.hero.当前状态 = 0, 0
        s.hero.释放技能组 = {}
        s.target.BUFF组 = {}
        direct(s).发生伤害()
        if i % 2 == 1 then assert(s.status(green)) else assert(s.status(red)) end
    end
    eq(s.charges(31), 300); eq(s.charges(126), 300)
end
print('AUTO_POISON_V282_PASS', mode, checks)
