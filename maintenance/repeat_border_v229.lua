return function(self, cleanup)
    local sprite = self.__gm_repeat_border_v229
    if cleanup then
        if sprite then sprite.销毁(); self.__gm_repeat_border_v229 = nil end
        return
    end
    local state = self.Hero and self.Hero.__gm_repeat_skill_v229
    if not state or not state.active or state.key ~= self.快捷键 or state.name ~= self.绑定技能 then return end
    local w, h = self.宽度, self.高度
    if w < 2 or h < 2 then return end
    if not sprite then
        sprite = Q__.创建精灵(0, 0, 0, 1, 1)
        sprite.置颜色(-16711936) -- FF00FF00, green; only this active-slot overlay.
        sprite.置混合模式(L常量.混合_默认)
        self.__gm_repeat_border_v229 = sprite
    end
    local x, y = self.坐标.x + self.偏移X, self.坐标.y + self.偏移Y
    local perimeter = 2 * (w + h)
    local position, left = state.phase * perimeter, perimeter * 0.22
    while left > 0 do
        local length
        if position < w then
            length = math.min(left, w - position)
            sprite.显示_高级(x + position, y, 0, length, 2)
        elseif position < w + h then
            length = math.min(left, w + h - position)
            sprite.显示_高级(x + w - 2, y + position - w, 0, 2, length)
        elseif position < 2 * w + h then
            length = math.min(left, 2 * w + h - position)
            sprite.显示_高级(x + 2 * w + h - position - length, y + h - 2, 0, length, 2)
        else
            length = math.min(left, perimeter - position)
            sprite.显示_高级(x, y + perimeter - position - length, 0, 2, length)
        end
        left = left - length
        position = (position + length) % perimeter
    end
end
