-- Native-only scheduler. Existing save collection, format and cryptography stay.
return function(S)
 if S.__gm_autosave_v278 then return end
 local C=coroutine
 local core=核心
 local job,capture
 local records={}
 local native_tag,phase_tag={},{}
 local function pack(...)return{n=select('#',...),...}end
 local function owned()return job and C.running()==job.thread end
 local function response(ok,...)
  if not ok then error((...),0)end
  return ...
 end
 -- The DM bindings use a stored main lua_State, not the calling coroutine.
 -- Relay only this save's native calls; never replace the global engine table.
 local function maincall(name,fn,...)
  if not owned()then return fn(...)end
  return response(C.yield(native_tag,name,fn,...))
 end
 local state={completed=0,cancelled=0,missed=0,failed=0,period=10,target=9}
 S.__gm_autosave_v278=state
 local function text(value)
  local ok,result=pcall(tostring,value)
  return ok and result or'<unprintable error>'
 end
 local function clock()
  if 引擎 and type(引擎.取运行时间)=='function'then return 引擎:取运行时间()end
  return os.clock()
 end
 local function report(message)
  records[#records+1]=os.date('%Y-%m-%d %H:%M:%S')..' '..message
  if #records>32 then table.remove(records,1)end
  if core and type(core.写到文件)=='function'then
   pcall(core.写到文件,'Log/guimeng_autosave_latest.txt',
    'Guimeng v1.279 autosave | native calls on main | period=10s target=9s | stage_ms excludes time between frames\n'..table.concat(records,'\n'))
  end
 end
 if core and type(core.读入文件)=='function'and type(core.写到文件)=='function'then
  local ok,old=pcall(core.读入文件,'Log/guimeng_autosave_latest.txt')
  if ok and type(old)=='string'and #old>0 then pcall(core.写到文件,'Log/guimeng_autosave_previous.txt',old)end
 end
 local function owner()
  return type(S.script_setting)=='table'and S.script_setting.Ux雌
 end
 local function context(j)
  local u=owner()
  local hp=type(S.Hero)=='table'and type(S.Hero.属性)=='table'and S.Hero.属性.hp
  return S.Hero==j.hero and S.Game_State==1 and type(u)=='table'
   and not(type(hp)=='number'and hp<=0)
   and u.人物选择==j.slot and u.版本选择==j.story
   and (Ae冻 and Ae冻.地图名称)==j.map
 end
 local function charge(j)
  if j.stamp then
   local elapsed=math.max(0,clock()-j.stamp)
   j.cost[j.phase]=(j.cost[j.phase]or 0)+elapsed
  end
  j.stamp=clock()
 end
 local function cancel(reason)
  if job then
   state.cancelled=state.cancelled+1
   report('cancel reason='..reason..' phase='..job.phase)
   job=nil;state.active=false
  end
 end
 local function step(phase)
  if not owned()then return end
  local j=job
  if not context(j)then error(j.cancel,0)end
  local transition=phase~=nil and phase~=j.phase
  if transition then
   C.yield(phase_tag,phase)
   if not context(j)then error(j.cancel,0)end
  end
  j.units=j.units+1
  -- Lua's own os.clock accepts the actual calling lua_State. Unlike the DM
  -- engine clock it is safe here and does not require a native relay per item.
  if os.clock()>=j.cpu_end or j.units>=j.unit_limit then
   C.yield()
   if not context(j)then error(j.cancel,0)end
  end
 end
 -- Capture keys before yielding; removing a skill/task cannot invalidate next.
 local function stable_pairs(value)
  if not owned()then return pairs(value)end
  local keys={};for k in pairs(value)do keys[#keys+1]=k end
  local pos=0
  return function()
   step()
   while pos<#keys do
    pos=pos+1;local k=keys[pos];local v=value[k]
    if v~=nil then return k,v end
   end
  end,nil,nil
 end
 -- Freeze only control metadata. Item content is collected atomically per item
 -- by the original collector, immediately before its following checkpoint.
 local function windows(list)
  if not owned()then return list end
  local out={}
  for i,w in ipairs(list)do
   local controls={};out[i]={控件组=controls}
   for n,v in ipairs(w.控件组)do
    local kind=v.类型;local row={类型=kind};controls[n]=row
    if kind==6 or kind==7 then
     row.名称=v.名称;local o=v.对象
     if type(o)=='table'then
      row.对象=kind==6 and{标识=o.标识,禁止存档=o.禁止存档}
       or{绑定技能=o.绑定技能,原始绑定=o.原始绑定}
     else row.对象=o end
    end
   end
  end
  return out
 end
 -- The final collection is private; referenced task lists are copied one entry
 -- at a time with the real proxy-aware table.copy before recursive sorting.
 local function freeze(value)
  if not owned()then return value end
  step('freeze')
  local out={}
  for k,v in pairs(value)do
   if type(v)~='table'then out[k]=v
   elseif getmetatable(v)~=nil or v.__p~=nil or v.__c~=nil then
    out[k]=table.copy(v,true);step()
   else
    local t={};out[k]=t
    for key,entry in stable_pairs(v)do
     local copied=table.copy({[key]=entry},true)
     for ck,cv in pairs(copied)do t[ck]=cv end
     step()
    end
   end
  end
  return out
 end
 local function dispatch(path,role,key)
  if owned()then return false end
  if not capture then cancel('synchronous_save');return false end
  if type(path)~='string'then return false end
  assert(not job,'one automatic save per request')
  local raw=S.__gm_autosave_raw_v278
  assert(type(raw)=='function','native save closure missing')
  local u=owner()
  local j={hero=S.Hero,slot=capture.slot,story=u.版本选择,map=Ae冻 and Ae冻.地图名称,
   start=capture.start,phase='collect',cost={},native_cost={},native_count={},peak=0,units=0,cancel={},resumes=0}
  j.thread=C.create(function()return raw(path,role,key)end)
  job=j;state.active=true;capture.queued=true
  return true
 end
 local function request(command,slot,unused,kind)
  if job then report('skip reason=busy');return end
  local u=owner();local ui=type(u)=='table'and u.窗口相关
  local callback=type(ui)=='table'and ui.存档读档
  assert(type(callback)=='function','automatic save UI is not ready')
  local started=clock();capture={slot=slot,start=started}
  local ok,err=pcall(callback,command,slot,unused,kind)
  local queued=capture.queued;capture=nil
  if not ok then state.failed=state.failed+1;cancel('prepare_error');report('prepare.error '..text(err));error(err,0)end
  if queued then
   job.cost.prepare=math.max(0,clock()-started)
   job.peak=job.cost.prepare
   report('queued slot='..tostring(slot)..' prepare_ms='..string.format('%.3f',job.cost.prepare*1000))
  else report('skip reason=original_save_gate')end
 end
 local function attach()
  local u=owner()
  if type(u)=='table'and u.__gm_auto_save_v278~=request then u.__gm_auto_save_v278=request end
 end
 local function tick()
  attach()
  local j=job
  if not j then return end
  if not context(j)then cancel('context_changed');return end
  local age=math.max(0,clock()-j.start)
  if age>=9 and not j.late then j.late=true;state.missed=state.missed+1;report('deadline_missed phase='..j.phase)end
  local budget=age>=8 and .012 or age>=7 and .004 or .001
  j.slice_end=clock()+budget;j.cpu_end=os.clock()+budget;j.unit_limit=age>=7 and 8192 or 1024;j.units=0
  local started=clock();j.stamp=started
  local function resume(...)
   j.resumes=j.resumes+1
   local result=pack(C.resume(j.thread,...));charge(j);return result
  end
  local result=j.pending or resume();j.pending=nil
  local calls=0
  while result[1]and result[2]==native_tag do
   if job~=j then return end
   if not context(j)then cancel('context_changed');return end
   if clock()>=j.slice_end or calls>=128 then j.pending=result;break end
   local name,fn=result[3],result[4]
   local native_started=clock()
   local reply=pack(pcall(fn,unpack(result,5,result.n)))
   local elapsed=math.max(0,clock()-native_started)
   if name~='clock'then
    j.native_cost[name]=(j.native_cost[name]or 0)+elapsed
    j.native_count[name]=(j.native_count[name]or 0)+1
    j.last_native=name
    if not reply[1]then report('native.error name='..name..' phase='..j.phase..' '..text(reply[2]))end
   end
   charge(j);calls=calls+1
   -- A callback may request a synchronous save; never resume its obsolete job.
   if job~=j then return end
   if not context(j)then cancel('context_changed');return end
   result=resume(unpack(reply,1,reply.n))
  end
  if result[1]and result[2]==phase_tag then j.phase=result[3]end
  local ok,err=result[1],result[2]
  charge(j);j.stamp=nil
  j.peak=math.max(j.peak,clock()-started)
  if not ok then
   job=nil;state.active=false
   if err==j.cancel then state.cancelled=state.cancelled+1;report('cancel reason=context_changed');return end
   state.failed=state.failed+1
   local stack=text(err)
   if debug and debug.traceback then
    local traced,result=pcall(debug.traceback,j.thread,stack)
    if traced and type(result)=='string'then stack=result end
   end
   report('error phase='..j.phase..' last_native='..tostring(j.last_native)..' '..string.sub(stack,1,4000));error(err,0)
  end
  if C.status(j.thread)=='dead'then
   local elapsed=clock()-j.start
   if elapsed>=9 and not j.late then
    j.late=true;state.missed=state.missed+1;report('deadline_missed phase='..j.phase)
   end
   local fields={}
   for phase,cost in pairs(j.cost)do fields[#fields+1]=phase..'_ms='..string.format('%.3f',cost*1000)end
   for name,cost in pairs(j.native_cost)do
    fields[#fields+1]='native.'..name..'_ms='..string.format('%.3f',cost*1000)..'/'..j.native_count[name]
   end
   table.sort(fields)
   report('returned elapsed_ms='..string.format('%.3f',elapsed*1000)
    ..' peak_slice_ms='..string.format('%.3f',j.peak*1000)..' resumes='..j.resumes..' '..table.concat(fields,' '))
   if err==false then state.failed=state.failed+1;report('write_returned_false')
   else state.completed=state.completed+1 end
   state.last_elapsed=elapsed;state.last_cost=j.cost;state.last_peak=j.peak
   job=nil;state.active=false
  end
 end
 __gm_save_dispatch_v278=dispatch
 __gm_save_step_v278=step
 __gm_save_pairs_v278=stable_pairs
 __gm_save_windows_v278=windows
 __gm_save_freeze_v278=freeze
 local function bind(name,expected)
  local fn=core[name]
  return function(...)
   local automatic=owned()
   local result=maincall(name,fn,...)
   if automatic and expected and type(result)~=expected then
    error('autosave native '..name..' returned '..type(result)..', expected '..expected,0)
   end
   return result
  end
 end
 __gm_save_core_v279={加解密_f=bind('加解密_f','string'),MD5=bind('MD5','string'),
  RC4=bind('RC4','string'),写到文件=bind('写到文件')}
 __gm_save_engine_v279={取运行时间=function()return maincall('clock',引擎.取运行时间,引擎)end}
 __gm_save_debug_v279=function(...)return maincall('debug',调试输出,...)end
 __gm_save_call0_v279=function(fn)return maincall('callback',fn)end
 local run=S.run
 S.run=function(...)tick();return run(...)end
 attach();report('installed')
end
