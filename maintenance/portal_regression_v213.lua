local work,mode=arg[1],arg[2]or'normal'
if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end
local checks=0
local function eq(a,b,msg)checks=checks+1;assert(a==b,(msg or'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function near(a,b,msg)checks=checks+1;assert(math.abs(a-b)<1e-8,msg or'near')end
local function load(name,env)local f=assert(loadfile(work..'/'..name..'.ljbc'));setfenv(f,env or _G);return f end
local function noop()end
local routes=assert(loadfile(work..'/routes.lua'))()
local function make(version,points,width,height,font_issue)
 width,height=width or 450,height or 300
 local draw,texts={},{};local measurements,fonts=0,0;local events={};local zoom,scrollx,scrolly=1,0,0
 local E={['游戏素材组']={},['渲染任务组']={},['渲染工作组']={}}
 local maze={ID1373=0,ID1374=0,ID1375=0,ID1376=0}
 local config={['地图迷阵']=maze}
 local U={['地图名称']='潘夜村落',['版本选择']='来世续缘',['胚子考虑']=function()return config end}
 local hero={id=1,['地图坐标']={x=0,y=0},['地图格子']={x=0,y=0},['锚点x']=0,['锚点y']=0,['方向']=1}
 local env={type=type,tonumber=tonumber,tostring=tostring,pairs=pairs,ipairs=ipairs,unpack=unpack,math=math,string=string,table=table,setmetatable=setmetatable,['Ae冻集']=E,['Ux雌']=U,['FXru胃啪']=hero,['L常量']={['混合_默认']=0},Sys={get=function()return nil end}}
 local function sprite()
  local color=-1
  return{['置颜色']=function(c)color=c end,['置中心点']=noop,['置混合模式']=noop,['置显示区域']=noop,['重置图片']=noop,
  ['显示']=function(x,y)draw[#draw+1]={x=x,y=y,c=color}end,['显示_高级']=function(x,y,...)draw[#draw+1]={x=x,y=y,c=color}end}
 end
 local function chars(s)
  local width,maxwidth,lines,i=0,0,1,1
  while i<=#s do local b=s:byte(i);if b==10 then maxwidth=math.max(maxwidth,width);width=0;lines=lines+1;i=i+1 else width=width+(b>=128 and 9 or 5);i=i+(b>=128 and 2 or 1)end end
  return math.max(maxwidth,width),lines*12
 end
 local rawfont={['取宽度']=function(s)measurements=measurements+1;return(chars(s))end,['取高度']=function(s)local _,h=chars(s);return h end,
 ['显示']=function(x,y,s,c,outline,edge)texts[#texts+1]={x=x,y=y,text=s,color=c,outline=outline,edge=edge,w=chars(s),h=select(2,chars(s))}end}
 env.__Res=function(kind,address)eq(kind,2);eq(address,'-553833251.img');fonts=fonts+1;if font_issue=='nil'then return nil elseif font_issue=='invalid'then return{} elseif font_issue=='throw'then error('font load failure')end;return rawfont end
 local native_engine={['创建精灵']=sprite,['创建渲染区']=function()return{}end,['取渲染区纹理']=function()return{}end,['销毁渲染区']=noop,['渲染开始']=noop,['清屏']=noop,['渲染结束']=noop,
 ['创建包围盒']=function(l,t,r,b)return{['检测_点']=function(x,y)return x>=l and y>=t and x<=r and y<=b end}end,
 ['取画面坐标']=function()return scrollx,scrolly end,['销毁图片']=noop}
 local G={['插件挂接_外形框']=noop,['地图信息']={['列数']=width,['行数']=height,['宽度']=width,['高度']=height},['取事件组']=function()return events end,['错误']=function(e)error(e)end}
 env['Gly独']=G
 local S={['L窗口_类']=function()return{}end,['Gly独_类']=function()return G end,['FXru胃啪_类']=function()return hero end,['CGgw椅诿_类']=function()return{}end}
 local host={type=type,tonumber=tonumber,tostring=tostring,pairs=pairs,ipairs=ipairs,unpack=unpack,math=math,string=string,table=table,os=os,bit=require('bit'),setmetatable=setmetatable,setfenv=setfenv,loadstring=loadstring,
 ['Ae冻集']=E,['Ae冻']=U,['核心']={},['L常量']=env['L常量'],Sys=env.Sys,__Res=env.__Res,EM_引擎=function()return native_engine end,['L窗口']={},['L插件']={map=load('map_'..version)}}
 -- Original finite table extensions used by the host, not extra plugin exports.
 local host_table={};for k,v in pairs(table)do host_table[k]=v end
 host_table.insert_=table.insert;host_table.remove_=table.remove;host.table=host_table
 local factory=load('event_engine_factory',host);debug.setupvalue(factory,1,S);S['L引擎_类']=factory
 local install=load('plugin_install',host);debug.setupvalue(install,1,S);install()
 env=S.pl_setting
 eq(env['引擎'],native_engine,'actual EM engine substituted for plugin')
 eq(env['引擎']['创建文字'],nil,'event font factory unavailable in native map plugin')
 eq(type(S.script_setting['引擎']['创建文字']),'function','event environment really has factory')
 eq(env.string.byte,nil,'restricted plugin string exports lack byte')
 eq(env.pcall,nil);eq(env._G,nil)
 eq(getfenv(host['L插件'].map),env,'actual installer binds plugin environment')
 load('font_registration',env)()
 local frame={x=0,y=0,w=width,h=height,['可视']=true,['父窗口']={x=0,y=0,['可视']=true}}
 local public=host['L插件'].map(frame,nil)
 local _,owner=debug.getupvalue(public['附加事件标识'],1)
 public['设置地图图片']({['指针']=1,['宽度']=width,['高度']=height})
 owner['X比例']=1;owner['Y比例']=1
 local function add(id,x,y,kind,visible)
  local obj={id=id,['地图坐标']={x=x,y=y},['地图格子']={x=x,y=y},['锚点x']=0,['锚点y']=0,['所属阵营']='中立',['资源动画']={},['属性']={hp=100,['可视']=true},['可视']=visible~=false}
  events[#events+1]=obj
  if kind~=false then public['附加事件标识'](id,kind or'地图标识_传送')end
  return obj
 end
 for _,p in ipairs(points or{})do add(unpack(p))end
 return {owner=owner,public=public,U=U,maze=maze,config=config,texts=texts,draw=draw,events=events,add=add,env=env,
 render=function()for i=#texts,1,-1 do texts[i]=nil end;for i=#draw,1,-1 do draw[i]=nil end;owner.render_obj.render();public['显示']()end,
 move=function(x,y,z)scrollx,scrolly=x,y;owner['X比例']=z or 1;owner['Y比例']=z or 1 end,
 fontMode=function(value)font_issue=value end,stats=function()return measurements,fonts end}
end
-- Reproduce the uploaded first error and the subsequent partial-state cascade.
do
 local s=make('broken',{{1047,100,100}})
 local ok,err=pcall(s.render);eq(ok,false);eq(err:find('创建文字',1,true)~=nil,true,'v212 exact missing font API')
 local state=s.owner.__gm_portal_labels_v212;eq(type(state),'table');eq(state.resolve,nil)
 ok,err=pcall(s.render);eq(ok,false);eq(err:find('resolve',1,true)~=nil,true,'v212 persistent half-state cascade')
end
-- A missing/invalid optional font disables labels once, without losing marker draws.
for _,issue in ipairs({'nil','invalid'})do
 local s=make('new',{{1047,100,100}},nil,nil,issue)
 s.render();eq(#s.texts,0);eq(s.owner.__gm_portal_labels_v212.disabled,true)
 local _,n=s.stats();s.render();eq(select(2,s.stats()),n,'no repeated failed font loading');eq(#s.draw>0,true)
end
-- Genuine resource loader errors propagate and cannot publish half-initialized state.
do
 local s=make('new',{{1047,100,100}},nil,nil,'throw');local ok,err=pcall(s.render)
 eq(ok,false);eq(err:find('font load failure',1,true)~=nil,true);eq(s.owner.__gm_portal_labels_v212,nil,'atomic initialization')
 s.fontMode(nil);s.render();eq(#s.texts,1)
end
-- Full original constructor/render/marker/font path, not a hand-drawn map.
do
 local points={{1047,100,100},{1048,240,120},{1053,350,180}}
 local old,new=make('old',points),make('new',points)
 old.render();new.render();eq(#old.texts,0);eq(#new.texts,3)
 eq(#old.draw,#new.draw,'all original marker draws retained')
 for i,p in ipairs(old.draw)do eq(p.x,new.draw[i].x);eq(p.y,new.draw[i].y);eq(p.c,new.draw[i].c,'original palette')end
 eq(new.texts[1].text,routes[1047]);eq(new.texts[1].y<100,true,'above when room permits')
 for _,t in ipairs(new.texts)do eq(t.color,-1);eq(t.outline,true);eq(t.edge,0xff000000)end
end
local function bounds(s,w,h)
 for _,t in ipairs(s.texts)do eq(t.x>=4 and t.y>=20 and t.x+t.w<=w-4 and t.y+t.h<=h-18,true,'label stays inside reserved map bounds')end
 for i,a in ipairs(s.texts)do for j=1,i-1 do local b=s.texts[j];eq(a.x+a.w<=b.x or b.x+b.w<=a.x or a.y+a.h<=b.y or b.y+b.h<=a.y,true,'labels do not overlap in layout fixture')end end
end
for _,points in ipairs({{{1047,4,4}},{{1047,445,4}},{{1047,4,295}},{{1047,445,295}},{{1047,210,100},{1048,212,100},{1053,214,100},{1520,216,100}}})do
 local s=make('new',points);s.render();eq(#s.texts,#points);bounds(s,450,300)
end
-- Native zoom/pan coordinates and narrow/large view layouts.
do
 local s=make('new',{{1047,150,100}});s.move(20,-10,1.5);s.render()
 local entry=s.owner.__gm_portal_labels_v212.queue[1]
 near(entry.x,245,'label follows zoom/pan x');near(entry.y,140,'label follows zoom/pan y');bounds(s,450,300)
 local narrow=make('new',{{1264,25,70}},50,150);narrow.render();eq(#narrow.texts,1);eq(narrow.texts[1].text:find('\n',1,true)~=nil,true,'long label wraps in narrow view');bounds(narrow,50,150)
 local large=make('new',{{1047,400,300}},800,600);large.render();bounds(large,800,600)
end
-- Hidden/outside/non-portal objects and duplicate attachment don't add labels.
do
 local s=make('new',{{1047,-100,100},{1048,120,120,'地图标识_传送',false}})
 s.add(1053,220,120,{['指针']=1,['宽度']=1,['高度']=1});s.render();eq(#s.texts,0)
 local event=s.add(1047,220,120);s.public['附加事件标识'](1047,'地图标识_传送');s.render();eq(#s.texts,1,'one label per exit')
 s.owner['外形框对象']['父窗口']['可视']=false;s.render();eq(#s.texts,0,'closed map draws no labels')
end
-- Known fixed destinations compared against the REAL original transfer script.
local function actual_destination(id,maze)
 local target;local config={['运送物资']={0},['地图迷阵']=maze or {ID1373=0,ID1374=0,ID1375=0,ID1376=0}}
 local U={['版本选择']='来世续缘',['胚子考虑']=function()return config end,['啾啾啵啵']=function()return{['任务']={['魔灵神主']=true}}end,['窗口相关']={['地图坐标']=function(x,y,name)target=name end,['随机传送']=noop}}
 local env={['Ux雌']=U,['物品格子18']={},['FXru胃啪']={},['Gly独']={}}
 local f=load('transfer',env);debug.setupvalue(f,1,{id=id});f();return target
end
local counted=0
for id,name in pairs(routes)do
 local s=make('new',{{id,220,120}});s.render();eq(#s.texts,1,'all 99 registered portal IDs have a label')
 if name~='@maze'and name~='@otherworld'then eq(s.texts[1].text,actual_destination(id),'actual fixed transfer destination '..id)end
 counted=counted+1
end
eq(counted,99)
-- Dynamic maze prediction must NOT advance the saved counters while drawing.
for _,values in ipairs({{0,0,0,0},{0,1,1,1},{1,1,1,1},{2,0,0,0},{0,2,0,0},{0,0,2,0},{0,0,0,2}})do
 for id=1373,1376 do
  local s=make('new',{{id,220,120}});s.U['地图名称']='魔灵迷阵'
  for i=1,4 do s.maze['ID'..(1372+i)]=values[i]end
  s.render()
  for i=1,4 do eq(s.maze['ID'..(1372+i)],values[i],'UI must not mutate maze')end
  local copy={};for k,v in pairs(s.maze)do copy[k]=v end
  local expected=actual_destination(id,copy);if expected==0 then expected='魔灵迷阵'end
  eq(s.texts[1].text,expected,'read-only prediction matches real post-increment rule')
 end
end
-- Temporary doors: original death-spawn block, actual marker-init callback,
-- full original dialog/entry actions, status expiry and map-change cleanup block.
-- Event movement, HP bridge, clock trigger, UI/lighting are finite engine boundaries.
for _,case in ipairs({{2,1329,0.5},{8,1330,1},{1,1331,2}})do
 local roll,id,multiplier=unpack(case)
 local s=make('new',{});local big=make('new',{});big.U['胚子考虑']=function()return s.config end;s.U['小地图']=s.public;s.U['大地图']=big.public
 local spawned,selected,teleported,closed=0,nil,nil,0
 local obj
 local function hostenv()
  return {['Ux雌']=s.U,['FXru胃啪']={['地图格子']={x=40,y=50},['瞬移']=function(x,y,name)teleported=name end},
   ['小图窗口']={},['大图窗口']={},['无图窗口']={},['无地图标签']={},['对话窗口']={['关闭']=function()closed=closed+1 end,['对话']=function(...)selected=select(5,...)end},
   ['Gly独']={['取随机数']=function(lo,hi)if hi==10 then return roll end;return 1 end,['事件对象']=function(query)eq(query,id);return obj end}}
 end
 s.U['窗口相关']={['对话窗口']=noop,['经验倍率']=function(x1,x2,y1,y2,ident,n)
  spawned=spawned+1;eq(ident,id);eq(n,1);eq(x1,34);eq(x2,46);eq(y1,44);eq(y2,56)
  obj=s.add(id,220,120,false);big.events[1]=obj
  local callback=load('door_callback'..id,{['Ux雌']=s.U});debug.setupvalue(callback,1,{id=id});callback()
 end}
 s.U['游戏音效']={['瞬移命中']={['播放']=noop}}
 s.config['公寓']={['设置全局亮度']=noop}
 local spawn=load('door_spawn',hostenv());debug.setupvalue(spawn,1,{['对象']={['重复刷新间隔']=30,['地图格子']={x=40,y=50},['属性']={['附加']={['静验']=100,['等级']=16}}}})
 spawn();eq(spawned,1,'original spawn selects expected temporary event');eq(s.config['异界之门刷新'],id)
 s.render();big.render();eq(#s.texts,1);eq(#big.texts,1)
 eq(s.texts[1].text,'异界潘夜村落');eq(big.texts[1].text,s.texts[1].text)
 local script=load('door_script'..id,hostenv())();script.Main();eq(type(selected),'string')
 local action=assert(selected:match('@(进入异界%d)@'),'original dialog offers expected entry')
 script[action]();eq(teleported,'潘夜村落','actual door enters the current map layer');eq(s.config['进入异界'],multiplier)
 -- Rendering must not execute any teleport action or modify layer multiplier.
 s.render();eq(s.config['进入异界'],multiplier);eq(spawned,1)
 -- Original expiry sets public HP=0 and clears the active door; bridge HP to
 -- native map attribute hp exactly as the engine object does, with finite table.
 local expire=load('door_expire',hostenv());debug.setupvalue(expire,1,{id='异界之门'});obj.HP=100
 expire(id);eq(obj.HP,0);eq(s.config['异界之门刷新'],nil)
 obj['属性'].hp=obj.HP;s.render();big.render();eq(#s.texts,0);eq(#big.texts,0)
 -- Same ID reused normally must recover the ship name instead of a stale label.
 obj['属性'].hp=100;s.render();eq(s.texts[1].text,'神舰')
 s.config['异界之门刷新']=id;s.config['进入异界']=nil;script.Main();eq(type(selected),'string')
 local clear=load('map_door_clear',{['Ux雌']=s.U});clear();eq(s.config['异界之门刷新'],nil)
 s.events[1]=nil;big.events[1]=nil;s.render();big.render();eq(#s.texts,0);eq(#big.texts,0)
end
-- All four original dialog factories use the same active-door rule, including
-- invalid active state (no entry button, so no guessed destination is printed).
for _,id in ipairs({1301,1329,1330,1331})do
 local s=make('new',{{id,220,120}});local dialog
 local env={['Ux雌']=s.U,['对话窗口']={['对话']=function(...)dialog=select(5,...)end}}
 s.U['窗口相关']={['对话窗口']=noop};local script=load('door_script'..id,env)()
 script.Main();s.render();eq(dialog:find('进入神舰',1,true)~=nil,true);eq(s.texts[1].text,'神舰')
 for _,door in ipairs({1329,1330,1331})do
  s.config['异界之门刷新']=door;script.Main();s.render();eq(dialog:find('进入异界',1,true)~=nil,true);eq(s.texts[1].text,'异界潘夜村落')
 end
 s.config['异界之门刷新']=999;dialog=nil;script.Main();s.render();eq(dialog,nil);eq(#s.texts,0)
 s.config['异界之门刷新']=nil;s.render();eq(s.texts[1].text,'神舰')
end
-- 200 representative renders reuse measurements/font and clear stale map data.
do
 local s=make('new',{{1047,200,100},{1048,210,100}});s.render();local measurements,fonts=s.stats()
 for i=1,200 do s.move(i%10,0,1);s.render();eq(#s.texts,2)end
 eq(s.stats(),measurements,'no repeated fixed-name measurement');local _,n=s.stats();eq(n,fonts,'font loaded once')
 s.U['地图名称']='骷髅洞穴';s.events[2]=nil;s.render();eq(#s.texts,1)
 local state=s.owner.__gm_portal_labels_v212;local n=0;for _ in pairs(state.cache)do n=n+1 end;eq(n,1,'old map labels removed')
end
print('PORTALS_V213_PASS',mode,checks,'99 exit IDs; actual plugin installer; v212 missing-API/cascade reproduction; native map/raw font; temporary spawn/dialog/entry/expiry/clear; 200 frames; finite engine boundaries, no Windows client')
