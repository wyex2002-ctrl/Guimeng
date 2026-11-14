local work,version,mode=arg[1],arg[2],arg[3]
if mode=='cold'then jit.off()else jit.on();if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end end
local events={};local tick=0
local function op(name)return function(...)events[#events+1]=name end end
local env
local function load(n)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,env);return f end
local E={['游戏进度']=1,['逻辑暂停']=0,['屏幕焦点']=true,['最后按键']=0,['界面可视']=true,['游戏暂停']=false,
 ['屏幕震动时间']=0,['屏幕宽度']=800,['屏幕高度']=600,['屏幕缩放']=1,['画面偏移']={x=0,y=0},
 ['鼠标_屏幕坐标']={x=0,y=0},['鼠标_地图坐标']={x=0,y=0},['鼠标_地图格子']={x=0,y=0},['遮罩信息']={['启动']=false}}
local S={Game_State=1,['控制对象']={},['Hero']={['更新']=op('hero.update'),['属性']={hp=100}},['script_setting']={['Ux雌']={},['Gly独']={}}}
for _,name in ipairs({'游戏技能组','道具CD信息组','屏幕特效组','屏幕锁链组','屏幕粒子组','屏幕事件组','屏幕子弹组','界面_窗口_数组','屏幕提示组','屏幕气泡组','Plug','动画精灵组','剧情对话框','剧情资源表','time_table','创建窗口组'})do S[name]={}end
for _,name in ipairs({'取鼠标所在窗口','状态图标显示控制','状态图标显示提示','焦点触发'})do S[name]=op(name)end
S.temp_spr={['置混合模式']=op('composite.blend'),['显示_范围缩放']=op('composite.draw')}
S['banner']={show=op('banner')};S['黑边特效']={show=op('letterbox')}
S.get=function(key)if key=='item_box'then return{}end end
S.Hero['焦点触发']=op('hero.focus')
S['中间提示组']={};S['中间遮罩']={['可视']=false};S['气泡提示组']={}
for i=0,9 do S['气泡提示组'][i]={['可视']=false}end
env={['Ae冻']={},['Ae冻集']=E,dt=0.016,Sys=S,['丰富文本_动画更新显示']=op('richtext'),['Q_公用动画库']={},['Q_提示框']={['可视']=false},
 ['Q_鼠标']={},['Q_地图']={['更新']=op('map.update'),['显示']=function()op('map.draw')();tick=tick+0.300 end},['Q_文字']={['显示']=op('text')},
 ['引擎']={['取按键按下']=function()return false end,['取按键弹起']=function()return false end,['调整屏幕']=op('camera')},
 ['L常量']={},['核心']={http_url_get=function()return {['总数']=0}end}}

setmetatable(env,{__index=function(_,k)if k=='__gm_bulk_sale_tick_v177'or k=='__gm_info_tick_v137'then return nil end;if _G[k]~=nil then return _G[k]end;error('MISSING GLOBAL '..tostring(k))end})
env._G=env;env.loadstring=function(src)local f,e=loadstring(src);if f then setfenv(f,env)end;return f,e end
local draws=0;local last;local sizes=0;local rebuilds=0
local function noop()end
local spr={['置颜色']=noop,['置混合模式']=noop,['显示']=noop,['显示_范围缩放']=noop}
env.type=type;env.tonumber=tonumber;env.tostring=tostring;env.rawget=rawget;env.math=math;env.table=table;env.pairs=pairs;env.ipairs=ipairs;env.setmetatable=setmetatable
E['渲染工作组']={{rebuild=function()rebuilds=rebuilds+1 end}}
env['引擎']['置窗口大小']=function(_,w,h)assert(w>=1024 and h>=600);sizes=sizes+1 end
env['引擎']['取图片宽度']=function()return 1 end;env['引擎']['取图片高度']=function()return 1 end
env['D2D_精灵']={['创建']=function()return spr end};env['D2D_包围盒']={['创建']=function()return{}end}
env['L常量']['颜色_全透明']=0;env['L常量']['混合_默认']=0
local ally={['属性']={['当前生命值']=50,['最大生命值']=100}}
env['Ae冻']['佣兵对象']=ally
S.get=function(k)if k=='Game_State'then return S.Game_State elseif k=='item_box'then return{}else error('unexpected Sys.get '..tostring(k))end end
env['Q_文字']['显示']=function(x,y,text,align,color,edge)draws=draws+1;last={x,y,text,align,color,edge}end
env.SETA=function(c,a)return c end
-- Finite engine primitive: writes register instance methods, while class
-- descriptors do not expose those methods for reads. This is the boundary
-- that v204's transparent class mock failed to cover.
local classmethods
local class_reads=0
env.class=function()
 local methods={};classmethods=methods
 local meta={__index=methods,__lt=function(a,b)return a.id<b.id end}
 local descriptor={}
 return setmetatable(descriptor,{
  __newindex=function(_,k,v)methods[k]=v end,
  __index=function(_,k)class_reads=class_reads+1;return nil end,
  __call=function(_,...)local o=setmetatable({},meta);methods['初始化'](o,...);return o end})
