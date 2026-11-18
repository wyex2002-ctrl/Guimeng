local function screen(env, U, owner, hero)
    local rows, drawn = {}, {}
    assert(owner.Hero == hero or owner.Hero == nil)
    owner.Hero, owner.中间提示组, hero.中间提示组 = hero, {}, {}
    owner.Win_Obj = {text = function()
        local title
        return {置标题 = function(...)
            title = (...)
            rows[#rows + 1] = {...}
            return 12
        end, 显示 = function(x, y, alpha)
            if alpha then drawn[#drawn + 1] = {title, x, y, alpha} end
        end}
    end}
    env.Ae冻集 = env.Ae冻集 or {}
    env.Ae冻集.屏幕宽度, env.Ae冻集.屏幕高度 = 1280, 720
    env.Ae冻集.默认文字_间距, env.Ae冻集.默认文字_行距 = 0, 0
    env.聊天窗口 = {可视 = false}
    env.Gly独.屏幕高度 = 720
    env.Q_文字 = {取宽度 = function(message) return #message * 6 end, 取高度 = function() return 12 end}
    env.ARGB = function(a, r, g, b) return ((a * 256 + r) * 256 + g) * 256 + b end
    U.托管显示 = {屏幕提示 = load('screen_notice', env)}
    return rows, drawn
end

local function setupUI(s, story)
    local E, N = s.db, s.env
    local U, chat = E.Ux雌, {}
    N.Ae冻, U.版本选择 = U, story
    N.L常量.颜色_红 = -65536
    E.L常量 = N.L常量
    E.错误处理 = noop
    E.是否为调试版 = function() return true end
    E.聊天文本框 = {内容高度 = 0, 内容 = '原有内容', 加入文本 = function(line)
        chat[#chat + 1] = line
    end}
    U.金轮法王 = function() return -1 end
    bound('chat_init', E, {})()
    local rows, drawn = screen(N, U, s.owner, s.hero)
    local original = N.FXru胃啪.取状态列表
    N.FXru胃啪.取状态列表 = function(...)
        local current = original(...)
        current.信息提醒 = true
        return current
    end
    return U, rows, chat, drawn
end

for _, story in ipairs({'前尘忆梦', '来世续缘'}) do
    for _, version in ipairs({'previous', 'new'}) do
        local s = setup(version, {skill = '火球术'})
        local h, N, E = s.hero, s.env, s.db
        local U, rows, chat, drawn = setupUI(s, story)
        local oil = bound('oil_notice', N, E)
        oil('祝福油使用成功，幸运提升至 +1！', -11474824)
        eq(#rows, 1, 'oil reaches the original visible label')
        eq(#chat, 1, 'oil chat is retained for comparison')
        eq(rows[1][1], '祝福油使用成功，幸运提升至 +1！')
        local queue = s.owner.中间提示组
        eq(queue[1].x, 0, 'visible with chat closed')
        local skill = s.skills.火球术
        skill.消耗魔法, skill.消耗魔法_百分比, skill.可使用 = 11, false, true
        h.属性.mp, h.远程目标 = 10, s.target
        h:技能配置('火球术')
        h.技能信息.火球术.可用 = true
        local slot = load('skill_slot', N)
        local shortcut = {Hero = h, 绑定技能 = '火球术'}
        local clock = 0
        N.引擎.取运行时间 = function() return clock end
        for i = 1, 200 do eq(slot(shortcut), false) end
        local fresh = version == 'new'
        eq(#rows, fresh and 2 or 1, 'mana shortage, chat closed and native notice state already active')
        eq(#chat, fresh and 1 or 2)
        eq(#h.释放技能组, 0)
        eq(h.技能信息.火球术.开始CD效果, false)
        eq(h.属性.mp, 10)
        clock = 999
        eq(slot(shortcut), false)
        eq(#rows, fresh and 2 or 1)
        clock = 1000
        eq(slot(shortcut), false)
        eq(#rows, fresh and 3 or 1)
        if fresh then
            eq(rows[2][1], '魔法值不足')
            eq(rows[3][1], '魔法值不足')
            eq(rows[2][3], -65536)
            eq(queue[2].y, queue[1].y, 'mana rejection uses the same anchor as oil')
            N.聊天窗口.可视 = true
            clock = 2000
            eq(slot(shortcut), false)
            eq(queue[4].x, 320, 'native chat-open offset')
            bound('render_notices', N, s.owner)()
            eq(#drawn, 4, 'native frame renders all four queued notices')
            eq(drawn[4][1], rows[1][1], 'oil message renders in the same lane')
            eq(drawn[3][1], rows[2][1], 'low mana renders in the same lane')
            eq(drawn[3][2], drawn[4][2])
            eq(drawn[3][4], 250)
        end
        h.属性.mp = 11
        eq(slot(shortcut), true)
        eq(h.属性.mp, 0)
    end
end

do
    local s = setup('new', {nativeSelect = true})
    local h, E, N = s.hero, s.db, s.env
    local U, rows, chat = setupUI(s, '来世续缘')
    U.窗口相关.命中状态 = noop
    U.胚子考虑 = function() return {技能操作 = 0} end
    local learned = U.啾啾啵啵().技能
    local charged = {'烈火剑法', '翔空剑法', '莲月剑法'}
    for _, name in ipairs(charged) do
        learned[name] = {0}
        local skill = s.skills[name]
        skill.消耗魔法, skill.消耗魔法_百分比, skill.可使用 = 100, false, true
    end
    for _, name in ipairs({'普通攻击', '半月弯刀', '十方斩'}) do s.skills[name].可使用 = true end
    s.skills.半月弯刀.消耗魔法, s.skills.十方斩.消耗魔法 = 15, 15
    h:技能配置('普通攻击', '半月弯刀', '十方斩', unpack(charged))
    local stored = {已经消失 = function() return false end, 解除判断 = noop,
                    取标识 = function() return charged[1] end,
                    取信息 = function() return charged[1], '', 0, 0, {} end}
    h.BUFF组 = {stored}
    h.清除状态 = function() error('the native selector must preserve the stored charge') end
    h.属性.mp = 0
    local clock = 0
    N.引擎.取运行时间 = function() return clock end
    for i = 1, 200 do
        clock = (i - 1) * 50
        eq(s:cast(i % 2 == 0 and '半月弯刀' or '十方斩'), true)
        eq(upstate(s).技能信息.对象.名称, '普通攻击')
        h.释放技能组, h.当前状态, h.__gm_melee_state_v208 = {}, 0, nil
        h.技能信息.普通攻击.开始CD效果 = false
    end
    eq(h.BUFF组[1], stored)
    eq(#rows, 1)
    eq(rows[1][1], '魔法值不足，无法自动蓄力【烈火剑法】')
    eq(#chat, 0)
    h.技能信息.烈火剑法.可用 = false
    clock = 9999
    h:__gm_melee_timing_v208('charge_select', '普通攻击')
    eq(#rows, 1, 'a different skill shares the 10s timer')
    clock = 10000
    h:__gm_melee_timing_v208('charge_select', '普通攻击')
    eq(#rows, 2)
    eq(rows[2][1], '魔法值不足，无法自动蓄力【翔空剑法】')
end

local function press(s, name)
    local h = s.hero
    s.skills[name].可使用 = true
    h:技能配置(name)
    h.技能信息[name].可用 = true
    return load('skill_slot', s.env)({Hero = h, 绑定技能 = name})
end

local function waitForHitAndRecovery(s)
    local clock = s.now()
    repeat
        s:step(1)
        assert(s.now() - clock < 3, 'native attack did not finish')
    until #s.hero.释放技能组 == 0 and (s.hero.当前状态 == 0 or s.hero.当前状态 == 99)
end

for _, version in ipairs({'previous', 'new'}) do
    local fresh = version == 'new'
    local s = setup(version)
    local h = s.hero
    chargeBoth(s)
    h.攻击目标, h.远程目标, h.待选目标 = nil, nil, s.target
    eq(press(s, '半月弯刀'), true, 'first press with only a cursor target')
    eq(#s.effects, 0, 'no poison before damage')
    waitForHitAndRecovery(s)
    eq(#s.hits, 1)
    eq(s.hits[1].id, s.target.id)
    eq(s.charges(31), fresh and 3 or 4, 'first-hit powder use')
    eq(s.status(green) ~= nil, fresh)
    if fresh then eq(s.effects[1].at, s.hits[1].at) end
    eq(s.poses(), 0)
end

for _, version in ipairs({'previous', 'new'}) do
    local s = setup(version)
    local h = s.hero
    chargeBoth(s)
    h.待选目标 = h.攻击目标
    eq(press(s, '半月弯刀'), true)
    waitForHitAndRecovery(s)
    assert(s.status(green))
    local other = s.add(7, 2, 0)
    -- A separate ranged selection refreshes during the second sword swing.
    h.待选目标, h.远程目标 = s.target, nil
    local clock = s.now()
    while not press(s, '十方斩') do
        s:step(1)
        assert(s.now() - clock < 2, 'the second attack should follow native recovery')
    end
    h.远程目标 = other
    waitForHitAndRecovery(s)
    eq(s.status(red) ~= nil, version == 'new', 'consecutive melee skill fills the second poison')
    eq(s.charges(31), 3)
    eq(s.charges(126), version == 'new' and 3 or 4)
    eq(#other.BUFF组, 0)
    eq(s.poses(), 0)
end

do
    local s = setup('new')
    local h = s.hero
    chargeBoth(s)
    h.技能模式, h.主角配置.绑定技能 = 1, '半月弯刀'
    for _, name in ipairs({'半月弯刀', '十方斩'}) do s.skills[name].可使用 = true end
    h:技能配置('半月弯刀', '十方斩')
    h.开始物理攻击动作 = s.methods.开始物理攻击动作
    h:开始物理攻击动作(true, false)
    eq(#h.释放技能组, 1, 'native consecutive attack opener')
    h.远程目标 = s.add(7, 2, 0)
    waitForHitAndRecovery(s)
    assert(s.status(green))
    h.主角配置.绑定技能 = '十方斩'
    local clock = s.now()
    repeat
        s:step(1)
        h:开始物理攻击动作(true, false)
        assert(s.now() - clock < 2, 'native consecutive attack second swing')
    until #h.释放技能组 > 0 or s.status(red)
    waitForHitAndRecovery(s)
    assert(s.status(red))
    eq(s.charges(31), 3)
    eq(s.charges(126), 3)
    eq(h.技能信息[poison], nil, 'automatic hits do not initialize the manual cooldown')
end

for _, kind in ipairs({'retarget', 'dodge', 'veto', 'dual'}) do
    local s = setup('new')
    chargeBoth(s)
    s.hero.待选目标 = s.target
    if kind == 'dodge' then s.damageResult = {0, 2, 0} end
    if kind == 'veto' then s.blockDamage = true end
    if kind == 'dual' then
        s.target:增加状态(green, 0, {})
        s.target:增加状态(red, 0, {})
    end
    eq(press(s, '半月弯刀'), true)
    if kind == 'retarget' then s.hero.攻击目标 = s.add(7, 2, 0) end
    waitForHitAndRecovery(s)
    eq(s.charges(31), 4, kind)
    eq(s.charges(126), 4, kind)
end

do
    local s = setup('new')
    local h = s.hero
    chargeBoth(s)
    h.攻击目标, h.远程目标, h.待选目标 = nil, nil, s.target
    eq(press(s, '半月弯刀'), true)
    local splash = s.add(7, 1, 0)
    h.待选目标 = splash
    waitForHitAndRecovery(s)
    eq(#s.hits, 2, 'the native swing hits both monsters')
    assert(s.status(green))
    eq(#splash.BUFF组, 0, 'moving the cursor during a swing does not poison a splash victim')
    eq(s.charges(31), 3)
end

for _, changed in ipairs({false, true}) do
    local s = setup('new')
    chargeBoth(s)
    s.move(s.target, 3, 0)
    s.hero.攻击目标, s.hero.远程目标 = nil, s.target
    attack(s, '火球术')
    if changed then s.hero.远程目标 = s.add(7, 2, 0) end
    waitForHitAndRecovery(s)
    eq(#s.projectiles, 1, 'real ranged projectile')
    eq(s.charges(31), changed and 4 or 3, 'ranged hit continues to honor the original lock')
end

local function groundEnv()
    local title
    local N = setmetatable({
        Ae冻集 = {默认文字_间距 = 0, 默认文字_行距 = 0, 地面道具描边 = false},
        Q__ = {创建动画 = function() return {置中心点 = noop} end},
        Q_公用图片库 = {地面物品闪烁序列图 = {}},
        Q_地图 = {逻辑格子到坐标 = function(x, y) return x * 10, y * 10 end,
                  坐标到逻辑格子 = function(x, y) return x / 10, y / 10 end, 置格子信息 = noop,
                  取地图信息_总 = function() return {宽度 = 1000, 高度 = 1000} end},
        Q_文字 = {取宽度 = function(t) return #t * 6 end, 取高度 = function() return 12 end},
        ARGB = function(a, r, g, b) return ((a * 256 + r) * 256 + g) * 256 + b end,
        引擎 = {取随机整数 = function(_, lo) return lo end, 取随机小数 = function(_, lo) return lo end,
                取运行时间 = function() return 0 end},
        __gm_merc_name_v253 = function(_, label) return label end,
    }, {__index = _G})
    N.Sys = load('public_sys', N)({get = function(key)
        if key == 'hero' then return {} end
        if key == 'win_tex' then return function() return {置标题 = function(...) title = {...} end} end end
        error('unexpected ground constructor get ' .. tostring(key))
    end})
    local old, new = load('ground_previous', N), load('ground_new', N)
    return function(version, item, quantity, outline)
        local construct = version == 'new' and new or old
        N.Ae冻集.地面道具描边, title = outline, nil
        local o = {}
        construct(o, item, 5, 5, quantity, 0)
        assert(title)
        return o, title, function() return title end
    end
end

local ground = groundEnv()
local templates = assert(loadfile(work .. '/ground_templates.lua'))()
for _, item in pairs(templates) do
    local before, category = item.颜色值, item.category
    for _, count in ipairs({1, 9}) do
        for _, outline in ipairs({false, true}) do
            local _, old = ground('previous', item, count, outline)
            local object, current = ground('new', item, count, outline)
            local override = category == 'coin' or category == 'sun' or category == 'book'
            eq(current[3], override and -1 or old[3], category .. ': ' .. item.名称)
            eq(object.__gm_ground_label_color_v287, override and -1 or nil, category)
            for i = 1, 7 do if i ~= 3 then eq(current[i], old[i], 'native label metrics and styling') end end
            eq(item.颜色值, before, 'ground colors never modify the item')
        end
    end
end
for tier = 0, 7 do
    local item = {名称 = '测试装备', 显示名 = '测试装备', 分类 = '装备', 子类 = '武器',
                  颜色值 = -26368, 附加 = {条数 = tier, 商店 = '书店'}}
    for _, outline in ipairs({false, true}) do
        local _, old = ground('previous', item, 1, outline)
        local _, actual = ground('new', item, 1, outline)
        for k = 1, 7 do eq(actual[k], old[k], 'native equipment quality tint and outline') end
    end
end

for _, name in ipairs({'祝福油', '灵魂神水', '回城卷', '金币卷', '太阳水材料'}) do
    local item = {名称 = name, 显示名 = name, 分类 = '道具', 子类 = '消耗品', 颜色值 = -65536}
    local _, actual = ground('new', item, 1, true)
    eq(actual[3], -65536, 'unrelated ground item')
end

local function altRun(story, version)
    local items, balance = {}, {金币 = 100}
    local role = {鸡皮 = {100, 101, 101}}
    local U = {版本选择 = story, 人物选择 = 1, 窗口相关 = {},
               啾啾啵啵 = function() return role end, 临时重量 = 0, 主角背包负重 = 100,
               独角兽下 = function() return {极品数值 = {}} end,
               游戏音效 = {金币音效 = {播放 = noop}}}
    local G = {取道具信息_名称 = function() return {附加 = {}, 最大破坏 = 1} end,
               取包裹空位 = function() return 1 end}
    local E = setmetatable({Ux雌 = U, Gly独 = G, FXru胃啪 = balance,
                            格式化数值 = tostring, 金币标签 = {}, 包裹声望标签 = {}, 声望标签 = {},
                            Q金币标签1 = {}, Q金币标签2 = {}, L常量 = {颜色_黄 = -256, 键_ALT = 18}}, {__index = _G})
    local hero, owner, chat = {回调脚本 = {拾取 = load('pickup_callback', E)}}, {}, {}
    E.Ae冻集 = {屏幕焦点 = true, 逻辑暂停 = 0}
    local rows = screen(E, U, owner, hero)
    balance.屏幕提示 = bound('draw_notice', E, owner)
    balance.取状态列表 = function() return {信息提醒 = true} end
    balance.增加状态 = noop
    U.开挖机的 = {孔爱琴泥 = function(message) chat[#chat + 1] = message end}
    local function key(x, y) return y * 100 + x end
    for i, value in ipairs({91, 114, 55}) do
        local obj = {物品 = {名称 = i == 3 and '青铜斧' or '测试装备', 显示名 = '测试装备',
                     分类 = '装备', 子类 = '武器', 价格 = value, 叠加 = 0, 附加 = {},
                     属性 = {最大破坏 = 1}}, Hero = hero, 数量 = 1, 格子 = {x = i, y = 5}}
        obj.拾取 = function(self) self.已经消失 = true; return true end
        items[key(i, 5)] = {obj}
    end
    -- Partially picking up a solar potion stack rebuilds its label.
    local base = templates.强效太阳水
    local sun = {}
    for k, v in pairs(base) do sun[k] = v end
    sun.附加, sun.叠加 = {叠加上限 = 3}, 1
    local stack, _, latest = ground(version, sun, 5, false)
    stack.拾取 = function(self) eq(self.数量, 3); return true end
    if version == 'new' then items[key(5, 5)] = {stack} end
    E.table = setmetatable({copy = function(orig)
        local copy = {}
        for k, value in pairs(orig) do copy[k] = value end
        return copy
    end}, {__index = table})
    E.Q_地图 = {__gm_range_state = {地图格子列数 = 20, 地图格子行数 = 20,
                   到逻辑格子 = key, 地面物品组 = items}}
    E.Sys = {get = function(what)
        if what == 'hero' then return hero end
        if what == '控制对象' then return {地图格子 = {x = 5, y = 5}} end
        return {}
    end, run = function(op, f, a) eq(op, 'fun'); return true, f(unpack(a)) end}
    E._G = E
    E.loadstring = function(source)
        local f, reason = _G.loadstring(source)
        if f then setfenv(f, E) end
        return f, reason
    end
    local down = false
    E.引擎 = {取按键按下 = function(_, key) eq(key, 18); return down end}
    local currency = load(story == '前尘忆梦' and 'currency_first_story' or 'currency', E)
    U.窗口相关.界面切换 = currency
    local alt = bound('alt_' .. version, E, {script_setting = E})
    alt()
    eq(#rows, 0)
    down = true
    alt()
    local fresh = version == 'new'
    eq(#rows, fresh and 1 or 0, 'once per pickup, no individual sale prices')
    eq(#chat, fresh and 0 or 1)
    local summary = fresh and rows[1][1] or chat[1]
    eq(summary, fresh and '自动出售了白色装备，获得金币【103】' or
                         '#c(-256)自动出售了白色装备，获得金币【103】#W')
    eq(story == '前尘忆梦' and role.鸡皮[1] or balance.金币, 203)
    if fresh then
        eq(stack.数量, 2)
        eq(latest()[3], -1, 'partial pickup keeps white ground color')
        items[key(5, 5)] = nil
    end
    alt()
    eq(#rows, fresh and 1 or 0, 'empty repeat has no sale notice')
    eq(#chat, fresh and 0 or 1)
end

for _, story in ipairs({'来世续缘', '前尘忆梦'}) do
    altRun(story, 'previous')
    altRun(story, 'new')
end
print('COMBAT_UI_GROUND_V287_PASS', mode, checks)
