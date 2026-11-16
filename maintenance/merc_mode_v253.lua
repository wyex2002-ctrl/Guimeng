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
  if ranged(actor)and skills[skill]then return 8 end
  return old
 end
 local function valid(target)
  return type(target)=='table'and target.是否有效~=false and not target.已经消失 and not target.不可选中 and type(target.属性)=='table'and type(target.属性.hp)=='number'and target.属性.hp>0
 end
 local function combat(actor)
  if not ismerc(actor)or not valid(actor)then return false end
  local target=actor.攻击来源
  if valid(target)and target~=actor and target.id~=0 then return true end
  if actor.当前状态==3 then
   target=actor.本次目标
   if valid(target)and target~=actor and target.id~=0 then return true end
  end
  return false
 end
 local function rawmerc()
  local id=mercid();if not id then return nil end
  for _,a in pairs(S.屏幕事件组 or{})do if type(a)=='table'and a.id==id then return a end end
 end
 local function message()
  local u=E.Ux雌;local out=u and u.开挖机的
  if out and type(out.孔爱琴泥)=='function'then out.孔爱琴泥('佣兵战斗中，无法更换武器',1)end
  local h=u and u.托管显示
  if h and type(h.屏幕提示)=='function'then h.屏幕提示('佣兵战斗中，无法更换武器',-1,true)end
 end
 local function block(slot,operation)
  if type(slot)~='table'then return false end
  local hit=slot.标识==397
  if operation=='use'and slot.标识 and slot.标识>=333 and slot.标识<=396 then
   local b=slot.格子组 and slot.格子组[slot.标识]
   hit=b and binding(b.道具)~=nil or false
  end
  if operation=='place'or operation=='swap'then
   local q=Q_鼠标
   hit=hit or(type(q)=='table'and q.格子标识==397)
  end
  if hit and combat(rawmerc())then message();return true end
  return false
 end
 local function request(args)
  if type(args)=='table'and type(args[1])=='number'and args[1]>=1 and args[1]<=6 and(args[2]==397 or args[4]==397)and combat(rawmerc())then message();return true end
  return false
 end
 local function name(item,text,slot)
  if type(text)~='string'or binding(item)~=basic then return text end
  local explicit=type(item.附加)=='table'and item.附加.绑定技能~=nil
  -- Default weapons are ranged only in companion UI context. Shared shop and
  -- ground labels stay neutral; item identities and saved names are untouched.
  if not explicit and not(type(slot)=='number'and slot>=333 and slot<=410)then return text end
  if text:sub(-#'（远程）')=='（远程）'then return text end
  return text..'（远程）'
 end
 local function chant(target)
  local a=rawmerc();if not ranged(a)then return 0 end
  local t=E.Gly独.事件对象(target)
  if type(t)~='table'or type(t.HP)~='number'or t.HP<=0 then return 2 end
  local p,q=a.地图格子,t.地图格子
  if not p or not q or math.max(math.abs(p.x-q.x),math.abs(p.y-q.y))>8 then return 2 end
  return 1
 end
 __gm_merc_request_v253=request;__gm_merc_range_v253=range;__gm_merc_ranged_v253=ranged;__gm_merc_block_v253=block;__gm_merc_name_v253=name
 E.__gm_merc_binding_v253=binding;E.__gm_merc_chant_v253=chant
end
