return function(S,E)
 local basic='刺客普通攻击'
 local skills={['刺客普通攻击']=true,['蝉舞']=true,['月桂']=true,['红莲']=true,['白莲']=true,['盛开']=true}
 local function binding(item)
  if type(item)~='table'or item.分类~='装备'or item.子类~='武器'then return nil end
  local a=item.附加;local b=type(a)=='table'and a.绑定技能 or nil
  if b==nil then return basic end
  return b
 end
 local function mercid()
  local m=E.Ux雌 and E.Ux雌.佣兵对象
  return type(m)=='table'and m.id or nil
 end
 local function ismerc(actor)
  local id=mercid()
  return type(actor)=='table'and type(id)=='number'and id>0 and actor.id==id
 end
 local function weapon()
  local b=S.包裹物品组 and S.包裹物品组[397]
  return type(b)=='table'and b.拿起~=true and b.道具 or nil
 end
 local function ranged(actor)
  return ismerc(actor)and binding(weapon())==basic and actor.绑定技能==basic
 end
 local function range(actor,old,skill)
  skill=skill or actor.临时绑定技能
  if skill==nil or skill=='无'then skill=actor.绑定技能 end
  if ranged(actor)and skills[skill]then return 6 end
  return old
 end
 local function rawmerc()
  local id=mercid();if not id then return nil end
  for _,a in pairs(S.屏幕事件组 or{})do if type(a)=='table'and a.id==id then return a end end
 end
 local function name(item,text,slot)
  if type(text)~='string'or binding(item)~=basic then return text end
  local explicit=type(item.附加)=='table'and item.附加.绑定技能~=nil
  if not explicit and not(type(slot)=='number'and slot>=333 and slot<=410)then return text end
  if text:sub(-#'（远程）')=='（远程）'then return text end
  return text..'（远程）'
 end
 local function chant(target)
  local a=rawmerc();if not ranged(a)then return 0 end
  local t=E.Gly独.事件对象(target)
  if type(t)~='table'or type(t.HP)~='number'or t.HP<=0 then return 2 end
  local p,q=a.地图格子,t.地图格子
  if not p or not q or math.max(math.abs(p.x-q.x),math.abs(p.y-q.y))>6 then return 2 end
  return 1
 end
 local function alive(a)
  return type(a)=='table'and not a.已经消失 and a.是否有效~=false and type(a.属性)=='table'and type(a.属性.hp)=='number'and a.属性.hp>0
 end
 -- Resolve both raw engine actors and original public event proxies.
 local function hitfactor(source,target)
  local mid=mercid()
  for side=1,2 do
   local a=side==1 and source or target
   local id=type(a)=='table'and a.id or a
   if type(id)~='number'or id<0 or id%1~=0 then return 1 end
   if type(a)~='table'and id~=0 and id~=mid then a=E.Gly独.事件对象(id)end
   local faction=type(a)=='table'and(a.所属阵营 or a.阵营)
   local party=false
   for depth=1,8 do
    if id==0 or(mid and mid>0 and id==mid)then party=true;break end
    if type(a)~='table'then break end
    local owner=a.主人id
    if owner==nil then local pet=a.宠物配置;owner=type(pet)=='table'and pet.主人 end
    id=type(owner)=='table'and owner.id or owner
    if type(id)~='number'or id<0 or id%1~=0 then break end
    a=type(owner)=='table'and owner or nil
    if id~=0 and id~=mid and not a then a=E.Gly独.事件对象(id)end
   end
   if side==1 and not party then return 1 end
   if side==2 and(party or faction~='敌方')then return 1 end
  end
  return 2.5
 end
 local function prepare(state,public)
  local actor,target,cfg=state.施法者,state.目标,state.对象
  if not ranged(actor)or cfg.名称~=basic or not alive(target)or target==actor then return end
  local item=weapon();local template=S.游戏道具组 and S.游戏道具组[item.名称]
  local image=item.地面图标 or(type(template)=='table'and template.地面图标)
  image=image or item.图标 or(type(template)=='table'and template.图标)
  if not image then return end
  local key=E.Ux雌 and E.Ux雌.版本选择=='前尘忆梦'and'Q火球术'or'火球术'
  local fireball=Sys.get('skill',key)
  local speed=type(fireball)=='table'and fireball.子弹速度
  if type(speed)~='number'or speed~=speed or speed<=0 or speed==math.huge then return end
  local original=state.伤害进度;local offsets={};local first=original and original[1]
  if type(first)~='number'then return end
  local retire=math.max(first,state.命中动画延迟 or 0)
  for i,v in ipairs(original)do offsets[i]=v-first;retire=math.max(retire,v);original[i]=math.huge end
  local shot={image=image,target=target,launch=math.max(0,state.起手动画延迟 or 0),speed=speed*1.2,
   retire=retire,offsets=offsets,raw=public.刷新,elapsed=0}
  state.命中动画延迟=math.huge
  state.__gm_merc_visual_v255=shot
  -- Native actor cleanup/combo scheduling retains its pre-flight deadline.
  -- Retired casts continue their original refresh on the projectile driver,
  -- so several already-paid attacks can be in flight without blocking casts.
  public.刷新=function()
   shot.elapsed=shot.elapsed+dt
   local done=shot.raw()
   if shot.cancelled or(done and not state.伤害产生_已结束)then shot.cancelled=true;return true end
   if shot.elapsed>=shot.retire and state.起手动画_已播放 then
    if not done then shot.retired=true;shot.skip=true end
    return true
   end
   return false
  end
 end
 local function step(state)
  local shot=state.__gm_merc_visual_v255
  if not shot then return end
  local actor,target=state.施法者,shot.target
  if shot.cancelled or not alive(target)or not alive(actor)then
   shot.cancelled=true;state.完成=true;return
  end
  if shot.arrived then
   if not shot.released then
    shot.released=true
    state.命中动画延迟=state.延迟dt
    for i,offset in ipairs(shot.offsets)do state.伤害进度[i]=state.延迟dt+offset-1e-9 end
   end
   return
  end
  if shot.sent or state.延迟dt<shot.launch then return end
  shot.sent=true
  local x=actor.地图坐标.x+(actor.锚点x or 0)
  local y=actor.地图坐标.y+(actor.锚点y or 0)-(actor.属性.中心Y偏移 or 0)*(actor.属性.模型大小 or 1)
  local tx=target.地图坐标.x+(target.锚点x or 0)
  local ty=target.地图坐标.y+(target.锚点y or 0)-(target.属性.中心Y偏移 or 0)*(target.属性.模型大小 or 1)
  local elapsed=0
  local function visual_tick(_,__,info)
   if shot.cancelled or(state.完成 and not state.伤害产生_已结束)or not alive(target)or not alive(actor)then info.命中=true;shot.cancelled=true;state.完成=true;return end
   local delta=dt
   if type(delta)~='number'or delta~=delta or delta<=0 then return end
   elapsed=elapsed+delta;info.__gm_spin_v255=elapsed*math.pi*24
   -- Keep the original fireball-family acceleration and target tracking.
   -- Never increase speed just to catch a pre-existing damage deadline.
   if elapsed>10 then info.命中=true;shot.cancelled=true;state.完成=true end
  end
  local opts={技能名称=state.对象.名称,渐入=0,渐出=0,穿透模式=0,发射起点=0,子弹射程=800}
  local bullet=__gm_merc_visual_factory_v255(x,y,tx,ty,shot.speed,actor,target,'图片',shot.image,false,visual_tick,{},nil,'敌方',0,opts)
  local update,ended,destroy=bullet.更新,bullet.已经消失,bullet.销毁
  bullet.更新=function()
   update()
   if ended()and not shot.cancelled then shot.arrived=true end
   if shot.retired and not state.完成 then
    if shot.skip then shot.skip=false else shot.raw()end
   end
  end
  bullet.已经消失=function()return ended()and(state.完成 or shot.cancelled)end
  bullet.销毁=function()shot.cancelled=true;state.完成=true;destroy()end
  Sys.add('屏幕子弹',bullet)
 end
 __gm_hit_factor_v260=hitfactor;E.__gm_hit_factor_v260=hitfactor
 __gm_merc_range_v253=range;__gm_merc_ranged_v253=ranged;__gm_merc_name_v253=name
 __gm_merc_visual_prepare_v255=prepare;__gm_merc_visual_step_v255=step
 E.__gm_merc_name_v253=name;E.__gm_merc_binding_v253=binding;E.__gm_merc_chant_v253=chant
end
