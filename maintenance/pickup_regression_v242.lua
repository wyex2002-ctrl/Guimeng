local work,mode=arg[1],arg[2]
if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')else jit.off()end
local count=0
local function eq(a,b,m)count=count+1;assert(a==b,(m or'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function load(n,env)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,env);return f end
local hero={}
load('hero_defaults',_G)(hero);eq(hero.__gm_pickup_sell_v242,true);eq(hero.__gm_auto_pickup_v242,false)
local E={屏幕焦点=true,逻辑暂停=0};local env=setmetatable({Ae冻集=E},{__index=_G})
local tick=load('timer',env)
eq(tick(false,hero,.5),false);hero.__gm_auto_pickup_v242=true
eq(tick(false,hero,.49),false);eq(tick(false,hero,.5),false);eq(tick(false,hero,.01),true)
eq(tick(true,hero,0),true)
hero.__gm_pickup_elapsed_v242=0;local ticks=0
for i=1,200 do if tick(false,hero,.1)then ticks=ticks+1 end end
eq(ticks>=19 and ticks<=20,true);E.屏幕焦点=false;eq(tick(false,hero,2),false);eq(hero.__gm_pickup_elapsed_v242,0);E.屏幕焦点=true
hero.__gm_pickup_sell_v242=false;load('hero_defaults',_G)(hero);eq(hero.__gm_pickup_sell_v242,true);eq(hero.__gm_auto_pickup_v242,false)
-- Native frame entry branches into the same embedded pickup path for manual
-- and scheduled input. The finite source execution below checks its effects.
local manual=false;local ran=0
local U,G={},{}
local frame_env=setmetatable({dt=.5,Ae冻集=E,L常量={键_ALT=1},引擎={取按键按下=function(self,k)eq(k,1);return manual end},loadstring=function(source)return function(u,g)eq(u,U);eq(g,G);ran=ran+1 end end,__gm_pickup_due_v242=tick},{__index=_G})
local owner={Hero=hero,script_setting={Ux雌=U,Gly独=G}}
local frame=load('frame_gate',frame_env);debug.setupvalue(frame,1,owner)
frame();eq(ran,0);manual=true;frame();eq(ran,1);manual=false;hero.__gm_auto_pickup_v242=true;hero.__gm_pickup_elapsed_v242=0
frame();eq(ran,1);frame();eq(ran,2)
local function clone(v)if type(v)~='table'then return v end;local out={};for k,x in pairs(v)do out[k]=clone(x)end;return out end
local function run(sell,full,protected,stack)
 local money,picked,tips=0,0,{}
 local h={__gm_pickup_sell_v242=sell,背包格子={{32,0,true}}};local bag={}
 local ref={附加={},最大破坏=1}
 local item={名称=protected and'青铜斧'or'测试白装',显示名='测试白装',分类='装备',子类='武器',叠加=0,价格=100,附加={},属性={最大破坏=1}}
 if stack then item={名称='回城卷',显示名='回城卷',分类='消耗',子类='消耗',叠加=1,价格=10,附加={叠加上限=999},属性={}};bag[32]={道具={名称='回城卷',数量=997}}end
 local function ground(x,y)
  return{物品=item,数量=stack and 5 or 1,格子={x=x,y=y},Hero={回调脚本={拾取=function()return false end}},拾取=function(self) picked=picked+self.数量;self.已经消失=true;return true end}
 end
 local buckets={};local function key(x,y)return x+y*100 end
 for _,p in ipairs({{5,5},{15,15},{4,10},{16,10}})do buckets[key(p[1],p[2])]={ground(p[1],p[2])}end
 local map={地面物品组=buckets,地图格子列数=30,地图格子行数=30,到逻辑格子=key}
 local S={get=function(k)if k=='hero'then return h elseif k=='item_arr'then return bag elseif k=='控制对象'then return{地图格子={x=10,y=10}}elseif k=='item_box'then return{}end end,run=function(op,cb,args)eq(op,'fun');return true,cb(unpack(args))end}
 local u={独角兽下=function()return{极品数值={}}end,窗口相关={界面切换=function(n)money=money+n end},托管显示={屏幕提示=function(t)tips[#tips+1]=t end}}
 local g={取道具信息_名称=function()return ref end,取包裹空位=function(k)return full and 0 or 1 end}
 local e=setmetatable({table=setmetatable({copy=clone},{__index=table}),Sys=S,Ae冻集=E,Q_地图={__gm_range_state=map}},{__index=_G});e._G=e
 local f=assert(loadfile(work..'/range_pickup_v242.lua'));setfenv(f,e);f(u,g)
 for _,t in ipairs(tips)do eq(t:find('失败',1,true),nil,t)end
 eq(buckets[key(4,10)][1].已经消失,nil,'outside west');eq(buckets[key(16,10)][1].已经消失,nil,'outside east')
 return money,picked,buckets
end
local m,p=run(true,false,false,false);eq(m,100);eq(p,0)
m,p=run(false,false,false,false);eq(m,0);eq(p,2)
m,p=run(true,true,false,false);eq(m,100);eq(p,0)
m,p=run(false,true,false,false);eq(m,0);eq(p,0)
m,p=run(true,false,true,false);eq(m,0);eq(p,2)
m,p=run(false,true,false,true);eq(m,0);eq(p>=2,true,'existing stack capacity')
print('PICKUP_V242_PASS',mode,count)
