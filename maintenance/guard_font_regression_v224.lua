local work,mode=arg[1],arg[2]
if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end
local n=0
local function eq(a,b,s)n=n+1;assert(a==b,(s or'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function load(k,env)local f=assert(loadfile(work..'/'..k..'.ljbc'));setfenv(f,env or _G);return f end
local env=setmetatable({class=function()return{}end,Sys={add=function()end},Ae冻集={剧情中=false}},{__index=_G})
load('event_class',env)();local cls=env.类_事件
local hero,merc={},{};local H={主角=hero,佣兵=merc}
local function actor(name)local a={属性={名称=name,禁攻击=false,禁移动=false,视野范围=10,混乱=false},Hero=H,宠物配置={},地图格子={x=1,y=1},攻击方向限制=0,绑定技能='无',所属阵营='友方'};setmetatable(a,{__index=cls});a.停止=function(self)self.stopped=(self.stopped or 0)+1 end;return a end
local owned={属性={hp=100},宠物配置={主人=hero},不可选中=false,隐身=false,出生中=false}
local hired={属性={hp=100},宠物配置={主人=merc},不可选中=false,隐身=false,出生中=false}
local wild={属性={hp=100},宠物配置={},不可选中=false,隐身=false,出生中=false}
local stranger={属性={hp=100},宠物配置={主人={}},不可选中=false,隐身=false,出生中=false}
local guard=actor('卫士');local skill_calls=0
local rows={owned,wild}
env.Q_地图={取指定范围内对象=function(x,y,r,camp,self,predicate)
 for _,v in ipairs(rows)do if v.属性.hp>0 and predicate(v) then return v end end
end,取格子信息=function()return rows end}
env.核心={取指定范围指定方向格子=function(pos,dir,range,out)out[1]={1,1}end}
for _,name in ipairs{'卫士','大刀卫士','弓箭卫士','大刀守卫','弓箭守卫','城镇卫士','守卫','弓箭手','大刀'}do
 local g=actor(name)
 eq(g:__gm_guard_ignore_v224(owned),true);eq(g:__gm_guard_ignore_v224(hired),true)
 eq(g:__gm_guard_ignore_v224(wild),false);eq(g:__gm_guard_ignore_v224(stranger),false)
 rows={owned,wild};eq(g:寻找目标(),wild,'guard skips summon and still finds monster')
 rows={hired};eq(g:寻找目标(),nil)
 rows={owned,wild};g.攻击方向限制=1;g.攻击方向配置={1};eq(g:寻找目标(),wild,'directional targeting')
 g.攻击来源=owned;g:继续攻击();eq(g.攻击来源,nil);eq(g.stopped,1)
 g.攻击来源=hired;g:继续追击();eq(g.攻击来源,nil);eq(g.stopped,2)
 eq(g:开始攻击(0,owned),false)
end
for _,name in ipairs{'沃玛卫士','祖玛卫士','冰魂卫士','霸王守卫','骷髅弓箭手','普通怪物'}do
 local a=actor(name);eq(a:__gm_guard_ignore_v224(owned),false);rows={owned,wild};eq(a:寻找目标(),owned,'wild monster behavior kept')
end
local nested={宠物配置={主人={宠物配置={主人=hero}}}};eq(guard:__gm_guard_ignore_v224(nested),true)
local cyclic={};cyclic.宠物配置={主人=cyclic};eq(guard:__gm_guard_ignore_v224(cyclic),false)
guard.宠物配置={主人=hero};eq(guard:__gm_guard_ignore_v224(owned),false);guard.宠物配置={}
-- Original downstream errors still propagate for a normal target.
local marker={};local originalattrs=guard.属性
guard.属性=setmetatable({名称='卫士'},{__index=function()error(marker)end})
local ok,err=pcall(cls.开始攻击,guard,0,wild);eq(ok,false);eq(err,marker);guard.属性=originalattrs
-- Reference native selector confirms this is a new exclusion, not a broken fixture.
local oldenv=setmetatable({class=function()return{}end,Sys=env.Sys,Ae冻集=env.Ae冻集,Q_地图=env.Q_地图},{__index=_G})
load('event_class_old',oldenv)();local oldcls=oldenv.类_事件
rows={owned,wild};eq(oldcls.寻找目标(guard),owned)
-- The method stays internal to the native class, not a new public entity API.
local api=load('entity_api');debug.setupvalue(api,1,{对象=guard});eq(api({},'__gm_guard_ignore_v224'),nil)
for i=1,200 do rows={owned,wild};eq(guard:寻找目标(),wild)end
-- Compare all existing unscaled draw arguments with the old native font method.
local before,after={},{}
local function record(out,...)out[#out+1]={n=select('#',...),...}end
local oldfont=load('font_layout_old');debug.setupvalue(oldfont,1,function(...)record(before,...)end)
local calls={};local colors={}
local fontenv={__Sprite={显示2=function(...)record(after,...)end,置渲染色=function(p,c)colors[p]=c end,显示_高级=function(p,x,y,a,sx,sy)calls[#calls+1]={p,x,y,a,sx,sy,colors[p]}end}}
local newfont=load('font_layout_native',fontenv)
local layout={{11,2,3},{12,10,13}}
for _,edge in ipairs{-14078936,false,-1234567}do oldfont(layout,20,30,-1,edge);newfont(layout,20,30,-1,edge)end
oldfont(layout,20,30,-45824);newfont(layout,20,30,-45824)
eq(#before,#after)
for i,a in ipairs(before)do local b=after[i];eq(a.n,b.n);for j=1,a.n do eq(a[j],b[j],'unscaled tooltip draw contract')end end
newfont(layout,20,30,-1,-14078936,.75);eq(#calls,10)
for i=5,10,5 do local c=calls[i];eq(c[5],.75);eq(c[6],.75);eq(c[7],-1)end
eq(calls[5][2],21.5);eq(calls[5][3],32.25);eq(calls[10][2],27.5);eq(calls[10][3],39.75)
print('GUARD_FONT_V224_PASS',mode,n,'native selectors, chase/begin gates; unscaled native font ABI preserved; finite geometry/glyph boundary')
