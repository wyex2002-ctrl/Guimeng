-- Native hero class only. A release owns one token, shared by all of its hit instances.
local poison = '施毒术'
local request = '__gm_poison_request_v282'
local greenEffect = '__gm_poison_green_v282'
local redEffect = '__gm_poison_red_v282'

local melee = {
    普通攻击 = true, 攻杀剑术 = true, 刺杀剑术 = true, 烈火剑法 = true,
    翔空剑法 = true, 莲月剑法 = true, 半月弯刀 = true, 十方斩 = true,
    -- The original dispatcher can substitute these passives for a normal swing.
    基本剑术 = true, 精神力战法 = true,
}
local scripted = {
    [poison] = true, 施毒大法 = true, 诱惑之光 = true,
    乾坤大挪移 = true, 斗转星移 = true,
    -- Both entry points can look single-target in the base configuration.
    炎天火雨 = true, 炎天火雨_引导 = true,
}

local meleeLock = '攻击目标'
local rangedLock = '远程目标'

local function liveMonster(target)
    if type(target) ~= 'table' or target.所属阵营 ~= '敌方'
        or target.可视 == false or target.已经死亡 or target.已经消失
        or target.是否有效 == false or target.不可选中
        or type(target.id) ~= 'number' or target.id <= 0 then return false end
    local attributes = target.属性
    return attributes and type(attributes.hp) == 'number' and attributes.hp > 0
end

local function singleTargetRanged(skill)
    if scripted[skill.名称] or skill.目标类型 ~= '敌方' or skill.施放位置 ~= '目标'
        or (skill.施法距离 or 0) <= 1 or (skill.类型 ~= 0 and skill.类型 ~= 1)
        or (skill.穿透模式 or 0) > 0 or (skill.地表持续时间 or 0) > 0
        or type(skill.作用范围) ~= 'table' then return false end
    for facing = 1, 8 do
        local area = skill.作用范围[facing]
        if type(area) ~= 'table' or #area > 1 then return false end
        local point = area[1]
        if point and (point.x ~= 0 or point.y ~= 0) then return false end
    end
    return true
end

local function prepare(hero, info, target)
    local skill = info.对象
    local isMelee = melee[skill.名称]
    if not isMelee and not singleTargetRanged(skill) then return end
    -- The release resolves its own target. An existing melee lock can still
    -- point elsewhere when a targeted skill updates the ranged lock.
    local preferRanged = not isMelee or
        (target ~= nil and target == hero[rangedLock] and target ~= hero[meleeLock])
    local primary, other = meleeLock, rangedLock
    if preferRanged then primary, other = rangedLock, meleeLock end
    if isMelee and not liveMonster(hero[primary]) then primary, other = other, primary end
    local monster = hero[primary]
    if not liveMonster(monster) or (not isMelee and target ~= monster) then return end
    return {target = monster, lock = primary, other = other, otherTarget = hero[other],
            map = Q_地图, mapId = Ae冻 and Ae冻.地图id}
end

local function stillLocked(hero, token)
    local other = hero[token.other]
    return hero[token.lock] == token.target
        and (other == token.otherTarget or other == token.target or not liveMonster(other))
end

local function missingColor(target)
    local green, red = false, false
    for _, buff in ipairs(target.BUFF组) do
        if not buff.已经消失() then
            local name = buff.取信息()
            if name == '灰色药粉' then green = true end
            if name == '黄色药粉' then red = true end
        end
    end
    if green and red then return end
    if green then return 2 end
    if red then return 1 end
    return 0
end

local function install(class, startCooldown, newSkillInfo)
    local lastNotice
    local errorReported = false

    local function apply(hero, target)
        local info = hero.技能信息[poison]
        if info and (info.开始CD效果 or info.可用 == false) then return end
        local skill = info and info.对象 or Sys.get('skill', poison)
        local callback = skill and skill.脚本 and skill.脚本.技能命中
        if type(callback) ~= 'function' or skill.可使用 == false then return end

        local needed = missingColor(target)
        if needed == nil then return end
        -- The existing poison script validates the learned rank and consumes
        -- the chosen powder in its own database environment.
        local arguments = {hero.id, {target.id}, needed, 0, request}
        local ok, paid = Sys.run('fun', callback, arguments)
        if not ok then return end
        if paid == 'missing' then
            local now = 引擎:取运行时间()
            if not lastNotice or now < lastNotice or now - lastNotice >= 10000 then
                lastNotice = now
                Sys.run('屏幕提示', '缺少施毒术所需的药粉。', '红')
            end
            return
        end
        if type(paid) ~= 'table' then return end

        if not info then
            info = newSkillInfo(skill)
            hero.技能信息[poison] = info
        end
        startCooldown(info)
        hero:MP改变(-paid[2])
        local position = target.地图坐标
        arguments[3], arguments[4] = math.round(position.x), math.round(position.y)
        arguments[5] = paid[1] == 1 and greenEffect or redEffect
        Sys.run('fun', callback, arguments)
    end

    class.__gm_poison_prepare_v282 = prepare
    class.__gm_poison_damage_v282 = function(hero, target, skill, ratio, extra, token, damage)
        if token.used or token.target ~= target then
            return damage(hero, target, skill, ratio, extra)
        end
        local before = target.属性.hp
        local result = damage(hero, target, skill, ratio, extra)
        -- Successful ordinary and critical hits report 0 and 1 respectively.
        -- A hurt callback can veto damage even after the accuracy roll succeeds.
        if type(result) ~= 'table' or (result[2] ~= 0 and result[2] ~= 1)
            or type(result[1]) ~= 'number' or result[1] <= 0
            or not liveMonster(target) or target.属性.hp >= before then return result end
        token.used = true
        if hero.已经死亡 or hero.属性.hp <= 0 or not stillLocked(hero, token)
            or Q_地图 ~= token.map
            or (Ae冻 and Ae冻.地图id) ~= token.mapId or Sys.get('hero') ~= hero
            or Sys.get('obj', target.id) ~= target then return result end
        local ok, why = pcall(apply, hero, target)
        if not ok and not errorReported then
            errorReported = true
            local logger = Sys.get('__gm_diag_checkpoint_v159')
            if type(logger) == 'function' then pcall(logger, 'skill.auto_poison.error', tostring(why)) end
        end
        return result
    end
end

return install
