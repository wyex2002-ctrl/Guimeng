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
 local draw,texts,lines,paint={},{},{},{};local measurements,fonts,sprites,parses=0,0,0,0;local events={};local zoom,scrollx,scrolly=1,0,0
 local E={['地面道具描边']=true,['默认文字_间距']=0,['默认文字_行距']=0,['游戏素材组']={},['渲染任务组']={},['渲染工作组']={}}
 local maze={ID1373=0,ID1374=0,ID1375=0,ID1376=0}
 local config={['地图迷阵']=maze}
 local U={['地图名称']='潘夜村落',['版本选择']='来世续缘',['胚子考虑']=function()return config end}
 local hero={id=1,['地图坐标']={x=0,y=0},['地图格子']={x=0,y=0},['锚点x']=0,['锚点y']=0,['方向']=1}
 local env={type=type,tonumber=tonumber,tostring=tostring,pairs=pairs,ipairs=ipairs,unpack=unpack,math=math,string=string,table=table,setmetatable=setmetatable,['Ae冻集']=E,['Ux雌']=U,['FXru胃啪']=hero,['L常量']={['混合_默认']=0},Sys={get=function()return nil end}}
 local function rect(l,t,r,b)return{['检测_点']=function(x,y)return x>=l and y>=t and x<=r and y<=b end}end
 local primitive={
 ['创建']=function(tex,x,y,w,h)sprites=sprites+1;return{c=-1,w=w,h=h}end,
 ['置渲染色']=function(p,c)p.c=c end,['置参照点']=noop,['置混合模式']=noop,
 ['置渲染区域']=noop,['重置纹理']=noop,
 ['显示']=function(p,x,y)draw[#draw+1]={x=x,y=y,c=p.c}end,
 ['显示_高级']=function(p,x,y,angle,sx,sy)
  if p.c==0xffe0ffe0 then
   eq(p.w,1);eq(p.h,1);eq(sy,1);eq(sx>0,true)
   lines[#lines+1]={x=x,y=y,angle=angle,length=sx,color=p.c,x2=x+math.cos(angle)*sx,y2=y+math.sin(angle)*sx}
   paint[#paint+1]='line'
  else draw[#draw+1]={x=x,y=y,c=p.c}end
 end}
 local sprite=load('sprite_factory',{type=type,__Sprite=primitive,Q__={['创建包围盒']=rect},__ed_debug=error})
 local function chars(s)
  local width,maxwidth,lines,i=0,0,1,1
  while i<=#s do local b=s:byte(i);if b==10 then maxwidth=math.max(maxwidth,width);width=0;lines=lines+1;i=i+1 else width=width+(b>=128 and 9 or 5);i=i+(b>=128 and 2 or 1)end end
  return math.max(maxwidth,width),lines*12
 end
 local function font(address)
  local function capture(x,y,s,align,color,edge,spacing,line_spacing)
   paint[#paint+1]='text';texts[#texts+1]={x=x,y=y,text=s,color=color,align=align,edge=edge,spacing=spacing,line_spacing=line_spacing,font=address,w=chars(s),h=select(2,chars(s)),scale=1}
  end
  local native=load('font_layout_native');debug.setupvalue(native,1,function(g,edge,color,x,y)if edge==-1234567 then edge=nil end;capture(x,y,g.text,0,color,edge,g.spacing,g.line_spacing)end)
  return{['取宽度']=function(s,spacing)measurements=measurements+1;return(chars(s))end,
   ['取高度']=function(s,line_spacing)local _,h=chars(s);return h end,
   ['取文字信息']=function()return 12,'宋体',2 end,
   ['解析']=function(s,spacing,line_spacing)parses=parses+1;return{{{text=s,spacing=spacing,line_spacing=line_spacing},0,0},text=s,spacing=spacing,line_spacing=line_spacing}end,
   ['显示配置']=native,
   ['显示']=capture}
 end
 local rawfont,largefont=font('400132927.img'),font('-553833251.img')
 env.__Res=function(kind,address)
  eq(kind,2);eq(address=='400132927.img'or address=='-553833251.img',true,'only verified original fonts')
  fonts=fonts+1
  if font_issue=='nil'then return nil elseif font_issue=='invalid'then return{} elseif font_issue=='throw'then error('font load failure')end
  return address=='400132927.img'and rawfont or largefont
 end
 local native_engine={['创建精灵']=sprite,['创建渲染区']=function()return{}end,['取渲染区纹理']=function()return{}end,['销毁渲染区']=noop,['渲染开始']=noop,['清屏']=noop,['渲染结束']=noop,
 ['创建包围盒']=rect,
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
 eq(env['引擎']['画线'],nil,'native plugin has no line API')
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
 return {owner=owner,public=public,U=U,maze=maze,config=config,E=E,resource=env.__Res,texts=texts,draw=draw,lines=lines,paint=paint,rawfont=rawfont,events=events,add=add,env=env,
 render=function()for i=#lines,1,-1 do lines[i]=nil end;for i=#paint,1,-1 do paint[i]=nil end;for i=#texts,1,-1 do texts[i]=nil end;for i=#draw,1,-1 do draw[i]=nil end;owner.render_obj.render();public['显示']()end,
 move=function(x,y,z)scrollx,scrolly=x,y;owner['X比例']=z or 1;owner['Y比例']=z or 1 end,
 fontMode=function(value)font_issue=value end,stats=function()return measurements,fonts,sprites,parses end}
end

for _,outline in ipairs{false,true}do
 local s=make('new',{{1047,100,100},{1048,220,120},{1053,330,180}});s.E['地面道具描边']=outline;s.render();eq(#s.texts,3)
 for _,t in ipairs(s.texts)do eq(t.color,-1);near(t.h,12);near(t.scale,1);eq(t.edge,outline and -14078936 or nil)end
 local m,f,p,layouts=s.stats()
 for i=1,200 do s.render();eq(#s.texts,3)end
 eq(s.stats(),m);eq(select(3,s.stats()),p);eq(select(4,s.stats()),layouts)
 s.events[1]=nil;s.events[2]=nil;s.events[3]=nil;s.render();eq(#s.texts,0)
end
for id in pairs(routes)do
 local s=make('new',{{id,220,120}});s.render()
 if #s.texts>0 then eq(s.texts[1].color,-1);near(s.texts[1].scale,1)end
end
local s=make('new',{{1047,220,120}});s.render();s.owner['外形框对象']['父窗口']['可视']=false;s.render();eq(#s.texts,0)

for _,points in ipairs({{{1047,4,4}},{{1047,445,295}},{{1047,210,100},{1048,212,100},{1053,214,100}}})do
 local s=make('new',points);s.render()
 for _,t in ipairs(s.texts)do eq(t.x>=4 and t.y>=20 and t.x+t.w<=446 and t.y+t.h<=282,true,'native-size label inside map')end
end
for _,issue in ipairs{'nil','invalid'}do local s=make('new',{{1047,100,100}},nil,nil,issue);s.render();eq(#s.texts,0);eq(s.owner.__gm_portal_labels_v212.disabled,true)end

print('PORTALS_V225_PASS',mode,checks,'white labels: native map constructor/render and actual restricted installer; finite glyphs, native 1:1 bitmap glyphs, no resampling; no per-frame allocations')
