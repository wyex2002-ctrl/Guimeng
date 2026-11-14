local work,mode=arg[1],arg[2]or'normal'
if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end
local count=0
local function eq(a,b,why)count=count+1;assert(a==b,(why or'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function load(n,env)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,env or _G);return f end
local function bind(n,S,env)local f=load(n,env);debug.setupvalue(f,1,S);return f end
local configs=assert(loadfile(work..'/configs.lua'))()
local function trial(name,old_display,which,override)
 local S={['script_setting']={}}
 local proxy=bind('proxy',S);S['数据保护']=proxy
 S.run=function(op,v,deep)eq(op,'数据保护');return proxy(v,deep)end
 local T={};for k,v in pairs(table)do T[k]=v end
 local env=setmetatable({table=T,Sys=S,['Q_鼠标']={['格子标识']=0},['Q_文字']={},['Ae冻集']={['道具提示宽度']=200},['丰富文本_解析']=function(_,text)return{text},0,0 end},{__index=_G})
 load('table_register',env)()
 local template=T.copy(configs[name],true)
 S['游戏道具组']=proxy({[name]=template},true);S['包裹物品组']=proxy({[32]={}},true)
 S['格式化道具属性']=load('tooltip_header',{})
 S['更新道具属性']=bind('update',S,env)
 S['script_setting']['Gly独']={['错误']=function(e)error(e)end}
 local observed
 local control={['格子ID']=32,['对象']={['计算属性']=false,['焦点']=false,['物品进入']=function()
  local item=S['包裹物品组'][32]['道具'];observed={item['显示名'],item['风格提示']['原始内容']}
 end}}
 local reset=bind(which,S,env)
 local argdata
 if override then argdata={['显示名']=old_display,['价格']=12345,['附加']=T.copy(template['附加'],true)}end
 eq(reset(control,name,1,0,argdata,false),true)
 local item=S['包裹物品组'][32]['道具'];eq(item['名称'],name);eq(item['数量'],1)
 local expected=which=='reset_old'and override and old_display or template['显示名']
 eq(item['显示名'],expected);eq(observed[1],expected)
 if override then eq(item['价格'],12345);eq(observed[2],'#Y'..expected..'\n');eq(item['附加']['强化书'],template['附加']['强化书']);eq(argdata['显示名'],expected)end
 eq(template['名称'],name);eq(template['显示名'],configs[name]['显示名'])
 eq(bind('item_info',S,env)(name)['显示名'],template['显示名'])
 eq(bind('slot_info',S,env)(32)['显示名'],expected)
end
for name,item in pairs(configs)do
 local strong=item['附加']['强化书'];local old=strong and(name:sub(5)..'(秘籍)')or item['显示名']
 trial(name,old,'reset',false);trial(name,old,'reset',true)
end
trial('四级雷电术','雷电术(秘籍)','reset_old',true)
trial('五级雷电术','雷电术(秘籍)','reset_old',true)
-- Repeated restore covers the hot path without multiplying every scenario.
for i=1,200 do trial('五级雷电术','雷电术(秘籍)','reset',true)end
print('BOOK_NAMES_V193_PASS',mode,count)
