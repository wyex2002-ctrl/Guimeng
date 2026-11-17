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
 local function prepare(state)
  local actor,target,cfg=state.施法者,state.目标,state.对象
  if not ranged(actor)or not skills[cfg.名称]or not alive(target)or target==actor then return end
  local item=weapon();local template=S.游戏道具组 and S.游戏道具组[item.名称]
  local image=item.地面图标 or(type(template)=='table'and template.地面图标)
  image=image or item.图标 or(type(template)=='table'and template.图标)
  if not image then return end -- Missing optional artwork never changes combat.
  local impact=state.命中动画延迟
  local first=state.伤害进度 and state.伤害进度[1]or state.伤害发生延迟
  if type(first)=='number'and first>=0 and(type(impact)~='number'or impact<=0 or first<impact)then impact=first end
  if type(impact)~='number'or impact~=impact or impact<=0 then return end
  local launch=math.max(0,math.min(state.起手动画延迟 or 0,impact*.5))
  state.__gm_merc_visual_v255={image=image,target=target,launch=launch,impact=impact}
 end
 local function step(state)
  local shot=state.__gm_merc_visual_v255
  if not shot or shot.sent or state.延迟dt<shot.launch then return end
  shot.sent=true
  local actor,target=state.施法者,shot.target
  if state.完成 or not alive(actor)or not alive(target)then return end
  -- A cast keeps its captured artwork/mode even if the player swaps weapons.
  -- The native projectile is never placed in state.子弹, so the native skill
  -- cannot enter a projectile-controlled damage branch or wait for arrival.
  local x=actor.地图坐标.x+(actor.锚点x or 0)
  local y=actor.地图坐标.y+(actor.锚点y or 0)-(actor.属性.中心Y偏移 or 0)*(actor.属性.模型大小 or 1)
  local tx=target.地图坐标.x+(target.锚点x or 0)
  local ty=target.地图坐标.y+(target.锚点y or 0)-(target.属性.中心Y偏移 or 0)*(target.属性.模型大小 or 1)
  -- Keep a fast/low-FPS throw visible for two visual updates. This does
  -- not gate, delay or reschedule the native skill's damage or next attack.
  local frame=type(dt)=='number'and dt>0 and dt or 1/60
  local remaining=math.max(frame*2,shot.impact-state.延迟dt)
  local speed=math.sqrt((tx-x)^2+(ty-y)^2)/remaining
  local elapsed=0
  local function visual_tick(_,__,info)
   if(state.完成 and not state.伤害产生_已结束)or not alive(target)or not alive(actor)then info.命中=true;return end
   local delta=dt
   if type(delta)~='number'or delta~=delta or delta<=0 then return end
   local left=math.max(delta,remaining-elapsed)
   local gx=target.地图坐标.x+(target.锚点x or 0)
   local gy=target.地图坐标.y+(target.锚点y or 0)-(target.属性.中心Y偏移 or 0)*(target.属性.模型大小 or 1)
   info.原始目标x=gx;info.原始目标y=gy
   info.移动速度=math.sqrt((gx-info.坐标x)^2+(gy-info.坐标y)^2)/left
   elapsed=elapsed+delta;info.__gm_spin_v255=elapsed*math.pi*6
   if elapsed>remaining+delta then info.命中=true end
  end
  local opts={技能名称=state.对象.名称,渐入=0,渐出=0,穿透模式=0,发射起点=0,子弹射程=800}
  local bullet=__gm_merc_visual_factory_v255(x,y,tx,ty,speed,actor,target,'图片',shot.image,false,visual_tick,{},nil,'敌方',0,opts)
  Sys.add('屏幕子弹',bullet)
 end
 __gm_merc_range_v253=range;__gm_merc_ranged_v253=ranged;__gm_merc_name_v253=name
 __gm_merc_visual_prepare_v255=prepare;__gm_merc_visual_step_v255=step
 E.__gm_merc_name_v253=name;E.__gm_merc_binding_v253=binding;E.__gm_merc_chant_v253=chant
end
