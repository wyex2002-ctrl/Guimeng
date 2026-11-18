
-- A melee lock can survive when a direct cast selects a different monster.
for _, skill in ipairs({'火球术', '雷电术', '普通攻击', '半月弯刀'}) do
    for _, version in ipairs({'previous', 'new'}) do
        local s = setup(version)
        chargeBoth(s)
        local previous = s.add(7, 2, 0)
        if skill == '半月弯刀' then
            s.hero.攻击目标, s.hero.远程目标 = previous, s.target
            previous.已经消失 = true
            eq(s.hero:技能释放(skill, true, nil, nil, false), true)
        else
            s.hero.攻击目标 = previous
            attack(s, skill)
        end
        local state = upstate(s)
        state.命中目标组 = {{s.target, 100}}
        state.发生伤害()
        eq(s.charges(31), version == 'new' and 3 or 4, skill)
        eq(#previous.BUFF组, 0)
    end
end

local charged = {'烈火剑法', '翔空剑法', '莲月剑法'}
do
    local s = setup('new', {nativeSelect = true})
    local h, E, N = s.hero, s.db, s.env
    local U = E.Ux雌
    N.Ae冻 = U
    E.L常量 = {颜色_红 = -65536}
    N.L常量.颜色_红 = E.L常量.颜色_红
    local tips, removed = {}, 0
    U.托管显示 = {屏幕提示 = function(message) tips[#tips+1] = message end}
    U.窗口相关.命中状态 = noop
    U.胚子考虑 = function() return {技能操作 = 0} end
    local learned = U.啾啾啵啵().技能
    for _, name in ipairs(charged) do
        learned[name] = {0}
        s.skills[name].消耗魔法 = 100
        s.skills[name].可使用 = true
        s.skills[name].消耗魔法_百分比 = false
    end
    s.skills.半月弯刀.消耗魔法 = 15
    s.skills.十方斩.消耗魔法 = 15
    s.skills.普通攻击.可使用 = true
    s.skills.半月弯刀.可使用 = true
    s.skills.十方斩.可使用 = true
    h:技能配置("普通攻击", "半月弯刀", "十方斩", unpack(charged))
    local function fireBuff()
        local name = charged[1]
        h.BUFF组 = {{已经消失 = function() return false end, 解除判断 = noop,
                      取标识 = function() return name end,
                      取信息 = function() return name, '', 0, 0, {} end}}
    end
    h.清除状态 = function() removed = removed + 1; h.BUFF组 = {} end
    h.属性.mp = 0
    fireBuff()
    local previous = load('selector_previous', E)
    eq(previous(5, 0, 0, '半月弯刀'), '普通攻击')
    eq(tips[1], '火之真气消失了')
    eq(tips[2], '[半月弯刀]关闭')
    eq(removed, 1)
    tips = {}
    fireBuff()
    local time = 0
    N.引擎.取运行时间 = function() return time end
    for i = 1, 200 do
        local skill = i % 2 == 0 and '半月弯刀' or '十方斩'
        eq(s:cast(skill), true)
        eq(upstate(s).技能信息.对象.名称, '普通攻击')
        h.释放技能组, h.当前状态 = {}, 0
        h.__gm_melee_state_v208 = nil
        local normal = h.技能信息.普通攻击
        normal.开始CD效果 = false
        time = 50 * (i-1)
    end
    eq(removed, 1, 'low mana keeps the reserved hit')
    eq(#tips, 1)
    eq(tips[1], '魔法值不足，无法自动蓄力【烈火剑法】')
    time = 9999
    h:__gm_melee_timing_v208('charge_select', '普通攻击')
    eq(#tips, 1)
    time = 10000
    h:__gm_melee_timing_v208('charge_select', '普通攻击')
    eq(#tips, 2)
end

local function altRun(story)
    local notices, items, balance = {}, {}, {金币 = 100}
    local role = {鸡皮 = {100, 101, 101}}
    local U = {版本选择 = story, 人物选择 = 1, 窗口相关 = {},
               啾啾啵啵 = function() return role end, 临时重量 = 0, 主角背包负重 = 100,
               独角兽下 = function() return {极品数值 = {}} end,
               托管显示 = {屏幕提示 = function(t) notices[#notices+1] = t end},
               游戏音效 = {金币音效 = {播放 = noop}}}
    local G = {取道具信息_名称 = function() return {附加 = {}, 最大破坏 = 1} end,
               取包裹空位 = function() return 1 end}
    local E = setmetatable({Ux雌 = U, Gly独 = G, FXru胃啪 = balance,
                            格式化数值 = tostring, 金币标签 = {}, 包裹声望标签 = {}, 声望标签 = {},
                            Q金币标签1 = {}, Q金币标签2 = {}, L常量 = {颜色_黄 = -256}}, {__index = _G})
    local hero = {回调脚本 = {拾取 = load('pickup_callback', E)}}
    local function key(x, y) return y*100+x end
    for i, value in ipairs({91, 114, 55}) do
        local obj = {物品 = {名称 = i == 3 and '青铜斧' or '测试装备', 显示名 = '测试装备',
                     分类 = '装备', 子类 = '武器', 价格 = value, 叠加 = 0, 附加 = {},
                     属性 = {最大破坏 = 1}}, Hero = hero, 数量 = 1, 格子 = {x = i, y = 5}}
        obj.拾取 = function(self) self.已经消失 = true; return true end
        items[key(i, 5)] = {obj}
    end
    E.Ae冻集 = {屏幕焦点 = true, 逻辑暂停 = 0}
    E.Q_地图 = {__gm_range_state = {地图格子列数 = 20, 地图格子行数 = 20,
                   到逻辑格子 = key, 地面物品组 = items}}
    E.Sys = {get = function(what)
        if what == 'hero' then return hero end
        if what == '控制对象' then return {地图格子 = {x = 5, y = 5}} end
        return {}
    end, run = function(op, f, a) eq(op, 'fun'); return true, f(unpack(a)) end}
    E._G = E
    local currency = load(story == '前尘忆梦' and 'currency_first_story' or 'currency', E)
    U.窗口相关.界面切换 = currency
    local alt = assert(loadfile(work .. '/range_pickup.lua'))
    setfenv(alt, E)
    alt(U, G)
    eq(#notices, 1)
    eq(notices[1], '自动出售了白色装备，获得金币【103】')
    eq(story == '前尘忆梦' and role.鸡皮[1] or balance.金币, 203)
    alt(U, G)
    eq(#notices, 1, 'empty repeat has no sale notice')
    if story == '来世续缘' then
        currency(3)
        eq(notices[2], '得到金币 3')
        eq(balance.金币, 206)
    end
end
altRun('来世续缘')
altRun('前尘忆梦')
print('COMBAT_PICKUP_V283_PASS', mode, checks)
