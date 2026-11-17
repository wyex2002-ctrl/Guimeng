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
 native.引擎={取随机整数=function(_,lo,hi)if hi==1000 then eq(lo,1);s.oil_rolls=(s.oil_rolls or 0)+1;return s.oil_roll or 1000 end;return lo end,取随机小数=function(_,lo,hi)return lo end,取运行时间=function()return 0 end}
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

-- Original death -> helper -> native drop -> full native ground constructor.
local s=make()
for i=1,200 do s.oil_roll=1;s.kill(100,0,false)end
eq(#s.drops,0,'all ordinary kills produce zero oil');eq(s.oil_rolls,nil,'ordinary mobs do not roll oil')
for _,roll in ipairs({1,2,3,4,999,1000})do
 s.oil_roll=roll;local n=#s.drops;local rolls=s.oil_rolls or 0;local v=s.kill(1,0,true)
 eq(#s.drops,n+(roll<=3 and 1 or 0),'exact three per thousand threshold')
 eq(s.oil_rolls,rolls+1);s.death(v,0);eq(s.oil_rolls,rolls+1,'failed corpse never rerolls')
end
for _,id in ipairs({42,77,88})do s.oil_roll=3;local n=#s.drops;s.kill(1,id,true);eq(#s.drops,n+1,'merc and both pets keep kill ownership')end
for _,id in ipairs({99,-1,123456})do local n=#s.drops;s.kill(100,id,true);eq(#s.drops,n,'uncredited kills excluded')end
local v=s.monster(1,true);v.所属阵营='友方';local n=#s.drops;s.death(v,0);eq(#s.drops,n)
v=s.monster(1,true);v.宠物配置.主人={id=0};s.death(v,0);eq(#s.drops,n,'owned summons cannot farm oil')
s.oil_roll=1000;v=s.kill(1,0,true);local rolls=s.oil_rolls;v.属性.hp=100;s.spawn(v,2);s.oil_roll=1;s.death(v,0);eq(s.oil_rolls,rolls+1,'new life gets one new roll');eq(#s.drops,n+1)

-- Real role getter, real post-read/profile-apply/load-tail and native inventory
-- add. UI setup preceding this tail and disk encryption are finite boundaries.
local function giftmake(story)
 local s=make();local env=s.env;local owner={};local role=load(story==149 and 'role_q' or 'role_main',env)
 debug.setupvalue(role,1,owner);s.U.啾啾啵啵=role
 s.oil.属性=s.sys.数据保护(s.oil.属性,true);s.oil.附加=s.sys.数据保护(s.oil.附加,true)
 local bag={};s.sys.包裹物品组=bag;s.sys.Hero.背包格子={{32,{},true},{33,{'消耗品'},true},{34,{'武器'},true}}
 for _,id in ipairs({32,33,34})do bag[id]={拿起=false}end
 local free=load('free_slots',env);debug.setupvalue(free,1,s.sys);s.sys.取包裹剩余空位=free;s.G.取包裹空位=free
 local template=load('template_info',env);debug.setupvalue(template,1,s.sys);s.G.取道具信息_名称=template
 local add=load('add_item',env);debug.setupvalue(add,1,s.sys);s.sys.增加物品=add
 local glyadd=load('gly_add',env);debug.setupvalue(glyadd,1,s.sys);s.G.增加物品=glyadd
 s.sys.取包裹指定物品个数=function(name)local n=0;for _,b in pairs(bag)do if b.道具 and b.道具.名称==name then n=n+b.道具.数量 end end;return n end
 s.sys.格式化道具属性=function()return''end;s.sys.更新道具属性=function()end
 load('stack_install',env)(s.sys)
 s.sys.qs_item_box=function()end;s.sys.界面_窗口_数组={};s.sys.脚本关联处理=function()end
 env.intable=function(a,x)for _,v in ipairs(a)do if v==x then return true end end;return false end
 env.Ae冻集.动感格子效果=false;env.Ae冻集.Game_State=0
 local disk={};local stored={名称='角色甲',职业='战士',性别='男',包裹=bag}
 -- Real save branch passes the entire role to the existing disk API. This
 -- bounded storage copy tests persistence of its marker, not Windows I/O.
 s.G.读档=function(path)eq(path,'save.dat');return clone(disk.role or stored)end
 s.G.存档=function(path,r,key)disk.role=clone(r);s.saves=(s.saves or 0)+1 end
 s.G.取控件对象=function()return{}end;s.G.鼠标道具=0
 s.G.转场特效=function()end;s.G.开始游戏=function()end
 s.G.账号信息={账号名称='',唯一标识=''}
 s.U.背景音乐={停止=function()end};s.U.读取人物={};s.U.金轮法王=function()return 0 end
 s.U.胚子考虑=function()return{}end
 env.Gly独=s.G;env.Ux雌=s.U;env.是否为调试版=function()return true end
 env.FXru胃啪={HP=100,等级=50};env.取系统时间=function()return 0 end
 env.物品格子18={}
 local config={配置文件=function()end,技能切换=function()end}
 local login=load('login_'..story,env);debug.setupvalue(login,1,config)
 local save=load('save_'..story,env);debug.setupvalue(save,1,config)
 function s.enter(r)
  if r then stored=r;disk.role=nil end
  login('save.dat')
  s.hero=role()
 end
 function s.save()save('存档',1,nil);return disk.role end
 s.role=role;s.bag=bag;s.disk=disk
 s.countoil=function()return s.sys.取包裹指定物品个数('祝福油')end
 return s
end
for _,story in ipairs({149,179})do
 local s=giftmake(story)
 -- No empty eligible slot; weapon-only slot is deliberately left empty.
 s.bag[32].道具={名称='占位',数量=1};s.bag[33].道具={名称='占位',数量=1}
 s.enter();eq(s.countoil(),0);eq(s.hero.__gm_oil_welcome_v259,nil,'full bag never marks claimed')
 s.save();eq(s.disk.role.__gm_oil_welcome_v259,nil)
 s.bag[32].道具=nil
 s.enter();eq(s.countoil(),1,'next entry awards exactly one');eq(s.hero.__gm_oil_welcome_v259,true)
 local saved=s.save();eq(saved.__gm_oil_welcome_v259,true,'normal save retains marker')
 for i=1,200 do s.enter()end;eq(s.countoil(),1,'repeated enters do not repeat saved gift')
 s.bag[32].道具=nil;s.enter();eq(s.countoil(),0,'consuming oil never resets claimed marker')
 s.enter({名称='角色乙',职业='法师',性别='女'});eq(s.countoil(),1,'different role has independent gift')
 s.save();s.bag[32].道具=nil;s.bag[33].道具=nil
 s.enter();eq(s.countoil(),0,'second role saved marker survives')
 -- Save itself never invokes gift, including a role with no claim marker.
 s.role({名称='角色丙',职业='道士',性别='男'});s.save();eq(s.countoil(),0);eq(s.role().__gm_oil_welcome_v259,nil)
end
-- Existing stacks do not bypass the explicit full-bag rule. A valid free
-- consumable slot enables receipt even without a generic slot.
for _,story in ipairs({149,179})do
 local s=giftmake(story)
 s.bag[32].道具={名称='祝福油',数量=5};s.bag[33].道具={名称='占位',数量=1}
 s.enter();eq(s.countoil(),5);eq(s.hero.__gm_oil_welcome_v259,nil)
 s.bag[33].道具=nil;s.enter();eq(s.countoil(),6);eq(s.hero.__gm_oil_welcome_v259,true)
 local failed=giftmake(story);failed.G.增加物品=function()return false end
 failed.enter();eq(failed.countoil(),0);eq(failed.hero.__gm_oil_welcome_v259,nil,'failed add never consumes eligibility')
end
print('OIL_V259_PASS',mode,count,'native boss-drop and post-load inventory gift checks')
