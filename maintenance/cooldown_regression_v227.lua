-- Native release 26/55 -> actual 26/54 factory -> 26/6 CD tick -> real 36 class
-- -> real 16/73 sprite wrapper. Summon execution/graphics are finite boundaries.
local s=scene('new');local h,env=s.hero,s.env
env.select=select;env.setmetatable=setmetatable;env.rawget=rawget;env.rawset=rawset
local get=load('getter',env);debug.setupvalue(get,1,{Hero=h,游戏技能组=s.skills})
local original=env.Sys
local api={get=get,run=original.run,add=original.add}
env.Sys=load('readonly',env)(api)
local count,deleted,area=0,0,0
local x0,y0,w0,h0=13,24,48,48
local grid={}
env.__Sprite={创建=function(id,x,y,w,h)eq(id,0);eq(w,1);eq(h,1);count=count+1;return{native=true}end,
 置渲染色=function(p,c)assert(p.native);eq(c,-2013265920)end,
 置混合模式=function(p,c)assert(p.native);eq(c,0)end,
 显示_高级=function(p,x,y,r,w,h)
  assert(p.native);eq(r,0);eq(h,1);assert(x>=x0 and y>=y0 and x+w<=x0+w0 and y+h<=y0+h0)
  area=area+w
  for xx=x-x0,x-x0+w-1 do local k=(y-y0)*w0+xx;assert(not grid[k],'overdraw');grid[k]=true end
 end,
 销毁=function(p)assert(p.native);deleted=deleted+1 end}
env.Q__={创建包围盒=function()return{}end}
env.Q__.创建精灵=load('sprite_factory',env)
local cd={};for _,k in ipairs({'置参照点','播放','置渲染色','置当前帧','显示_高级','销毁','置混合模式'})do cd[k]=noop end
cd.创建=function()return 1 end
env.__Animation=cd;env.__ed_debug=error
env.Q__.创建动画=load('cd_factory',env)
env.D2D_包围盒={创建=function()return{置位置=noop}end}
env.Q_公用图片库={CD图片=1};env.Q_公用动画库={}
env.L常量.混合_默认=0;env.L常量.颜色_白=-1
-- Real factory skills use sprites. Finite base icon drawing is separate from the mask.
for _,v in pairs(s.skills)do v.精灵={置图片=noop,置混合模式=noop,置颜色=noop,显示_范围缩放=noop}end
load('slot_class',env)()
local name='召唤神兽'
h.技能配置(h,name);eq(s.skills[name].冷却时间,1.5)
local slot=env.类_格子_技能格子();slot.初始化(slot,10,20,48,48,name,0,false,'slot')
local function draw()
 grid={};area=0;slot.显示(slot,nil,nil,3,4);return area
end
eq(draw(),0,'idle');eq(s:cast(name),true,'native release accepted')
eq(h.技能信息[name].开始CD效果,true,'release starts actual CD')
eq(draw(),48*48,'full mask immediately after release')
local cache=slot.__gm_cooldown_mask_v227;eq(count,1)
-- Inspect all cached sectors for monotonic area, no holes in angular coverage,
-- clockwise opening, confinement and no overlapping alpha spans.
local prev=48*48
for f=1,60 do
 h.技能信息[name].当前帧=f
 local a=draw();assert(a<=prev and a>0);prev=a
 if f==16 then eq(grid[10*48+35],nil,'top right cleared first');eq(grid[35*48+10],true,'bottom left still covered')end
end
-- Restore fresh actual release state, then drive the unmodified native CD clock.
h.技能信息[name].当前帧=1
local last=48*48;local advanced=false
for i=1,200 do
 s:step();local a=draw();assert(a<=last);if a<last then advanced=true end;last=a
end
assert(advanced);eq(h.技能信息[name].开始CD效果,false);eq(last,0)
eq(count,1);eq(slot.__gm_cooldown_mask_v227,cache,'cached across frames')
-- Geometry-only reset after the native lifecycle assertion. Fixture art has a long action.
h.技能信息[name].开始CD效果=true;h.技能信息[name].当前帧=1;eq(draw(),48*48);eq(count,1)
slot.坐标.x=20;slot.坐标.y=35;x0,y0=23,39;eq(draw(),48*48,'move with parent offset')
slot.宽度=60;slot.高度=40;w0,h0=60,40;eq(draw(),60*40,'resize rebuild');eq(count,2);eq(deleted,1)
slot.绑定技能=nil;eq(draw(),0);slot.销毁(slot);eq(deleted,2)
print('COOLDOWN_V227_PASS '..mode..' summon release -> native CD tick -> native slot -> sprite wrapper; 60 sectors; completion; caching; cleanup')
