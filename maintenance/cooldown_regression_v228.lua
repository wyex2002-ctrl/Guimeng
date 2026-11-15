-- A separate real automatic-charge scene supplies native BUFF instances.
local charge=charge_scene('new')
charge.hero.属性.mp=100000
charge:step(20)
local hero=charge.hero
local slots={}
x0,y0,w0,h0=13,24,48,48
for _,name in ipairs(charged)do
 local item=env.类_格子_技能格子();item.初始化(item,10,20,48,48,name,0,false,'charge')
 item.Hero=hero;slots[name]=item
 eq(hero.__gm_auto_charge_v216.ready[_],true,'native automatic reserve')
end
local function drawcharge(name)
 grid={};area=0;local item=slots[name];item.显示(item,nil,nil,3,4);return area
end
local initial={}
for _,name in ipairs(charged)do
 local item=hero.技能信息[name];eq(item.开始CD效果,false,'no body CD needed')
 initial[name]=drawcharge(name);assert(initial[name]>0)
end
-- The old 227 helper hides in exactly this state; the new one follows actual CD BUFFs.
charge:step(200)
for _,name in ipairs(charged)do assert(drawcharge(name)>0 and drawcharge(name)<initial[name],'still charging after 1.5 seconds')end
local function remaining(name)
 for _,buff in ipairs(hero.BUFF组)do
  if not buff.已经消失()and buff.取标识()==name..'CD'then
   local id,desc,total,left=buff.取信息();eq(total,10);return left
  end
 end
end
-- Repeated rendering does not advance or reset the actual status clock.
local fixed=remaining(charged[1]);local fixed_area=drawcharge(charged[1]);local sprites_before=count
for i=1,200 do eq(drawcharge(charged[1]),fixed_area)end
near(remaining(charged[1]),fixed);eq(count,sprites_before,'reuse cached sprite')
-- Spending a reserve changes neither elapsed time nor the display's source.
local before=remaining(charged[1]);local visible=drawcharge(charged[1])
selected(charge,'普通攻击',charged[1])
near(remaining(charged[1]),before,'spend does not reset status clock')
eq(drawcharge(charged[1]),visible,'body frame reset does not reset charge mask')
-- Other reserves stay stored; all three native CD statuses expire at their own deadline.
-- Prevent automatic refill of the spent one while native BUFFs still tick.
hero.属性.mp=0
charge:step(900)
for _,name in ipairs(charged)do eq(remaining(name),nil);eq(drawcharge(name),0,'hide expired CD despite body flags')end
-- A fresh native status is immediately observed; no slot-local countdown or stale cache.
assert(hero.增加状态(hero,charged[2]..'CD'))
eq(drawcharge(charged[2]),48*48,'new CD starts full')
hero.清除状态(hero,charged[2]..'CD')
eq(drawcharge(charged[2]),0,'removed native status hides immediately')
for _,item in pairs(slots)do item.销毁(item)end
print('COOLDOWN_V228_PASS '..mode..' three actual auto-charge statuses -> duration/remaining getter -> masks, >1.5s, spend/no reset, expiration, renewal/removal; native summon path retained')
