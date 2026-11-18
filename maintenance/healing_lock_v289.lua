return function(class)
    local heal = '治愈术'

    local function live(unit)
        if type(unit) ~= 'table' or unit.已经死亡 or unit.已经消失
            or unit.是否有效 == false or unit.不可选中
            or type(unit.地图格子) ~= 'table' or type(unit.地图坐标) ~= 'table' then return false end
        local attrs = unit.属性
        return type(attrs) == 'table' and type(attrs.hp) == 'number' and attrs.hp > 0
            and type(attrs.maxhp) == 'number'
            and (not attrs.附加 or attrs.附加.不能治愈 == nil)
    end

    local function eligible(hero, unit, mercId)
        if not live(unit) or unit.所属阵营 ~= hero.所属阵营 then return false end
        if unit == hero then return true end
        local id = unit.id
        if type(id) ~= 'number' or id <= 0 then return false end
        local owner = unit.主人id
        if owner == nil and type(unit.宠物配置) == 'table' then owner = unit.宠物配置.主人 end
        if type(owner) == 'table' then owner = owner.id end
        return id == mercId or owner == hero.id or (mercId ~= nil and owner == mercId)
    end

    local function companionId()
        local merc = Ae冻 and Ae冻.佣兵对象
        return type(merc) == 'table' and merc.id or nil
    end

    local function mapId()
        return Ae冻 and Ae冻.地图id
    end

    class.__gm_heal_capture_v289 = function(hero, target, queued)
        if queued and hero.下次技能 == heal and hero.__gm_heal_pending_v289 then
            return hero.__gm_heal_pending_v289
        end
        local mercId = companionId()
        local mouse = Ae冻集.鼠标焦点事件对象
        if eligible(hero, mouse, mercId) and mouse ~= hero and Sys.get('obj', mouse.id) == mouse then
            target = mouse
        elseif not eligible(hero, target, mercId) or (target ~= hero and Sys.get('obj', target.id) ~= target) then
            target = hero
            if hero.属性.hp >= hero.属性.maxhp then
                for _, unit in ipairs(Sys.get('__gm_screen_objects_v154') or {}) do
                    if unit ~= hero and eligible(hero, unit, mercId) and unit.属性.hp < unit.属性.maxhp
                        and (target == hero or unit.属性.hp < target.属性.hp
                        or (unit.属性.hp == target.属性.hp
                            and (unit.id == mercId or (target.id ~= mercId and unit.id < target.id)))) then
                        target = unit
                    end
                end
            end
        end
        return {target = target, map = Q_地图, id = mapId()}
    end

    class.__gm_heal_target_v289 = function(hero, cast)
        local target = cast and cast.target
        if not cast or Q_地图 ~= cast.map or mapId() ~= cast.id
            or not eligible(hero, target, companionId())
            or (target ~= hero and Sys.get('obj', target.id) ~= target) then return nil end
        if 判断是否在攻击范围(hero.地图格子, target.地图格子, hero.本次攻击距离) < 0 then
            return false
        end
        if target ~= hero then
            local p, q = hero.地图坐标, target.地图坐标
            hero.方向 = 核心.取两点间方向(p.x + hero.锚点x, p.y + hero.锚点y,
                q.x + target.锚点x, q.y + target.锚点y)
        end
        return target
    end

    class.__gm_heal_init_v289 = function(_, state)
        if state.技能信息.对象.名称 ~= heal then return false end
        state.__gm_heal_lock_v289 = {map = Q_地图, id = mapId()}
        state.技能施放位置 = '目标'
        return true
    end

    local function invalid(hero, state)
        local lock = state.__gm_heal_lock_v289
        if not lock then return false end
        local target = state.目标
        if Q_地图 == lock.map and mapId() == lock.id and Sys.get('hero') == hero
            and eligible(hero, target, companionId())
            and (target == hero or Sys.get('obj', target.id) == target) then return false end
        state.完成 = true
        return true
    end

    class.__gm_heal_invalid_v289 = invalid
    class.__gm_heal_hits_v289 = function(hero, state)
        if not state.__gm_heal_lock_v289 then return false end
        if not invalid(hero, state) then
            state.命中目标组[1] = {state.目标, 100}
        end
        return true
    end
end
