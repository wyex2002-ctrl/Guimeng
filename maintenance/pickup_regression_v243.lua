local work,mode=arg[1],arg[2]
if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')else jit.off()end
local count=0
local function eq(a,b,m)count=count+1;assert(a==b,(m or'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function load(n,env)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,env);return f end
local E={屏幕焦点=true,逻辑暂停=0}
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
 local f=assert(loadfile(work..'/range_pickup.lua'));setfenv(f,e);f(u,g)
 for _,t in ipairs(tips)do eq(t:find('失败',1,true),nil,t)end
 eq(buckets[key(4,10)][1].已经消失,nil,'outside west');eq(buckets[key(16,10)][1].已经消失,nil,'outside east')
 return money,picked,buckets
end
local m,p=run(true,false,false,false);eq(m,100);eq(p,0)
m,p=run(false,false,false,false);eq(m,100);eq(p,0,'stale false flag cannot disable original Alt auto-sale')
m,p=run(false,true,false,false);eq(m,100);eq(p,0)
m,p=run(true,false,true,false);eq(m,0);eq(p,2)
m,p=run(false,true,false,true);eq(m,0);eq(p>=2,true)
print('PICKUP_V243_PASS',mode,count)
