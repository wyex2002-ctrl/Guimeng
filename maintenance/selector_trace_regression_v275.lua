-- Real slot initialization creates the event closure via FNEW. Both selectors
-- share real slot9 -> hero55 and the original logger. Graphics/grid are finite.
local work,mode=arg[1],arg[2]
if mode=='normal'then jit.off()else jit.opt.start('hotloop=1','hotexit=1')end
local checks=0
local function eq(a,b,m)checks=checks+1;assert(a==b,(m or'check')..' '..tostring(a)..' ~= '..tostring(b))end
local function load(n,e)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,e);return f end
local function noop()end
local sentinel={message='original release error'}
local function setup(version)
 local files,writes,now={},0,0;local stepwrites=0
 local e={dt=.05,Ae冻={},Ae冻集={逻辑暂停=0,快捷事件组={},画面偏移={x=0,y=0},屏幕宽度=800,屏幕高度=600,鼠标_地图坐标={x=0,y=0}}}
 e.os={date=os.date,time=function()return math.floor(now)end,clock=function()return now end,exit=noop}
 e.核心={写到文件=function(p,t)files[p]=t;writes=writes+1;if p=='Log/guimeng_skill_steps_latest.txt'then stepwrites=stepwrites+1 end end,读入文件=function(p)return files[p]end}
 setmetatable(e,{__index=function(_,key)return _G[key]end})
 local cfg={施放位置='目标',目标类型='敌方',施法距离=8,穿透模式=0,发射数量=0,作用范围={{},{},{},{},{},{},{},{}}}
 local hero={id=0,属性={hp=100,mp=100,禁攻击=true},硬直=0,地图格子={x=0,y=0},技能信息={雷电术={对象=cfg,可用=true}},释放技能组={},当前状态=0}
 local function enemy(id,x)return{id=id,属性={hp=50,可视=true,透明度=255},地图格子={x=x,y=0},地图坐标={x=x*48,y=40},锚点x=0,锚点y=0,可视=true,屏幕可视=true,是否有效=true,已经消失=false,所属阵营='敌方',资源动画={}}end
 local a,b=enemy(101,2),enemy(102,3);local objects={a,b}
 e.取两格子间距离=function(x,y,tx,ty)return math.sqrt((tx-x)^2+(ty-y)^2)end
 e.判断是否在攻击范围=function(p,t,r)return e.取两格子间距离(p.x,p.y,t.x,t.y)<=r and 1 or -1 end
 local calls,stages={},{};local require_before=false;local ordered=0
 local S={Hero=hero,Game_State=1,shelp={},script_setting={Gly独={错误=function(err)error(err,0)end}}}
 S.__gm_diag_checkpoint_v159=function(stage)
  stages[#stages+1]=stage
 end
 S.__gm_detail_v179=noop;S.fun=function(f,...)return f(...)end
 S.get=function(key,v)
  if key=='hero'then return hero elseif key=='skill'then return cfg
  elseif key=='__gm_diag_checkpoint_v159'then return S.__gm_diag_checkpoint_v159
  elseif key=='__gm_screen_objects_v154'then return objects
  elseif key=='__gm_visible_target_v156'then return v.是否有效 and not v.已经消失 end
  error('unexpected get '..tostring(key))
 end
 S.run=function(op,args)
  if op=='qs_skill_drop'then calls[#calls+1]=table.concat({args[1],args[2],args[4]},':');return true,false end
  if op==nil then now=now+e.dt end
  return false,nil
 end
 load('legacy_diag',e)(S)
 local checkpoint=S.__gm_diag_checkpoint_v159
 S.__gm_diag_checkpoint_v159=function(stage,...)
  if require_before then assert(files['Log/guimeng_skill_steps_latest.txt']:find('stage='..stage,1,true),'progress precedes original checkpoint');ordered=ordered+1 end
  return checkpoint(stage,...)
 end
 load('watch',e)(S)
 e.Sys=load('readonly',e)({get=S.get,run=function(...)return S.run(...)end})
 hero.技能释放=load('hero_skill',e);hero.__gm_melee_timing_v208=load('melee_timing',e)
 local original_release=hero.技能释放
 e.D2D_包围盒={创建=function()return{}end}
 e.Q__={创建动画=function()return{置中心点=noop,播放=noop}end};e.Q_公用图片库={CD图片=1}
 local slot={释放=load('skill_slot',e)}
 load(version=='old'and'slot_init_old'or'slot_init',e)(slot,0,0,48,48,'雷电术',112,false,'skill1')
 eq(#e.Ae冻集.快捷事件组,1);local event=e.Ae冻集.快捷事件组[1].事件;eq(type(event),'function')
 local function invoke(case)
  a.属性.hp=50;a.是否有效=true;a.已经消失=false;b.是否有效=true
  hero.攻击目标=nil;hero.远程目标=nil;hero.待选目标=nil;hero.__gm_queued_target_v155=nil;hero.__gm_queued_skill_v155=nil;hero.下次技能=nil
  cfg.施法距离=8;e.Ae冻集.逻辑暂停=0;hero.技能释放=original_release
  local flag=2
  if case==1 then flag=1 elseif case==2 then flag=3 elseif case==3 then flag=4
  elseif case==4 then flag=0 elseif case==5 then flag=nil
  elseif case==6 then hero.攻击目标=a
  elseif case==7 then a.属性.hp=0;a.已经消失=true
  elseif case==8 then a.是否有效=false;b.是否有效=false
  elseif case==9 then cfg.施法距离=1
  elseif case==10 then e.Ae冻集.逻辑暂停=1
  elseif case==11 then hero.技能释放=function()error(sentinel,0)end end
  local ok,err=pcall(event,flag)
  if not ok then
   if case==11 then eq(err,sentinel,'original error identity')else eq(type(err),'string','original invalid-flag error')end
  end
  local function id(v)return type(v)=='table'and v.id or tostring(v)end
  local snapshot=table.concat({tostring(ok),tostring(err),id(hero.攻击目标),id(hero.远程目标),id(hero.待选目标),id(hero.__gm_queued_target_v155),tostring(hero.__gm_queued_skill_v155),tostring(hero.下次技能)},'|')
  S.run();return snapshot
 end
 return{invoke=invoke,files=files,S=S,e=e,calls=calls,stats=function()return stepwrites end,order=function(on)require_before=on;return ordered end}
end
local a,b=setup('old'),setup('new')
for i=1,200 do local case=(i-1)%12;eq(a.invoke(case),b.invoke(case),'selector/release state unchanged')end
eq(table.concat(a.calls,'|'),table.concat(b.calls,'|'),'original dispatch inputs/order')
local steps=b.files['Log/guimeng_skill_steps_latest.txt'];assert(steps and #steps<16000)
assert(steps:find('v1.275',1,true));assert(steps:find('stage=skill.event.enter',1,true));assert(steps:find('stage=skill.dispatch.begin',1,true))
local n=0;for line in steps:gmatch('[^\r\n]+')do if line:sub(1,1)=='#'then n=n+1 end end;assert(n<=12)
-- The original checkpoint verifies that the accepted step is already on disk
-- before it runs. No OS facility is involved.
for i=1,6 do b.S.run()end
b.order(true)
local before=b.stats();b.S.__gm_diag_checkpoint_v159('skill.event.enter',2);assert(b.stats()>before)
b.S.__gm_diag_checkpoint_v159('skill.dispatch.begin',2);assert(b.order(false)>=2)
local w=b.stats();for i=1,200 do b.S.__gm_diag_checkpoint_v159('ordinary',i)end;eq(b.stats(),w,'ordinary checkpoints never write the progress file')
b.e.核心.写到文件=function()error('disk unavailable')end
b.S.__gm_diag_checkpoint_v159('skill.dispatch.begin',2)
print('SELECTOR_TRACE_V275_PASS '..mode..' checks='..checks..'; real slot FNEW -> selector -> slot9 -> hero55, 200 varied calls, original errors/dispatch and bounded synchronous breadcrumbs')
