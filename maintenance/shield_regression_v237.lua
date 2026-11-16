io.stdout:setvbuf('no')
local work,mode=arg[1],arg[2]
if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')else jit.off()end
local checks=0
local function eq(a,b,msg)checks=checks+1;assert(a==b,(msg or'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function noop()end
local function load(n,env)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,env);return f end
local M={};for k,v in pairs(math)do M[k]=v end;M.round=function(n)return math.floor(n+.5)end
local T={};for k,v in pairs(table)do T[k]=v end
T.copy=function(t)local out={};for k,v in pairs(t)do out[k]=v end;return out end
local function split(s,sep)local out={};local pos=1;while true do local a,b=string.find(s,sep,pos,true);if not a then out[#out+1]=string.sub(s,pos);return out end;out[#out+1]=string.sub(s,pos,a-1);pos=b+1 end end
local configs=assert(loadfile(work..'/configs.lua'))()
local function read(s,section,key,default)s=configs[s]or s;for line in string.gmatch(s,'[^\r\n]+')do local k,v=string.match(line,'^(.-)=(.*)$');if k==key then return v end end;return default end
local custom={'最小防御','最大防御','最小魔防','最大魔防','抵抗真伤','抵抗暴击','攻火元素','攻冰元素','攻雷元素','攻风元素','攻神元素','攻暗元素','攻幻元素'}
local basekeys={'物理伤害','魔法伤害','物理防御','魔法防御','最大生命','最大法力','生命值','法力值','命中','躲避','暴击','移动速度','攻击速度','移动速度倍数','攻击速度倍数','maxhp','maxmp'}
local ids={4498,4511,4539,4552,4565,4583,4596,4609,4627,4640,4653,4666,4679,4692,4710,4723,4741,4987,5000}
local spells={'幽灵盾','神圣战甲术'}
local function scene(story,legacy)
 local h={id=1,['BUFF组']={},['属性']={hp=1000,mp=1000,['名称']='test',['等级']=30,['附加']={},['资源']={},['属性集']={}},['动作转移']={},['自定义属性表']={},['本次移动速度倍数']=10,['实时移动速度']=10}
 for _,k in ipairs(basekeys)do h['属性'][k]=0;h['属性']['附加_'..k]=0 end
 for _,k in ipairs(custom)do h['自定义属性表'][k]=true;h['属性'][k]=0;h['属性']['属性集'][k]=0;h['属性']['附加_'..k]=0 end
 h['属性'].maxhp=1000;h['属性'].maxmp=1000
 -- Finite raw actor foundation. BUFF arithmetic and public base+bonus reads
 -- are real; the engine's equipment/level/final stat recomputation is not.
 h['属性更新']=noop;h['HP改变']=function(_,n)eq(n,0,'zero native status heal')end;h['MP改变']=function(_,n)eq(n,0,'zero native status mana')end
 local parsed,drawn,timer,icons={}, {},0,0;local hover=true;local statuses={}
 local E={['自定义属性表']=custom,['状态图标显示模式']=0,['UI焦点']=false,['鼠标_屏幕坐标']={x=12,y=12},['屏幕宽度']=1024,['状态提示透明']=255}
 E['风格框_状态']={['显示']=function(x,y,w,h,alpha,rich)drawn[#drawn+1]=rich.text end}
 local env={type=type,tonumber=tonumber,tostring=tostring,math=M,table=T,string=string,pairs=pairs,ipairs=ipairs,unpack=unpack,setmetatable=setmetatable,rawget=rawget,rawset=rawset,select=select,
  dt=.1,['Ae冻集']=E,['核心']={['读配置项_内存']=read,['ARGB分解']=function()return 0,0,0,0 end},['分割文本']=split,['L常量']={['混合_默认']=1,['混合_灯光']=2,['颜色_白']=-1},ARGB=function()return -1 end,['Q_文字']={},['Q_提示框']={['可视']=false},class=function()return{}end}
 env.__Res=function(kind,path)return{['宽度']=24,['高度']=24,['路径']=path}end
 env['丰富文本_解析']=function(font,text)parsed[#parsed+1]=text;return{text=text},36,210 end
 env['Q__']={['创建精灵']=function(image)
  eq(type(image),'table','real parsed image resource');return{['置中心点']=noop,['置混合模式']=noop,['置颜色']=noop,['取包围盒']=function()return{['检测_点']=function()return hover end}end,['显示']=function()icons=icons+1 end,['释放']=noop,['销毁']=noop}
 end}
 local S={};env.Sys=S
 S.add=function(kind,name,value)eq(kind,'状态配置');statuses[name]=value end
 S.get=function(kind,name)
  if kind=='status'then return statuses[name]end
  if kind=='win_tex'then return function()return{['置标题']=function()timer=timer+1 end,['显示']=function()timer=timer+1 end,['销毁']=noop}end end
  error('unexpected native get '..tostring(kind))
 end
 S.run=function(op,f,args,...)
  if op=='adds'then return f()end
  if op=='fun'then return true,f(unpack(args))end
  error('unexpected native run '..tostring(op))
 end
 env['引擎']={['取随机整数']=function(_,a,b)return a end}
 load('statuses',env)();eq(statuses[spells[1]]['持续时间'],0);eq(statuses[spells[2]]['持续时间'],0)
 load(legacy and'old_buff_class'or'buff_class',env)()
 h['增加状态']=load('add',env);h['清除状态']=load('clear',env);h['取状态列表']=load('list',env);h['修改状态']=load('modify',env)
 local api=load('hero_api',env);local owner={Hero=h,['屏幕事件组']={}};debug.setupvalue(api,2,owner);env['FXru胃啪']=api()
 local role={['技能']={}};for _,name in ipairs(spells)do role['技能'][name]={0,0,5}end
 local getrole=load(story=='来世续缘'and'role_b'or'role_a',env);debug.setupvalue(getrole,1,{['角色组']=role})
 local rules=load('rules',env)();eq(#rules[spells[1]],6);eq(#rules[spells[2]],6)
 local U={['版本选择']=story,['大堵塞就']=function()return rules end,['啾啾啵啵']=getrole,['主角最小破坏']=0,['主角最大破坏']=0,['主角最小自然']=0,['主角最大自然']=0,['主角最小灵魂']=0,['主角最大灵魂']=0,['主角攻暗元素']=5,['主角攻神元素']=5}
 env['Ux雌']=U;env['Ae冻']=U
 env['Gly独']={['取出技能信息']=function(name)return{['显示名']=name}end,['取随机数']=function(a,b)return a end,['事件对象']=function(id)return id==1 and env['FXru胃啪']or nil end}
 local function clear()for _,name in ipairs(spells)do h['清除状态'](h,name)end end
 return{h=h,env=env,role=role,rules=rules,statuses=statuses,clear=clear,
  counters=function()return icons,timer,#drawn end,drawn=drawn,hover=function(v)hover=v end,
  elements=function(self,values)
   for i,e in ipairs({'火','冰','雷','风','神','暗','幻'})do local k='攻'..e..'元素';h['属性']['属性集'][k]=values[i]or 0;h['属性']['附加_'..k]=i%2 end
  end,
  cast=function(self,name,level,idx,target)
   role['技能'][name][1]=level or 0
   local f=load(legacy and'old_dispatch'or('dispatch'..(idx or 4498)),env);debug.setupvalue(f,1,{id=name})
   f(nil,{target or 0},nil,nil,nil,nil)
   return h['BUFF组'][#h['BUFF组']]
  end}
end
local function state(buff)return select(2,debug.getupvalue(buff['取属性表'],1))end
local function check(s,name,v)
 local h=s.h;local b=h['BUFF组'][#h['BUFF组']];local t=state(b);local def=name==spells[1]and'魔防'or'防御';local res=name==spells[1]and'真伤'or'暴击'
 eq(t['持续时间'],0);eq(t['时间计次'],0)
 eq(h['属性']['附加_最大'..def],v,'actual native defense delta');eq(h['属性']['附加_最小'..def],0,'minimum unchanged');eq(h['属性']['附加_抵抗'..res],v)
 eq(t['状态说明'],(name==spells[1]and'魔法防御'or'物理防御')..'增加：0-'..v..'\n'..res..'抵抗增加：'..v)
 b['显示'](10,10,true);local _,timers,shown=s.counters();eq(timers,0,'no timer title/draw')
 b['显示提示']();local _,_,after=s.counters();eq(after,shown+1,'real hover tooltip')
 eq(s.drawn[#s.drawn],'#Y'..name..'\n#W'..t['状态说明'],'original title/body colors')
 s.hover(false);b['显示'](10,10,true);b['显示提示']();local _,_,hidden=s.counters();eq(hidden,after,'no hover no tooltip');s.hover(true)
 s.env.dt=86400;b['更新']();eq(b['已经消失'](),false);eq(t['时间计次'],0)
 return b
end
for _,story in ipairs({'归梦','来世续缘'})do
 local s=scene(story);eq(s.env.pcall,nil);eq(s.env.xpcall,nil);eq(s.env._G,nil,'database restrictions')
 for _,name in ipairs(spells)do
  for level=0,5 do
   s:elements({1,2,3,4,5,6,7}) -- base 28 + four existing native element bonuses = 32
   s:cast(name,level);check(s,name,6+2*level+16)
   eq(s.rules[name][level+1]['消耗魔法'],10+5*level);eq(s.rules[name][level+1]['持续时间'],0)
   s.clear();eq(#s.h['BUFF组'],0)
  end
 end
 -- Odd sum rounds only once, all seven source fields include native bonuses.
 s:elements({1});s:cast(spells[1]);check(s,spells[1],9);s.clear()
 s:elements({});s:cast(spells[2]);check(s,spells[2],8);s.clear()
 -- Original friendly-event branch, in addition to player sentinel 0.
 s:cast(spells[1],0,nil,1);check(s,spells[1],8);s.clear()
 for _,idx in ipairs(ids)do s:elements({2,3,4,5,6,7,8});s:cast(spells[1],2,idx);check(s,spells[1],30);s.clear()end
 -- Actual same-name recast clears/destroys the old instance before replacement.
 s:elements({1});local old=s:cast(spells[1],0);s:cast(spells[1],5);eq(old['已销毁'](),true);eq(#s.h['BUFF组'],1);check(s,spells[1],19)
 s:cast(spells[2],0);eq(#s.h['BUFF组'],2);check(s,spells[2],9)
 s.clear();eq(s.h['属性']['附加_最大魔防'],0);eq(s.h['属性']['附加_抵抗真伤'],0);eq(s.h['属性']['附加_最大防御'],0)
 s:cast(spells[1],0);s:cast(spells[2],0);load('death_buffs',s.env)(s.h)
 for _,b in ipairs(s.h['BUFF组'])do eq(b['已经消失'](),true,'original death removes defensive buff')end
 s.clear();eq(s.h['属性']['附加_最大魔防'],0);eq(s.h['属性']['附加_最大防御'],0,'death cleanup no residue')
 -- Current save-field export/reload through actual public insertion.
 local b=s:cast(spells[1],0);local saved=T.copy(b['取属性表']());s.clear()
 eq(s.env['FXru胃啪']['增加状态'](spells[1],0,saved),true);check(s,spells[1],9);s.clear()
 -- Legacy timer data receives no expiry but keeps its actual saved bonus
 -- until the player recasts. No old save files are edited.
 s.env['FXru胃啪']['增加状态'](spells[1],0,{['持续时间']=25,['剩余时间']=7,['最大魔防']=17,['抵抗真伤']=11})
 local t=state(s.h['BUFF组'][1]);eq(t['持续时间'],0);eq(t['时间计次'],0);eq(t['状态说明'],'魔法防御增加：0-17\n真伤抵抗增加：11');s.clear()
 -- Non-target status keeps original positive timer and has no forced caption.
 local other=T.copy(s.statuses[spells[1]]);other['标识']='finite_other';other['显示名']='finite_other';other['持续时间']=2;s.statuses.finite_other=other
 s.h['增加状态'](s.h,'finite_other',0,{});local finite=s.h['BUFF组'][1];eq(state(finite)['持续时间'],2);s.env.dt=3;finite['更新']();eq(finite['已经消失'](),true);s.h['清除状态'](s.h,'finite_other')
 -- One representative 200-cast hot path covers allocation, old destruction,
 -- actual element reads, native add/remove arithmetic and draw caching.
 for i=1,200 do s:elements({i%7,2,3,4,5,6,7});s:cast(spells[1],i%6);eq(#s.h['BUFF组'],1);local b=s.h['BUFF组'][1];b['显示'](10,10,true);b['显示提示']()end
 s.clear();eq(s.h['属性']['附加_最大魔防'],0);eq(s.h['属性']['附加_抵抗真伤'],0)
end
-- Old implementation is a real negative control for both formula and saved
-- positive timers; unchanged timer renderer must still draw other countdowns.
do
 local s=scene('来世续缘',true);s:elements({1,2,3,4,5,6,7});local b=s:cast(spells[1],0)
 eq(s.h['属性']['附加_最大魔防'],7,'old dark-only 10 percent formula');s.clear()
 s.env['FXru胃啪']['增加状态'](spells[1],0,{['持续时间']=25,['剩余时间']=7,['最大魔防']=17,['抵抗真伤']=11})
 b=s.h['BUFF组'][1];eq(state(b)['持续时间'],25,'old saved timer survives in old constructor');b['显示'](10,10,true);local _,timer=s.counters();eq(timer>0,true,'old positive timer rendered')
 s.env.dt=30;b['更新']();eq(b['已经消失'](),true);s.clear()
end
print('SHIELDS_V237_PASS',mode,checks)
