-- Execute the unchanged module46 factory and its real private update/render/
-- hit/disposal functions. Geometry, graphics and damage sinks are finite.
local work,mode=arg[1],arg[2]
if mode=='normal'then jit.off()else jit.opt.start('hotloop=1','hotexit=1')end
local checks=0
local function eq(a,b,msg)checks=checks+1;assert(a==b,(msg or'check')..' '..tostring(a)..' ~= '..tostring(b))end
local function load(n,e)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,e);return f end
local function pack(...)return{n=select('#',...),...}end
local function same(a,b)eq(a.n,b.n);for i=1,a.n do eq(a[i],b[i])end end
local function setup(instrumented)
 local files,calls,frame={}, {},0
 local writes,damage,callbacks=0,0,0
 local failure,fail_object
 local function note(name,...)local t={name};for i=1,select('#',...)do t[#t+1]=tostring(select(i,...))end;calls[#calls+1]=table.concat(t,'|')end
 local function op(name)return function(...)note(name,...);if failure==name then error(fail_object,0)end end end
 local actor={id=20,地图坐标={x=0,y=32},地图格子={x=0,y=1},锚点x=0,锚点y=0,属性={hp=100,中心Y偏移=0,模型大小=1}}
 local target={id=21,地图坐标={x=192,y=32},地图格子={x=4,y=1},锚点x=0,锚点y=0,属性={hp=100,中心Y偏移=0,模型大小=1},是否有效=true,已经消失=false}
 actor.发生伤害=function(self,t,name,ratio,extra,...)eq(self,actor);eq(t,target);eq(name,'诊断测试');damage=damage+1;note('damage',frame)end
 local function visual(kind)
  return{置中心点=op(kind..'.center'),置混合模式=op(kind..'.blend'),置颜色=op(kind..'.color'),
   显示_高级=op(kind..'.draw'),显示=function(self,...)op(kind..'.draw')(...)end,
   更新=function(self)op(kind..'.update')()end,销毁=function(self)op(kind..'.destroy')()end}
 end
 local env={dt=.02,__ResPath='',L常量={混合_默认=0},
  Ae冻集={逻辑暂停=0,画面偏移={x=0,y=0},屏幕偏移={x=0,y=0}},
  os={date=os.date,time=os.time,clock=os.clock,exit=function()end},
  核心={写到文件=function(p,t)files[p]=t;writes=writes+1 end,读入文件=function(p)return files[p]end,
   取两点间角度=function(x,y,tx,ty)return math.deg(math.atan2(ty-y,tx-x))end,
   取两点间距离=function(x,y,tx,ty)return math.sqrt((tx-x)^2+(ty-y)^2)end,
   取移动步幅=function(deg)return math.cos(math.rad(deg)),math.sin(math.rad(deg))end},
  ARGB=function(a,r,g,b)return a*16777216+r*65536+g*256+b end,
  __Res=function(kind,path)note('asset',kind,path);if failure=='asset'then error(fail_object,0)end;return{宽度=24,高度=40,指针=path}end,
  Q__={创建精灵=function()note('sprite.create');return visual('sprite')end},
  类_轻动画={创建=function(path)note('animation.create',path);return visual('animation')end}}
 env.Q_地图={坐标到逻辑格子=function(x,y)return math.floor(x/48),math.floor(y/32)end,
  逻辑格子到坐标=function(x,y)return x*48,y*32 end,
  范围内对象检测=function(x,y,_,faction,sx,sy,multiple)
   note('collision',x,y,faction)
   if x==target.地图格子.x and y==target.地图格子.y and target.属性.hp>0 and not target.已经消失 then return multiple and{target}or target end
  end}
 setmetatable(env,{__index=function(_,key)if _G[key]~=nil then return _G[key]end;error('MISSING GLOBAL '..tostring(key))end})
 local S={Hero=actor,Game_State=1,shelp={},script_setting={Gly独={错误=function(err)error(err,0)end}}}
 local dispatch=load('dispatch',env);debug.setupvalue(dispatch,1,S);S.fun=dispatch
 S.get=function(key)eq(key,'hero');return actor end
 S.run=function(action,...)
  if action=='fun'then return S.fun(...)end
  if action==nil then frame=frame+1 end
  return false,nil
 end
 S.__gm_diag_checkpoint_v159=function()end;S.__gm_detail_v179=function()end
 env.Sys=load('readonly',env)({get=S.get,run=function(...)return S.run(...)end})
 env.子弹类=load('projectile_factory',env)
 local raw_factory=env.子弹类
 if instrumented then load('watch',env)(S)end
 local function managed(owner_id,target_id,info,extra)
  eq(owner_id,20);eq(target_id,21);eq(extra,false);callbacks=callbacks+1
  if failure=='callback'then error(fail_object,0)end
 end
 S.shelp[tostring(managed)]={sid='projectile-test',msg='original managed projectile callback'}
 local function create(kind,scenario)
  local info={技能名称='诊断测试',渐出=0,渐入=0,子弹射程=800,穿透模式=0,发射起点=0}
  local f=env.子弹类
  local tx,ty=192,32
  if scenario=='collision'then tx=-1;ty=0;info.穿透模式=1 end
  return f(0,32,tx,ty,240,actor,target,kind,'test.res',false,managed,false,nil,'敌方',0,info)
 end
 return{S=S,env=env,actor=actor,target=target,calls=calls,files=files,create=create,raw=raw_factory,
  stats=function()return writes,damage,callbacks,frame end,
  fail=function(where,obj)failure=where;fail_object=obj end}
end
local function run(instrumented,kind,scenario)
 local t=setup(instrumented);local bullet=t.create(kind,scenario);eq(type(bullet),'table')
 local history={};local gone=false
 for i=1,200 do
  if scenario=='move'and i==3 then t.target.地图坐标.y=64;t.target.地图格子.y=2 end
  if scenario=='dead'and i==3 then t.target.属性.hp=0;t.target.已经消失=true;t.target.是否有效=false end
  t.S.run();same(pack(bullet.更新()),{n=0});same(pack(bullet.显示()),{n=0})
  local x,y=bullet.取坐标();local hit=bullet.取命中对象();gone=bullet.已经消失()
  history[#history+1]=table.concat({i,tostring(x),tostring(y),tostring(hit and hit.id),tostring(gone)},'|')
  if gone then break end
 end
 assert(gone,'original projectile reaches its normal termination')
 same(pack(bullet.销毁()),{n=0})
 -- A diagnostic error forces a final snapshot of buffered projectile history.
 if instrumented then
  t.S.__gm_detail_v179('projectile.test.error','final snapshot')
  local text=t.files['Log/guimeng_native_watch_latest.txt']
  for _,s in ipairs({'projectile=true','projectile.create','projectile.gone','projectile.destroy','skill=诊断测试'})do assert(text:find(s,1,true),s)end
 end
 return table.concat(history,'\n'),table.concat(t.calls,'\n'),pack(t.stats()),t
end
for _,case in ipairs({{'图片','normal'},{'动画','move'},{'图片','dead'},{'图片','collision'}})do
 local ah,ac,ast=run(false,case[1],case[2]);local bh,bc,bst=run(true,case[1],case[2])
 eq(ah,bh,'position/hit/termination times');eq(ac,bc,'engine, original callback and damage ordering')
 for i=2,4 do eq(ast[i],bst[i],'damage/callback/frame count')end
 if case[2]=='collision'then eq(bst[2],1,'original penetrating projectile damages once')end
 assert(bst[1]<40,'ordinary projectile events stay buffered')
end
-- Failure injection is at finite engine sinks reached by the real methods.
-- No fake projectile replaces the original factory, update or disposal code.
for _,where in ipairs({'asset','animation.update','animation.draw','animation.destroy'})do
 local t=setup(true);local sentinel=setmetatable({},{__tostring=function()return 'PROJECTILE_SENTINEL'end})
 local bullet
 if where~='asset'then bullet=t.create('动画')end
 t.fail(where,sentinel)
 local ok,err
 if where=='asset'then ok,err=pcall(t.create,'图片')
 elseif where=='animation.update'then ok,err=pcall(bullet.更新)
 elseif where=='animation.draw'then ok,err=pcall(bullet.显示)
 else ok,err=pcall(bullet.销毁)end
 eq(ok,false);eq(err,sentinel,'original engine error identity')
 t.S.__gm_detail_v179('outer.error','after projectile context restored')
 local text=t.files['Log/guimeng_native_watch_latest.txt'];assert(text:find('FIRST_LUA_FAULT native.projectile.error',1,true));assert(text:find('PROJECTILE_SENTINEL',1,true));assert(text:find('skill=诊断测试',1,true));assert(text:find('stack traceback:',1,true));eq(t.S.__gm_native_watch_v268.depth,0)
 assert(text:find('projectile_owner id=20',1,true));assert(text:find('launch_target id=21',1,true))
end
-- Repeated constructors in one native environment must not nest the factory.
local t=setup(true);local factory=t.env.子弹类
local new={run=function()return false,nil end};load('watch',t.env)(new);eq(t.env.子弹类,factory)
local bullet=t.create('图片');bullet.更新();eq(new.__gm_native_watch_v268.depth,0)
assert(not t.S.__gm_native_watch_v268.projectile,'old session context is restored')
-- Failed diagnostics preserve the normal update return convention.
t.env.核心.写到文件=function()error('disk unavailable')end
same(pack(bullet.更新()),{n=0});same(pack(bullet.显示()),{n=0});same(pack(bullet.销毁()),{n=0})
print('PROJECTILE_TRACE_V274_PASS '..mode..' checks='..checks..'; actual module46 factory/update/render/hit/disposal and original dispatcher; finite geometry/graphics/damage sinks')
