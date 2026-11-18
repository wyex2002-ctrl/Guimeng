local function panel(env, config, messages, story)
    env.错误处理 = noop
    env.是否为调试版 = function() return true end
    env.聊天文本框 = {内容高度 = 0, 内容 = '原有内容', 加入文本 = function(text)
        messages[#messages + 1] = text
    end}
    config.版本选择 = story
    config.金轮法王 = function() return -1 end
    bound('chat_init', env, {})()
    eq(type(config.开挖机的.孔爱琴泥), 'function')
end

local redPrefix = '#c(-65536)'
for _, story in ipairs({'前尘忆梦', '来世续缘'}) do
    local s = setup('new', {skill = '火球术'})
    local h, E, N = s.hero, s.db, s.env
    local U, messages, oilFloat = E.Ux雌, {}, {}
    N.Ae冻 = U
    N.L常量.颜色_红 = -65536
    panel(E, U, messages, story)
    U.托管显示 = {屏幕提示 = function(text) oilFloat[#oilFloat + 1] = text end}
    local oil = bound('oil_notice', N, E)
    oil('祝福油使用成功，幸运提升至 +1！', -11474824)
    eq(messages[1], '#c(-11474824)祝福油使用成功，幸运提升至 +1！#W')
    eq(#oilFloat, 1)
    E.聊天文本框.内容高度 = 500
    local skill = s.skills.火球术
    skill.消耗魔法, skill.消耗魔法_百分比 = 11, false
    skill.可使用 = true
    h.属性.mp = 10
    h.远程目标 = s.target
    h:技能配置('火球术')
    h.技能信息.火球术.可用 = true
    local slot = load('skill_slot', N)
    local shortcut = {Hero = h, 绑定技能 = '火球术'}
    local time = 0
    N.引擎.取运行时间 = function() return time end
    eq(slot(shortcut), false)
    eq(messages[2], redPrefix .. '魔法值不足#W')
    eq(E.聊天文本框.内容, '')
    for i = 1, 200 do eq(slot(shortcut), false) end
    eq(#messages, 2)
    eq(#oilFloat, 1)
    eq(#s.notices, 0)
    eq(h.属性.mp, 10)
    eq(h.技能信息.火球术.开始CD效果, false)
    eq(#h.释放技能组, 0)
    time = 999
    eq(slot(shortcut), false)
    eq(#messages, 2)
    time = 1000
    eq(slot(shortcut), false)
    eq(#messages, 3)
    h.属性.maxmp, skill.消耗魔法_百分比 = 100, true
    h.属性.mp = 11
    eq(slot(shortcut), true)
    eq(h.属性.mp, 0)
    eq(#messages, 3)
end

do
    local s = setup('new', {nativeSelect = true})
    local h, N, E = s.hero, s.env, s.db
    local U, messages = E.Ux雌, {}
    N.Ae冻 = U
    N.L常量.颜色_红 = -65536
    panel(E, U, messages, '来世续缘')
    U.托管显示 = {屏幕提示 = function(text) error('unexpected floating notice ' .. text) end}
    E.L常量 = N.L常量
    U.窗口相关.命中状态 = noop
    U.胚子考虑 = function() return {技能操作 = 0} end
    local learned = U.啾啾啵啵().技能
    learned.烈火剑法 = {0}
    s.skills.烈火剑法.消耗魔法, s.skills.烈火剑法.可使用 = 100, true
    h.属性.mp = 0
    local time = 0
    N.引擎.取运行时间 = function() return time end
    h:__gm_melee_timing_v208('charge_select', '普通攻击')
    eq(messages[1], redPrefix .. '魔法值不足，无法自动蓄力【烈火剑法】#W')
    time = 9999
    h:__gm_melee_timing_v208('charge_select', '普通攻击')
    eq(#messages, 1)
    time = 10000
    h:__gm_melee_timing_v208('charge_select', '普通攻击')
    eq(#messages, 2)
end

do
    local s = setup('new')
    local E, N = s.db, s.env
    local U, messages = E.Ux雌, {}
    N.Ae冻 = U
    N.L常量.颜色_红 = -65536
    panel(E, U, messages, '前尘忆梦')
    s.target:增加状态(green, 0, {})
    local time = 0
    N.引擎.取运行时间 = function() return time end
    direct(s).发生伤害()
    eq(messages[1], redPrefix .. '缺少施毒术所需的药粉。#W')
    time = 9999
    direct(s).发生伤害()
    eq(#messages, 1)
    time = 10000
    direct(s).发生伤害()
    eq(#messages, 2)
    eq(#s.notices, 0)
    s.stock(126, red, 200000)
    direct(s).发生伤害()
    assert(s.status(red))
    eq(s.charges(126), 200000 - s.rank.数量)
    eq(#messages, 2)
end

local function runShop()
    local balance, reputation = 1000000, 10000
    local inventory, slots, marks, options = {}, {}, {}, {}
    local role = {胶布香港 = {0, 0, reputation}}
    local template = {}
    local G = {}
    local U = {邮箱了啦 = 0, 游戏音效 = {按键音效1 = {播放 = noop}},
               胚子考虑 = function() return options end, 啾啾啵啵 = function() return role end,
               托管显示 = {屏幕提示 = function(text) error(text) end}, 窗口相关 = {}}
    local T = {}
    for k, v in pairs(table) do T[k] = v end
    local env = setmetatable({
        Ux雌 = U, Gly独 = G, table = T, Ae冻集 = {Game_State = 0},
        FXru胃啪 = setmetatable({}, {__index = function() return balance end}),
        对话窗口 = {对话 = noop}, 商店窗口 = {打开 = noop}, 背包窗口 = {打开 = noop},
        商店列表框 = {清空 = function() marks = {} end, 插入行 = noop, 置丰富文本 = noop,
                      置标记 = function(i, entry) marks[i] = entry end,
                      取标记 = function(i) return marks[i] end},
        物品格子18 = {}, 购买输入框 = {内容 = '1'},
        到数值 = tonumber, 分割文本 = split, 格式化数值 = tostring,
        intable = function(values, name)
            for _, value in ipairs(values) do if name == value then return true end end
            return false
        end,
    }, {__index = _G})
    load('table_register', env)()
    local sys = {script_setting = {Gly独 = G}, 游戏道具组 = template,
                 取包裹指定物品个数 = function() return 0 end,
                 Hero = {背包格子 = slots}, 包裹物品组 = inventory,
                 格式化道具属性 = function() return '' end, 更新道具属性 = noop,
                 qs_item_box = noop, 界面_窗口_数组 = {}, 脚本关联处理 = noop, 屏幕提示 = error}
    load('merc_helper', env)(sys, {Ux雌 = U})
    sys.数据保护 = bound('data_protection', env, sys)
    sys.增加物品 = bound('add_item', env, sys)
    sys.取包裹剩余空位 = bound('free_slots', env, sys)
    G.取包裹空位 = sys.取包裹剩余空位
    G.取道具信息_名称 = bound('template_info', env, sys)
    G.增加物品 = bound('gly_add', env, sys)
    load('stack_install', env)(sys)
    for _, powder in ipairs({green, red}) do
        local item = {名称 = powder, 显示名 = powder, 附加 = {叠加上限 = 999, 商店 = '杂货店'},
                      价格 = 1000, 分类 = '道具', 子类 = '药品', 叠加 = 1, 属性 = {}, 风格提示 = {}}
        item.附加 = sys.数据保护(item.附加, true)
        item.属性 = sys.数据保护(item.属性, true)
        template[powder] = item
    end
    for i = 31, 90 do
        slots[#slots + 1] = {i, {}, true}
        inventory[i] = {拿起 = false}
    end
    U.窗口相关.界面切换 = function(delta, kind)
        if kind == '声望' then role.胶布香港[3] = role.胶布香港[3] + delta
        else balance = balance + delta end
    end
    local shop = bound('shop', env, {信息窗口 = noop})
    U.窗口相关.商店窗口 = shop
    U.震爆山巅 = function(rows) shop(rows.声望, '珍宝阁') end

    local function buy(index)
        env.商店列表框.现行选中行 = index
        shop('购物')
        U.信息按钮()
    end
    bound('stock_old', env, {})()
    for i, entry in ipairs(marks) do
        if split(entry, '附加')[2] == green .. '(小)' then buy(i); break end
    end
    local legacy = assert(inventory[31].道具)
    eq(legacy.附加.最小次数, 100)
    eq(legacy.附加.最大次数, 100)
    legacy.附加.最小次数 = 88

    local expected = {小 = 20000, 中 = 40000, 大 = 60000, 特 = 100000, 特大 = 200000}
    local count = 0
    for _, catalog in ipairs({7783, 8395, 8780, 9149, 10031, 10635, 11161, 18485, 142}) do
        bound('stock_' .. catalog, env, {})()
        local checked = 0
        for index, entry in ipairs(marks) do
            local row = split(entry, '附加')
            if row[1] == green or row[1] == red then
                local size = row[2]:match('%((.-)%)')
                local charges = assert(expected[size])
                local price = tonumber(row[3])
                eq(tonumber(row[4]), charges)
                local previous, oldBalance = {}, balance
                for id = 31, 90 do
                    local previousItem = inventory[id].道具
                    previous[id] = previousItem and previousItem.数量 or 0
                end
                buy(index)
                count, checked = count + 1, checked + 1
                local item
                for id = 31, 90 do
                    local bought = inventory[id].道具
                    if bought and bought.数量 ~= previous[id] then
                        eq(item, nil, 'one slot gains a powder')
                        eq(bought.数量, previous[id] + 1)
                        item = bought
                    end
                end
                assert(item, row[2])
                eq(item.名称, row[1])
                eq(item.显示名, row[2])
                eq(item.附加.最小次数, charges)
                eq(item.附加.最大次数, charges)
                if row[5] == '声望' then
                    reputation = reputation - price
                    eq(role.胶布香港[3], reputation)
                else
                    eq(balance, oldBalance - price)
                end
                eq(inventory[31].道具, legacy)
                eq(legacy.数量, 1)
                eq(legacy.附加.最小次数, 88)
                eq(legacy.附加.最大次数, 100)
                eq(template[row[1]].附加.最大次数, nil)
            end
        end
        eq(checked, catalog == 8780 and 2 or 6)
    end
    eq(count, 50)
end

runShop()
