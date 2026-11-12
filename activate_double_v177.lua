local owner
return function()
  Ux雌.游戏音效.按键音效1.播放()
  Ux雌.开挖机的.可激动了('__gm_daily_refresh_v173')
  local hero = Ux雌.啾啾啵啵()
  local pool = type(hero) == 'table' and hero.爽不精英 or nil
  local seconds = type(pool) == 'table' and tonumber(pool[1]) or 0
  if not seconds or seconds ~= seconds or seconds <= 0 then
    对话窗口.对话(0,0,37,30,'双倍经验剩余时间不足。\n每日新增时间会自动累计，玛法名俊每天可增加四小时。\n\n#Y#@Main@返回#W',nil,owner)
  elseif tonumber(pool[3]) == 1 then
    对话窗口.对话(0,0,37,30,'双倍经验已开启，剩余 ' .. 格式化数值(math.ceil(seconds/60)) .. ' 分钟正在生效。\n新领取的每日时间会直接累加到此余额，上限二十四小时。\n同一份余额无需重复领取。\n\n#Y#@Main@返回#W',nil,owner)
  else
    对话窗口.关闭()
    FXru胃啪.增加状态('双倍经验')
  end
end
