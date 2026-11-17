local work,mode=assert(arg[1]),arg[2] or 'normal'
if mode=='hot' then require('jit.opt').start('hotloop=1','hotexit=1')else jit.off()end
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
 load('merc_helper',native)(s.sys,s.sys.script_setting)
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
 local water=assert(loadfile(work..'/water_base.lua'))();water.属性={};water.附加={};water.资源={};water.风格提示={}
 local base={['自然神水_小']=water}
 for _,k in ipairs({'最大破坏','最小破坏','最大自然','最小自然','最大灵魂','最小灵魂'})do base['自然神水_小'].属性[k]=0 end
 s.oil=template_factory(base['自然神水_小']);eq(type(s.oil.物品脚本.Main),'function','existing oil use script retained');eq(s.oil.名称,'祝福油');eq(s.oil.颜色值,-65536)
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
 native.引擎={取随机整数=function(_,lo,hi)if hi==50000 or hi==300 then eq(lo,1);s.last_oil_max=hi;s.oil_rolls=(s.oil_rolls or 0)+1;local roll=s.oil_roll or hi;assert(roll>=lo and roll<=hi,'oil roll outside integer range');return roll end;return lo end,取随机小数=function(_,lo,hi)return lo end,取运行时间=function()return 0 end}
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
 s.death=load('death_new',native);
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

-- Live hero level60: ordinary>=40, Boss>=40; all lower bands use fallback.
local s=make()
for _,case in ipairs({{39,false,1},{40,false,5},{41,false,5},{100,false,5},{39,true,1,300},{40,true,500},{41,true,500},{100,true,500}})do
 local level,boss,threshold,denom=unpack(case);denom=denom or 50000
 for _,roll in ipairs({1,threshold,threshold+1,denom})do
  s.oil_roll=roll;local n,rc=#s.drops,s.oil_rolls or 0;local v=s.kill(level,0,boss)
  eq(#s.drops,n+1,'saturated band still executes level branch and native drop')
  eq(s.oil_rolls,rc+1,'one oil roll per eligible death');eq(s.last_oil_max,denom,'exact integer denominator');s.death(v,0);eq(s.oil_rolls,rc+1,'failed corpse never rerolls')
 end
end
-- Representative repeated death callbacks cannot multiply this independent loot.
for i=1,200 do
 s.oil_roll=6;local n,rc=#s.drops,s.oil_rolls;s.kill(40,0,false);eq(#s.drops,n+1);eq(s.oil_rolls,rc+1)
end
-- Hero current level, not companion/summon level, determines the band.
s.live.属性.等级=100;s.actors[42].属性={等级=1}
for _,id in ipairs({0,42,77,88})do
 for _,case in ipairs({{79,false,5,false},{80,false,5,true},{79,true,2,false},{80,true,500,true}})do
  s.oil_roll=case[3];local n=#s.drops;s.kill(case[1],id,case[2]);eq(#s.drops,n+1,'main hero live level retained for all party ownership')
 end
end
s.live.属性.等级=60
-- The original fallback branch also saturates, including very low-level mobs.
for _,boss in ipairs({false,true})do s.oil_roll=1;local n=#s.drops;s.kill(1,0,boss);eq(#s.drops,n+1)end
for _,id in ipairs({99,-1,123456})do
 s.oil_roll=1;local n,rc=#s.drops,s.oil_rolls;local v=s.kill(100,id,true);eq(#s.drops,n);eq(s.oil_rolls,rc,'uncredited kill does not roll')
end
for _,kind in ipairs({'friend','owned'})do
 local v=s.monster(100,true);if kind=='friend'then v.所属阵营='友方'else v.宠物配置.主人={id=0}end
 s.oil_roll=1;local n,rc=#s.drops,s.oil_rolls;s.death(v,0);eq(#s.drops,n);eq(s.oil_rolls,rc,'non-wild enemy excluded')
end
-- Native respawn clears the once-per-life guard for the next life.
s.oil_roll=50000;local v=s.kill(40,0,false);local rc,n=s.oil_rolls,#s.drops
v.属性.hp=100;s.spawn(v,2);s.oil_roll=5;s.death(v,0);eq(s.oil_rolls,rc+1);eq(#s.drops,n+1)
-- Unknown/nonfinite levels keep the original fallback branch, then receive the test multiplier.
for _,value in ipairs({'invalid',math.huge,-math.huge})do
 local v=s.monster(100,true);v.属性.hp=0;v.属性.附加.等级=value;s.oil_roll=2
 local n=#s.drops;s.env.__gm_oil_drop_v242(v,0,nil);eq(#s.drops,n+1)
end
eq(s.oil.叠加,0);eq(s.oil.附加.叠加上限,1);eq(s.oil.数量,nil,'template quantity untouched')
print('OIL_DROP_V276_PASS '..mode..' checks='..count..'; retained level/RNG bands, saturated drops, native death/respawn/drop/ground, finite engine/map/graphics')
