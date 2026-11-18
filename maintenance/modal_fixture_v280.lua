-- Finite UI primitives around the actual modal class registration/init/update.
return function(work,env)
 local ui={now=0,draws={}}
 local function noop()end
 local E=env.Ae冻集 or{};env.Ae冻集=E
 E.屏幕宽度=800;E.屏幕高度=600;E.鼠标_屏幕坐标={x=0,y=0}
 local engine=env.引擎 or{};env.引擎=engine
 engine.取运行时间=function()return ui.now end
 engine.取按键按下=function(_,key)return key=='enter'and ui.enter or false end
 engine.取按键事件=function()return false end
 env.L常量={键_回车='enter',键_鼠标左='mouse'}
 env.math=setmetatable({round=function(x)return math.floor(x+.5)end},{__index=math})
 env.丰富文本_解析=function(font,text,color)ui.parsed={font,text,color};return{},24,160 end
 env.Q_文字={}
 env.class=function()return{}end
 env.D2D_精灵={创建=function()return{置颜色=noop,显示_范围缩放=noop}end}
 env.D2D_包围盒={创建=function()return{置位置=noop,置宽高=noop,检测_点=function()return false end,显示=noop}end}
 local sys=env.Sys or{};env.Sys=sys;local oldget=sys.get
 sys.get=function(key,...)
  if key=='win_tip'then return function()return{更新提示=noop,显示=function(...)ui.draws[#ui.draws+1]={...}end}end end
  if key=='win_button'then return function()
   local b={}
   b.置位置=noop
   b.更新=function()b.clicked=ui.click==b end
   b.取是否单击=function()local hit=b.clicked;b.clicked=false;return hit end
   b.是否有焦点=function()return false end
   b.显示=function()ui.draws[#ui.draws+1]=b end
   return b
  end end
  if oldget then return oldget(key,...)end
  error('unexpected modal Sys.get '..tostring(key))
 end
 local register=assert(loadfile(work..'/modal_class.ljbc'));setfenv(register,env);register()
 local cls=env.类_信息提示框;ui.box=setmetatable({},{__index=cls})
 cls.初始化(ui.box,{},{宽度=100,高度=24},{宽度=100,高度=24},false)
 env.Q_提示框=ui.box
 function ui.update(time,kind)
  ui.now=time;ui.enter=kind=='enter';ui.click=kind=='click'and ui.box.确定_按钮 or kind=='cancel'and ui.box.取消_按钮 or nil
  ui.box:更新();ui.enter=false;ui.click=nil
 end
 function ui.show(text,kind,yes,no)ui.box:提示(kind or'确定',text,-1,yes,no)end
 return ui
end