end
load('class_'..version)()
local c=env['类_窗口_基础'];local a=c(564,'底部窗口',10,10,300,200,0,0,0,0,1,nil);local b=c(111,'其他窗口',10,10,300,200,0,0,0,0,1,nil)
a['可视']=true;b['可视']=true
S['界面_窗口_数组']={b,a}
if version=='new'then
 assert(classmethods.__gm_draw_merc_hp_v204==nil,'no class-field registration dependency')
 local name,helper=debug.getupvalue(classmethods['显示'],1)
 assert(name=='window_hp_overlay'and type(helper)=='function','helper must be captured lexically')
 collectgarbage('collect');local _,again=debug.getupvalue(classmethods['显示'],1);assert(again==helper,'helper lost after module closure returned')
end
local frame=load('frame_'..version);debug.setupvalue(frame,1,S);debug.setupvalue(frame,2,{})
local set=load('screen_setter');debug.setupvalue(set,1,S)
local G=setmetatable({},{__newindex=set});local U={['胚子考虑']=function()return{['无地图']=1}end,['游戏音效']={['按键音效1']={['播放']=noop}},['窗口相关']={}}
env['Gly独']=G;env['Ux雌']=U;env['物品格子18']={}
E['屏幕宽度']=1024;E['屏幕高度']=600
local label={['标题']='1024 * 600'};env['分辨率标签']=label
local layout=0
local function reflow()
 layout=layout+1;a['坐标']={x=E['屏幕宽度']-300,y=E['屏幕高度']-200}
 local hp={['名称']='佣兵血量进度条',x=10,y=20,w=100,['可视']=false}
 local other={['名称']='other',x=1,y=2,w=12,['可视']=false}
 a['控件组']=layout%2==0 and{other,hp}or{hp,other};a.ready=layout%2==0
end
local opened,closed=0,0
env['底部窗口']={['关闭']=function()closed=closed+1 end,['打开']=function()opened=opened+1;reflow()end}
for _,name in ipairs({'无图窗口','小图窗口','聊天窗口','快捷窗口'})do env[name]={['可视']=false,['关闭']=noop,['打开']=noop}end
U['窗口相关']['窗口开关']=noop;U['窗口相关']['大图窗口']=noop
local resolution=load('resolution');debug.setupvalue(resolution,1,U['窗口相关']);U['窗口相关']['系统窗口']=resolution
local button=load('button')()
local labels={'1280 * 700','全屏','1024 * 600'}
-- Include the initial state=0 frame, before a role or ally is restored.
S.Game_State=0;E['游戏进度']=0;env['Ae冻']['佣兵对象']=nil
for i=1,3 do frame()end
assert(draws==0,'startup must not draw ally HP');S.Game_State=1;E['游戏进度']=1;env['Ae冻']['佣兵对象']=ally

-- Actual UI callback -> actual public setter -> reflow -> complete native frame.
-- Repetition is one 200-frame scenario, not 200 multiplied by each boundary.
for i=1,200 do
 button.Main();assert(label['标题']==labels[(i-1)%3+1]);frame()
end
assert(draws==200,'HP_DRAW_MISMATCH: '..draws..' / 200')
assert(opened==200 and closed==200 and sizes>0 and sizes==rebuilds,'resolution chain not exercised')
assert(last[3]=='50','HP must still show current health');assert(last[1]==a['坐标'].x+60 and last[2]==math.max(0,a['坐标'].y+6),'HP position changed')
-- Optional overlay boundaries use the real registered complete display, no mocks.
local function checkdraw(expected,change)
 local before=draws;change();a['显示'](a);assert(draws==before+expected,'boundary draw count')
end
checkdraw(0,function()env['Ae冻']['佣兵对象']=nil end);env['Ae冻']['佣兵对象']=ally
checkdraw(0,function()a['可视']=false end);a['可视']=true
checkdraw(0,function()S.Game_State=0 end);S.Game_State=1
checkdraw(0,function()ally['属性']['当前生命值']=0/0 end);ally['属性']['当前生命值']=0
checkdraw(1,function()end);assert(last[3]=='0')
ally['属性']['当前生命值']=50
checkdraw(0,function()ally['属性']['最大生命值']=0 end);ally['属性']['最大生命值']=100
checkdraw(0,function()ally['属性']['当前生命值']=math.huge end);ally['属性']['当前生命值']=50
checkdraw(0,function()a['控件组']={}end);reflow()
checkdraw(1,function()end)
-- The overlay must not mutate valid input records or coordinates while drawing.
local controls=a['控件组'];local pos=a['坐标'];local x,y=pos.x,pos.y
checkdraw(1,function()end);assert(a['控件组']==controls and a['坐标']==pos and pos.x==x and pos.y==y)
-- Existing instances retain their helper if the module/class descriptor is reloaded.
load('class_'..version)();collectgarbage('collect');checkdraw(1,function()end)
local original=env['Q_文字']['显示'];local original_error={tag='renderer error'}
env['Q_文字']['显示']=function()error(original_error,0)end
local ok,err=pcall(a['显示'],a);assert(not ok and err==original_error,'normal rendering errors must propagate')
env['Q_文字']['显示']=original
assert(class_reads==0,'display must not read methods from the class descriptor')
print('RESOLUTION_V205_PASS',version,mode,'actual button/setter/class/init/display/native frame; 200 frames; no physical Windows device test')
