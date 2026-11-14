local work,mode=arg[1],arg[2]or'normal'
if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end
local checks=0
local M={};for k,v in pairs(math)do M[k]=v end;M.round=function(x)return math.floor(x+.5)end
local function eq(a,b,why)checks=checks+1;assert(a==b,(why or'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function near(a,b,why)checks=checks+1;assert(math.abs(a-b)<1e-8,(why or'near')..': '..tostring(a)..' ~= '..tostring(b))end
local function load(n,env)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,env or _G);return f end
local configs=assert(loadfile(work..'/configs.lua'))()
local scripts=assert(loadfile(work..'/scripts.lua'))()
local function split(s,sep)local t={};s=s or'';if s==''then return t end;local at=1;while true do local a,b=string.find(s or'',sep,at,true);if not a then t[#t+1]=string.sub(s or'',at);return t end;t[#t+1]=string.sub(s,at,a-1);at=b+1 end end
local function read(s,section,key,default)for line in string.gmatch(s,'[^\r\n]+')do local a,b=string.match(line,'^(.-)=(.*)$');if a==key then return b end end;return default end
local function noop()end
local factory_env={tonumber=tonumber,math=M,table=table,string=string,['分割文本']=split,['核心']={['读配置项_内存']=read},['Ae冻集']={['自定义属性表']={},['游戏素材组']={}},['D2D_精灵']={['创建']=function()return{['置中心点']=noop}end},Sys={add=noop}}
factory_env['核心']['按方向矩阵转换']=load('rotate',factory_env)
local factory=load('skill_factory',factory_env)
local function scene(version,opts)
 opts=opts or{};local now=0;local events={};local skills={};local methods;local classreads=0
 for name,cfg in pairs(configs)do skills[name]=factory(0,0,nil,nil,name,'魔法','',cfg);skills[name]['脚本']={Main=function()end};skills[name]['起手动画']={};skills[name]['目标动画']={};skills[name]['起手音效']=nil;skills[name]['击中音效']=nil end
 local E={['游戏进度']=1,['逻辑暂停']=0,['屏幕焦点']=true,['UI焦点']=false,['游戏暂停']=false,['遮罩信息']={['触发']=false},['鼠标_地图坐标']={x=1,y=0},['鼠标_地图格子']={x=1,y=0},['屏幕帧率']=60,['画面偏移']={x=0,y=0},['游戏素材组']={}}
 local S={};local env={type=type,tonumber=tonumber,tostring=tostring,math=M,table=table,string=string,pairs=pairs,ipairs=ipairs,unpack=unpack,pcall=pcall,dt=opts.dt or .01,Sys=S,['Ae冻集']=E,['Ae冻']={},['Q_提示框']={['可视']=false},['L常量']={['键_鼠标右']=2,['混合_颜色乘']=1},['分割文本']=split,['核心']={['取两点间方向']=function()return 1 end},['引擎']={['取运行时间']=function()return now*1000 end,['取按键事件']=function()return false end,['取随机整数']=function(_,a,b)return a end},['判断是否在攻击范围']=function()return 1 end,['取两格子间距离']=function(x,y,xx,yy)return math.max(math.abs(x-xx),math.abs(y-yy))end}
 env['Q_地图']={FindPath=function()return -1,{}end,['取格子信息']=function()return{}end,['坐标到逻辑格子']=function(x,y)return x,y end,['逻辑格子到坐标']=function(x,y)return x,y end}
 local animation=load('animation',env);local reverse=load('reverse',env);local reset=load('reset',env)
 local images={};for i=1,100 do images[i]={['图片']=1,['精灵']={},['帧宽']=1,['帧高']=1}end
 local function sprite()
  return {['动画资源']={['PAK信息组']=images,['图层信息组']={}},['更新']=animation,['反向更新']=reverse,['重置']=reset,['停止']=false,['可视']=false,['总帧数']=100,['全局计次']=0,['时间累积']=0,['动画帧']=0,['动作结束']=false,['置中心点']=noop,['置颜色']=noop,['置混合模式']=noop}
 end
 env.class=function()
  methods={};local mt={__index=methods}
  return setmetatable({},{__index=function()classreads=classreads+1;return nil end,__newindex=function(_,k,v)methods[k]=v end,__call=function()return setmetatable({},mt)end})
 end
 S.add=function(k,c)eq(k,'hero');env.hero_class=c end
 S.get=function(k,name)if k=='skill'then return assert(skills[name],'unknown skill '..tostring(name))elseif k=='__gm_diag_checkpoint_v159'then return nil end;error('unexpected get '..tostring(k))end
 S.run=function(op,args,...)
  if op=='qs_skill_drop'then
   local flag=args[1];events[#events+1]={op=flag,t=now,name=args[4]}
   if flag==5 and opts.convert then return true,opts.convert end
   return true,nil
  elseif op=='fun'then if type(args)=='function'then return true,args(unpack((...)))end;return true,nil elseif op=='屏幕提示'then return true,nil end
  error('unexpected run '..tostring(op))
 end
 load('class_'..version,env)();eq(classreads,0)
 local h=env.hero_class();local victim={['敌方']=true,id=2,['属性']={hp=100000},['地图格子']={x=1,y=0},['地图坐标']={x=1,y=0},['是否有效']=true,['所属阵营']='敌方',['锚点x']=0,['锚点y']=0}
 local frames={};for i=1,opts.frames or 8 do frames[i]=i end
 local acts={};for _,name in ipairs({'战斗准备','停止','移动','物理攻击','施法'})do acts[name]={['帧数组']={[1]=frames},['帧率']=opts.frame_rate or 10,['锚点x']=0,['锚点y']=0,['混合组']={},['翻转组']={}}end
 local data={['属性']={hp=1000,maxhp=1000,mp=1000,maxmp=1000,['禁攻击']=false,['攻击距离']=1,['攻击速度']=opts.period or .8,['攻击速度倍数']=opts.speed or 10,['模型大小']=1,['中心Y偏移']=0},['硬直']=0,['当前状态']=0,['上次状态']=0,['技能信息']={},['回调脚本']={},['主角配置']={['攻击动作']='物理攻击',['绑定技能']=opts.bound or '普通攻击',['右键技能']='普通攻击',['左键步距']=1,['右键步距']=0,['左键动作']='移动',['右键动作']='移动'},['动画组']={{['动画']=sprite(),['动作组']=acts,['动画翻转']=1}},['动作转移']={},['动作']='停止',['方向']=1,['本次移动速度倍数']=10,['施法速度']=1,['攻击速度_计次']=100,['释放技能组']={},['BUFF组']={},['攻击目标']=victim,['地图格子']={x=0,y=0},['地图坐标']={x=0,y=0},['锚点x']=0,['锚点y']=0,['所属阵营']='友方',['移动步幅']={x=0,y=0},['抵达目标点']=true,['僵直效果']=true,['动作反向播放']=false,['动作残影效果']=false,['键盘移动']=false,['移动音效间隔']=0,['移动音效计次']=0,['剧情表']={},['动画暂停']=false,['技能模式']=1,['击退信息']={['击退中']=false,['冲刺模式']=false},['掉血特效组']={},['已经死亡']=false}
 for k,v in pairs(data)do h[k]=v end
 h.id=1;env['物品格子1']={};env['FXru胃啪']={['取状态列表']=function()return{}end,['删除状态']=noop};env['Ux雌']={['游戏音效']={},['大堵塞就']=function()return{}end};env['Gly独']={['从ID取对象']=function(id)return id==1 and h or victim end,['创建音效']=function(name)return{['播放']=function()events[#events+1]={op='sound',name=name,t=now}end}end}
 for name,file in pairs(scripts)do skills[name]['脚本']=load(file,env)()end
 env['Q_地图']['范围内对象检测']=function()return victim end
 env['Q_地图']['取格子信息']=function(x,y,faction)if faction=='敌方'and x==victim['地图格子'].x and y==victim['地图格子'].y then return{victim}end;return{}end
 h['HP改变']=function(_,v)h['属性'].hp=h['属性'].hp+v end;h['MP改变']=function(_,v)h['属性'].mp=h['属性'].mp+v end
 local attack=methods['开始物理攻击动作'];h['开始物理攻击动作']=function(self,...)events[#events+1]={op='attempt',t=now};return attack(self,...)end
 h['BUFF状态更新']=noop;h['播放音效']=noop
 h['发生伤害']=function(_,target,skill,power)events[#events+1]={op='damage',t=now,name=skill['名称'],target=target};return {true,1,0} end
 local tick=load('tick_'..version,env)
 return {hero=h,target=victim,env=env,skills=skills,events=events,methods=methods,
 now=function()return now end,
 cast=function(self,name)return h['技能释放'](h,name,true,victim,nil,false)end,
 step=function(self,n)
  for _=1,n or 1 do now=now+env.dt;tick(h);h['技能更新'](h);if opts.hold and h['当前状态']==0 then h['开始物理攻击动作'](h,true,true)end;h['状态更新'](h);h['动作更新'](h)end
 end}
end
local function times(s,op)
 local t={};for _,e in ipairs(s.events)do if e.op==op then t[#t+1]=e.t end end;return t
end
local function upstate(s)
 return select(2,debug.getupvalue(s.hero['释放技能组'][1]['刷新'],1))
end
local melee={'普通攻击','基本剑术','攻杀剑术','刺杀剑术','半月弯刀','翔空剑法','烈火剑法','十方斩','莲月剑法','快刀斩麻'}
for _,name in ipairs(melee)do
 local old,new=scene('old'),scene('new')
 eq(old:cast(name),true,name);eq(new:cast(name),true,name)
 local a,b=upstate(old),upstate(new)
 near(b['起手动画延迟'],a['起手动画延迟']*.7,name)
 near(b['命中动画延迟'],a['命中动画延迟']*.7,name)
 near(b['伤害进度'][1],a['伤害进度'][1]*.7,name)
 eq(old.skills[name]['冷却时间'],new.skills[name]['冷却时间']);eq(old.skills[name]['施法速度'],new.skills[name]['施法速度'])
 old:step(110);new:step(110)
 near(times(old,'damage')[1],.70,name..' old hit');near(times(new,'damage')[1],.49,name..' earlier hit');eq(#times(old,'damage'),#times(new,'damage'),name..' hit count')
 local a,b=times(old,'sound'),times(new,'sound');eq(#a,#b);near(b[1],a[1]*.7,'start sound timing')
end
for _,case in ipairs({{speed=5},{speed=10},{speed=25},{dt=1/15},{dt=1/60},{frames=12,frame_rate=12}})do
 for _,direct in ipairs({false,true})do
  case.hold=not direct;local old,new=scene('old',case),scene('new',case)
  eq(old:cast('普通攻击'),true);eq(new:cast('普通攻击'),true)
  for i=1,1200 do
   old:step();new:step()
   if direct then old:cast('普通攻击');new:cast('普通攻击')end
   if #times(old,0)>=4 and #times(new,0)>=4 then break end
  end
  local a,b=times(old,0),times(new,0)
  eq(#a,#b,'start count');eq(#a>=4,true,'continuous starts')
  for i=1,#a do near(a[i],b[i],'original start schedule')end
 end
end
-- The same real class can still cast unrelated skills with original timing.
do
 local old,new=scene('old'),scene('new');old.skills['火球术']['脚本'].Main=function()end;new.skills['火球术']['脚本'].Main=function()end
 eq(old:cast('火球术'),true);eq(new:cast('火球术'),true)
 local a,b=upstate(old),upstate(new)
 near(a['起手动画延迟'],b['起手动画延迟']);near(a['命中动画延迟'],b['命中动画延迟']);near(a['伤害发生延迟'],b['伤害发生延迟'])
 eq(new.hero.__gm_melee_state_v208,nil)
end
-- Native automatic substitution and the existing attack-range conversion.
for _,skill in ipairs({'攻杀剑术','刺杀剑术','烈火剑法'})do
 local old,new=scene('old',{convert=skill}),scene('new',{convert=skill})
 eq(old:cast('普通攻击'),true);eq(new:cast('普通攻击'),true)
 eq(upstate(new)['技能信息']['对象']['名称'],upstate(old)['技能信息']['对象']['名称'])
 old:step(110);new:step(110)
 eq(#times(old,'damage'),#times(new,'damage'));near(times(new,'damage')[1],.49)
end
-- Attempting a different skill cannot escape the original recovery animation.
do
 local old,new=scene('old'),scene('new');old:cast('普通攻击');new:cast('普通攻击')
 old:step(60);new:step(60)
 eq(old:cast('烈火剑法'),false);eq(new:cast('烈火剑法'),false)
 eq(#times(new,0),1,'no second accepted attack');eq(new.hero['属性'].mp,old.hero['属性'].mp)
 local accepted_old,accepted_new
 for i=1,100 do
  old:step();new:step()
  if not accepted_old and old:cast('烈火剑法')then accepted_old=old.now()end
  if not accepted_new and new:cast('烈火剑法')then accepted_new=new.now()end
  if accepted_old and accepted_new then break end
 end
 near(accepted_old,accepted_new,'skill alternation timing')
end
-- Actual move-request gate: a finite final move primitive accepts the request;
-- full path traversal/rendering is outside this fixture. Cooldown survives it.
do
 local old,new=scene('old'),scene('new');old:cast('普通攻击');new:cast('普通攻击')
 old:step(65);new:step(65)
 eq(old.hero['当前状态'],3);eq(new.hero['当前状态']~=3,true,'earlier recovery')
 local moves=0
 new.hero['开始移动']=function(h) moves=moves+1;h['改变动作'](h,1);return true end
 eq(new.hero['移动到'](new.hero,1,0,1),true);eq(moves,1,'movement allowed before next attack')
 eq(old.hero['移动到'](old.hero,1,0,1),false)
 eq(new:cast('普通攻击'),false,'moving does not reset attack recovery')
 new.hero['改变动作'](new.hero,0)
 new.target['地图格子'].x=2;new.hero['攻击目标']=new.target
 new.hero['开始物理攻击动作'](new.hero,true,true)
 eq(#times(new,0),1,'target change does not grant attack')
end
-- Bound melee skills retain their cooldown schedule, including high attack speed.
for _,case in ipairs({{bound='半月弯刀'},{bound='烈火剑法'},{bound='快刀斩麻'},{bound='烈火剑法',speed=25}})do
 case.hold=true;local old,new=scene('old',case),scene('new',case)
 old:cast(case.bound);new:cast(case.bound)
 for i=1,1600 do
  old:step();new:step();if #times(old,0)>=4 and #times(new,0)>=4 then break end
 end
 local a,b=times(old,0),times(new,0);eq(#a,#b);eq(#a>=4,true)
 for i=1,#a do near(a[i],b[i],'bound skill/CD schedule')end
end
-- Runtime script multi-hit overrides pass through the actual instance builder.
-- No segment is inserted, removed or multiplied twice; physical type's
-- original single-hit interpretation is retained, rather than invented here.
do
 local old,new=scene('old'),scene('new')
 for _,s in ipairs({old,new})do
  s.skills['莲月剑法']['脚本'].Main=function()return{['施法速度']=.8,['多段伤害']={200,400,700}}end
  eq(s:cast('莲月剑法'),true)
 end
 local a,b=upstate(old),upstate(new);eq(#a['伤害进度'],3);eq(#b['伤害进度'],3)
 for i=1,3 do near(b['伤害进度'][i],a['伤害进度'][i]*.7)end
 old:step(100);new:step(100);eq(#times(old,'damage'),1);eq(#times(new,'damage'),1) -- original physical type remains single-hit
end
-- Explicitly animation-free script overrides cannot leave a permanent gate;
-- genuine hurt/knockback cancels retain the original control of recovery.
do
 local s=scene('new');s.skills['普通攻击']['脚本'].Main=function()return{['施法动作']='无'}end
 eq(s:cast('普通攻击'),true);eq(s.hero.__gm_melee_state_v208.no_animation,true)
 eq(s.hero['__gm_melee_timing_v208'](s.hero,'direct_gate'),true)
 for _,kind in ipairs({'hurt','knockback','dead'})do
  local x=scene('new');x:cast('普通攻击')
  if kind=='hurt'then x.hero['当前状态']=4 elseif kind=='dead'then x.hero['属性'].hp=0 else x.hero['击退信息']['击退中']=true end
  x.hero['__gm_melee_timing_v208'](x.hero,'tick',.01)
  eq(x.hero.__gm_melee_state_v208,nil,kind..' has no stale melee gate')
 end
end
-- Real scripts and native update/animation chain for one representative 200
-- accepted attack comparison. No per-skill Cartesian stress multiplication.
do
 local old,new=scene('old',{hold=true}),scene('new',{hold=true})
 old:cast('普通攻击');new:cast('普通攻击')
 local n=0
 while #times(old,0)<200 or #times(new,0)<200 do
  old:step();new:step();n=n+1;assert(n<40000,'attack chain stalled')
 end
 local a,b=times(old,0),times(new,0);eq(#a,200);eq(#b,200)
 for i=1,200 do near(a[i],b[i],'200 accepted start schedule')end
 -- The last newly accepted hit is not yet due. Earlier feedback must not
 -- create extra hits after both queues are drained with targeting disabled.
 old.hero['攻击目标']=nil;new.hero['攻击目标']=nil;old:step(150);new:step(150)
 eq(#times(old,'damage'),200);eq(#times(new,'damage'),200)
end
print('MELEE_V208_PASS',mode,checks,'real class/release/scripts/state/animation, 200 attack schedule parity; finite assets/move/damage boundary, no Windows test')
