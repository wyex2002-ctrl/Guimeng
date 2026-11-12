-- DB sandbox: use explicit exported APIs only; no pcall/xpcall/global writes.
return function(mode, unused)
  local hero = Ux雌.啾啾啵啵()
  if type(hero) == 'table' then
    local today = os.date('%Y-%m-%d')
    local pool = hero.爽不精英
    if type(today) == 'string' and #today == 10 and type(pool) == 'table' then
      local premium = tonumber(pool[9]) == 1
      local entitlement = premium and 14400 or 7200
      local credited = 0
      if hero.__gm_double_day_v173 == today then
        credited = tonumber(hero.__gm_double_granted_v177) or 7200
        if credited ~= credited or credited < 0 then credited = 7200 end
      end
      if credited < entitlement then
        local before = tonumber(pool[1]) or 0
        if before ~= before or before < 0 then before = 0 end
        pool[1] = math.min(before + entitlement - credited, 86400)
        hero.__gm_double_day_v173 = today
        hero.__gm_double_granted_v177 = entitlement
        if type(调试输出2) == 'function' then
          调试输出2('[gm.double.v177] day=' .. today .. ' premium=' .. tostring(premium) .. ' credited=' .. credited .. ' entitlement=' .. entitlement .. ' before=' .. before .. ' after=' .. pool[1])
        end
      end
    end
  end
  if mode ~= '__gm_daily_refresh_v173' then
    Ux雌.窗口相关.定时检测(3, 取系统时间(1))
  end
end
