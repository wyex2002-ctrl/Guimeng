do
 -- A whole-callback regression; the old short span supplied numeric constants
 -- directly and never executed the preceding equipment/element scratch reuse.
 local saved={role=U.啾啾啵啵,settings=U.胚子考虑,window=U.窗口相关,skill=E.Gly独.取出技能信息,random=E.Gly独.取随机数,split=E.分割文本}
 local old_props_count=#props
 local elements={'攻神元素','攻火元素','攻冰元素','攻雷元素','攻风元素','攻幻元素','攻暗黑元素'}
 local fields={'准确几率','真伤几率','百分伤害','普攻绿毒','击中回血','击中回蓝','暴击几率','暴击系数','攻神元素','攻火元素','攻冰元素','攻雷元素','攻风元素','攻幻元素','攻暗黑元素'}
 for _,key in ipairs(fields)do
  local present=false;for _,k in ipairs(props)do if k==key then present=true end end
  if not present then props[#props+1]=key end
  merc.属性.属性集[key]=0;merc.属性['附加_'..key]=0
 end
 merc.属性.属性集.准确几率=100
 local role={佣兵={技能={}},技能={}};local config={行会选中={},元素位置=elements}
 U.啾啾啵啵=function()return role end;U.胚子考虑=function()return config end
 U.窗口相关={佣兵修炼=noop,佣兵窗口=noop}
 local target={id=70,HP=10000,等级=1,属性=zero(),附加={等级=1},增加状态=noop}
 target.属性.附加=target.附加;actors[70]=target
 local old_controls={};for _,id in ipairs({15,18,408})do local key='物品格子'..id;old_controls[key]=E[key];E[key]={道具=nil}end
 E.物品格子18.道具=nil
 E.分割文本=split
 local invalid=0;local strict=false;local engine_calls={}
 N.引擎.取随机整数=function(_,lo,hi)
  engine_calls[#engine_calls+1]={lo,hi}
  if type(lo)~='number'or type(hi)~='number'then invalid=invalid+1;assert(not strict,'non-numeric native random bounds')end
  -- Observed legacy engine accepts these calls before math.max fails. The
  -- old-only permissive bridge is explicit; new calls must all be numeric.
  return math.floor(((tonumber(lo)or 0)+(tonumber(hi)or 0))/2)
 end
 E.Gly独.取随机数=load('native_random',N)
 local actual_pair=E.__gm_luck_pair_v244;local seen
 E.__gm_luck_pair_v244=function(lo,hi,sl,sh,...)
  seen={lo,hi,sl,sh};return actual_pair(lo,hi,sl,sh,...)
 end
 E.Gly独.取出技能信息=function(name)return {名称=name,显示名=name,施放位置='自身'}end
 local old,new=load('native_merc_old',E),load('native_merc',E)
 local function stats(luck,element)
  merc.属性.属性集.最小破坏=10;merc.属性.属性集.最大破坏=20
  merc.属性.属性集.最小自然=2;merc.属性.属性集.最大自然=4
  merc.属性.属性集.最小灵魂=3;merc.属性.属性集.最大灵魂=6
  merc.属性.属性集.幸运=luck
  for _,key in ipairs(elements)do merc.属性.属性集[key]=key==element and 5 or 0 end
 end
 -- Full old callback must reproduce the exact uploaded math.max/string error.
 stats(7,'攻火元素');float=0;strict=false
 local ok,err=pcall(old,70,'普通攻击',1)
 eq(ok,false);eq(tostring(err):find("bad argument #1 to 'max' (number expected, got string)",1,true)~=nil,true,'uploaded exception')
 eq(seen[3],'防火元素','native element key leaked into skill damage bound')
 local oldinvalid=invalid;strict=true
 local result=new(70,'普通攻击',1);eq(type(result),'table');eq(seen[3],0);eq(seen[4],0);eq(invalid,oldinvalid,'new callback never relies on engine coercion')
 -- No elemental source also formerly retained equipment table or nil in R11.
 for _,gear in ipairs({false,true})do
  E.物品格子408.道具=gear and{附加={}}or nil
  stats(7,nil);float=0;strict=false;local ok=pcall(old,70,'普通攻击',1);eq(ok,false)
  strict=true;local before=invalid;new(70,'普通攻击',1);eq(seen[3],0);eq(seen[4],0);eq(invalid,before)
 end
 E.物品格子408.道具=nil
 -- Original optional configured min/max still override the new 0 defaults.
 local cfg={伤害方式='破坏',最小伤害=2,最大伤害=4}
 role.佣兵.技能.测试伤害={0};local rules={测试伤害={cfg}};local rule_getter=U.大堵塞就
 U.大堵塞就=function()return rules end
 stats(7,'攻雷元素');new(70,'测试伤害',1);eq(seen[3],2);eq(seen[4],4)
 cfg.最小伤害=nil;new(70,'测试伤害',1);eq(seen[3],0);eq(seen[4],4)
 cfg.最小伤害=2;cfg.最大伤害=nil;new(70,'测试伤害',1);eq(seen[3],2);eq(seen[4],0)
 U.大堵塞就=rule_getter;role.佣兵.技能={}
 -- Every element / zero-to-seven luck / both chance outcomes, plus hot mix.
 for _,element in ipairs(elements)do for luck=0,7 do for _,roll in ipairs({0,.999})do
  stats(luck,element);float=roll;local before=float_calls;local before_invalid=invalid
  local out=new(70,'普通攻击',1);eq(type(out),'table');eq(seen[3],0);eq(seen[4],0)
  eq(float_calls,before+1,'one merged merc attack luck roll');eq(invalid,before_invalid)
 end end end
 for i=1,200 do stats(i%8,elements[i%7+1]);float=i%2==0 and 0 or .999;eq(type(new(70,'普通攻击',1)),'table')end
 while #props>old_props_count do table.remove(props)end
 E.__gm_luck_pair_v244=actual_pair;E.Gly独.取随机数=saved.random;E.Gly独.取出技能信息=saved.skill;E.分割文本=saved.split
 U.啾啾啵啵=saved.role;U.胚子考虑=saved.settings;U.窗口相关=saved.window
 for key,value in pairs(old_controls)do E[key]=value end
 for _,id in ipairs({15,18,408})do local key='物品格子'..id;if old_controls[key]==nil then E[key]=nil end end
 print('MERC_FULL_V248_PASS',mode,'old string/nil/table failures reproduced; new strict numeric calls passed')
end
