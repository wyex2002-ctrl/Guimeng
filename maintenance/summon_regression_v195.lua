local work,mode=arg[1],arg[2]or'normal'
if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end
local checks=0
local function eq(a,b,label)checks=checks+1;assert(a==b,(label or'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function load(n,env)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,env or _G);return f end
local function bind(n,owner,env)local f=load(n,env);debug.setupvalue(f,1,owner);return f end
local skeleton,beast='召唤骷髅','召唤神兽'
local prototypes={4498,4511,4539,4552,4565,4583,4596,4609,4627,4640,4653,4666,4679,4692,4710,4723,4741,4987,5000}
local function scene(label,index,enhanced)
 local C={['宝宝']={},['宝宝数量']=0,['宝宝操作']=0,['租赁怪物']={},['光影']={},['宝宝颜色']={[0]=1,[1]=1,[2]=1,[3]=1,[4]=1,[5]=1}}
 local skills={[skeleton]={0},[beast]={0}}
 if enhanced then skills['超强召唤骷髅']={enhanced};skills['超强召唤神兽']={enhanced}end
 local hero={['名称']='测试角色',['技能']=skills};local skilldata={}
 for _,name in ipairs({skeleton,beast,'超强召唤骷髅','超强召唤神兽'})do
  skilldata[name]={};for lv=1,6 do skilldata[name][lv]={['初始等级']=1,['限制等级']=7,['继承幻影']=0}end
 end
 local world={};local nextid=100;local spawned,recalls=0,{};local fail=false
 local U={['版本选择']='来世续缘',['啾啾啵啵']=function()return hero end,['胚子考虑']=function()return C end,['大堵塞就']=function()return skilldata end}
 U['窗口相关']={['元素窗口']=function()end,['随机传送']=function(p)recalls[p.id]=(recalls[p.id]or 0)+1 end,['宝宝属性']=function(p,lv)p['updated_level']=lv end}
 U['游戏音效']={['神兽变身音效']={['播放']=function()end}};U['托管显示']={['屏幕提示']=function()end}
 local FX={HP=100,['属性']={['附加']={}},['取状态列表']=function()return{}end}
 world[0]=FX
 local function make(id,kind)
  local attr={['名称']=kind or '租赁怪物',['附加']={}}
  local p={id=id,HP=100,['等级']=1,['属性']=attr,['附加']={['召唤技能']=kind},['states']={}}
  p['增加状态']=function(n)p.states[n]=true end;p['删除状态']=function(n)p.states[n]=nil end
  p['动画包更新']=function(_,body)p.body=body end;p['更新血条样式']=function()end;p['更新显示名称']=function(n)p.name=n end
  p['动作转移']=function(n)p.action=n end
  p['播放动作']=function(_,_,_,callback)if callback then callback(nil,1,1)end end
  world[id]=p;return p
 end
 local G={['镜头缩放']=0,['取出技能信息']=function(n)return{['显示名']=n}end,['事件对象']=function(id)return world[id]end,
 ['主仆绑定']=function(template)
  if fail then return -1 end
  nextid=nextid+1;spawned=spawned+1
  make(nextid,(template==1042 or template==1110)and skeleton or beast);return nextid
 end}
 local env={type=type,tonumber=tonumber,tostring=tostring,pairs=pairs,ipairs=ipairs,math=math,string=string,table=table,['Ux雌']=U,['Gly独']=G,['FXru胃啪']=FX,['L常量']={['键_A']=65},['物品格子18']={}}
 env['底部窗口']={['可视']=true};env['信息窗口']={['可视']=false};env['对话窗口']={['可视']=false};env['聊天输入框']={['焦点']=false}
 local S={script_setting=env,tbl_controls={}}
 bind('sandbox_install',S,_G)();eq(env.Sys,nil);eq(env._G,nil);eq(env.pcall,nil)
 local control=bind('control',U['窗口相关'],env);U['窗口相关']['宝宝操作']=control
 local funcs={};for _,kind in ipairs({skeleton,beast})do funcs[kind]=bind(label..'_'..(index or 4498),{id=kind},env)end
 local s={C=C,world=world,skills=skills,U=U,env=env,recalls=recalls}
 function s.cast(kind)funcs[kind](nil,{},nil,nil,nil,nil)end
 function s.live(kind)local n=0;local last;for id,p in pairs(world)do if id>0 and p.HP>0 and p['附加']['召唤技能']==kind and p['附加']['魅惑']==nil then n=n+1;last=p end end;return n,last end
 function s.count()return spawned end
 function s.fail(v)fail=v end
 function s.add(kind,extra)
  nextid=nextid+1;local p=make(nextid,kind);C['宝宝']['宝宝'..p.id]=p.id;C['宝宝数量']=C['宝宝数量']+1
  if extra then for k,v in pairs(extra)do p['附加'][k]=v end end
  return p
 end
 function s.flush()
  for id,p in pairs(world)do
   if id>0 and p.HP<=0 then
    local f=bind('death',{id=id,['对象']=p},env);f(nil,nil,0,nil)
   end
  end
 end
 function s.destroy(p)bind('destroy',{id=p.id,['对象']=p},env)()end
 function s.verify()
  local n=0;for _,id in pairs(C['宝宝'])do if id>0 then n=n+1 end end;eq(C['宝宝数量'],n,'registry/count consistent')
 end
 return s
end
-- Baseline control: summoning the other kind hits the shared cap and returns.
local old=scene('old');old.cast(skeleton);eq(old.live(skeleton),1,'baseline initial summon');old.cast(beast);eq(old.live(skeleton),1,'baseline keeps skeleton but blocks beast');eq(old.live(beast),0,'baseline returns before beast spawn')
-- All nineteen actual dispatch copies take the independent-kind path.
for _,i in ipairs(prototypes)do
 local s=scene('new',i);s.cast(skeleton);s.cast(beast);eq(s.live(skeleton),1,'skeleton and beast coexist');eq(s.live(beast),1);eq(s.count(),2);s.verify()
 local _,a=s.live(skeleton);local _,b=s.live(beast);s.cast(skeleton);s.cast(beast);eq(s.count(),2,'same-kind recast does not duplicate');eq((s.recalls[a.id]or 0)>1,true,'same-kind recall executed');eq((s.recalls[b.id]or 0)>1,true);eq(a.HP>0,true);eq(b.HP>0,true);s.verify()
end
local s=scene('new');s.cast(beast);s.cast(skeleton);local _,a=s.live(skeleton);local _,b=s.live(beast)
-- Representative hot/cold repetition; deliberately not multiplied per variant.
for i=1,200 do s.cast(i%2==0 and skeleton or beast);eq(s.live(skeleton),1);eq(s.live(beast),1)end
eq(s.count(),2);eq(a.HP>0,true);eq(b.HP>0,true)
-- Death callback removes one ID exactly once, even when retried; re-summon only missing kind.
a.HP=0;s.flush();s.verify();eq(s.C['宝宝数量'],1);s.destroy(a);eq(s.live(beast),1,'destroy one kind preserves the other');s.flush();eq(s.C['宝宝数量'],1);s.cast(skeleton);eq(s.live(skeleton),1);eq(s.live(beast),1);eq(b.HP>0,true);s.verify()
-- A dead-but-not-yet-cleaned slot must not block a replacement.
local _,dead=s.live(skeleton);dead.HP=0;s.cast(skeleton);eq(s.live(skeleton),1);s.flush();s.verify();eq(s.C['宝宝数量'],2)
-- Missing engine object or a stale high total does not block a different kind.
local stale=scene('new');stale.C['宝宝']['宝宝999']=999;stale.C['宝宝数量']=6;stale.cast(beast);stale.cast(skeleton);eq(stale.live(beast),1);eq(stale.live(skeleton),1)
-- An engine spawn failure never registers an extra pet or increments the total.
local failed=scene('new');failed.fail(true);failed.cast(skeleton);eq(failed.C['宝宝数量'],0);eq(next(failed.C['宝宝']),nil);failed.fail(false);failed.cast(skeleton);eq(failed.live(skeleton),1)
-- Existing enhanced variants, including legacy duplicate same-kind pets.
for _,lv in ipairs({0,2,5})do
 local e=scene('new',4498,lv);local first=e.add(skeleton);local second=e.add(skeleton);local other=e.add(beast)
 e.cast(skeleton);eq(e.live(skeleton),1,'legacy same-kind extras retired');eq(other.HP>0,true,'other kind survives');e.flush();e.verify();eq(e.C['宝宝数量'],2)
 e.cast(beast);eq(e.live(beast),1);eq(e.live(skeleton),1)
 local fresh=scene('new',4498,lv);fresh.cast(skeleton);fresh.cast(beast);eq(fresh.live(skeleton),1);eq(fresh.live(beast),1)
end
-- Control loop continues to affect both kinds and leased pets; charm remains excluded.
local c=scene('new');c.cast(skeleton);c.cast(beast);local _,ca=c.live(skeleton);local _,cb=c.live(beast)
local leased=c.add(nil);c.C['宝宝']['宝宝'..leased.id]=nil;c.C['宝宝数量']=c.C['宝宝数量']-1;c.C['租赁怪物'][1]=leased.id
local charm=c.add(skeleton,{['魅惑']=1});c.cast(skeleton);eq(charm.HP>0,true,'charmed pet untouched')
c.U['窗口相关']['宝宝操作'](0);eq(ca.states['宝宝休息'],true);eq(cb.states['宝宝休息'],true);eq(leased.states['宝宝休息'],true);eq(charm.states['宝宝休息'],nil)
c.U['窗口相关']['宝宝操作'](1);eq(ca.states['宝宝休息'],nil);eq(cb.states['宝宝休息'],nil);eq(leased.states['宝宝休息'],nil)
-- Actual Ctrl+A keyboard handler uses the unchanged common control loop.
local keyboard=load('keyboard',c.env);c.C['宝宝操作']=0
keyboard(65,1);eq(ca.states['宝宝休息'],true);eq(cb.states['宝宝休息'],true);eq(leased.states['宝宝休息'],true);eq(c.C['宝宝操作'],1)
keyboard(65,1);eq(ca.states['宝宝休息'],nil);eq(cb.states['宝宝休息'],nil);eq(leased.states['宝宝休息'],nil);eq(c.C['宝宝操作'],0)
local pre=scene('new');pre.U['版本选择']='前尘忆梦';pre.cast(beast);pre.cast(skeleton);eq(pre.live(beast),1);eq(pre.live(skeleton),1)
-- Transform changes appearance, not species identity used by the new cap.
cb['附加']['变身']=1;bind('transform',{},c.env)(cb.id);eq(cb['附加']['变身'],0,'actual transform callback');eq(cb['附加']['召唤技能'],beast);local before=c.count();c.cast(beast);eq(c.count(),before);eq(cb.HP>0,true)
-- Existing rest state is respected on newly summoned pets.
local rest=scene('new');rest.C['宝宝操作']=1;rest.cast(skeleton);rest.cast(beast);local _,ra=rest.live(skeleton);local _,rb=rest.live(beast);eq(ra.states['宝宝休息'],true);eq(rb.states['宝宝休息'],true)
print('SUMMON_V195_PASS',mode,'checks',checks)
