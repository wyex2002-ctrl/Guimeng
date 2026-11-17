-- Physical input is finite; the callback, nearest-target scan, release and sprite wrapper are real.
do
 local r=scene('new');local hero,env=r.hero,r.env
 env.select=select;env.setmetatable=setmetatable;env.rawget=rawget;env.rawset=rawset
 local held,edges={},{}
 env.引擎.取按键事件=function(_,key)return held[key]or false end
 env.引擎.取按键按下=function(_,key)return edges[key]or false end
 env.引擎.取运行时间=function()return 0 end -- Hold duration must depend on frame seconds, not clock units.
 env.L常量.键_ALT=18;env.L常量.键_鼠标左=1;env.L常量.键_鼠标右=2
 env.Ae冻集.镜头ID=hero.id;env.Ae冻集.遮罩信息.触发=true;env.Ae冻集.快捷事件组={}
 env.Q_鼠标={被占用=false};env.Ae冻.地图id=1
 local windows,objects={},{}
 local get=load('getter',env);debug.setupvalue(get,1,{Hero=hero,游戏技能组=r.skills,界面_窗口_数组=windows,屏幕事件组=objects})
 local native_cast_selector,native_stiff_tick
 local dispatches=0
 local original_add=env.Sys.add
 local raw={get=get,Hero=hero,游戏技能组=r.skills,界面_窗口_数组=windows,屏幕事件组=objects,add=function(k,v)if k=='屏幕子弹'then return end;return original_add(k,v)end}
 env.子弹类=function()return{已经消失=function()return true end}end -- Explicit projectile-flight boundary; scheduling and release stay native.
 env.Ux雌.版本选择='前尘忆梦'
 local controls={}
 env.Gly独.取控件对象=function(name)return controls[name]end
 local selector=load('selector',env)
 raw.run=function(op,args,...)
  if op=='qs_skill_drop' then
   r.events[#r.events+1]={op=args[1],t=r.now(),name=args[4]}
   if args[1]==0 and native_cast_selector then native_cast_selector(unpack(args))end
   if args[1]==4 then dispatches=dispatches+1;return selector(unpack(args))end
   if args[1]==5 then return true,selector(unpack(args))end
   return true,nil
  end
  if op=='fun'then if type(args)=='function'then return true,args(unpack((...)))end;return true,nil end
  if op=='屏幕提示'then return true,nil end
  error('unexpected run '..tostring(op))
 end
 debug.setupvalue(get,1,raw)
 local diagnostic=nil
 env.Sys=load('readonly',env)(raw)
 for _,v in pairs(r.skills)do v.精灵={置图片=noop,置混合模式=noop,置颜色=noop,显示_范围缩放=noop}end
 local green,black,created,destroyed=0,0,0,0
 local borders={}
 env.__Sprite={创建=function(id,x,y,w,h)eq(id,0);created=created+1;return{}end,
  置渲染色=function(p,c)p.color=c;assert(c==-16711936 or c==-2013265920)end,
  置混合模式=noop,
  显示_高级=function(p,x,y,rot,w,h)
   if p.color==-16711936 then green=green+1;borders[#borders+1]={x,y,w,h};assert(x>=10 and y>=20 and x+w<=58.000001 and y+h<=68.000001)
   else black=black+1 end
  end,
  销毁=function()destroyed=destroyed+1 end}
 env.Q__={创建包围盒=function()return{}end}
 env.Q__.创建精灵=load('sprite_factory',env)
 local cd={};for _,k in ipairs({'置参照点','播放','置渲染色','置当前帧','显示_高级','销毁','置混合模式'})do cd[k]=noop end;cd.创建=function()return 1 end
 env.__Animation=cd;env.__ed_debug=error;env.Q__.创建动画=load('cd_factory',env)
 env.D2D_包围盒={创建=function()return{置位置=noop}end};env.Q_公用图片库={CD图片=1};env.Q_公用动画库={}
 env.L常量.混合_默认=0;env.L常量.颜色_白=-1
 load('slot_class',env)()
 local function slot(name,key,id)
  hero.技能配置(hero,name)
  local obj=env.类_格子_技能格子();obj.初始化(obj,10,20,48,48,name,key,false,id)
  controls[id]={禁止拖放=false,对象=obj,技能=name}
  return obj
 end
 local fire=slot('月魂灵波',112,'repeat_fire')
 local summon=slot('召唤神兽',113,'repeat_summon')
 local melee=slot('普通攻击',114,'repeat_melee')
 local lightning=slot('雷电术',117,'repeat_lightning')
 local head=load('repeat_head',env)
 local function pump(n)
  for i=1,n or 1 do head(hero);if native_stiff_tick then native_stiff_tick(hero)end;r:step();edges={}end
 end
 local function key(key,down)edges[key]=down and not held[key];held[key]=down end
 local function active()return hero.__gm_repeat_skill_v229 and hero.__gm_repeat_skill_v229.active end
 local function clear()
  held={};edges={};load('repeat_reset',env)(hero);env.dt=.01
  env.Ae冻集.UI焦点=false;env.Ae冻集.游戏暂停=false;env.Ae冻集.屏幕焦点=true;env.Ae冻集.最后按键=nil
  env.Q_鼠标.被占用=false;windows={};raw.界面_窗口_数组=windows
  hero.抵达目标点=true;head(hero)
 end
 local function arm()
  clear();key(112,true);head(hero);env.dt=.999;head(hero);assert(not active(),'under one second')
  env.dt=.001;head(hero);assert(active(),'one-second exact boundary');key(112,false);env.dt=.01;head(hero)
 end
 -- Old helper remains inactive at one second, new helper arms at that point.
 clear();local old=load('control_old',env);key(112,true);old(hero);env.dt=1;old(hero);assert(not active(),'264 negative control at one second')
 for _,fps in ipairs({15,30,60,100})do
  clear();env.dt=1/fps;key(112,true);head(hero)
  for i=1,fps-1 do head(hero)end
  assert(not active(),'less than one second at '..fps..' FPS');head(hero);assert(active(),'one second at '..fps..' FPS')
 end
 -- A release before threshold must reset the hold, not combine two presses.
 clear();key(112,true);head(hero);env.dt=.999;head(hero);key(112,false);env.dt=.01;head(hero)
 key(112,true);head(hero);env.dt=.5;head(hero);assert(not active(),'short holds do not accumulate')
 -- Representative native hot path cycles and callback dispatch after release.
 for i=1,200 do
  arm();local before=dispatches;env.dt=.1;head(hero);eq(dispatches,before+1,'same registered slot callback after releasing key')
  key(112,true);env.dt=.01;head(hero);assert(not active(),'fresh skill press exits')
 end
 arm();env.Ae冻集.UI焦点=true;key(1,true);head(hero);assert(not active(),'UI click exits')
 arm();env.Q_鼠标.被占用=true;head(hero);assert(not active(),'item dragging exits')
 arm();env.Ae冻集.游戏暂停=true;head(hero);assert(not active(),'pause exits')
 arm();hero:__gm_repeat_control_v229('cancel');assert(not active(),'map cleanup cancellation')
 arm();windows[1]={名称='背包窗口',可视=true};head(hero);assert(not active(),'inventory interaction exits')
 -- Ground movement and a background focus transition preserve prior behavior.
 arm();hero.抵达目标点=false;key(1,true);head(hero);assert(active(),'ground move retains mode')
 key(1,false);hero.抵达目标点=true;env.Ae冻集.屏幕焦点=false;head(hero);assert(active(),'focus loss retains mode')
 env.Ae冻集.屏幕焦点=true;head(hero);assert(active(),'focus return retains mode')
 -- Summon and melee slots remain ineligible for automatic ranged mode.
 for _,code in ipairs({113,114})do clear();key(code,true);head(hero);env.dt=1.2;head(hero);assert(not active(),'non-ranged slot is ineligible')end
 print('REPEAT_HOLD_V265_PASS '..mode..' checks='..checks..'; native classes/update/slot callback, one-second boundary, finite input/graphics and dispatch')
end
