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
 s.save=load('save_new',db);debug.setupvalue(s.save,1,{['配置文件']=function()end,['技能切换']=function()end})
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
for reward=1,3 do
 local s=make();s.roll=reward;local sum=0
 for chance=1,100 do
  s.chance=chance;local v=s.kill(30,({0,42,77,88})[chance%4+1]);if chance<=10 then sum=sum+reward end
  eq(s.hero['胶布香港'][3],sum,'independent per-kill chance exact bins')
  eq(s.hero[COUNT],nil,'old ten-kill counter unused')
  local calls=s.random_calls;s.death(v,0);eq(s.random_calls,calls,'settled corpse never rerolls')
 end
 eq(s.chance_calls,100);eq(s.reward_calls,10);eq(s.hero['胶布香港'][4]-s.hero['胶布香港'][3],1)
end
do
 local s=make();s.chance=10;s.roll=3
 s.kill(29);eq(s.chance_calls,nil,'level minus31 excluded')
 s.kill(30);eq(s.hero['胶布香港'][3],3,'level minus30 eligible')
 s.chance=11;s.kill(30);eq(s.hero['胶布香港'][3],3,'11 misses')
 s.live['属性']['等级']=61;s.kill(30);eq(s.chance_calls,2,'live level change respected')
 s.chance=1;s.kill(31,77);eq(s.hero['胶布香港'][3],6)
 for _,id in ipairs({99,-1,123456})do s.kill(100,id);eq(s.hero['胶布香港'][3],6)end
 local v=s.monster(100);v['所属阵营']='友方';s.death(v,0);eq(s.hero['胶布香港'][3],6)
 v=s.monster(100);v['宠物配置']['主人']={id=0};s.death(v,0);eq(s.hero['胶布香港'][3],6)
 s.save('GameDate',1,'',nil);eq(s.saved['胶布香港'][3],6);s.hero=clone(s.saved);s.kill(31);eq(s.hero['胶布香港'][3],9)
end
do
 local s=make();local sum=0
 for level=1,2000 do s.kill(level,0,true);sum=sum+math.ceil(level/3);eq(s.hero['胶布香港'][3],sum)end
 eq(s.chance_calls,nil,'Boss never rolls ordinary chance');eq(s.hero[COUNT],nil)
 local v=s.kill(40,42,true);eq(s.hero['胶布香港'][3],sum+14)
 s.death(v,42);eq(s.hero['胶布香港'][3],sum+14)
 v['属性'].hp=100;s.spawn(v,2);s.death(v,77);eq(s.hero['胶布香港'][3],sum+28)
 s.kill(1,0,0);eq(s.hero['胶布香港'][3],sum+29,'native numeric-zero Boss flag')
end
do
 local s=make();local native=s.U['窗口相关']['界面切换']
 s.U['窗口相关']['界面切换']=function()error('unavailable UI')end
 s.roll=2;local v=s.kill(30);eq(s.hero[PENDING],2);eq(s.hero['胶布香港'][3],0)
 s.death(v,0);eq(s.hero[PENDING],2,'no duplicate queue')
 s.save('GameDate',1,'',nil);eq(s.saved[PENDING],2);s.hero=clone(s.saved)
 s.U['窗口相关']['界面切换']=native;s.chance=100;s.kill(30);eq(s.hero['胶布香港'][3],2);eq(s.hero[PENDING],nil,'pending paid even on a miss')
 s.U['窗口相关']['界面切换']=function(a,k)native(a,k);error('after payment')end
 s.chance=1;s.kill(30);eq(s.hero['胶布香港'][3],4);eq(s.hero[PENDING],nil,'paid reward not queued twice')
 s.U['窗口相关']['界面切换']=native;s.chance=100;s.kill(30);eq(s.hero['胶布香港'][3],4)
end
do
 local s=make();local sum=0
 for i=1,10000 do
  s.chance=i%100+1;s.roll=i%3+1;local boss=i%17==0;local level=boss and i%200+1 or 30
  local v=s.kill(level,({0,42,77,88})[i%4+1],boss)
  if boss then sum=sum+math.ceil(level/3)elseif s.chance<=10 then sum=sum+s.roll end
  eq(s.hero['胶布香港'][3],sum);if i%13==0 then s.death(v,0);eq(s.hero['胶布香港'][3],sum)end
 end
 eq(s.callbacks,10000+math.floor(10000/13))
end
do
 local s=make();local protect=load('data_protection',{Sys=s.sys});debug.setupvalue(protect,1,s.sys);s.sys['数据保护']=protect
 s.live['属性']=protect({['等级']='60',['金币']=100})
 s.hero['胶布香港']=protect({100,101,0,1})
 local old=s.monster(30);old['属性']['附加']['等级']='30'
 s.old(old,0);eq(s.hero['胶布香港'][3],0,'old helper rejects numeric-string monster level')
 eq(#s.logs,0,'old logger misses Sys-owned diagnostic receiver')
 local v=s.monster(30);v['属性']=protect({hp=100,['可视']=true,['附加']={['等级']='30'}},true)
 s.death(v,'0');eq(s.hero['胶布香港'][3],1,'numeric-string id and level compatible through actual protected tables')
 assert(#s.logs>0);count=count+1
 local last=s.logs[#s.logs];assert(last:find('award kind=ordinary',1,true));count=count+1
end
do
 local legacy=make();legacy.live['属性']['等级']=21
 local broken=load('death_v177',legacy.env);broken(legacy.monster(7),0)
 eq(legacy.hero['胶布香港'][3],0,'v177 public Sys reproduces ordinary failure')
 eq(legacy.random_calls,0,'failure occurs before RNG')
 broken(legacy.monster(7,true),0);eq(legacy.hero['胶布香港'][3],3,'v177 Boss still awards')
 local original_rng=load('rng_original',{['引擎']={['取随机整数']=function(self,lo,hi)eq(lo,1);eq(hi,100);return 10 end}})
 eq(original_rng(1,100),10,'original engine RNG call convention')
 for _,killer in ipairs({0,42,77,88})do
  local s=make();s.live['属性']['等级']=21;s.roll=2;s.kill(7,killer,false)
  eq(s.hero['胶布香港'][3],2,'screenshot public interface')
 end
 local s=make();s.live['属性']['等级']=21;s.roll=2
 for roll=1,100 do s.chance=roll;s.kill(7,0,false) end
 eq(s.hero['胶布香港'][3],20,'exact chance bins via native engine API')
 local no=make();no.env['引擎']=nil;no.kill(30);eq(no.hero['胶布香港'][3],0,'missing rng no award')
 local before=no.random_calls;no.kill(7,0,true);eq(no.hero['胶布香港'][3],3,'Boss independent of ordinary rng');eq(no.random_calls,before)
end
print('REPUTATION_PASS',mode,count)
print('PASS',mode,count)
