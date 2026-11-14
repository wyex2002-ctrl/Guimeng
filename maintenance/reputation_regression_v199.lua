local work,mode=assert(arg[1]),arg[2] or 'normal'
if mode=='hot' then require('jit.opt').start('hotloop=1','hotexit=1')end
local count=0
local function eq(a,b,why)assert(a==b,(why or 'check')..': '..tostring(a)..' ~= '..tostring(b));count=count+1 end
local function load(name,env)
 local f=assert(loadfile(work..'/'..name..'.ljbc'));setfenv(f,setmetatable(env or {},{__index=_G}));return f
end
local function clone(v)
 if type(v)~='table' then return v end
 local r={};for k,x in pairs(v)do r[k]=clone(x)end;return r
end
local COUNT,PENDING,DONE='__gm_rep_kills_v168','__gm_rep_pending_v170','__gm_rep_done_v168'
local function make()
 local s={hero={['名称']='测试角色',['胶布香港']={100,101,0,1}},
  live={['属性']={['等级']=60,['金币']=100}},actors={},logs={},notices={},callbacks=0,payments=0,random_calls=0,id=1000,roll=1}
 s.sys={Hero=s.live,script_setting={}}
 local getter=load('fx_getter');debug.setupvalue(getter,1,s.sys)
 -- Execute the actual original FX proxy getter, including live level/money.
 local fx=setmetatable({},{__index=getter})
 local U={['啾啾啵啵']=function()return s.hero end,['佣兵对象']={id=42},
  ['人物选择']=1,['读取人物']={},['窗口相关']={},
  ['托管显示']={['屏幕提示']=function(t)s.notices[#s.notices+1]=t end}}
 local G={['事件对象']=function(id)return s.actors[id]end,
  ['存档']=function(path,role,key)eq(role,s.hero);s.saved=clone(role)end,
  ['结束游戏']=function()error('unexpected anti-check')end,
  ['增加物品']=function()error('unexpected anti-check mutation')end,
  ['取随机数']=function(lo,hi)eq(lo,1);s.random_calls=s.random_calls+1;if hi==100 then s.chance_calls=(s.chance_calls or 0)+1;return s.chance or 1 end;eq(hi,3);s.reward_calls=(s.reward_calls or 0)+1;return s.roll end}
 s.sys.script_setting={['Ux雌']=U,['Gly独']=G,['FXru胃啪']=fx}
 local db={['Ux雌']=U,['Gly独']=G,['FXru胃啪']=fx,['是否为调试版']=function()return false end,
  ['格式化数值']=tostring,['包裹声望标签']={},['声望标签']={},['金币标签']={},['L常量']={['颜色_黄']=-256}}
 local currency=load('currency_new',db);debug.setupvalue(currency,1,{})
 U['窗口相关']['界面切换']=function(amount,kind)s.payments=s.payments+1;return currency(amount,kind)end
 local native={Sys=s.sys,['Ae冻']=U,['Ae冻集']={['死亡掉宝延迟']=1},Log=function()error('must use Sys diagnostic receiver')end}
 s.sys.__gm_diag_checkpoint_v159=function(stage,t)eq(stage,'reputation.v179');s.logs[#s.logs+1]=t end
 local proxy=load('public_sys');local getter=load('public_get');debug.setupvalue(getter,1,s.sys)
 local exports={run=function()end,game_start=function()end,add=function()end}
 exports.get=function(key,...)
  if key=='obj' then local objects={};for _,actor in pairs(s.actors)do objects[#objects+1]=actor end;s.sys['屏幕事件组']=objects end
  return getter(key,...)
 end
 native.Sys=proxy(exports)
 assert(native.Sys.Hero==nil and native.Sys.script_setting==nil and native.Sys.__gm_diag_checkpoint_v159==nil)
 native['引擎']={['取随机整数']=function(self,lo,hi) return G['取随机数'](lo,hi) end}
 s.death=load('death_new',native);s.old=load('death_old',native)
 s.spawn=load('spawn',native)
 s.env=native;s.db=db;s.U=U;s.G=G;s.fx=fx
 s.actors[42]=U['佣兵对象'];s.actors[77]={id=77,['主人id']=0}
 s.actors[88]={id=88,['宠物配置']={['主人']=U['佣兵对象']}};s.actors[99]={id=99,['主人id']=99}
 function s.monster(level,boss)
  s.id=s.id+1
  local v={id=s.id,['名称']='测试怪物',['所属阵营']='敌方',
   ['属性']={hp=100,['附加']={['等级']=level or 30,BOSS=boss},['可视']=true},
   ['宠物配置']={},['刷新间隔']=300,['当前状态']=0,['地图格子']={x=5,y=7},
   ['BUFF组']={},['死亡消失间隔']=2,['dropitem']=false}
  v['播放音效']=function(self,kind)eq(kind,4)end
  v['改变动作_']=function(self,state)self['当前状态']=state end
  v['场景剔除']=function(self,a,b)eq(a,true);eq(b,false)end
  v['事件回调']=function(self,event,data)eq(event,'死亡');eq(data[1],5);eq(data[2],7);s.callbacks=s.callbacks+1 end
  return v
 end
 function s.kill(level,killer,boss)local v=s.monster(level,boss);s.death(v,killer or 0);return v end
 return s
end

-- Exactly 200 ordinary draws, cycle every engine result twice. Alternating
-- owners and rewards exercise the actual public lookup and currency path.
local s=make();local expected=0
for i=1,200 do
 s.chance=(i-1)%100+1;s.roll=(i-1)%3+1
 local v=s.kill(30,({0,42,77,88})[(i-1)%4+1])
 if s.chance<=4 then expected=expected+s.roll end
 eq(s.hero['胶布香港'][3],expected,'4 percent exact random bins')
 s.death(v,0);eq(s.hero['胶布香港'][3],expected,'corpse cannot pay twice')
end
eq(s.chance_calls,200);eq(s.reward_calls,8)
for _,message in ipairs(s.logs)do if message:find('ordinary roll=5 ',1,true)then eq(message:find('hit=false',1,true)~=nil,true,'diagnostic threshold updated')end end
-- Compare the old ten-percent boundary using the actual old death method.
local old=make();old.chance=5;old.old(old.monster(30),0);eq(old.hero['胶布香港'][3],1)
local now=make();now.chance=5;now.kill(30);eq(now.hero['胶布香港'][3],0)
-- Inclusive 4, rejected 5; all original 1..3 reward outcomes retained.
for reward=1,3 do local x=make();x.chance=4;x.roll=reward;x.kill(30);eq(x.hero['胶布香港'][3],reward);x.chance=5;x.kill(30);eq(x.hero['胶布香港'][3],reward)end
local levels={{1,1},{4,1},{5,1},{6,2},{10,2},{11,3},{16,4},{40,8},{100,20},{999,200}}
local b=make();local sum=0
for _,pair in ipairs(levels)do b.kill(pair[1],0,true);sum=sum+pair[2];eq(b.hero['胶布香港'][3],sum,'ceil(level/5)')end
eq(b.chance_calls,nil,'Boss has no ordinary chance gate')
local v=b.kill(40,42,true);sum=sum+8;eq(b.hero['胶布香港'][3],sum);b.death(v,42);eq(b.hero['胶布香港'][3],sum)
v['属性'].hp=100;b.spawn(v,2);b.death(v,77);eq(b.hero['胶布香港'][3],sum+8,'respawn can settle once again')
-- Existing level, ownership and pending-accounting rules remain unchanged.
local x=make();x.roll=3;x.chance=4;x.kill(29);eq(x.hero['胶布香港'][3],0);x.kill(30);eq(x.hero['胶布香港'][3],3)
for _,id in ipairs({99,-1,123456})do x.kill(100,id);eq(x.hero['胶布香港'][3],3)end
local friend=x.monster(100);friend['所属阵营']='友方';x.death(friend,0);eq(x.hero['胶布香港'][3],3)
local owned=x.monster(100);owned['宠物配置']['主人']={id=0};x.death(owned,0);eq(x.hero['胶布香港'][3],3)
local pending=make();pending.roll=2;pending.chance=4;local currency=pending.U['窗口相关']['界面切换'];pending.U['窗口相关']['界面切换']=function()error('temporary UI failure')end
local corpse=pending.kill(30);eq(pending.hero[PENDING],2);pending.death(corpse,0);eq(pending.hero[PENDING],2)
pending.U['窗口相关']['界面切换']=currency;pending.chance=100;pending.kill(30);eq(pending.hero['胶布香港'][3],2);eq(pending.hero[PENDING],nil)
local protected=make();local protect=load('data_protection',{Sys=protected.sys});debug.setupvalue(protect,1,protected.sys);protected.sys['数据保护']=protect
protected.live['属性']=protect({['等级']='60',['金币']=100});protected.hero['胶布香港']=protect({100,101,0,1})
protected.chance=4;protected.roll=3;protected.kill('30','77');eq(protected.hero['胶布香港'][3],3,'protected numeric-string fields/public pet lookup')
print('REPUTATION_V199_PASS',mode,count)
