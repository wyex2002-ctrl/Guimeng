return function(self, cleanup)
    local cache = self.__gm_cooldown_mask_v227
    if cleanup then
        if cache then cache.sprite.销毁(); self.__gm_cooldown_mask_v227 = nil end
        return
    end
    local hero = self.Hero
    local info = hero and hero.技能信息 and hero.技能信息[self.绑定技能]
    if not info or not info.开始CD效果 then return end
    local frame = info.当前帧
    if type(frame) ~= 'number' or frame ~= frame then return end
    local step = math.floor(frame - 1)
    if step < 0 then step = 0 end
    if step >= 60 then return end
    local w, h = math.floor(self.宽度), math.floor(self.高度)
    if w < 1 or h < 1 then return end
    if not cache or cache.w ~= w or cache.h ~= h then
        if cache then cache.sprite.销毁() end
        local sprite = Q__.创建精灵(0, 0, 0, 1, 1)
        sprite.置颜色(-2013265920) -- 0x88000000, translucent black
        sprite.置混合模式(L常量.混合_默认)
        local angles = {}
        for y = 0, h - 1 do
            local row = {}
            for x = 0, w - 1 do
                local angle = math.atan2(x + 0.5 - w / 2, h / 2 - y - 0.5)
                if angle < 0 then angle = angle + math.pi * 2 end
                row[x + 1] = angle * 60 / (math.pi * 2)
            end
            angles[y + 1] = row
        end
        local masks = {}
        for f = 0, 59 do
            local spans = {}
            for y = 0, h - 1 do
                local start = nil
                for x = 0, w do
                    local covered = x < w and angles[y + 1][x + 1] >= f
                    if covered and not start then start = x end
                    if not covered and start then
                        spans[#spans + 1] = {start, y, x - start}
                        start = nil
                    end
                end
            end
            masks[f + 1] = spans
        end
        cache = {sprite = sprite, masks = masks, w = w, h = h}
        self.__gm_cooldown_mask_v227 = cache
    end
    local x = self.坐标.x + self.偏移X
    local y = self.坐标.y + self.偏移Y
    local spans = cache.masks[step + 1]
    for i = 1, #spans do
        local span = spans[i]
        cache.sprite.显示_高级(x + span[1], y + span[2], 0, span[3], 1)
    end
end
