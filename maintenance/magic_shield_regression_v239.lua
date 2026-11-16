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
local custom={'伤害减免','最小防御','最大防御','最小魔防','最大魔防','抵抗真伤','抵抗暴击','攻火元素','攻冰元素','攻雷元素','攻风元素','攻神元素','攻暗元素','攻幻元素'}
local basekeys={'物理伤害','魔法伤害','物理防御','魔法防御','最大生命','最大法力','生命值','法力值','命中','躲避','暴击','移动速度','攻击速度','移动速度倍数','攻击速度倍数','maxhp','maxmp'}
local ids={4498,4511,4539,4552,4565,4583,4596,4609,4627,4640,4653,4666,4679,4692,4710,4723,4741,4987,5000}
local spells={'幽灵盾','神圣战甲术','魔法盾'}
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
 local U={['游戏动画']={},['版本选择']=story,['大堵塞就']=function()return rules end,['啾啾啵啵']=getrole,['主角最小破坏']=0,['主角最大破坏']=0,['主角最小自然']=0,['主角最大自然']=0,['主角最小灵魂']=0,['主角最大灵魂']=0,['主角攻暗元素']=5,['主角攻神元素']=5}
 env['Ux雌']=U;env['Ae冻']=U
 env['Gly独']={['创建动画']=function(name)return{['可视']=false,['播放_绑定']=function()end}end,['取出技能信息']=function(name)return{['显示名']=name}end,['取随机数']=function(a,b)return a end,['事件对象']=function(id)return id==1 and env['FXru胃啪']or nil end}
 local function clear()for _,name in ipairs(spells)do h['清除状态'](h,name)end end
 return{h=h,env=env,role=role,rules=rules,statuses=statuses,clear=clear,
  counters=function()return icons,timer,#drawn end,drawn=drawn,hover=function(v)hover=v end,
  elements=function(self,values)
   for i,e in ipairs({'火','冰','雷','风','神','暗','幻'})do local k='攻'..e..'元素';h['属性']['属性集'][k]=values[i]or 0;h['属性']['附加_'..k]=i%2 end
  end,
  cast=function(self,name,level,idx,target)
   role['技能'][name][1]=level or 0
   local f=load(legacy and'old_dispatch'or('dispatch'..(idx or(name=='魔法盾'and 4115 or 4498))),env);debug.setupvalue(f,1,{id=name})
   f(nil,{target or 0},nil,nil,nil,nil)
   return h['BUFF组'][#h['BUFF组']]
  end}
end
local function state(buff)return select(2,debug.getupvalue(buff['取属性表'],1))end
local function check(s,name,v)
 local h=s.h;local b=h['BUFF组'][#h['BUFF组']];local t=state(b);local def=name==spells[1]and'魔防'or'防御';local res=name==spells[1]and'真伤'or'暴击'
 eq(t['持续时间'],0);eq(t['时间计次'],0)
 eq(h['属性']['附加_最大'..def],v,'actual native defense delta');eq(h['属性']['附加_最小'..def],0,'minimum unchanged');eq(h['属性']['附加_抵抗'..res],v)
 eq(t['状态说明'],(name==spells[1]and'魔法防御'or'物理防御')..'增加：0-'..v..'\n'..res..'抵抗增加：'..v..'\n攻击元素总和越高，加成越高')
 b['显示'](10,10,true);local _,timers,shown=s.counters();eq(timers,0,'no timer title/draw')
 b['显示提示']();local _,_,after=s.counters();eq(after,shown+1,'real hover tooltip')
 eq(s.drawn[#s.drawn],'#Y'..name..'\n#W'..t['状态说明'],'original title/body colors')
 s.hover(false);b['显示'](10,10,true);b['显示提示']();local _,_,hidden=s.counters();eq(hidden,after,'no hover no tooltip');s.hover(true)
 s.env.dt=86400;b['更新']();eq(b['已经消失'](),false);eq(t['时间计次'],0)
 return b
end
local magic_ids={4115,4130,4145,4160,4175,4190,4215,4230,4245,4260,4275,4295,4310,4325,4340,4355,4370,4385,4405,4420,4435,4450,4465,4480,4766,4781,4796,4811,5622,5637,5652,5667,6025,6040}
local reductions={20,30,40,50,55,60}
local function magic_check(s,value)
 local b=s.h['BUFF组'][#s.h['BUFF组']];assert(b,'native cast produced no buff')
 local t=state(b);eq(t['持续时间'],0);eq(t['时间计次'],0)
 eq(s.h['属性']['附加_伤害减免'],value,'native damage reduction applied once')
 eq(s.h['属性']['附加_抵抗真伤'],math.ceil(value*.5),'native penetration resistance applied once')
 eq(t['状态说明'],'伤害减免增加：'..value..'\n破防抵抗增加：'..math.ceil(value*.5))
 b['显示'](10,10,true);local _,timer,n=s.counters();eq(timer,0,'permanent icon has no countdown')
 b['显示提示']();local _,_,shown=s.counters();eq(shown,n+1)
 eq(s.drawn[#s.drawn],'#Y魔法盾\n#W'..t['状态说明'],'actual original-colored hover tooltip')
 s.hover(false);b['显示'](10,10,true);b['显示提示']();local _,_,hidden=s.counters();eq(hidden,shown);s.hover(true)
 s.env.dt=86400;b['更新']();eq(b['已经消失'](),false,'no timed expiry after a day')
 eq(s.env['Ux雌']['游戏动画']['魔法盾']['可视'],true,'shield animation visible after cast/replacement')
 return b
end
for _,story in ipairs({'归梦','来世续缘'})do
 local s=scene(story);eq(s.env._G,nil);eq(s.env.pcall,nil);eq(s.env.xpcall,nil)
 eq(#s.rules['魔法盾'],6)
 for level=0,5 do
  local prev=s.h['BUFF组'][1];s:cast('魔法盾',level);eq(#s.h['BUFF组'],1)
  magic_check(s,reductions[level+1]);if prev then eq(prev['已销毁'](),true,'upgrade replaces old native instance')end
  eq(s.rules['魔法盾'][level+1]['持续时间'],0)
  eq(s.rules['魔法盾'][level+1]['消耗魔法'],20+level*30,'original MP rows preserved')
 end
 -- The latest cast replaces even a stronger existing shield; never add
 -- deltas onto the old effect and never keep a stale high-level caption.
 local prev=s.h['BUFF组'][1];s:cast('魔法盾',2);eq(prev['已销毁'](),true);magic_check(s,40)
 s:cast('魔法盾',2);eq(#s.h['BUFF组'],1);magic_check(s,40)
 s.clear();eq(s.h['属性']['附加_伤害减免'],0);eq(s.h['属性']['附加_抵抗真伤'],0)
 eq(s.env['Ux雌']['游戏动画']['魔法盾']['可视'],false,'native disappearance callback still runs')
 for _,idx in ipairs(magic_ids)do s:cast('魔法盾',4,idx);magic_check(s,55);eq(#s.h['BUFF组'],1)end
 s.clear()
 -- Old save values retain their exact actual bonuses, drop their timer,
 -- then can be overwritten immediately by a newly learned tier.
 eq(s.env['FXru胃啪']['增加状态']('魔法盾',0,{['持续时间']=55,['剩余时间']=11,['伤害减免']=27,['抵抗真伤']=9}),true)
 local b=s.h['BUFF组'][1];local t=state(b);eq(t['持续时间'],0);eq(t['时间计次'],0)
 eq(t['状态说明'],'伤害减免增加：27\n破防抵抗增加：9','show separate actual saved bonuses')
 s:cast('魔法盾',5);eq(b['已销毁'](),true);magic_check(s,60)
 local saved=T.copy(s.h['BUFF组'][1]['取属性表']());s.clear()
 s.env['FXru胃啪']['增加状态']('魔法盾',0,saved);eq(state(s.h['BUFF组'][1])['持续时间'],0)
 eq(state(s.h['BUFF组'][1])['状态说明'],'伤害减免增加：60\n破防抵抗增加：30')
 s:cast('魔法盾',0);magic_check(s,20)
 -- Original death processing still clears the shield and native destruction
 -- removes its attributes and visual, with no residual reduction.
 load('death_buffs',s.env)(s.h);eq(s.h['BUFF组'][1]['已经消失'](),true)
 s.clear();eq(s.h['属性']['附加_伤害减免'],0);eq(s.h['属性']['附加_抵抗真伤'],0)
 -- Condensation was part of the old recast guard. Its own state is untouched
 -- while the latest magic shield always replaces the previous one.
 local other=T.copy(s.statuses['神圣战甲术']);other['标识']='凝血离魂';other['显示名']='凝血离魂';other['持续时间']=20;s.statuses['凝血离魂']=other
 s.h['增加状态'](s.h,'凝血离魂',0,{});local condensation=s.h['BUFF组'][1]
 s:cast('魔法盾',0);s:cast('魔法盾',5);magic_check(s,60);eq(#s.h['BUFF组'],2);eq(condensation['已经消失'](),false);eq(state(condensation)['持续时间'],20)
 s.h['清除状态'](s.h,'凝血离魂');s.clear()
 -- Both previous permanent defensive spells pass through the same extended
 -- constructor without any changed formula, text or removal behavior.
 s:elements({1,2,3,4,5,6,7});s:cast('幽灵盾',0,4498);check(s,'幽灵盾',22);s.clear()
 s:cast('神圣战甲术',0,4498);check(s,'神圣战甲术',22);s.clear()
end
-- Representative repeated cast/upgrade path in both normal and hot modes.
do
 local s=scene('来世续缘')
 for i=1,200 do local old=s.h['BUFF组'][1];s:cast('魔法盾',i%6);eq(#s.h['BUFF组'],1);if old then eq(old['已销毁'](),true)end;magic_check(s,reductions[i%6+1])end
 s.clear();eq(s.h['属性']['附加_伤害减免'],0);eq(s.h['属性']['附加_抵抗真伤'],0)
end
-- Actual previous dispatcher demonstrates the blocked recast. The native
-- positive timer path and original amount calculation form a negative control.
do
 local s=scene('来世续缘',true);s.rules['魔法盾'][1]['持续时间']=30;s.rules['魔法盾'][6]['持续时间']=80
 local old=s:cast('魔法盾',0);assert(old,'old native cast must work')
 eq(s.h['属性']['附加_伤害减免'],20);eq(state(old)['持续时间'],30)
 s:cast('魔法盾',5);eq(s.h['BUFF组'][1],old,'old guard blocks upgrade');eq(s.h['属性']['附加_伤害减免'],20)
 old['显示'](10,10,true);local _,timer=s.counters();eq(timer>0,true,'old timer rendered')
 s.env.dt=31;old['更新']();eq(old['已经消失'](),true);s.clear()
end
print('MAGIC_SHIELD_V239_PASS',mode,checks)
