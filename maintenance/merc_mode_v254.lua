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
 local function rawmerc()
  local id=mercid();if not id then return nil end
  for _,a in pairs(S.屏幕事件组 or{})do if type(a)=='table'and a.id==id then return a end end
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
 __gm_merc_range_v253=range;__gm_merc_ranged_v253=ranged;__gm_merc_name_v253=name
 E.__gm_merc_name_v253=name;E.__gm_merc_binding_v253=binding;E.__gm_merc_chant_v253=chant
end
