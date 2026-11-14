-- Native window overlay only. Registered once on the existing base-window class.
-- Keep current-health text, positioning, visibility and native API contracts.
local function draw(window)
    if type(window) ~= 'table' or rawget(window, 'id') ~= 564 then return end
    if Sys.get('Game_State') ~= 1 or not rawget(window, '可视') then return end
    if type(Ae冻) ~= 'table' then return end
    local ally = Ae冻.佣兵对象
    if type(ally) ~= 'table' then return end
    local attr = ally.属性
    if type(attr) ~= 'table' then return end
    local hp, maxhp = attr.当前生命值, attr.最大生命值
    if type(hp) ~= 'number' or hp ~= hp or hp == math.huge or hp == -math.huge or hp < 0 then return end
    if type(maxhp) ~= 'number' or maxhp ~= maxhp or maxhp == math.huge or maxhp == -math.huge or maxhp <= 0 then return end
    local controls, pos = rawget(window, '控件组'), rawget(window, '坐标')
    if type(controls) ~= 'table' or type(pos) ~= 'table' then return end
    local x, y = rawget(pos, 'x'), rawget(pos, 'y')
    if type(x) ~= 'number' or x ~= x or x == math.huge or x == -math.huge then return end
    if type(y) ~= 'number' or y ~= y or y == math.huge or y == -math.huge then return end
    for i = 1, #controls do
        local control = controls[i]
        if type(control) ~= 'table' then return end
        if rawget(control, '名称') == '佣兵血量进度条' then
            local cx, cy, width = rawget(control, 'x'), rawget(control, 'y'), rawget(control, 'w')
            if type(cx) ~= 'number' or cx ~= cx or cx == math.huge or cx == -math.huge then return end
            if type(cy) ~= 'number' or cy ~= cy or cy == math.huge or cy == -math.huge then return end
            if type(width) ~= 'number' or width ~= width or width == math.huge or width == -math.huge then return end
            local drawx, drawy = x + cx + width / 2, y + cy - 14
            if drawy < 0 then drawy = 0 end
            Q_文字.显示(drawx, drawy, tostring(math.floor(hp)), 1, -1, SETA(0, 255))
            return
        end
    end
end
return draw
