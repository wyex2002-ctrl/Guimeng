-- Physical input is finite; the callback, nearest-target scan, release and sprite wrapper are real.
do
 local r=scene('new');local hero,env=r.hero,r.env
 env.select=select;env.setmetatable=setmetatable;env.rawget=rawget;env.rawset=rawset
 local held,edges={},{}
 env.引擎.取按键事件=function(_,key)return held[key]or false end
 env.引擎.取按键按下=function(_,key)return edges[key]or false end
 env.引擎.取运行时间=function()return 0 end -- Hold duration must depend on frame seconds, not clock units.
 env.L常量.键_鼠标左=1;env.L常量.键_鼠标右=2
 env.Ae冻集.镜头ID=hero.id;env.Ae冻集.遮罩信息.触发=true;env.Ae冻集.快捷事件组={}
 env.Q_鼠标={被占用=false};env.Ae冻.地图id=1
 local windows,objects={},{}
 local get=load('getter',env);debug.setupvalue(get,1,{Hero=hero,游戏技能组=r.skills,界面_窗口_数组=windows,屏幕事件组=objects})
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
   if args[1]==4 then dispatches=dispatches+1;return selector(unpack(args))end
   if args[1]==5 then return true,selector(unpack(args))end
   return true,nil
  end
  if op=='fun'then if type(args)=='function'then return true,args(unpack((...)))end;return true,nil end
  if op=='屏幕提示'then return true,nil end
  error('unexpected run '..tostring(op))
 end
 debug.setupvalue(get,1,raw)
 local diagnostic=assert(loadfile(work..'/repeat_diagnostics.lua'))()(raw)
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
 local head=load('repeat_head',env)
 local function pump(n)
  for i=1,n or 1 do head(hero);r:step();edges={}end
 end
 local function key(key,down)edges[key]=down and not held[key];held[key]=down end
 local function active()return hero.__gm_repeat_skill_v229 and hero.__gm_repeat_skill_v229.active end
 local function arm()
  key(112,false);pump(2);key(112,true);pump(1);pump(199);assert(not active(),'less than two seconds')
  pump(2);assert(active(),'two-second long hold')
  key(112,false);pump(1)
 end
 local victim=r.target;victim.所属阵营='敌方';victim.不可选中=false;victim.是否有效=true
 victim.可视=true;victim.屏幕可视=true;victim.资源动画={};victim.属性.可视=true;victim.属性.透明度=255;victim.属性.中心Y偏移=0;victim.属性.模型大小=1;env.Ae冻集.屏幕宽度=800;env.Ae冻集.屏幕高度=600
 objects[1]=victim
 hero.攻击目标=nil;hero.远程目标=nil

 local focus=load('input_focus',env);debug.setupvalue(focus,1,{按住激活=false})
 local function hover(on)
  env.Ae冻集.鼠标焦点窗口对象=on and {鼠标穿透=false}or nil
  env.Ae冻集.鼠标_屏幕坐标={x=100,y=on and 320 or 100}
  env.Ae冻集.遮罩信息={启动=true,x=0,y=0,w=800,h=300,触发=true}
  focus();env.Q_提示框.可视=on
 end
 hover(true);eq(env.Ae冻集.UI焦点,true);eq(env.Ae冻集.遮罩信息.触发,false)
 -- Reproduce229 failure with the same real native hover flags and visible tooltip.
 key(112,true);local legacy=load('repeat_legacy',env)
 env.引擎.取运行时间=function()return r.now()*1000 end
 for i=1,220 do legacy(hero);r:step()end
 assert(not active(),'229 cannot arm under native hotbar hover')
 key(112,false);load('repeat_reset',env)(hero)
 env.引擎.取运行时间=function()return 0 end
 pump(1)
 -- Real48 class, constructor/proxies and12/142 parent/open code. Only engine graphics,
 -- class allocation and scrollbar primitives are finite; no replacement parent/open logic.
 local oldclass=env.class
 env.class=function()
  local c={};c.创建=function(...)local o=setmetatable({},{__index=c});c.初始化(o,...);return o end
  return c
 end
 load('window_class',env)();env.class=oldclass
 local oldsprite=env.D2D_精灵;local oldcore=env.核心
 env.D2D_精灵={创建=function()return{置颜色=noop,置混合模式=noop}end}
 env.核心={读配置项_内存=read};env.引擎.取图片宽度=function()return 282 end;env.引擎.取图片高度=function()return 484 end
 env.Q__.创建纵向滚动条=function()return{}end
 env.L常量.颜色_全透明=0
 local parent=env.类_窗口_基础.创建(539,'背包窗口',657,22,282,484,1,0,0,0,1,'[配置]\n鼠标穿透=0\n九宫模式=0')
 local child=env.类_窗口_基础.创建(540,'背包格子',0,0,243,625,1,0,0,0,1,'[配置]\n鼠标穿透=0\n九宫模式=0')
 parent.脚本={Main=noop};child.脚本={Main=noop}
 local frame={tbl={},w=243,h=400,脚本={},可视=true};parent.控件组[1]=frame
 windows[1]=parent;windows[2]=child
 env.背包窗口=parent.tbl;env.背包格子=child.tbl;env.背包子夹=frame.tbl
 load('parent_setup',env)()
 eq(parent.可视,false);eq(child.可视,true);eq(child.父窗口,parent);eq(child.父外形框,frame)
 env.D2D_精灵=oldsprite;env.核心=oldcore
 local old230=load('repeat230',env)
 key(112,false);load('repeat_reset',env)(hero);old230(hero)
 key(112,true);for i=1,220 do old230(hero)end
 assert(not active(),'230 blocked by actual opened child with hidden parent')
 key(112,false);load('repeat_reset',env)(hero);pump(2);arm()
 assert(active(),'231 ignores actual hidden-parent child')
 env.背包窗口.打开();eq(parent.可视,true);head(hero);assert(not active(),'real parent opening cancels')
 env.背包窗口.关闭();eq(parent.可视,false);eq(child.可视,true)
 key(112,false);pump(2);arm()
 -- Native page frame visibility: a raw-visible child named as an unsafe window on
 -- an inactive page must be ignored, but visible page must block immediately.
 windows[1]=child;parent.可视=true;frame.可视=false;head(hero);assert(active(),'hidden page ignored')
 frame.可视=true;head(hero);assert(not active(),'visible page blocks')
 parent.可视=false;windows[1]=parent;key(112,false);pump(2);arm()


 local before=dispatches;pump(200);assert(dispatches>before,'original callback repeated after release')
 assert(#times(r,0)>0,'actual hero release reached')
 local first=green;fire.显示(fire,nil,nil,0,0);assert(green>first,'green active border')
 local bx,by=borders[1][1],borders[1][2];pump(20);borders={};fire.显示(fire,nil,nil,0,0);assert(#borders>0 and (borders[1][1]~=bx or borders[1][2]~=by),'moving border phase')
 local allocations=created;for i=1,200 do fire.显示(fire,nil,nil,0,0)end;eq(created,allocations,'cached border and mask')
 -- Ground movement retains mode but issues no automatic casts while the mouse is held
 -- or the native arrival flag is false. Last-key mouse codes must also be ignored.
 hover(false);key(1,true);env.Ae冻集.最后按键=1
 local state=hero.__gm_repeat_skill_v229
 state.pending='月魂灵波';hero.下次技能='月魂灵波';hero.__gm_queued_skill_v155='月魂灵波';hero.__gm_queued_target_v155=victim
 before=dispatches;for i=1,20 do head(hero)end;assert(active());eq(dispatches,before,'ground click pauses without cancelling')
 eq(hero.下次技能,nil,'move clears only owned queued cast');eq(hero.__gm_queued_target_v155,nil)
 state.pending='月魂灵波';hero.下次技能='治愈术';head(hero);eq(hero.下次技能,'治愈术','preserve different manual queue');hero.下次技能=nil
 key(1,false);hero.抵达目标点=false
 for i=1,20 do head(hero)end;assert(active());eq(dispatches,before,'path movement pauses requests')
 hero.抵达目标点=true;env.Ae冻集.最后按键=nil
 pump(200);assert(active()and dispatches>before,'resume after movement arrives')

 -- Old target dies: let the unchanged native scanner pick the next nearest visible enemy.
 local nextenemy={};for k,v in pairs(victim)do nextenemy[k]=v end
 local attr={};for k,v in pairs(victim.属性)do attr[k]=v end;nextenemy.属性=attr
 nextenemy.id=3;nextenemy.地图格子={x=2,y=0};nextenemy.地图坐标={x=2,y=0}
 objects[2]=nextenemy;victim.属性.hp=0
 pump(200)
 assert(hero.远程目标==nextenemy or hero.待选目标==nextenemy,'native scanner retargets after death')
 nextenemy.属性.hp=0;objects[1]=nil;objects[2]=nil
 local mana=hero.属性.mp;pump(200);eq(hero.属性.mp,mana,'no valid enemy does not consume mana');assert(active(),'wait for next valid enemy')

 key(112,true);pump(1);assert(not active(),'same key cancels');local inactive=green;fire.显示(fire,nil,nil,0,0);eq(green,inactive)
 pump(220);assert(not active(),'cancel hold cannot immediately rearm');key(112,false);pump(2)
 key(113,true);pump(220);assert(not active(),'summon not eligible');key(113,false);pump(2)
 key(114,true);pump(220);assert(not active(),'melee not eligible');key(114,false);pump(2)
 arm();key(113,true);pump(1);assert(not active(),'other skill key cancels');key(113,false);pump(2)
 local cases={'focus','ui','pause','logic','dead','drag','chat','warehouse','mapid','mapobject','rebind','keydown','scripted','disabled','stun','penetrate','npc','dialogue'}
 for _,case in ipairs(cases)do
  arm()
  if case=='focus'then env.Ae冻集.屏幕焦点=false
  elseif case=='ui'then env.Ae冻集.UI焦点=true;key(1,true)
  elseif case=='pause'then env.Ae冻集.游戏暂停=true
  elseif case=='logic'then env.Ae冻集.逻辑暂停=1
  elseif case=='dead'then hero.已经死亡=true
  elseif case=='drag'then env.Q_鼠标.被占用=true
  elseif case=='mouse'then key(1,true)
  elseif case=='chat'then windows[1]={名称='聊天',可视=true,是否有输入框焦点=function()return true end}
  elseif case=='warehouse'then windows[1]={名称='仓库窗口',可视=true,是否有输入框焦点=function()return false end}
  elseif case=='mapid'then env.Ae冻.地图id=2
  elseif case=='mapobject'then env.Q_地图={}
  elseif case=='rebind'then env.Ae冻集.快捷事件组[1].绑定技能='召唤神兽'
  elseif case=='keydown'then env.Ae冻集.最后按键=27;edges[27]=true
  elseif case=='scripted'then hero.剧情表[1]={}
  elseif case=='disabled'then hero.技能信息.月魂灵波.可用=false
  elseif case=='stun'then hero.硬直=1
  elseif case=='penetrate'then r.skills.月魂灵波.穿透模式=1
  elseif case=='npc'then env.Ae冻集.鼠标焦点事件对象={所属阵营='中立'};key(1,true)
  elseif case=='dialogue'then windows[1]={名称='对话窗口',可视=true,是否有输入框焦点=function()return false end}end
  -- No physical key is held; only the new scheduler could issue another request.
  before=dispatches;head(hero);assert(not active(),'cancel '..case);eq(dispatches,before,'no auto request during '..case)
  env.Ae冻集.屏幕焦点=true;env.Ae冻集.UI焦点=false;env.Ae冻集.游戏暂停=false;env.Ae冻集.逻辑暂停=0;hero.已经死亡=false
  env.Q_鼠标.被占用=false;key(1,false);windows[1]=parent;env.Ae冻集.快捷事件组[1].绑定技能='月魂灵波';env.Ae冻.地图id=1
  -- restore the finite map used by native release/movement
  if case=='mapobject'then env.Q_地图={FindPath=function()return -1,{}end,取格子信息=function()return{}end,坐标到逻辑格子=function(x,y)return x,y end,逻辑格子到坐标=function(x,y)return x,y end}end
  hero.剧情表={};hero.技能信息.月魂灵波.可用=true;hero.硬直=0;r.skills.月魂灵波.穿透模式=0;env.Ae冻集.最后按键=nil;env.Ae冻集.鼠标焦点事件对象=nil;edges={}
  pump(2)
 end
 -- The same threshold is measured in frame seconds at both low and common FPS.
 for _,fps in ipairs({15,60})do
  key(112,false);load('repeat_reset',env)(hero);env.dt=1/fps;head(hero)
  key(112,true);head(hero)
  for i=1,2*fps-1 do head(hero)end
  assert(not active(),'under two seconds at '..fps..' FPS')
  head(hero);assert(active(),'two seconds at '..fps..' FPS')
  key(112,false);head(hero)
 end
 env.dt=.01;load('repeat_reset',env)(hero);pump(2)
 arm()
 local cleanup=load('map_cleanup',env)
 debug.setupvalue(cleanup,1,{Hero=hero,屏幕特效组={},屏幕锁链组={},屏幕子弹组={},屏幕事件组={},屏幕粒子组={}})
 cleanup();assert(not active(),'actual complete native map cleanup')
 arm();load('repeat_reset',env)(hero);eq(hero.__gm_repeat_skill_v229,nil,'native constructor reset prefix')
 diagnostic.check(hero,env,head,fire,arm,key,pump,active)
 fire.销毁(fire);summon.销毁(summon);melee.销毁(melee);assert(destroyed>0,'border cleanup')
 print('REPEAT_V231_PASS '..mode..' native hover/tooltip229 negative control; two-second frame timer, moon soul wave callback/release, ground movement preservation, interaction cancellation, cleanup')
end
