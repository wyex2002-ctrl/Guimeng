local work, mode = arg[1], arg[2]
if mode == 'hot' then require('jit.opt').start('hotloop=1', 'hotexit=1') end
local checks = 0
local function eq(actual, expected, note)
    checks = checks + 1
    assert(actual == expected, (note or 'check') .. ': ' .. tostring(actual) .. ' ~= ' .. tostring(expected))
end
local function load(name, env, upvalue)
    local f = assert(loadfile(work .. '/' .. name .. '.ljbc'))
    if env then setfenv(f, env) end
    if upvalue then debug.setupvalue(f, 1, upvalue) end
    return f
end
local function clone(value)
    if type(value) ~= 'table' then return value end
    local copy = {}
    for k, v in pairs(value) do copy[k] = clone(v) end
    return copy
end
local function split(text, delimiter)
    local result = {}
    local start = 1
    while true do
        local a, b = text:find(delimiter, start, true)
        if not a then
            result[#result + 1] = text:sub(start)
            return result
        end
        result[#result + 1] = text:sub(start, a - 1)
        start = b + 1
    end
end
local function noop() end

local templates = assert(loadfile(work .. '/templates.lua'))()
local red, med, blue = '金创药_小', '金创药_中', '魔法药_小'
local sun, sun2, ice, water = '太阳水', '强效太阳水', '万年雪霜', '攻击神水_小'
local function fixture()
    local now, hpPending, mpPending = 100, 0, 0
    local state, notices, nativeNotices, legacyWrites = {}, {}, {}, {}
    local slots, cells, bank, rows = {}, {}, {}, {}
    local hero = {HP = 1000, 属性 = {等级 = 60, 性别 = '男', 职业 = '战士', maxhp = 1000, maxmp = 1000},
                  回调脚本 = {系统反馈 = function(_, text) nativeNotices[#nativeNotices + 1] = text; return true end},
                  BUFF状态更新 = noop, HP改变 = noop, MP改变 = noop, 背包格子 = {}}
    hero.取状态列表 = function() return state end
    hero.增加状态 = function(key, _, value) state[key] = value or true end
    local role = {法治观念 = true, 技能 = {}}
    local config = {行会选中 = {}, 技能操作 = 0, 运送物资 = {0}}
    local U = {版本选择 = '来世续缘', 主角HP = 1000, 主角MP = 1000,
               主角MAXHP = 1000, 主角MAXMP = 1000, 主角红恢复量 = 0, 主角蓝恢复量 = 0,
               啾啾啵啵 = function() return role end, 胚子考虑 = function() return config end,
               呦西鸽子 = function() return slots end, 佣兵背包 = {},
               托管显示 = {飘字 = noop, 屏幕提示 = function(text, color, placement)
                   eq(color, 42); eq(placement, 0)
                   notices[#notices + 1] = text
               end}}
    local G = {取按键状态 = function() return false end, 取运行时间 = function() return now end, 从ID取格子 = function(i) return slots[i] end,
               取道具信息_格子 = function(i) return slots[i] and slots[i].道具 end,
               取道具信息_名称 = function(n) return templates[n] end,
               取控件对象 = function(n) return cells[tonumber(n:sub(9))] end}
    local E = {
        Ux雌 = U, Gly独 = G, FXru胃啪 = hero, L常量 = {颜色_红 = 42}, 物品格子18 = {},
        type = type, math = math, pairs = pairs, table = table, tonumber = tonumber,
        分割文本 = split,
        __gm_oil_event_v245 = function() return false end,
    }
    local N = setmetatable({
        Ae冻 = U, Ae冻集 = {自定义属性表 = {}}, Q_鼠标 = {格子标识 = 0}, 取鼠标右键按下 = function() return true end,
        取鼠标左键按下 = function() return false end,
        __gm_oil_commit_v263 = function(item, remaining) item.数量 = remaining end,
    }, {__index = _G})
    for _, name in ipairs({'仓库窗口', '商店窗口', '佣兵窗口', '行会仓库', '信息窗口', '仓库窗口2', '信息窗口2', '商店窗口2'}) do
        E[name] = {可视 = false}
    end
    local function settings(prefix)
        for _, key in ipairs({'红', '蓝'}) do
            E[prefix .. '加' .. key .. '选择框'] = {选中 = false}
            E[prefix .. '加' .. key .. '滑块条'] = {位置 = 50}
        end
    end
    settings(''); settings('佣兵')
    local originalWindows = {}
    load('setup', E, originalWindows)()
    local windows = U.窗口相关
    eq(type(windows.__gm_potions_v293), 'function', 'real 来世 registry')
    windows.加血加蓝 = function(n, kind)
        if kind == 1 then hpPending = hpPending + n else mpPending = mpPending + n end
    end
    eq(E.Sys, nil); eq(E.pcall, nil); eq(E._G, nil)
    local itemEvent = load('item_event', E)
    local S = {tbl_qs = {qs_item_box = {Main = itemEvent}}, Hero = hero, 包裹物品组 = slots,
               界面_窗口_数组 = {{控件组 = rows}}, 脚本关联处理 = noop, shelp = {}, sid = 0}
    local function register(callback)
        S.shelp[tostring(callback)] = {sid = 5, msg = 'controlled potion callback'}
        return callback
    end
    local originalError
    G.错误 = function(message) originalError = message end
    S.script_setting = E
    local dispatch = load('dispatch', N, S)
    S.fun = function(callback, arguments)
        if callback then register(callback) end
        local ok, result = dispatch(callback, arguments, 0)
        assert(ok, tostring(originalError or result))
        return ok, result
    end
    local itemEventBridge = load('run_item_event', N, S)
    N.Sys = load('public_sys')({run = function(name, a, b, c)
        if name == 'qs_item_box' then
            -- Quest side effects on zero stock are outside the potion callback.
            if a[1] == 2 then return true end
            return itemEventBridge(a)
        elseif name == 'fun' then
            return S.fun(a, b)
        elseif name == '道具冷却更新' then
            legacyWrites[#legacyWrites + 1] = {a, b}
        elseif name == '屏幕提示' then
            nativeNotices[#nativeNotices + 1] = a
        elseif name ~= '脚本关联处理' then
            error('unexpected native call: ' .. name)
        end
    end})
    S.使用包裹物品 = load('use_bag', N, S)
    -- Reuse the exact Gly wrappers for live lookup and native dispatch. The
    -- named controls are a fixture for the engine's registered control array.
    local factory = load('gly_factory', N)
    debug.setupvalue(factory, 1, S)
    debug.setupvalue(factory, 2, S)
    local exported = factory()
    G.使用物品 = exported.使用物品
    local use, consume, mouse = load('item_use', N), load('consume', N), load('mouse_use', N)
    local function item(name, count, resource)
        local result = clone(assert(templates[name], name))
        result.数量 = count
        result.属性 = {}
        for _, key in ipairs({'生命值', '法力值', '生命值_百分比', '法力值_百分比',
                               '物理伤害', '魔法伤害', '魔法防御', '物理防御',
                               '命中', '躲避', '暴击', '移动速度', '攻击速度'}) do
            result.属性[key] = result[key] or 0
        end
        if resource ~= false then
            local encoded = name:gsub('.', function(c) return string.format('%02x', c:byte()) end)
            result.物品脚本 = load('script_' .. encoded, E)()
        end
        return result
    end

    for id = 21, 126 do
        slots[id] = {}
        local cell = setmetatable(
            {可用 = true, 标识 = id, Hero = hero, 道具CD组 = bank, 格子组 = slots,
             tbl = {}, 包围盒 = {检测_点 = function() return true end}, 使用物品 = use, 消耗 = consume, 焦点 = true, 更新道具属性 = noop},
            {__index = slots[id]})
        cells[id] = cell
        rows[#rows + 1] = {类型 = 6, 格子ID = id, 对象 = cell}
        if id >= 31 then hero.背包格子[#hero.背包格子 + 1] = {id, false, true} end
    end
    G.取包裹空位 = function()
        local count = 0
        for id = 31, 126 do if not slots[id].道具 then count = count + 1 end end
        return count
    end
    G.取物品数量 = function(name)
        local count = 0
        for id = 31, 126 do
            local t = slots[id].道具
            if t and t.名称 == name then count = count + t.数量 end
        end
        return count
    end
    G.增加物品 = function(name, count)
        for id = 31, 126 do
            if not slots[id].道具 then
                slots[id].道具 = item(name, count)
                return true
            end
        end
        return false
    end
    local function mercenary()
        local attrs = {最大生命值 = 1000, 最大法力值 = 1000, 红恢复量 = 0, 蓝恢复量 = 0}
        local merc = {HP = 1000, MP = 1000, id = 220, 属性 = attrs}
        setmetatable(attrs, {__index = function(_, key)
            if key == '当前生命值' then return merc.HP end
            if key == '当前法力值' then return merc.MP end
        end})
        U.佣兵对象, U.佣兵背包 = merc, {}
        for i = 1, 24 do
            local slot = {}
            slot.重置道具 = function(name)
                slot.道具 = name and item(name, 1)
            end
            slot.更新道具属性 = function(delta)
                for k, v in pairs(delta) do slot.道具[k] = v end
            end
            U.佣兵背包[i] = slot
        end
        return merc, U.佣兵背包
    end
    return {
        U = U, E = E, N = N, hero = hero, buff = state, notices = notices,
        nativeNotices = nativeNotices, legacyWrites = legacyWrites, legacy = bank,
        tick = load('periodic', E), advance = function(delta) now = now + delta end,
        recover = function()
            U.主角HP, U.主角MP = U.主角HP + hpPending, U.主角MP + mpPending
            hpPending, mpPending = 0, 0
        end,
        requested = function() return hpPending, mpPending end,
        put = function(i, name, quantity, shortcut)
            local bottle = name and item(name, quantity, not shortcut)
            if shortcut then bottle.附加.快捷物品 = 0 end
            slots[i].道具 = bottle
            return bottle
        end,
        count = function(i) return slots[i].道具 and slots[i].道具.数量 or 0 end,
        manual = function(i) return use(cells[i]) end,
        mouse = function(i) return mouse(cells[i]) end,
        key = function(i)
            local t = slots[i].道具
            return G.使用物品(t.名称, {__gm_autopotion_slot_v142 = i})
        end,
        mercenary = mercenary,
        mercPut = function(i, name, count)
            local bottle = name and item(name, count)
            U.佣兵背包[i].道具 = bottle
            return bottle
        end,
        mercCount = function(i) return U.佣兵背包[i].道具 and U.佣兵背包[i].道具.数量 or 0 end,
    }
end

do
    local f = fixture()
    f.put(31, red, 3).冷却时间 = 500
    f.put(32, med, 2)
    f.put(33, blue, 2)
    f.put(34, sun, 2)
    f.put(35, ice, 1)
    f.put(21, med, 1, true)
    f.legacy[red] = {开始CD效果 = true}
    eq(f.manual(31), true); eq(f.count(31), 2); eq(#f.legacyWrites, 0)
    f.mouse(21); eq(f.count(32), 2); eq(f.count(21), 1)
    eq(f.notices[1], '冷却中，请稍后再使用【金创药(中)】')
    eq(f.key(21), false); eq(#f.notices, 1, 'repeated manual notice throttled')
    eq(f.manual(33), true); eq(f.count(33), 1)
    eq(f.manual(34), true); eq(f.count(34), 1)
    eq(f.manual(35), false); eq(f.notices[2], '冷却中，请稍后再使用【万年雪霜】')
    local item = f.put(36, red, 2)
    f.put(31, nil)
    f.advance(2999); eq(f.manual(36), false); eq(item.数量, 2)
    f.advance(1); eq(f.manual(36), true); eq(item.数量, 1)
    eq(f.key(21), false); eq(f.count(32), 2, 'moved same group remains locked')
    eq(f.manual(35), true); eq(f.count(35), 0)
end

do
    local f = fixture()
    f.put(31, water, 3)
    f.put(32, red, 2)
    f.put(33, blue, 2)
    f.put(34, sun, 2)
    eq(f.manual(31), true); eq(f.count(31), 2)
    eq(f.buff.道具CD, true); eq(f.buff.攻击神水.最大破坏, 10)
    eq(f.manual(31), false); eq(f.count(31), 2)
    eq(f.notices[1], '冷却中，请稍后再使用【攻击神水(小)】')
    eq(f.manual(32), true); eq(f.manual(33), true); eq(f.manual(34), true)
    f.buff.道具CD = nil
    eq(f.manual(31), true); eq(f.count(31), 1)
    f.legacy[water] = {开始CD效果 = true}
    f.advance(500)
    eq(f.manual(31), false); eq(#f.notices, 2); eq(#f.nativeNotices, 0)
    f.put(35, '回城卷', 2)
    eq(f.manual(35), false)
    eq(f.notices[3], '冷却中，请稍后再使用【回城卷】')
end

do
    local f = fixture()
    f.U.主角HP, f.U.主角MP = 500, 400
    f.put(31, red, 2); f.put(32, med, 2); f.put(33, blue, 2)
    f.put(34, ice, 2); f.put(35, sun, 2); f.put(21, med, 1, true)
    f.tick()
    eq(f.count(31), 2); eq(f.count(32), 1, 'quick source wins over small bag potion')
    eq(f.count(33), 1, 'blue also used'); eq(f.count(35), 2)
    f.advance(999); f.tick(); eq(f.count(35), 2)
    f.advance(1); f.tick()
    eq(f.count(35), 1, 'one compound for two checks')
    eq(f.count(34), 2); eq(#f.notices, 0)
    f.tick(); eq(f.count(35), 1, 'same round and subsequent ticks respect cooldown')
end

do
    local f = fixture()
    f.U.主角HP, f.U.主角MP = 470, 470
    f.put(21, med, 1, true)
    f.put(31, med, 2); f.put(32, red, 1); f.put(33, blue, 1); f.put(34, sun, 2)
    f.put(31, nil)
    local earlier = f.put(40, red, 1)
    earlier.附加.加血 = 120
    f.tick(); eq(f.count(32), 0); eq(f.count(40), 1, 'uses the exact weakest live stack')
    eq(f.count(33), 0)
    f.U.主角HP = 471
    f.recover()
    f.advance(1000); f.tick(); eq(f.count(34), 2, 'fresh maximum and stats at rescue')
    f.U.主角MP = 100
    f.tick(); eq(f.count(34), 1, 'immediate when ordinary potion is absent or cooling')
end

do
    local f = fixture()
    f.U.主角HP = 50
    f.put(31, '金创药_小_包', 2); f.put(32, '强效太阳水_包', 1)
    f.tick()
    eq(f.count(31), 1, 'uses actual pack callback and consumes one pack')
    eq(f.E.Gly独.取物品数量(red), 5)
    eq(f.count(32), 1)
    f.advance(1000); f.tick()
    eq(f.count(32), 0)
    eq(f.E.Gly独.取物品数量(sun2), 5)
end

do
    local f = fixture()
    local merc = f.mercenary()
    f.U.主角HP, f.U.主角MP, merc.HP, merc.MP = 300, 1000, 150, 150
    f.put(31, sun, 2); f.put(32, red, 2)
    f.mercPut(1, med, 2); f.mercPut(2, red, 3); f.mercPut(3, blue, 2); f.mercPut(4, sun, 2)
    eq(f.manual(31), true)
    f.tick()
    eq(f.count(32), 1)
    eq(f.mercCount(1), 2); eq(f.mercCount(2), 2); eq(f.mercCount(3), 1)
    eq(merc.HP, 180); eq(merc.MP, 190)
    f.advance(999); f.tick(); eq(f.mercCount(4), 2)
    f.advance(1); f.tick(); eq(f.mercCount(4), 1, 'merc compound unaffected by hero cooldown')
    eq(merc.HP, 250); eq(merc.MP, 300); eq(f.count(31), 1); eq(#f.notices, 0)
    f.advance(1999); f.tick(); eq(f.mercCount(2), 2)
    f.advance(1); f.tick(); eq(f.mercCount(2), 1); eq(f.mercCount(3), 0)
    eq(f.mercCount(4), 1, 'new ordinary uses wait 1s')
    local second = f.mercenary()
    second.HP = 50; f.mercPut(1, sun, 1)
    f.tick(); eq(f.mercCount(1), 0, 'second merc instance has independent group clock')
end

do
    local f = fixture()
    local merc = f.mercenary()
    merc.HP, merc.MP = 50, 30
    f.put(31, red, 2); f.put(32, blue, 2); f.put(33, sun, 2)
    f.tick()
    eq(merc.HP, 50); eq(merc.MP, 30); eq(f.count(31), 2); eq(f.count(33), 2)
    f.mercPut(1, '强效太阳水_包', 2)
    f.mercPut(2, '金创药_小_包', 2)
    f.mercPut(3, '魔法药_小_包', 2)
    f.tick(); eq(merc.HP, 80); eq(merc.MP, 70)
    eq(f.mercCount(1), 2, 'compound pack reserved for rescue')
    eq(f.mercCount(2), 1); eq(f.mercCount(3), 1)
    f.advance(1000); f.tick(); eq(f.mercCount(1), 1)
    eq(merc.HP, 190); eq(merc.MP, 250)
end

do
    local f = fixture()
    local merc, bag = f.mercenary()
    merc.HP = 470
    f.mercPut(1, med, 1); f.mercPut(2, sun2, 1)
    f.tick()
    eq(merc.HP, 540)
    f.advance(1000); f.tick(); eq(f.mercCount(2), 1, 'merc heal exceeded threshold')
    f.advance(2000); merc.HP = 100; f.mercPut(1, med, 2)
    f.tick()
    merc.HP = 0; f.tick(); f.advance(1000); f.tick(); eq(f.mercCount(2), 1)
    local before = f.mercCount(1)
    f.U.佣兵对象 = nil; f.tick()
    f.advance(2000); f.U.佣兵对象, f.U.佣兵背包 = merc, bag
    merc.HP = 100
    f.tick(); eq(f.mercCount(1), before - 1, 'no stale rescue after death and departure')
    eq(f.mercCount(2), 1)
    f.E.佣兵加红选择框.选中 = true
    f.advance(1000); f.tick(); eq(f.mercCount(2), 1, 'disabled merc cancels rescue')
end

do
    local f = fixture()
    f.U.主角HP = 100
    f.put(31, red, 2); f.put(32, sun, 2)
    f.E.商店窗口.可视 = true; f.tick(); eq(f.count(31), 2)
    f.E.商店窗口.可视 = false; f.E.物品格子18.道具 = {}
    f.tick(); eq(f.count(31), 2)
    f.E.物品格子18.道具 = nil; f.tick(); eq(f.count(31), 1)
    f.E.加红选择框.选中 = true
    f.advance(1000); f.tick(); eq(f.count(32), 2)
    f.advance(2000); f.E.加红选择框.选中 = false
    f.tick(); eq(f.count(31), 0)
    f.E.加红滑块条.位置 = 5
    f.advance(1000); f.tick(); eq(f.count(32), 2, 'uses live setting')
end

do
    local f = fixture()
    local n = f.put(31, red, 2)
    f.put(32, sun, 2)
    f.E.物品格子18.道具 = {}
    eq(f.manual(31), false); eq(n.数量, 2)
    f.E.物品格子18.道具 = nil
    eq(f.manual(31), true, 'failed potion callback never starts cooldown')
    f.U.主角HP = 100
    f.tick(); eq(f.count(32), 1, 'manual red cooldown feeds the automatic fallback')
    eq(#f.notices, 0)
end

do
    local f = fixture()
    local merc = f.mercenary()
    merc.HP, merc.MP = 100, 1000
    f.mercPut(1, red, 2); f.mercPut(2, blue, 2)
    f.mercPut(3, sun, 3); f.mercPut(4, sun, 2)
    f.tick()
    f.advance(500); merc.MP = 100; f.tick()
    eq(f.mercCount(2), 1, 'blue can run during red cooldown')
    f.advance(500); merc.HP = 600; f.tick()
    eq(f.mercCount(3), 3, 'red check reads current health')
    f.advance(499); f.tick(); eq(f.mercCount(3), 3, 'separate one-second blue deadline')
    f.advance(1); f.tick(); eq(f.mercCount(3), 2, 'tie uses earlier merc slot')
    eq(f.mercCount(4), 2)
end

do
    local f = fixture()
    f.U.版本选择 = '前尘忆梦'
    load('setup', f.E, {})()
    eq(f.U.窗口相关.__gm_potions_v293, nil, 'original 前尘 registry')
    f.put(31, red, 2).冷却时间 = 500
    f.legacy[red] = {开始CD效果 = true}
    eq(f.manual(31), false); eq(f.count(31), 2); eq(#f.notices, 0)
    eq(f.nativeNotices[1], '正在冷却中，还不能使用 金创药(小)')
    f.legacy[red] = nil
    eq(f.manual(31), true); eq(f.count(31), 1)
    eq(#f.legacyWrites, 1, 'original stack cooldown follows previous story')
end

for _, story in ipairs({'前尘忆梦', '来世续缘'}) do
    local N = setmetatable({Ae冻 = {版本选择 = story}}, {__index = _G})
    local description = load('tooltip_description', N)
    for _, name in ipairs({sun, sun2, ice, water, red}) do
        local item = templates[name]
        local original = item.道具说明
        local updated = story == '来世续缘' and (name == sun or name == sun2 or name == ice)
        eq(description(item), updated and (original .. '\n#md与红蓝药冷却独立。') or original)
        eq(item.道具说明, original)
    end
    local buff = load('buff_visible', N)
    eq(buff({标识 = '道具CD'}, nil, nil, nil, {可视 = true}).可视, story == '前尘忆梦')
    eq(buff({标识 = '中毒'}, nil, nil, nil, {可视 = true}).可视, true)
end

for _ = 1, 200 do
    local f = fixture()
    f.U.主角HP, f.U.主角MP = 499, 499
    f.put(31, red, 2); f.put(32, blue, 2); f.put(33, sun, 2)
    f.tick()
    f.advance(1000); f.tick()
    eq(f.count(31), 1); eq(f.count(32), 1); eq(f.count(33), 1)
end
print(('POTIONS_V293_PASS %s (%d checks)'):format(mode, checks))
