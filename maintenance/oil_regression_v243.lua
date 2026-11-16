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
local T={};for k,v in pairs(table)do T[k]=v end;T.copy=clone;table=T
load('table_register',{table=T})()
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
 local template_env={table=table,setmetatable=setmetatable,type=type,math=math,pairs=pairs,Sys={run=function(op,f,...)if op=='adds'then return f()end;if op=='add'then return end;error(op)end}}
 local template_factory=load('oil_template',template_env)
 local base={['自然神水_小']={属性={},附加={},资源={},风格提示={}}}
 for _,k in ipairs({'最大破坏','最小破坏','最大自然','最小自然','最大灵魂','最小灵魂'})do base['自然神水_小'].属性[k]=0 end
 s.oil=template_factory(base['自然神水_小']);eq(s.oil.物品脚本.Main(),false,'preview luck unchanged');eq(s.oil.名称,'祝福油');eq(s.oil.颜色值,-65536)
 eq(s.oil.道具说明,'蕴含神秘祝福的油剂，使用后有机会提升已装备坐骑的幸运。')
 s.drops={};s.sys.游戏道具组={祝福油=s.oil};s.sys.Hero=s.live
 local protect=load('data_protection',native);debug.setupvalue(protect,1,s.sys);s.sys.数据保护=protect
 -- Finite engine primitives; complete native drop and ground constructor run.
 local noop=function()end
 native.Ae冻集.掉落模式=s.dropmode or 0
 native.Ae冻集.默认文字_间距=0;native.Ae冻集.默认文字_行距=0;native.Ae冻集.地面道具描边=0
 native.Q__={创建动画=function()return{置中心点=noop}end};native.Q_公用图片库={地面物品闪烁序列图={}}
 native.Q_地图={八方向是否可移动检测=function()return true end,逻辑格子到坐标=function(x,y)return x*10,y*10 end,坐标到逻辑格子=function(x,y)return x/10,y/10 end,取地图信息_总=function()return{宽度=1000,高度=1000}end,置格子信息=noop}
 native.Q_文字={取宽度=function(t)return #t*6 end,取高度=function()return 12 end};native.ARGB=function()return 0 end
 native.引擎={取随机整数=function(_,lo,hi)return lo end,取随机小数=function(_,lo,hi)return lo end,取运行时间=function()return 0 end}
 s.sys.取最近的可掉落格子=function(x,y)return x,y end;s.sys.递归查找最近=function(x,y)return x,y end
 local get0=exports.get;exports.get=function(key,...)if key=='win_tex'then return function()return{置标题=function(title,align,color)eq(title,'祝福油');eq(color,-65536);s.last_label=title end}end end;return get0(key,...)end
 local constructor=load('ground_init',native)
 native.地图物品类={创建=function(item,x,y,quantity,mode)
  local object={};constructor(object,item,x,y,quantity,mode)
  eq(type(object.物品),'table');eq(object.物品.名称,'祝福油');eq(object.数量,1);eq(object.物品.颜色值,-65536);eq(object.显示内容,'祝福油')
  s.drops[#s.drops+1]=object;return object
 end}
 local drop=load('native_drop',native);debug.setupvalue(drop,1,s.sys)
 exports.run=function(op,...)
  if op=='数据保护'then return protect(...)end
  if op=='掉落物品'then return drop(...)end
  error('unexpected operation '..tostring(op))
 end
 native.__gm_oil_drop_v242=load('oil_helper',native)
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


local s=make()
for i=1,200 do
 local v=s.kill((i%2==0)and 1 or 100,({0,42,77,88})[(i-1)%4+1],i%2==0)
 eq(#s.drops,i,'one test oil every player/merc/pet kill');s.death(v,0);eq(#s.drops,i,'no corpse duplicate')
end
local v=s.monster(1);s.death(v,0);eq(#s.drops,201)
v.属性.hp=100;s.spawn(v,2);s.death(v,0);eq(#s.drops,202,'respawn permits next oil')
for _,id in ipairs({99,-1,123456})do s.kill(100,id);eq(#s.drops,202)end
v=s.monster(1);v.所属阵营='友方';s.death(v,0);eq(#s.drops,202)
v=s.monster(1);v.宠物配置.主人={id=0};s.death(v,0);eq(#s.drops,202)
-- Saved metadata is normalized by actual replacement wrapper, input immutable.
local state={包裹物品组={[32]={道具={名称='祝福油'}}}}
local reset=load('oil_reset');debug.setupvalue(reset,1,state)
local seen;debug.setupvalue(reset,2,function(id,change,mode)seen=change;return false,nil,'kept'end)
local change={道具说明='old',颜色值=-1,数量=4};local a,b,c=reset(32,change,1)
eq(a,false);eq(b,nil);eq(c,'kept');eq(seen.颜色值,-65536);eq(seen.道具说明,s.oil.道具说明);eq(change.颜色值,-1);eq(seen.数量,4)
-- Old helper must fail through the same real drop/ground initializer, not
-- a mock expecting the incorrect argument order.
local old=make();local oldhelper=load('old_oil_helper',old.env);local victim=old.monster(1);victim.属性.hp=0
local ok,err=pcall(oldhelper,victim,0,-1)
eq(ok,false);eq(tostring(err):find("number value",1,true)~=nil,true,tostring(err));eq(#old.drops,0)
print('V242_USER_GROUND_ERROR_REPRODUCED',tostring(err))
-- Both engine placement modes and disabled-drop return paths.
for _,mode_value in ipairs({0,1,2})do local x=make();x.env.Ae冻集.掉落模式=mode_value;x.kill(1);eq(#x.drops,1)end
print('OIL_V243_PASS',mode,count)
