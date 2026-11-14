local work,mode=arg[1],arg[2]or'normal'
if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end
local checks=0
local function eq(a,b,label)checks=checks+1;assert(a==b,(label or'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function load(n,e)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,e or _G);return f end
local function bind(n,s,e)local f=load(n,e);debug.setupvalue(f,1,s);return f end
local function copy(x)if type(x)~='table'then return x end;if rawget(x,'__p')~=nil then x=x()end;local y={};for k,v in pairs(x)do y[k]=copy(v)end;return y end
local GOLD,EDGE=4294946098,4283051026
local function color(x)return x%4294967296 end
-- Actual UI initialization, difficulty persistence and native title setter.
for _,story in ipairs({'来世续缘','前尘忆梦'})do
 for difficulty=0,2 do
  local state={};local calls=0;local engine={['置窗口标题']=function(_,title)state.title=title end,['隐藏鼠标']=function()end}
  local set=bind('window_setter',{}, {['Ae冻集']=state,['引擎']=engine})
  local G=setmetatable({['鼠标指针动画']=function()end},{__newindex=set})
  local U={['粑粑麻麻']=function(v)if v~=nil then state.internal=v;return end;calls=calls+1;return -8.8908208316175e-215 end,
   ['游戏音效']={['窗口音效']={['播放']=function()end},['按键音效2']={['播放']=function()end}}}
  local env={tonumber=tonumber,['Ux雌']=U,['Gly独']=G,['读配置项']=function(_,_,key)if key=='Ver'then return story end;return difficulty end,['写配置项']=function(_,_,key,v)eq(key,'GuimengDifficulty');state.saved=v end}
  for _,key in ipairs({'选择框4','选择框5','选择框6','启动图片','来世续缘','前尘忆梦','动画框4','登录按钮','登录按钮2','版本号标签'})do env[key]={['播放']=function()end}end
  load('ui',env)();eq(env['版本号标签']['标题'],'魔改版 1.203');eq(state.internal,story=='来世续缘'and 226 or 1)
  local levels={[0]='普通',[1]='简单',[2]='困难'}
  eq(state.title,'归梦 ['..story..'-'..levels[difficulty]..'] 魔改版 1.203');eq(calls,0,'display never divides internal version');eq(state.saved,difficulty)
 end
end
-- Real tooltip and generator, retaining native proxy/template name lookup.
local config=load('config')();local raw=assert(loadfile(work..'/template.lua'))();local base=copy(raw);base['附加']={['等级']=40,['商店']='防具店'};base['属性']={}
for k in pairs(config['极品数值'])do base[k]=base[k]or 0;base['属性'][k]=base[k]end
for _,k in ipairs({'身体舒适','物品腕力','物品重量','穿戴肩力','武器腕力'})do base['属性'][k]=0 end
local S={};S['数据保护']=bind('proxy',S);S['游戏道具组']=S['数据保护']({[base['名称']]=base},true)
local info=bind('item_info',S,{table={copy=copy},pairs=pairs})
local U={['独角兽下']=function()return config end,['胚子考虑']=function()return{['装备操作']=0}end,['啾啾啵啵']=function()return{['职业']='战士',['等级']=100,['性别']='男',['人物选择']=1}end}
local env={type=type,tonumber=tonumber,tostring=tostring,pairs=pairs,ipairs=ipairs,math=math,string=string,table={copy=copy,remove=table.remove},['Ux雌']=U,['Gly独']={['取道具信息_名称']=info,['取随机数']=function(a,b)return math.random(a,b)end},['物品格子18']={},['商店窗口']={['可视']=false},['商店窗口2']={['可视']=false},['格式化数值']=tostring,['L常量']={},['FXru胃啪']={['职业']='战士',['性别']='男',['等级']=100}}
local old,new=load('tip_old',env),load('tip_new',env);local go,gn=load('gen_old',env),load('gen_new',env)
local seven
for tier=3,7 do
 local a=copy(info(base['名称']));a['附加']['条数']=tier;a['最小防御']=2;a['最大防御']=5;a['移动速度']=3;a['身体舒适']=1;a['防暗元素']=3
 local previous,current=old(a,1,32),new(a,1,32)
 if tier<7 then eq(current,previous,'other qualities byte-identical')else
  local head=current:match('([^\n]+)');eq(head:find('宋_9_炭灰',1,true)~=nil,true,'same font as other qualities');eq(head:find('宋_9_鎏金',1,true),nil,'no private outline');eq(head:find('-21198',1,true)~=nil,true,'bright orange name')
  eq(current:match('\n(.*)'),previous:match('\n(.*)'),'all attribute rows/comfort unchanged');seven=current
 end
 math.randomseed(200+tier);local x=copy(info(base['名称']));go(x,40,tier)
 math.randomseed(200+tier);local y=copy(info(base['名称']));gn(y,40,tier)
 local expected=tier==7 and GOLD or color(x['颜色值']);eq(color(y['颜色值']),expected)
 x['颜色值']=y['颜色值'];for k,v in pairs(x)do if type(v)~='table'then eq(y[k],v,'generation changes only seven name color')end end
end
-- Actual ground-name style setter: existing saved orange is overridden for
-- seven only; unrelated qualities and non-equipment keep original settings.
for _,outline in ipairs({false,true})do
 for tier=3,7 do
  local captured,oldcapture;local item={['分类']='装备',['附加']={['条数']=tier},['颜色值']=-26368}
  local function object(save)return{['物品']=item,['名称标签']={['置标题']=save},['显示内容']='测试装备',['显示宽度']=40,['显示高度']=12}end
  load('ground_old',{['Ae冻集']={['地面道具描边']=outline}})(object(function(...)oldcapture={...}end))
  load('ground_new',{['Ae冻集']={['地面道具描边']=outline}})(object(function(...)captured={...}end))
  if tier==7 then eq(color(captured[3]),GOLD);eq(captured[4],outline);eq(color(captured[5]),4280888360)else for i=1,7 do eq(captured[i],oldcapture[i],'other ground qualities')end end
 end
end
-- Font alias executes the existing native draw closure with all eight args.
local args;local basefont={tag='original', ['显示']=function(...)args={...};return 'draw',nil,27 end}
local fontenv={Q_文字=basefont,setmetatable=setmetatable,['Ae冻集']={['游戏素材组']={other={['地址']='other-font'}}},__Res=function()return basefont end,Sys={run=function()error('unregistered font')end}}
local getter=load('font_new',fontenv);local normal=load('font_old',fontenv)('宋_9_炭灰');local alias=getter('宋_9_鎏金')
local function draw(f,edge)
 local a,b,c=f['显示'](10,20,'item',-21198,true,0,1,0);eq(a,'draw');eq(b,nil);eq(c,27);eq(args[1],10);eq(args[2],20);eq(args[3],'item');eq(args[4],-21198);eq(args[5],true);eq(color(args[6]),edge);eq(args[7],1);eq(args[8],0);eq(f.tag,'original')
end
draw(normal,4280888360);draw(getter('宋_9_炭灰'),4280888360);draw(alias,EDGE);eq(getter('other'),basefont)
for i=1,200 do draw(i%2==0 and alias or getter('宋_9_炭灰'),i%2==0 and EDGE or 4280888360)end
-- The unchanged real rich-text parser recognizes the private font marker.
local function chars(s)local t={};local i=1;while i<=#s do local n=s:byte(i)>=128 and 2 or 1;t[#t+1]=s:sub(i,i+n-1);i=i+n end;return t end
local function split(s,sep)local t={};local at=1;while true do local a,b=s:find(sep,at,true);if not a then t[#t+1]=s:sub(at);return t end;t[#t+1]=s:sub(at,a-1);at=b+1 end end
local parser=load('parser',{type=type,tonumber=tonumber,string=string,table=table,['分割为字符组']=chars,['分割文本']=split,['Ae冻集']={['默认文字_间距']=0,['默认文字_行距']=0},['L常量']={['颜色_白']=-1,['颜色_黄']=-256}})
debug.setupvalue(parser,1,0);debug.setupvalue(parser,2,{{'W',-1}});debug.setupvalue(parser,3,{})
local parsed=parser(seven);local seen=false
local function walk(t)if type(t)~='table'then return end;for k,v in pairs(t)do if v=='宋_9_炭灰'then seen=true end;if type(v)=='table'then walk(v)end end end
walk(parsed);eq(seen,true,'real parser uses standard equipment font')
print('DISPLAY_V203_PASS',mode,checks)
