local work, mode = arg[1], arg[2]
if mode == 'hot' then require('jit.opt').start('hotloop=1', 'hotexit=1') else jit.off() end
local checks = 0
local function eq(actual, expected, label)
    checks = checks + 1
    assert(actual == expected, (label or 'check') .. ': ' .. tostring(actual) .. ' ~= ' .. tostring(expected))
end

local function loadChunk(name, env)
    return setfenv(assert(loadfile(work .. '/' .. name .. '.ljbc')), env)
end

local function bind(name, env, sys)
    local chunk = loadChunk(name, env)
    assert(debug.setupvalue(chunk, 1, sys))
    return chunk
end

local function noop() end

local function scene()
    local bag, slots, templates, notices = {}, {}, {}, {}
    local G = {}
    local T = {}
    for k, v in pairs(table) do T[k] = v end
    local env = setmetatable({
        table = T, Ae冻集 = {Game_State = 0}, Gly独 = G, Q_鼠标 = {被占用 = false},
        L常量 = {颜色_红 = -65536}, 对话窗口 = {关闭 = noop},
        intable = function(values, name)
            for _, value in ipairs(values) do if name == value then return true end end
            return false
        end,
        Ux雌 = {游戏音效 = {按键音效1 = {播放 = noop}}, 托管显示 = {屏幕提示 = function(text)
            notices[#notices + 1] = text
        end}},
    }, {__index = _G})
    loadChunk('table_register', env)()
    local sys = {script_setting = {Gly独 = G}, 游戏道具组 = templates, 包裹物品组 = bag,
                 Hero = {背包格子 = slots}, 格式化道具属性 = function() return '' end,
                 更新道具属性 = noop, qs_item_box = noop, 界面_窗口_数组 = {},
                 脚本关联处理 = noop, 屏幕提示 = function(text) error(text) end}
    for field, source in pairs({数据保护 = 'data_protection', 取包裹指定物品个数 = 'count_item',
                                减少包裹物品 = 'remove_item', 增加物品 = 'add_item',
                                取包裹剩余空位 = 'free_slots'}) do
        sys[field] = bind(source, env, sys)
    end
    G.取物品数量 = bind('gly_count', env, sys)
    G.减少物品 = bind('gly_remove', env, sys)
    G.增加物品 = bind('gly_add', env, sys)
    loadChunk('stack_install', env)(sys)
    for i = 31, 39 do
        slots[#slots + 1] = {i, {}, true}
        bag[i] = {拿起 = false}
    end
    for _, name in ipairs({'灰色药粉', '黄色药粉'}) do
        templates[name] = {名称 = name, 显示名 = name, 分类 = '道具', 子类 = '药品', 叠加 = 1,
                           价格 = 1000, 风格提示 = {}, 附加 = sys.数据保护({商店 = '杂货店', 叠加上限 = 999}, true),
                           属性 = sys.数据保护({}, true)}
    end
    return env, bag, templates, notices
end

for _, root in ipairs({7868, 9261, 10400}) do
    for powder, ingredients in pairs({
        灰色药粉 = {'食人花树叶', '食人花果实', '毒蜘蛛牙齿'},
        黄色药粉 = {'食人花树叶', '蛆卵', '蝎子的尾巴'},
    }) do
        for _, size in ipairs({'小', '中'}) do
            local env, bag, templates, notices = scene()
            local name = '嘱托' .. powder .. '_' .. size
            local old = loadChunk('npc_' .. root .. '_old', env)()[name]
            local new = loadChunk('npc_' .. root .. '_new', env)()[name]
            local cost = size == '小' and 1 or 2
            local function fill(missing, surplus)
                for i, ingredient in ipairs(ingredients) do
                    bag[32 + i].道具 = {名称 = ingredient, 数量 = cost + surplus - (i == missing and 1 or 0)}
                end
            end
            local function checkIngredients(expected)
                for _, ingredient in ipairs(ingredients) do eq(env.Gly独.取物品数量(ingredient), expected, ingredient) end
            end

            fill(nil, 0)
            old()
            checkIngredients(0)
            local legacy = assert(bag[31].道具)
            eq(legacy.附加.最大次数, cost * 100)
            eq(legacy.附加.最小次数, cost * 100)
            legacy.附加.最小次数 = legacy.附加.最小次数 - 1
            for i = 1, #ingredients do
                fill(i, 0)
                new()
                eq(#notices, i)
                eq(notices[i], '所需物品数量不足')
                eq(env.Gly独.取物品数量(powder), 1)
                for j, ingredient in ipairs(ingredients) do
                    eq(env.Gly独.取物品数量(ingredient), cost - (j == i and 1 or 0))
                end
            end

            fill(nil, 1)
            new()
            checkIngredients(1)
            eq(#notices, 3)
            eq(env.Gly独.取物品数量(powder), 2)
            eq(bag[31].道具, legacy)
            eq(legacy.数量, 1)
            eq(legacy.附加.最大次数, cost * 100)
            eq(legacy.附加.最小次数, cost * 100 - 1)
            local crafted = assert(bag[32].道具)
            eq(crafted.名称, powder)
            eq(crafted.显示名, powder .. '(' .. size .. ')')
            eq(crafted.价格, legacy.价格)
            eq(crafted.附加.商店, legacy.附加.商店)
            eq(crafted.数量, 1)
            eq(crafted.附加.最小次数, cost * 20000)
            eq(crafted.附加.最大次数, cost * 20000)
            eq(templates[powder].附加.最大次数, nil)
        end
    end
end

print('POWDER_CRAFT_V286_PASS', mode, checks)
