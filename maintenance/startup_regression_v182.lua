local work,mode=assert(arg[1]),arg[2]or'normal'
if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end
local count=0
local function eq(a,b,why)count=count+1;assert(a==b,(why or 'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function load(name,env)local f=assert(loadfile(work..'/'..name..'.ljbc'));setfenv(f,env);return f end
local function make(version)
 local s={events={},errors={}}
 local t={};for k,v in pairs(table)do t[k]=v end
 local sys={script_setting={}}
 local env=setmetatable({table=t,Sys=sys,['Ae冻集']={['状态图标X']=0,['状态图标Y']=0},['Q_方向']={['下']=4}},{__index=_G})
 s.env,s.table,s.sys=env,t,sys
 sys.run=function(command,a,b,c)
  if command=='数据保护'then return sys['数据保护'](a,b)end
  if command=='脚本关联处理'or command=='剧情关联处理'then s.events[#s.events+1]={command,a,b};return end
  if command=='debug_msg'then s.errors[#s.errors+1]={a,b};return end
  error('unexpected native request '..tostring(command))
 end
 local wrap=load('data_proxy',env);debug.setupvalue(wrap,1,sys);sys['数据保护']=wrap;s.wrap=wrap
 -- Actual native registration instructions and their actual closure subtrees.
 load('table_register_'..version,env)()
 s.global=load('global_proxy_'..version,env)
 s.init=load('hero_init',env);s.defaults=load('hero_defaults',env)
 return s
end
local function attributes(s)
 local h={};s.defaults(h,10,20,{});local a=h['属性']
 a['属性集']={'maxhp','maxmp'};a['动画次序']='无';a['等级']=21
 a['扩展']={name='test',list={1,2,3},enabled=true};return a
end
-- Reproduce the exact first failure in the user's trace: native hero init at
-- line 166 -> native table.copy(...,true) -> table.check -> reverse(nil).
do
 local s=make('old');local a=attributes(s);local proxy=s.wrap(a,true)
 s.sys.get=function(kind,key)eq(kind,'char');return proxy end
 local ok,why=pcall(s.init,{},10,20,{['绑定属性']='战士'})
 eq(ok,false);assert(tostring(why):find("reverse",1,true),tostring(why));count=count+1
 print('V181_STARTUP_REPRODUCED',mode,'reverse(nil)')
end
-- Run the same ORIGINAL hero initialization bytecode through the completed
-- property-copy stage; no fake clone or fake check function is injected.
for i=1,300 do
 local s=make('new');local raw=attributes(s);local proxy=s.wrap(raw,true)
 raw['等级']=99;proxy.__p['等级']=nil -- external/native changes are permitted
 s.sys.get=function(kind,key)eq(kind,'char');eq(key,'战士');return proxy end
 local hero={};s.init(hero,10,20,{['绑定属性']='战士'})
 eq(hero['基础属性']['等级'],99);eq(hero['属性']['等级'],99)
 eq(hero['属性']['扩展'].list[3],3);eq(hero['基础属性']['扩展'].enabled,true)
 eq(rawget(hero['基础属性'],'__p'),nil);eq(rawget(hero['基础属性'],'__数据'),nil)
 hero['属性']['扩展'].list[1]=700
 eq(raw['扩展'].list[1],1);eq(hero['基础属性']['扩展'].list[1],1,'working/base tables independent')
 eq(#s.errors,0)
end
-- Copy true/false/nil check modes, ordinary and proxy inputs, nested tables,
-- false/zero/nil values, independently mutable copies, and direct check callers.
for i=1,500 do
 local s=make('new');local source={n=0,flag=false,nested={value=i}}
 for _,wrap in ipairs({false,true})do for _,check in ipairs({false,true,'default'})do
  local value=wrap and s.wrap(source,true)or source
  local copied=s.table.copy(value,check=='default'and nil or check)
  eq(copied.n,0);eq(copied.flag,false);eq(copied.nested.value,i);copied.nested.value=-1;eq(source.nested.value,i)
  eq(rawget(copied,'__数据'),nil);eq(s.table.check(value),true)
 end end
 eq(s.table.copy(false),false);eq(s.table.copy(21),21);eq(s.table.copy('text'),'text');eq(s.table.copy(nil),nil)
 eq(#s.errors,0)
end
-- Both append/positional insert and removal operate on the underlying list;
-- they must not maintain a second mirror list or alter inserted values.
do
 local s=make('new');local data={'a','b'};local p=s.wrap(data,true)
 for i=1,300 do
  s.table.insert_(p,'tail');eq(data[3],'tail');eq(s.table.getn(p),3)
  s.table.insert_(p,2,{value=i});eq(data[2].value,i);eq(data[3],'b');eq(s.table.getn(p),4)
  s.table.remove_(p,2);eq(data[2],'b');s.table.remove_(p,3);eq(#data,2);eq(#p.__p,0)
 end
 local plain={};s.table.insert_(plain,'plain');s.table.insert_(plain,1,'first');eq(plain[1],'first');s.table.remove_(plain,1);eq(plain[1],'plain')
 eq(#s.errors,0)
end
-- The database numeric proxy still emits task/story notifications on value
-- changes, although the removed anti-tampering mirror no longer exists.
do
 local s=make('new');local p=s.global({counter=1,label='old'});p.__任务绑定.counter=true;p.__剧情绑定.counter=true
 eq(p.counter,1);p.__数据.counter=100;eq(p.counter,100);eq(#s.errors,0)
 p.counter=101;eq(#s.events,2);eq(s.events[1][1],'脚本关联处理');eq(s.events[2][1],'剧情关联处理')
 p.counter=101;eq(#s.events,2,'unchanged values do not re-notify')
 p.label='new';eq(p.label,'new');eq(p.__p.counter,nil);eq(next(p.__p),nil)
end
print('STARTUP_AND_TABLE_PASS',mode,count)
