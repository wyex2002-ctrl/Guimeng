return function(manual,hero,delta)
 if not hero then return manual end
 if hero.__gm_auto_pickup_v242~=true then hero.__gm_pickup_elapsed_v242=0;return manual end
 if hero.已经死亡 or not Ae冻集.屏幕焦点 or Ae冻集.游戏暂停 or (Ae冻集.逻辑暂停 or 0)>0 then
  hero.__gm_pickup_elapsed_v242=0;return manual
 end
 if type(delta)~='number'or delta~=delta or delta<0 then return manual end
 local elapsed=(hero.__gm_pickup_elapsed_v242 or 0)+delta
 if elapsed>=1 then hero.__gm_pickup_elapsed_v242=elapsed%1;return true end
 hero.__gm_pickup_elapsed_v242=elapsed
 return manual
end
