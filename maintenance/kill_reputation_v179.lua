-- UTF-8 source; compile game strings as GBK using official LuaJIT 2.0.
return function(victim, killer_id, former_owner_id)
  local function finite(v)
    return type(v) == 'number' and v == v and v > -math.huge and v < math.huge
  end
  local function log(message)
    local S = type(Sys) == 'table' and Sys or nil
    local out
    if S and type(S.get)=='function' then
      local ok,value=pcall(S.get,'__gm_diag_checkpoint_v159')
      if ok then out=value end
    end
    if type(out)~='function' then out=S and S.__gm_diag_checkpoint_v159 or nil end
    if type(out) ~= 'function' then out = __gm_diag_checkpoint_v159 end
    if type(out) == 'function' then
      pcall(out, 'reputation.v179', message)
    else
      local setting = S and S.script_setting or nil
      local fallback = type(setting) == 'table' and setting.Log or Log
      if type(fallback) == 'function' then pcall(fallback, '[gm.rep.v179] ' .. message) end
    end
  end
  local function work()
    killer_id = tonumber(killer_id)
    if former_owner_id ~= nil then former_owner_id = tonumber(former_owner_id) or former_owner_id end
    if type(victim) ~= 'table' then log('skip: invalid victim type=' .. type(victim)); return end
    log('entry name=' .. tostring(victim.名称) .. ' faction=' .. tostring(victim.所属阵营) .. ' killer=' .. tostring(killer_id) .. ' former_owner=' .. tostring(former_owner_id))
    if victim.所属阵营 ~= '敌方' then log('skip: non-hostile victim'); return end
    if former_owner_id ~= nil and former_owner_id ~= -1 then log('skip: owned victim'); return end
    local stats = victim.属性
    if type(stats) ~= 'table' or not finite(tonumber(stats.hp)) or tonumber(stats.hp) > 0 then log('skip: invalid or living victim'); return end
    if victim.__gm_rep_done_v168 then log('skip: settled corpse'); return end
    local extra = stats.附加
    if type(extra) ~= 'table' then log('skip: missing monster attributes'); return end
    local boss = not not extra.BOSS
    local raw_level = extra.等级
    local level = tonumber(raw_level)
    if not finite(level) then level = tonumber(victim.等级) end
    if not finite(level) then level = tonumber(stats.等级) end
    log('data monster_level=' .. tostring(raw_level) .. ' type=' .. type(raw_level) .. ' hp=' .. tostring(stats.hp))
    if not finite(level) or level < 1 then log('skip: invalid monster level name=' .. tostring(victim.名称)); return end
    -- This function runs in the native event environment, not the database
    -- sandbox. Resolve its documented native aliases and script settings.
    local setting = type(Sys) == 'table' and Sys.script_setting or nil
    if type(setting) ~= 'table' then setting = {} end
    local U = Ae冻
    if type(U) ~= 'table' then U = setting.Ux雌 end
    if type(U) ~= 'table' then U = Ux雌 end
    local G = setting.Gly独
    if type(G) ~= 'table' then G = Gly独 end
    if type(U) ~= 'table' or type(U.啾啾啵啵) ~= 'function' then
      log('skip: missing native role accessor'); return
    end
    if not finite(killer_id) or killer_id < 0 or killer_id % 1 ~= 0 then
      log('skip: invalid killer=' .. tostring(killer_id)); return
    end
    local hero = U.啾啾啵啵()
    if type(hero) ~= 'table' then log('skip: invalid role'); return end
    local merc = U.佣兵对象
    if type(merc) == 'function' then
      local ok, value = pcall(merc)
      merc = ok and value or nil
    end
    local merc_id
    if type(merc) == 'table' then
      merc_id = tonumber(merc.id)
      if not finite(merc_id) and type(merc.对象) == 'table' then merc_id = tonumber(merc.对象.id) end
    elseif finite(merc) then merc_id = merc end
    local credited, current = killer_id == 0, killer_id
    for depth = 1, 8 do
      if credited then break end
      if finite(merc_id) and merc_id > 0 and current == merc_id then credited = true; break end
      local actor
      if type(Sys)=='table' and type(Sys.get)=='function' then
        actor=Sys.get('obj',current)
      elseif type(G)=='table' and type(G.事件对象)=='function' then actor=G.事件对象(current) end
      if type(actor) ~= 'table' then break end
      local owner = tonumber(actor.主人id)
      if not finite(owner) then
        local pet = actor.宠物配置
        owner = type(pet) == 'table' and pet.主人 or nil
        if type(owner) == 'table' then owner = owner.id end
        owner = tonumber(owner)
      end
      if not finite(owner) or owner < 0 or owner % 1 ~= 0 then break end
      if owner == 0 then credited = true; break end
      current = owner
    end
    if not credited then log('skip: unowned kill=' .. killer_id); return end
    local window, wallet = U.窗口相关, hero.胶布香港
    if type(window) ~= 'table' or type(window.界面切换) ~= 'function' or
       type(wallet) ~= 'table' or not finite(tonumber(wallet[3])) then
      log('skip: unavailable reward API or wallet'); return
    end
    local pending = hero.__gm_rep_pending_v170
    if pending == nil then pending = 0 end
    if not finite(pending) or pending < 0 or pending % 1 ~= 0 then
      log('skip: invalid pending reputation'); return
    end
    local amount, roll, hero_level = 0, nil, nil
    if boss then
      amount = math.ceil(level / 3)
    else
      -- The persistent role record has no flat 等级 field. Read the same
      -- runtime Hero.属性.等级 that the original FX proxy getter uses.
      local live
      if type(Sys)=='table' and type(Sys.get)=='function' then
        local ok,value=pcall(Sys.get,'hero');if ok then live=value end
      end
      if type(live)~='table' then live=type(Sys)=='table' and Sys.Hero or nil end
      local attributes = type(live) == 'table' and live.属性 or nil
      hero_level = type(attributes) == 'table' and tonumber(attributes.等级) or nil
      if not finite(hero_level) then
        local fx = setting.FXru胃啪
        if type(fx) == 'table' then hero_level = tonumber(fx.等级) end
      end
      if not finite(hero_level) and type(FXru胃啪) == 'table' then hero_level = tonumber(FXru胃啪.等级) end
      if not finite(hero_level) or hero_level < 1 then
        log('skip ordinary: missing live hero level; monster_level=' .. level .. ' killer=' .. killer_id)
        return
      end
      if level < hero_level - 30 then
        log('skip ordinary: below threshold; monster_level=' .. level .. ' hero_level=' .. hero_level ..
            ' minimum=' .. (hero_level - 30) .. ' killer=' .. killer_id)
        return
      end
      local rng=type(G)=='table' and G.取随机数 or nil
      local engine_rng=false
      -- Same engine RNG used by the original Gly API (module14/proto90).
      if type(rng)~='function' and 引擎 and type(引擎.取随机整数)=='function' then
        rng=引擎.取随机整数;engine_rng=true
      end
      if type(rng)~='function' then log('skip: missing ordinary reward RNG');return end
      if engine_rng then roll=rng(引擎,1,100) else roll=rng(1,100) end
      if not finite(roll) or roll < 1 or roll > 100 or roll % 1 ~= 0 then
        log('skip: invalid chance RNG'); return
      end
      if roll <= 10 then
        if engine_rng then amount=rng(引擎,1,3) else amount=rng(1,3) end
        if not finite(amount) or amount < 1 or amount > 3 or amount % 1 ~= 0 then
          log('skip: invalid ordinary reward RNG'); return
        end
      end
      log('ordinary roll=' .. roll .. ' hit=' .. tostring(roll <= 10) .. ' amount=' .. amount .. ' hero_level=' .. hero_level .. ' monster_level=' .. level)

    end
    local total = pending + amount
    if not finite(total) or total > 9007199254740991 or tonumber(wallet[3]) + total > 9007199254740991 then
      log('skip: reward outside exact numeric range'); return
    end
    -- Keep the existing per-life marker, which all original spawn/reset hooks
    -- already clear. Queue the reward in the persistent role record first.
    victim.__gm_rep_done_v168 = true
    hero.__gm_rep_pending_v170 = total
    if total == 0 then
      hero.__gm_rep_pending_v170 = nil
      return
    end
    local before = tonumber(wallet[3])
    local ok, err = pcall(window.界面切换, total, '声望')
    local after = type(hero.胶布香港) == 'table' and tonumber(hero.胶布香港[3]) or nil
    if finite(after) and after - before == total then
      hero.__gm_rep_pending_v170 = nil
      log('award kind=' .. (boss and 'boss' or 'ordinary') .. ' name=' .. tostring(victim.名称) .. ' level=' .. level ..
          ' hero_level=' .. tostring(hero_level) .. ' killer=' .. killer_id .. ' amount=' .. amount .. ' queued=' .. pending ..
          ' paid=' .. total .. ' before=' .. before .. ' after=' .. after)
      if not ok then log('UI error after successful award: ' .. tostring(err)) end
    else
      log('defer kind=' .. (boss and 'boss' or 'ordinary') .. ' level=' .. level .. ' pending=' .. total .. ' before=' .. before ..
          ' after=' .. tostring(after) .. ' error=' .. tostring(err))
    end
  end
  local ok, err = pcall(work)
  if not ok then log('error: ' .. tostring(err)) end
end
