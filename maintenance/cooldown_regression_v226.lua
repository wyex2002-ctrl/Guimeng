local dir,mode=arg[1],arg[2]
if mode=='hot'then jit.opt.start('hotloop=1','hotexit=1')else jit.off()end
local function noop()end
local function load(name,env)local f=assert(loadfile(dir..'/'..name..'.ljbc'));setfenv(f,env);return f end
local tint,frame,draws,creates=0,0,0,0
local native={}
-- Native graphics are the finite boundary. All public animation methods are real 16/39 closures.
for _,k in ipairs({'置参照点','播放','置混合模式','销毁'})do native[k]=noop end
native.创建=function(...)creates=creates+1;return 123 end
native.置渲染色=function(p,c)assert(p==123);tint=c end
native.置当前帧=function(p,f)assert(p==123);frame=f end
native.显示_高级=function(...)draws=draws+1 end
local env=setmetatable({__Animation=native,__ed_debug=error,Q__={创建包围盒=function()return{}end}}, {__index=_G})
local animation=load('animation',env)
local info={开始CD效果=true,当前帧=1}
local icon={置图片=noop,置混合模式=noop,置颜色=noop,显示_范围缩放=noop,宽度=30,高度=30}
local hero={技能信息={test=info}}
env.Q__.创建动画=animation
env.Sys={get=function(k)if k=='hero'then return hero else return{精灵=icon,图标=1}end end}
env.D2D_包围盒={创建=function()return{置位置=noop}end}
env.Ae冻集={快捷事件组={},游戏调试=false}
env.Q_公用图片库={CD图片=1};env.L常量={混合_默认=0,颜色_白=-1};env.Q_公用动画库={}
local init=load('init',env);local draw=load('draw',env)
local slot={};init(slot,10,20,48,48,'test',0,false,'slot')
assert(tint==-1996488705 and creates==1)
for i=1,60 do info.当前帧=i;draw(slot,nil,nil,3,4);assert(frame==i-1)end
local n=draws;info.开始CD效果=false;draw(slot,nil,nil,0,0);assert(draws==n)
info.开始CD效果=true
for i=1,200 do info.当前帧=i%60+1;draw(slot,nil,nil,0,0)end
assert(creates==1)
slot.绑定技能=nil;n=draws;draw(slot);assert(draws==n)
print('COOLDOWN_V226_PASS '..mode..' real constructor, animation wrapper, 60 frames, completion, unbind, 200 cached draws')
