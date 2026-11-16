local work,mode=arg[1],arg[2]
if mode=='hot' then require('jit.opt').start('hotloop=1','hotexit=1') end
local count=0
local function eq(a,b,label) count=count+1;assert(a==b,(label or'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function load(n,env)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,env or _G);return f end
local function bind(n,S,env)local f=load(n,env);debug.setupvalue(f,1,S);return f end
local skin_color,text_y
local slice_y
local hit=true;local down,up=false,false
local registry={};local controls={};local opened,sounds,draws,closed=0,0,0,0
local function noop()end
local function sprite(img,x,y,w,h)
 local r={}
 r.置中心点=noop;r.置混合模式=noop;r.置颜色=noop;r.销毁=noop;r.置显示区域=noop
 r.显示_高级=function(...)draws=draws+1 end;r.显示=noop
 r.取包围盒=function()return{检测_点=function()return hit end,显示=noop,置位置=noop}end
 r.取宽度=function()return w end;r.取高度=function()return h end
 return r
end
local ui=setmetatable({Ae冻集={游戏调试=false},L常量={混合_默认=0,颜色_白=-1},Q_提示框={可视=false},SETA=function(c)return c end},{__index=_G})
ui.核心={ARGB分解=function()return 255,255,255,255 end,RGB2ARGB=function(v)return v end,读配置项_内存=function(s,section,key,default)return s:match(key..'=([^\n]+)')or default end}
local win={id=539,名称='背包窗口',控件组={},坐标={x=10,y=20},焦点=true}
local W={界面_窗口_数组={win}}
local lookup=bind('window_lookup',W,ui)
ui.Sys={add=function(kind,k,v)if kind=='tbl_controls'then controls[k]=v else registry[kind]=k end end,get=function(k)return registry[k]end}
ui.Sys.run=function(op,f,...)
 if op=='取窗口对象'then return lookup(f)end
 if op=='adds'then return f()end
 if op=='fun'then return f(unpack((...)))end
 error('unexpected Sys.run '..tostring(op))
end
ui.Q__={创建精灵=sprite,创建包围盒=function()return{检测_点=function()return hit end,置位置=noop,置宽高=noop,显示=noop}end}
ui.__Sprite={置渲染区域=function(p,x,y,w,h)assert(p.native);p.w=w;p.h=h end,取宽度=function(p)return p.w end,取高度=function(p)return p.h end,创建=function(id,x,y,w,h)return{native=true,w=w,h=h}end,
 置渲染色=function(p,c)assert(p.native);eq(type(c),'number');if p.w==6 then skin_color=c end end,
 显示_高级=function(p,...)assert(p.native);if p.w==6 then slice_y=select(2,...) end;draws=draws+1 end,
 置参照点=function(p,...)assert(p.native)end,
 置混合模式=function(p,...)assert(p.native)end,
 销毁=function(p)assert(p.native)end}
ui.Q__.创建精灵=load('sprite_native',ui)
ui.D2D_精灵={创建=function(...)local obj=sprite(...);obj.置颜色=function(self,c)assert(type(self)=='table','attempt to index self (a number value)')end;return obj end}
local font={解析=function(t,sp,lp)eq(sp,0);eq(lp,0);return {text=t}end,取宽度=function(s)return #s/2*12 end,取高度=function()return 12 end,显示=function()error('wrong type-2 font signature')end,显示配置=function(layout,x,y,c,o)eq(layout.text,'仓库');eq(c,-1);eq(o,-15724528);text_y=y;draws=draws+1 end}
ui.__Res=function(kind,path)
 if kind==2 then eq(path,'400132927.img');return font end
 eq(path,'-1657209002.img');return{指针=1,宽度=102,高度=17}
end
ui.Ux雌={游戏音效={按键音效1={播放=function()sounds=sounds+1 end}}}
ui.仓库窗口={可视=false};ui.仓库窗口.打开=function()opened=opened+1;ui.仓库窗口.可视=true end;ui.仓库窗口.关闭=function()closed=closed+1;ui.仓库窗口.可视=false end
ui.取鼠标左键按下=function()return down end;ui.取鼠标左键弹起=function()return up end
ui.引擎={取按键事件=function()return down end,取按键弹起=function()return up end}
load('button_register',ui)()
win.闭包=load('bind_control',ui);win.增加控件=load('add_control',ui)
local root=load('ui_root',ui);root();eq(#win.控件组,1);eq(controls['远程仓库按钮'].名称,'远程仓库按钮')
local c=win.控件组[1];eq(c.w,44);eq(c.h,22);eq(c.x,180);eq(c.y,20)
down=true;c.对象.更新(100,200);eq(opened,0)
down=false;up=true;c.对象.更新(100,200);eq(opened,1);eq(sounds,1)
up=false;hit=false;down=true;c.对象.更新(0,0);down=false;up=true;c.对象.更新(0,0);eq(opened,1)
up=false;hit=true
c.对象.显示(100,200,1,1,0,-1,1);assert(draws>=4)
root();eq(#win.控件组,1)
-- Native hover/pressed/released feedback keeps the hit rectangle fixed.
c.对象.更新(100,200);c.对象.显示(100,200,1,1,0,-1,1);eq(slice_y,219);eq(skin_color,-4671304);eq(text_y,204)
down=true;c.对象.更新(100,200);c.对象.显示(100,200,1,1,0,-1,1);eq(slice_y,220);eq(skin_color,-5723992);eq(text_y,205)
down=false;up=true;c.对象.更新(100,200);up=false;eq(closed,1);eq(ui.仓库窗口.可视,false)
for i=1,200 do c.对象.显示(100+i,200,1,1,0,-1,1)end
c.对象.销毁()
-- Anchor layout uses actual preceding control bounds, not a fixed screenshot.
win.控件组={{名称='选择框_背包2',x=70,y=30,w=45,h=28}}
root();local aligned=win.控件组[2];eq(aligned.x+aligned.w+11,235);eq(aligned.y+aligned.h/2,31);aligned.对象.销毁()
print('UI_V243_PASS',mode,count)
