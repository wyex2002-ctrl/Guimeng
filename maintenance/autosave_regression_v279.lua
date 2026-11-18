local work,mode=arg[1],arg[2]
if mode=='hot'then jit.opt.start('hotloop=1','hotexit=1')else jit.off()end
local checks=0
local function eq(a,b,why)
 checks=checks+1
 if a~=b then error((why or'check')..' '..tostring(a)..' ~= '..tostring(b))end
end
local function load(n,e)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,e);return f end
local function noop()end
local function fixture(version,items,uuid,clocked,via_constructor)
 local f={time=0,work=0,frames=0,writes=0,files={},packed={},trace={},costs=clocked}
 local function main_only(name)
  if coroutine.running()~=nil then
   f.off_main=(f.off_main or 0)+1
   error('main lua_State required: '..name,0)
  end
  f.native_calls=(f.native_calls or 0)+1
 end
 local N=setmetatable({},{__index=_G});f.N=N
 -- Model CPU work separately from native-clock affinity; the real os.clock
 -- belongs to LuaJIT and is safe from a coroutine.
 N.os=setmetatable({clock=function()return f.time+f.work end},{__index=os})
 local T={};for k,v in pairs(table)do T[k]=v end;N.table=T
 N.math=setmetatable({round=function(n,p)local m=10^(p or 0);return math.floor(n*m+.5)/m end},{__index=math})
 load('table_register',N)()
 local realcopy=T.copy
 T.copy=function(...)if f.costs then f.work=f.work+(f.copy_cost or .000003)end;return realcopy(...)end
 N.引擎={取运行时间=function()
  if version~='broken'then main_only('clock')end
  return f.time+f.work
 end}
 N.Ae冻={地图名称='测试地图'}
 local S={Game_State=1,user_info={uuid=uuid},save_info={uid='save-id',stime=1,ptime=0,last_save_time=0},
  界面_窗口_数组={{控件组={}}},包裹物品组={},游戏任务组={},任务列表={'任务一'},已完成任务表={任务二=true},道具CD信息组={},hack_item_copy=noop}
 local hero={技能信息={},BUFF组={},属性={hp=123,mp=456,等级=37,经验值=789,金币=1000},地图格子={x=10,y=20},方向=2,
  显示名称='测试角色',名称显示偏移x=1,名称显示偏移y=2,主角配置={绑定属性={},绑定技能='雷电术'}}
 S.Hero=hero;f.S=S
 local role={名称='测试角色',性别='男',职业='道士',佣兵={幸运=7},赠油=true}
 local U={人物选择=1,版本选择='前尘忆梦',读取人物={},啾啾啵啵=function()return role end,金轮法王=function()return 1 end}
 U=load('variable_proxy',N)(U)
 S.script_setting={Ux雌=U};N.Ux雌=U;N.Ae冻集={};N.镜头选择框={选中=false}
 N.是否为调试版=function()return false end
 N.调试输出=function(...)
  main_only('debug');f.debug_args={n=select('#',...),...}
  if f.on_debug then f.on_debug()end
  return nil,false,'native-tail'
 end
 N.取系统时间=function()return'2026-11-18'end
 N.Sys={run=function(op,...)error('unexpected '..tostring(op))end}
 local protect=load('protect',N);debug.setupvalue(protect,1,S);S.数据保护=protect
 f.protect=protect
 for i=1,items do
  local mount=i==1 or i==2
  local extra={标签='item-'..i}
  if mount then extra.__gm_oil_batch_v263={version=1,length=5,next=3,values={'0.1','0.2','0.3','0.4','0.5'}}end
  local item={名称=mount and'坐骑'or'测试物品',显示名='测试物品',数量=i,价格=100,需要等级=1,冷却时间=0,
   属性=protect({幸运=mount and 7 or 0,破坏=100},true),附加=protect(extra,true),分类='装备',子类=mount and'坐骑'or'武器',
   性别要求='不限',职业要求='不限',道具说明='说明',颜色值=-1,禁止出售=false,禁止丢弃=false}
  S.包裹物品组[i]={道具=item};S.界面_窗口_数组[1].控件组[i]={类型=6,名称='slot'..i,对象={标识=i,禁止存档=false}}
 end
 S.界面_窗口_数组[1].控件组[items+1]={类型=7,名称='快捷技能',对象={绑定技能='雷电术',原始绑定=1}}
 S.界面_窗口_数组[1].控件组[items+2]=setmetatable({类型=1},
  {__index=function()error('unrelated control fields must not be queried')end})
 for i=1,20 do
  hero.技能信息['技能'..i]={可用=true,持续开启=false,开始CD效果=true,技能延时=.5,技能延时计次=.25,当前帧=1,冷却时间=2,dt=.1}
  S.游戏任务组['任务'..i]={接受条件={{类型='变量',名称='任务变量'..i}},完成条件={{类型='变量',名称='完成变量'..i}}}
  N.Ae冻['任务变量'..i]=i;N.Ae冻['完成变量'..i]=false
  S.道具CD信息组['药'..i]={延时计次=1,当前帧=2,dt=.1,冷却时间=3}
 end
 hero.BUFF组[1]={取标识=function()main_only('buff.id');return'祝福'end,
  取属性表=function()main_only('buff.data');return{时间=10,数值=7}end}
 if version=='broken'then hero.BUFF组={}end
 local sort=load('sort_'..version,N);debug.setupvalue(sort,1,sort)
 local native_encode=load('encode_'..version,N)
 local function encode(v)local s=native_encode(v);f.packed[s]=v;return s end
 local decode=load('decode_old',N);debug.setupvalue(decode,1,decode)
 N.核心={
  -- Finite engine bridges. The real original codec/MD5 call sequence remains.
  MD5=function(s)
   main_only('MD5')
   if f.costs then f.work=f.work+.0001 end
   local sum=0;for i=1,#s do sum=(sum+s:byte(i)*i)%16777213 end
   return string.format('%08x%08x%08x%08x',#s,sum,#s,sum)
  end,
  加解密_f=function(s,key,a,b)
   -- A stored-main-state binding pushes no result to the coroutine: its last
   -- boolean argument is returned instead. Reproduce 278's observed CAT error.
   if version=='broken'and coroutine.running()~=nil then f.off_main=(f.off_main or 0)+1;return b end
   main_only('encrypt_f')
   if f.bad_crypto then return false end
   return s
  end,
  RC4=function(s,key,flag,callback)
   main_only('RC4');eq(callback(),false,'original encryption callback')
   if f.costs then f.work=f.work+.0002 end
   f.encrypt_key=key
   f.trace[#f.trace+1]={'encrypt',key,flag};return s
  end,
  RS=function(key,s)eq(key,f.encrypt_key,'existing encryption key retained');eq(type(f.packed[s]),'table','original codec output found');return{f.packed[s]}end,
  写到文件=function(path,data)
   main_only('write')
   if path:find('Log/',1,true)~=1 then
    if f.failure then error(f.failure)end
    if f.false_write then return false end
    if f.costs then f.work=f.work+.0003 end
    f.writes=f.writes+1;f.last_path=path
   end
   f.files[path]=data;return true
  end,
  读入文件=function(path)main_only('read');return f.files[path]end}
 local factory=load('gly_factory_'..version,N)
 for i=1,9 do debug.setupvalue(factory,i,0)end
 debug.setupvalue(factory,2,S);debug.setupvalue(factory,3,0);debug.setupvalue(factory,4,sort);debug.setupvalue(factory,5,encode)
 local G=factory();S.script_setting.Gly独=G;N.Gly独=G
 S.run=function()f.frames=f.frames+1;return nil,false,'frame'end
 U.窗口相关={存档读档=function(cmd,slot,unused,kind)
  eq(cmd,'存档');eq(slot,U.人物选择);eq(unused,nil);eq(kind,0)
  G.存档('GameDate/test.dat',role,'test-key')
 end}
 if version=='new'or version=='broken'then
  if via_constructor then
   local exporter=load('public_exports',N);debug.setupvalue(exporter,5,load('readonly',N));f.public=exporter(S)
   eq(f.public.run,S.run,'constructor exports scheduled run');eq(f.public.__gm_autosave_v278,nil,'native state remains private')
  else load(version=='broken'and'install_broken'or'install',N)(S)end
 end
 function f.request()U.__gm_auto_save_v278('存档',U.人物选择,nil,0)end
 function f.tick(dt)
  f.time=f.time+(dt or 1/60)
  local a,b,c=(f.public and f.public.run or S.run)();eq(a,nil);eq(b,false);eq(c,'frame')
 end
 function f.finish(dt)
  for i=1,600 do f.tick(dt);if not S.__gm_autosave_v278.active then return i end end
  error('automatic job failed to finish')
 end
 function f.read()
  local reader=load('read_native',N);debug.setupvalue(reader,1,S);debug.setupvalue(reader,2,encode);debug.setupvalue(reader,3,decode)
  local key=f.encrypt_key
  if uuid then key=key:sub(1,-#uuid-1)end
  return reader(f.last_path or'GameDate/test.dat',key)
 end
 function f.raw()return G.存档('GameDate/test.dat',role,'test-key')end
 function f.ui(story)
  local callback=load('ui_'..story,N)
  local controller={配置文件=function()f.configs=(f.configs or 0)+1 end,
   技能切换=function()f.switches=(f.switches or 0)+1 end}
  debug.setupvalue(callback,1,controller)
  U.窗口相关.存档读档=callback
  U.版本选择=story=='a'and'前尘忆梦'or'来世续缘'
  U.胚子考虑=function()return{}end
  N.Q_鼠标={被占用=false};N.FXru胃啪={HP=123,等级=37};N.物品格子18={道具=nil}
 end
 function f.quit(story)
  N.Gly独=setmetatable({结束游戏=function(flag)eq(flag,true);f.quits=(f.quits or 0)+1 end},{__index=G})
  local callback=load('quit_'..story,N);debug.setupvalue(callback,1,{存档读档=U.窗口相关.存档读档});callback()
 end
 return f
end

-- Main-state-only engine bridges distinguish the old failure from the repair.
local broken=fixture('broken',10,nil,true)
broken.request()
local ok,err=pcall(broken.finish)
eq(ok,false);assert(tostring(err):find('concatenate a boolean',1,true),tostring(err))
eq(broken.writes,0);eq(broken.S.__gm_autosave_v278.failed,1);eq(broken.off_main,1)
print('AUTOSAVE_V279_REPRODUCED_278',mode,tostring(err))
local invalid=fixture('new',10,nil,true);invalid.bad_crypto=true;invalid.request()
local ok,err=pcall(invalid.finish);eq(ok,false)
assert(tostring(err):find('returned boolean, expected string',1,true));eq(invalid.writes,0)

-- Defer an engine request when the slice is exhausted. Its arguments and
-- nil/false results survive resumption; cancellation discards the pending call.
local relay=fixture('new',2,nil,true)
relay.S.__gm_autosave_raw_v278=function()
 relay.work=relay.work+.01
 local a,b,c=relay.N.__gm_save_debug_v279(nil,false,'tail')
 eq(a,nil);eq(b,false);eq(c,'native-tail');return true
end
relay.request();relay.tick();eq(relay.debug_args,nil,'native request deferred at budget')
relay.finish();eq(relay.debug_args.n,3);eq(relay.debug_args[1],nil);eq(relay.debug_args[2],false);eq(relay.debug_args[3],'tail')
eq(relay.S.__gm_autosave_v278.completed,1)
local discard=fixture('new',2,nil,true)
discard.S.__gm_autosave_raw_v278=function()discard.work=discard.work+.01;discard.N.__gm_save_debug_v279('obsolete')end
discard.request();discard.tick();discard.N.Ae冻.地图名称='另一地图';discard.tick()
eq(discard.debug_args,nil);eq(discard.S.__gm_autosave_v278.cancelled,1)
local reentrant=fixture('new',2,nil,true)
reentrant.S.__gm_autosave_raw_v278=function()
 reentrant.N.__gm_save_debug_v279('save-now')
 reentrant.N.__gm_save_core_v279.写到文件('obsolete','must not write')
end
reentrant.on_debug=function()reentrant.on_debug=nil;reentrant.raw()end
reentrant.request();reentrant.finish();eq(reentrant.writes,1);eq(reentrant.files.obsolete,nil)
eq(reentrant.S.__gm_autosave_v278.cancelled,1)

-- Full native collector: no changing clock/world, identical byte packet.
for _,uuid in ipairs({false,'abcdefghijklmnopqrstuvwx'})do
 local id=uuid or nil
 local old=fixture('old',40,id,false);local new=fixture('new',40,id,false)
 old.raw();new.request();eq(new.writes,0,'request never blocks on collector/write')
 -- Frozen engine clock isolates format equivalence from allowed time skew.
 for i=1,400 do new.S.run();if not new.S.__gm_autosave_v278.active then break end end
 eq(new.writes,1);eq(new.files['GameDate/test.dat'],old.files['GameDate/test.dat'],'same original file packet')
 eq(new.off_main,nil,'all save native calls run on main');assert(new.native_calls>0)
 local decoded=new.read();eq(decoded[1].slot1.属性.幸运,7)
 eq(decoded[1].slot2.附加.__gm_oil_batch_v263.next,3)
 eq(decoded[1].slot40.数量,40);eq(decoded[2].快捷技能[1],'雷电术')
 eq(decoded[9],1001);eq(decoded[10].完成变量1,false)
 local roletext=decoded[8];eq(type(roletext),'string');eq(new.N.table.loadstring(roletext).赠油,true)
end

-- Representative workload at several frame rates completes under the target.
for _,fps in ipairs({15,30,60})do
 local f=fixture('new',180,nil,true);f.request();local frames=f.finish(1/fps)
 eq(f.writes,1);eq(f.S.__gm_autosave_v278.completed,1)
 assert(f.S.__gm_autosave_v278.last_elapsed<9,'normal workload under nine seconds')
 assert(frames>5,'work spread across multiple game frames')
 assert(f.files['Log/guimeng_autosave_latest.txt']:find('peak_slice_ms=',1,true))
 print('AUTOSAVE_MODEL',mode,fps,frames,f.S.__gm_autosave_v278.last_elapsed,f.S.__gm_autosave_v278.last_peak)
end
local exported=fixture('new',40,nil,true,true);exported.request();exported.finish();eq(exported.writes,1)
local accelerated=fixture('new',180,nil,true);accelerated.copy_cost=.0003;accelerated.request();accelerated.finish(1/15)
assert(accelerated.S.__gm_autosave_v278.last_elapsed<9,'larger modeled copy cost still meets normal target')
eq(accelerated.S.__gm_autosave_v278.missed,0)
print('AUTOSAVE_ACCELERATED_MODEL',mode,accelerated.S.__gm_autosave_v278.last_elapsed,accelerated.S.__gm_autosave_v278.last_peak)

-- Manual save wins; a suspended automatic generation can never write later.
local f=fixture('new',100,nil,true);f.request();f.tick();f.raw();eq(f.writes,1)
for i=1,20 do f.tick()end;eq(f.writes,1);eq(f.S.__gm_autosave_v278.cancelled,1)
local cancelled=fixture('new',50,nil,true);cancelled.request();cancelled.tick();cancelled.S.Hero={}
cancelled.tick();eq(cancelled.writes,0);eq(cancelled.S.__gm_autosave_v278.active,false)
local map=fixture('new',50,nil,true);map.request();map.tick();map.N.Ae冻.地图名称='新地图';map.tick();eq(map.writes,0)
local slot=fixture('new',50,nil,true);slot.request();slot.N.Ux雌.人物选择=2;slot.tick();eq(slot.writes,0)
local dead=fixture('new',50,nil,true);dead.request();dead.S.Hero.属性.hp=0;dead.tick();eq(dead.writes,0)

-- UI lists/skill/task dictionaries can change between slices safely.
local changing=fixture('new',200,nil,true);changing.request()
for i=1,8 do changing.tick()end
changing.S.界面_窗口_数组={};changing.S.Hero.技能信息.技能1=nil;changing.S.游戏任务组.任务1=nil
changing.finish();eq(changing.writes,1)

-- Error identity, no overlapping generations, and deadline reporting.
local failure=fixture('new',10,nil,true);failure.request();local sentinel={};failure.failure=sentinel
local ok,err=pcall(failure.finish);eq(ok,false);eq(err,sentinel);eq(failure.writes,0)
local unreadable=fixture('new',5,nil,true);unreadable.request()
local opaque=setmetatable({},{__tostring=function()error('tostring must not replace original failure')end})
unreadable.failure=opaque;local ok,err=pcall(unreadable.finish);eq(ok,false);eq(err,opaque)
local busy=fixture('new',10,nil,true);busy.request();busy.request();busy.finish();eq(busy.writes,1)
local late=fixture('new',10,nil,true);late.request();late.time=10;late.finish();eq(late.S.__gm_autosave_v278.missed,1)
local rejected=fixture('new',10,nil,true);rejected.false_write=true;rejected.request();rejected.finish()
eq(rejected.S.__gm_autosave_v278.completed,0);eq(rejected.S.__gm_autosave_v278.failed,1)

-- Actual story save callbacks: original paths, configuration and skill setup.
for _,story in ipairs({'a','b'})do
 local ui=fixture('new',20,nil,true);ui.ui(story);ui.request();eq(ui.writes,0);eq(ui.configs,2);eq(ui.switches,1)
 ui.finish();eq(ui.writes,1);assert(ui.last_path:find('GameDate/',1,true));eq(ui.read()[1].slot1.属性.幸运,7)
 local blocked=fixture('new',5,nil,true);blocked.ui(story);blocked.N.FXru胃啪.HP=0
 blocked.request();eq(blocked.writes,0);eq(blocked.S.__gm_autosave_v278.active,nil)
 local exit=fixture('new',20,nil,true);exit.ui(story);exit.request();exit.tick();exit.quit(story)
 eq(exit.writes,1);eq(exit.quits,1)
 for i=1,20 do exit.tick()end;eq(exit.writes,1,'cancelled generation cannot overwrite exit save')
end

-- Repeated complete generations must not retain stale writers or queue jobs.
local repeated=fixture('new',2,nil,true)
for i=1,200 do
 repeated.request();repeated.finish();eq(repeated.writes,i);eq(repeated.S.__gm_autosave_v278.active,false)
end

-- The actual bounded timer region preserves selection/debug gates.
for _,story in ipairs({'a','b'})do
 for _,selected in ipairs({false,true,'nil'})do
  for _,debugging in ipairs({false,true})do
   local U={人物选择=2};local owner={角色组={},配置={征集死亡=0},金轮法王=1}
   for key,name in pairs({啾啾啵啵='role_'..story,胚子考虑='config_'..story,金轮法王='mode_get'})do
    U[key]=load(name,{Ux雌=U});debug.setupvalue(U[key],1,owner)
   end
   U.开挖机的={正弦函数=noop};local requests=0
   U.__gm_auto_save_v278=function(cmd,s,a,k)eq(cmd,'存档');eq(s,2);eq(a,nil);eq(k,0);requests=requests+1 end
   local choice=selected;if choice=='nil'then choice=nil end
   local env={Ux雌=U,镜头选择框={选中=choice},是否为调试版=function()return debugging end}
   local timer=load('timer_new',env);local state={咯是=100}
   for i=1,200 do timer(state)end
   eq(requests,selected==false and not debugging and 2 or 0,'ten-second period')
  end
 end
end
if mode=='hot'then eq(jit.status(),true)end
print('AUTOSAVE_V279_PASS',mode,checks,'checks; main-state engine affinity, native format/decoder, proxies, slices/gates/cancellation/errors; finite engine/file/crypto clocks')
