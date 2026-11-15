local work,mode=arg[1],arg[2]
if mode=='hot' then require('jit.opt').start('hotloop=1','hotexit=1') end
local count=0
local function eq(a,b,label) count=count+1;assert(a==b,(label or'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function load(n,env)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,env or _G);return f end
local function bind(n,S,env)local f=load(n,env);debug.setupvalue(f,1,S);return f end
local function sale(label,plot,n,wrong,ctrl,forbidden,guild)
 local id=plot=='前尘忆梦'and 8 or 32
 local item={名称='金创药_小',显示名='金创药(小)',数量=n,价格=101,附加={商店='药店'},禁止出售=forbidden or false}
 local slot={道具=item};local removed=0;slot.重置道具=function(v)eq(v,nil);removed=removed+1;slot.道具=nil end
 local money=0;local tips=0;local state={商店类型=wrong and'杂货店'or'药店',行会选中={货通百铺=guild and true or nil}}
 local env=setmetatable({商店窗口={可视=true},商店窗口2={可视=true},佣兵窗口={可视=false},行会仓库={可视=false},仓库窗口={可视=false},L常量={键_SHIFT=1,键_CTRL=2,颜色_红=-1}},{__index=_G})
 env.Gly独={取按键状态=function(k)return k==2 and ctrl end,从ID取格子=function(i)eq(i,id);return slot end}
 env.Ux雌={版本选择=plot,呦西鸽子=function()return{[id]=slot}end,胚子考虑=function()return state end,托管显示={屏幕提示=function()tips=tips+1 end},开挖机的={孔爱琴泥=function()end},窗口相关={界面切换=function(v)money=money+v end,王二狗水=function()end,信息窗口=function()tips=tips+1 end}}
 local event=load('event_'..label,env);local ok,result=pcall(event,3,id);assert(ok,label..' '..plot..' '..n..' '..tostring(wrong)..' '..tostring(ctrl)..': '..tostring(result));eq(result,true,'event '..label..' '..plot..' '..n..' '..tostring(wrong)..' '..tostring(ctrl))
 if forbidden then eq(money,0);eq(removed,0);eq(slot.道具,item);return end
 if not ctrl then eq(money,0);eq(removed,0);assert(env.Ux雌.信息按钮);env.Ux雌.信息按钮() end
 local unit=math.ceil(101/2)
 if wrong and not guild then unit=math.ceil(101/2*.8) end
 local expected=unit*n
 if label=='old' and (plot~='前尘忆梦' or wrong) then expected=unit end
 eq(money,expected,'sale '..label..' '..plot);eq(removed,1);eq(slot.道具,nil)
 return money
end
for _,plot in ipairs{'前尘忆梦','来世续缘'}do
 for _,n in ipairs{1,2,192,999}do
  for _,wrong in ipairs{false,true}do for _,ctrl in ipairs{false,true}do sale('new',plot,n,wrong,ctrl)end end
 end
 sale('new',plot,20,false,true,true)
 eq(sale('old',plot,192,true,true),math.ceil(101/2*.8))
end
sale('new','来世续缘',192,true,true,false,true)
for i=1,200 do sale('new','来世续缘',192,true,true)end
-- Existing bounded stack validators now accept return scrolls, still reject malformed counts.
for _,label in ipairs{'old','new'}do
 local v=load('validator_'..label)
 eq(v({道具={名称='回城卷',可叠加=true,数量=192}}),label=='new')
 for _,n in ipairs{0,-1,1000,1.5,'2',false}do eq(v({道具={名称='回城卷',可叠加=true,数量=n}}),false)end
 eq(v({道具={名称='金创药_小',可叠加=true,数量=192}}),true)
 eq(v({道具={名称='未知',可叠加=true,数量=2}}),false)
end
local cfg=assert(loadfile(work..'/scroll.lua'))()
local function copy(t)local r={};for k,v in pairs(t)do r[k]=type(v)=='table'and copy(v)or v end;return r end
local T={copy=copy};setmetatable(T,{__index=table})
local table_env=setmetatable({table=T},{__index=_G});load('table_register',table_env)()
local S={游戏道具组={回城卷=cfg},包裹物品组={}}
local proxy=bind('proxy',S);S.数据保护=proxy;S.游戏道具组=proxy(S.游戏道具组,true)
local info=bind('item_info',S,setmetatable({table=T},{__index=_G}))('回城卷')
eq(info.可叠加,true);eq(info.附加.叠加上限,999)
local install=load('stack_install',table_env);local mergeS={包裹物品组={},增加物品=function()return false end,格式化道具属性=function()return ''end,更新道具属性=function()end}
install(mergeS);assert(type(mergeS.__gm_potion_merge_v158)=='function')
-- Run the original native sorting merger with two return-scroll stacks.
local first=copy(cfg);first.数量=990
local second=copy(cfg);second.数量=20
local bag={[32]={道具=first},[33]={道具=second}}
local rows={{id=32,数量=990},{id=33,数量=20}}
mergeS.__gm_potion_sort_v158(rows,bag,{32,33})
eq(first.数量,999);eq(second.数量,11);eq(rows[1].数量,999);eq(rows[2].数量,11)
-- The original consume method decrements one scroll and clears only the last.
local consume_env=setmetatable({Q_鼠标={格子标识=0},Sys={run=function()end}},{__index=_G})
local consume=load('consume_native',consume_env)
local data=copy(cfg);data.数量=2;data.冷却时间=0;data.任务关联=false
local slots={[32]={道具=data}};local control={格子组=slots,标识=32}
consume(control);eq(data.数量,1);eq(slots[32].道具,data)
consume(control);eq(slots[32].道具,nil)
-- Native window lookup -> real add_control/binding -> real image-button factory.
-- Low-level image, rectangle and font operations are finite engine substitutes.
local hit=true;local down,up=false,false
local registry={};local controls={};local opened,sounds,draws=0,0,0
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
ui.Q__={创建精灵=sprite,创建包围盒=function()return{检测_点=function()return true end,置位置=noop,显示=noop}end}
ui.D2D_精灵={创建=sprite}
local font={取宽度=function(s)return #s/2*12 end,取高度=function()return 12 end,显示=function(x,y,s,a,c,o)eq(s,'仓库');eq(a,0);draws=draws+1 end}
ui.__Res=function(kind,path)
 if kind==2 then eq(path,'400132927.img');return font end
 eq(path,'-1657209002.img');return{指针=1,宽度=102,高度=17}
end
ui.Ux雌={游戏音效={按键音效1={播放=function()sounds=sounds+1 end}}}
ui.仓库窗口={打开=function()opened=opened+1 end}
ui.取鼠标左键按下=function()return down end;ui.取鼠标左键弹起=function()return up end
ui.引擎={取按键事件=function()return down end,取按键弹起=function()return up end}
load('button_register',ui)()
win.闭包=load('bind_control',ui);win.增加控件=load('add_control',ui)
local root=load('ui_root',ui);root();eq(#win.控件组,1);eq(controls['远程仓库按钮'].名称,'远程仓库按钮')
local c=win.控件组[1];eq(c.w,42);eq(c.h,17);eq(c.x+c.w,230);eq(c.y,20)
down=true;c.对象.更新(100,200);eq(opened,0)
down=false;up=true;c.对象.更新(100,200);eq(opened,1);eq(sounds,1)
up=false;hit=false;down=true;c.对象.更新(0,0);down=false;up=true;c.对象.更新(0,0);eq(opened,1)
up=false;hit=true
c.对象.显示(100,200,1,1,0,-1,1);assert(draws>=4)
root();eq(#win.控件组,1)
for i=1,200 do c.对象.显示(100+i,200,1,1,0,-1,1)end
c.对象.销毁()
print('INVENTORY_V219_PASS',mode,count)
