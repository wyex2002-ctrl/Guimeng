-- Native map render coordinates. No movement callbacks run while drawing.
local function labels(map, mode, event, x, y, icon)
    local state = map.__gm_portal_labels_v212
    if not state then
        local routes = {} -- ROUTES_GENERATED
        state = {used = 0, queue = {}, cache = {}}
        -- Map plugins receive EM_引擎, not the event-only L引擎 wrapper.
        -- __Res is explicitly copied into pl_setting by the original installer.
        -- Same resource as Q_文字 in original 12/313, used by ground names.
        local font = __Res(2, '400132927.img')
        if not font or type(font.显示配置) ~= 'function' or type(font.解析) ~= 'function'
            or type(font.取宽度) ~= 'function' or type(font.取高度) ~= 'function' then
            state.disabled = true
            map.__gm_portal_labels_v212 = state
            return
        end
        state.font = font
        local h=math.max(1,font.取高度('入口',0))
        state.scale=math.max(1,h-3)/h
        -- EM_引擎 has no 画线. Its existing public sprite factory exposes
        -- rotation/scaling, so a cached one-pixel sprite supplies the thin line.
        local line = 引擎.创建精灵(0, 0, 0, 1, 1)
        line.置颜色(0xffe0ffe0)
        line.置中心点(0, 0.5)
        line.置混合模式(L常量.混合_默认)
        state.line = line
        state.resolve = function(id)
            local name = routes[id]
            if name == '@otherworld' then
                -- These same event IDs also serve as the normal ship entrance.
                local config = Ux雌.胚子考虑()
                local door = config and config.异界之门刷新
                if door == nil then return '神舰' end
                if door == 1329 or door == 1330 or door == 1331 then
                    local current = Ux雌.地图名称
                    if type(current) == 'string' and current ~= '' then return '异界' .. current end
                end
                return nil
            end
            if name ~= '@maze' then return name end
            -- The real entrance adds one to this counter before choosing.
            -- Preview the result without changing the player's saved counters.
            local config = Ux雌.胚子考虑()
            local maze = config and config.地图迷阵
            if not maze then return '魔灵迷阵' end
            local a = (tonumber(maze.ID1373) or 0) + (id == 1373 and 1 or 0)
            local b = (tonumber(maze.ID1374) or 0) + (id == 1374 and 1 or 0)
            local c = (tonumber(maze.ID1375) or 0) + (id == 1375 and 1 or 0)
            local d = (tonumber(maze.ID1376) or 0) + (id == 1376 and 1 or 0)
            if a == 1 and b == 1 and c == 1 and d == 1 then return '魔灵神殿' end
            if a >= 2 then return '魔灵冰殿' end
            if b >= 2 then return '魔灵风殿' end
            if c >= 2 then return '魔灵火殿' end
            if d >= 2 then return '魔灵雷殿' end
            return Ux雌.地图名称 or '魔灵迷阵'
        end
        state.render = function(owner)
            local width, height = owner.规格.w, owner.规格.h
            if width < 24 or height < 38 then return end
            local left, top, right, bottom = 4, 20, width - 4, height - 18
            for i = 1, state.used do
                local entry = state.queue[i]
                local w, h = entry.w, entry.h
                local best_x, best_y, best_score
                -- Prefer above, then below, left, right. Further rings handle
                -- adjacent exits. All candidates stay inside the map texture.
                for ring = 0, 3 do
                    local gap = 7 + ring * (h + 3)
                    for direction = 1, 4 do
                        local lx, ly
                        if direction == 1 then lx, ly = entry.x - w / 2, entry.y - gap - h
                        elseif direction == 2 then lx, ly = entry.x - w / 2, entry.y + gap
                        elseif direction == 3 then lx, ly = entry.x - gap - w, entry.y - h / 2
                        else lx, ly = entry.x + gap, entry.y - h / 2 end
                        local overflow = math.max(0, left - lx) + math.max(0, lx + w - right)
                            + math.max(0, top - ly) + math.max(0, ly + h - bottom)
                        lx = math.max(left, math.min(lx, right - w))
                        ly = math.max(top, math.min(ly, bottom - h))
                        local overlap = 0
                        for j = 1, i - 1 do
                            local other = state.queue[j]
                            if lx < other.lx + other.w + 3 and lx + w + 3 > other.lx
                                and ly < other.ly + other.h + 2 and ly + h + 2 > other.ly then
                                overlap = overlap + 1
                            end
                        end
                        for j = 1, state.used do
                            local point = state.queue[j]
                            if point.x >= lx - 4 and point.x <= lx + w + 4
                                and point.y >= ly - 4 and point.y <= ly + h + 4 then
                                overlap = overlap + 1
                            end
                        end
                        local score = overlap * 100000 + overflow * 100 + ring * 4 + direction
                        if not best_score or score < best_score then best_x, best_y, best_score = lx, ly, score end
                    end
                end
                entry.lx, entry.ly = math.floor(best_x), math.floor(best_y)
            end
            -- Draw connectors before every label, so a later line cannot cover
            -- earlier text. Use the nearest label edge, leaving the dot clear.
            for i = 1, state.used do
                local entry = state.queue[i]
                local tx = math.max(entry.lx, math.min(entry.x, entry.lx + entry.w))
                local ty = math.max(entry.ly, math.min(entry.y, entry.ly + entry.h))
                local dx, dy = tx - entry.x, ty - entry.y
                local distance = math.sqrt(dx * dx + dy * dy)
                if distance > 12 then
                    local ux, uy = dx / distance, dy / distance
                    line.显示_高级(entry.x + ux * 5, entry.y + uy * 5,
                        math.atan2(dy, dx), distance - 7, 1)
                end
            end
            for i = 1, state.used do
                local entry = state.queue[i]
                -- Match ground-name 72/3: cached parsed glyphs and the same
                -- optional outline, without the larger baked-outline font.
                local outline
                if Ae冻集.地面道具描边 then outline = -14078936 end -- FF292C28
                font.显示配置(entry.layout, entry.lx, entry.ly, -1, outline, state.scale)
            end
        end
        map.__gm_portal_labels_v212 = state
    end
    if state.disabled then return end
    if mode == 'begin' then
        -- Drop previous-map entities and widths once, not a growing global list.
        if state.map ~= map.上次地图对象 or state.image ~= map.上次地图标识 or state.name ~= Ux雌.地图名称 then
            state.cache = {}; state.queue = {}; state.map = map.上次地图对象; state.image = map.上次地图标识; state.name = Ux雌.地图名称
        end
        state.used = 0; state.frame = (state.frame or 0) + 1
    elseif mode == 'collect' then
        local markers = map.__gm_minimap_v1101
        if not markers or icon ~= markers.portal then return end
        local name = state.resolve(event.id)
        if not name or name == '' then return end
        local entry = state.cache[event.id]
        if not entry then entry = {}; state.cache[event.id] = entry end
        if entry.frame == state.frame then return end
        entry.frame = state.frame
        local font = state.font
        local available = (map.规格.w - 8)/state.scale
        local spacing = Ae冻集.默认文字_间距 or 2
        local line_spacing = Ae冻集.默认文字_行距 or -3
        if entry.raw ~= name or entry.available ~= available
            or entry.spacing ~= spacing or entry.line_spacing ~= line_spacing then
            entry.raw, entry.available = name, available
            entry.spacing, entry.line_spacing = spacing, line_spacing
            local wrapped, line, i = '', '', 1
            while i <= #name do
                local count = string.sub(name, i, i) > '\127' and 2 or 1
                local char = string.sub(name, i, i + count - 1)
                if line ~= '' and font.取宽度(line .. char, spacing) > available then
                    wrapped = wrapped .. line .. '\n'; line = char
                else line = line .. char end
                i = i + count
            end
            entry.text = wrapped .. line
            entry.w = font.取宽度(entry.text, spacing)*state.scale
            entry.h = math.max(1, font.取高度(entry.text, line_spacing))*state.scale
            entry.layout = font.解析(entry.text, spacing, line_spacing)
        end
        entry.x, entry.y = x, y
        state.used = state.used + 1
        state.queue[state.used] = entry
    elseif mode == 'draw' then
        state.render(map)
    end
end
return labels
