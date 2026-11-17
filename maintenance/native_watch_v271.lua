-- Diagnostic-only native installation. Never exported to DB or serialized.
return function(S)
 if S.__gm_native_watch_v268 then return end
 local core=核心
 if not core or type(core.写到文件)~='function'then return end
 local ring={};for i=1,48 do ring[i]={}end
 local w={seq=0,frame=0,age=0,last=-1,phase='init',busy=false}
 S.__gm_native_watch_v268=w
 local flush
 local function record(kind,actor,callback)
  w.seq=w.seq+1;local r=ring[(w.seq-1)%48+1]
  r.seq=w.seq;r.frame=w.frame;r.kind=kind;r.phase=w.phase;r.actor=actor;r.callback=callback;r.sid=S.sid;r.action=w.action
  if flush then flush(kind)end
 end
 local function text(v)
  local ok,s=pcall(tostring,v);return ok and string.sub(s,1,180)or'<unprintable>'
 end
 local function describe(a)
  if type(a)~='table'then return text(a)end
  local p=type(a.属性)=='table'and a.属性 or{}
  local at=type(a.地图格子)=='table'and a.地图格子 or{}
  local owner=type(a.宠物配置)=='table'and a.宠物配置.主人
  local target=a.攻击目标 or a.远程目标
  return 'id='..text(a.id)..' name='..text(a.名称 or p.名称)..' owner='..text(type(owner)=='table'and owner.id or a.主人id or owner)
   ..' state='..text(a.当前状态)..' action='..text(a.动作)..' hp='..text(p.hp)..' mp='..text(p.mp)..' level='..text(p.等级)
   ..' xy='..text(at.x)..','..text(at.y)..' target='..text(type(target)=='table'and target.id or target)
   ..' paused='..text(a.动画暂停)..' stiffness='..text(a.硬直)..' arrived='..text(a.抵达目标点)
   ..' next='..text(a.下次技能)..' releases='..text(type(a.释放技能组)=='table'and #a.释放技能组)
 end
 local function callback_label(f)
  local meta=type(S.shelp)=='table'and S.shelp[tostring(f)]
  return type(meta)=='table'and text(meta.msg)or text(f)
 end
 local function output(reason)
  local jitstate=type(jit)=='table'and type(jit.status)=='function'and jit.status()or'unknown'
  local lines={'Guimeng v1.271 native watch | '..os.date('%Y-%m-%d %H:%M:%S'),
   'reason='..text(reason)..' frame='..w.frame..' phase='..text(w.phase)..' game='..text(S.Game_State)..' sid='..text(S.sid)..' jit='..text(jitstate),
   'hero '..describe(S.Hero),'current_actor '..describe(w.actor),'current_callback '..callback_label(w.callback),
   'action='..text(w.action)..' save='..text(w.save)..' (in-progress markers identify immediately recorded operations; older actor rows show current referenced state)'}
  if type(debug)=='table'and type(debug.traceback)=='function'then
   local ok,stack=pcall(debug.traceback,'live operation',2)
   if ok and type(stack)=='string'then lines[#lines+1]=string.sub(stack,1,16384)end
  end
  for n=math.max(1,w.seq-47),w.seq do
   local r=ring[(n-1)%48+1]
   lines[#lines+1]='#'..r.seq..' frame='..r.frame..' '..text(r.kind)..' phase='..text(r.phase)..' sid='..text(r.sid)..' action='..text(r.action)
    ..(r.actor and(' actor '..describe(r.actor))or'')..(r.callback and(' callback '..callback_label(r.callback))or'')
  end
  core.写到文件('Log/guimeng_native_watch_latest.txt',table.concat(lines,'\r\n')..'\r\n')
 end
 flush=function(reason)
  if w.busy then return end
  w.busy=true;pcall(output,reason);w.busy=false
 end
 -- Rotate once, keeping the prior attempt intact; write failures never stop play.
 if type(core.读入文件)=='function'then
  local ok,previous=pcall(core.读入文件,'Log/guimeng_native_watch_latest.txt')
  if ok and type(previous)=='string'then pcall(core.写到文件,'Log/guimeng_native_watch_previous.txt',previous)end
 end
 local function trace(stage,err)
  local msg=text(err)
  if type(debug)=='table'and type(debug.traceback)=='function'then
   local ok,t=pcall(debug.traceback,msg,2);if ok then msg=t end
  end
  record(stage,w.actor,w.callback);flush(stage..' '..msg)
  local emit=S.__gm_detail_v179
  if type(emit)=='function'then pcall(emit,stage,msg,true)end
  return err
 end
 local function save_error(err)return trace('native.save.error',err)end
 local function save_finished(ok,...)
  w.save=ok and'returned'or'error';record('save.'..w.save);flush('save.'..w.save)
  if not ok then error((...),0)end
  return ...
 end
 local saved_wrapper
 local function attach_save()
  local e=S.script_setting;local g=type(e)=='table'and e.Gly独
  local f=type(g)=='table'and g.存档
  if type(f)~='function'or f==saved_wrapper then return end
  local original=f
  -- One wrapper per installed API, not per call. Original varargs/errors retained.
  saved_wrapper=function(...)
   w.save='entered';record('save.enter');flush('save.enter')
   return save_finished(xpcall(original,save_error,...))
  end
  g.存档=saved_wrapper
 end
 local phase=S.__gm_perf_phase_v186
 if type(phase)=='function'then
  S.__gm_perf_phase_v186=function(name)
   w.phase=name;record('phase');return phase(name)
  end
 end
 local actor=S.__gm_perf_actor_v189
 if type(actor)=='function'then
  S.__gm_perf_actor_v189=function(start,v)
   if start then w.actor=v;record('actor.enter',v)else record('actor.return',w.actor);w.actor=nil end
   return actor(start,v)
  end
 end
 local fun=S.fun
 if type(fun)=='function'then
  local function returned(previous,...)
   record('callback.return',nil,w.callback);w.callback=previous;return ...
  end
  S.fun=function(f,...)
   local previous=w.callback;w.callback=f;record('callback.enter',nil,f)
   return returned(previous,fun(f,...))
  end
 end
 local run=S.run
 if type(run)=='function'then
  local sampled=false
  local function frame_error(err)return trace('native.frame.error',err)end
  local function frame_finished(ok,...)
   record('frame.return',w.actor,w.callback)
   if sampled then flush(ok and'frame.return'or'frame.error')end
   if not ok then error((...),0)end
   return ...
  end
  local function action_finished(previous,...)
   record('action.return',w.actor,w.callback);w.action=previous
   pcall(attach_save);return ...
  end
  S.run=function(action,...)
   if action~=nil then
    local previous=w.action;w.action=action;record('action.enter',w.actor,w.callback)
    return action_finished(previous,run(action,...))
   end
   w.frame=w.frame+1;w.actor=nil;w.callback=nil;w.phase='frame.begin'
   local delta=dt
   if type(delta)=='number'and delta==delta and delta>0 then w.age=w.age+math.min(delta,1)end
   sampled=true -- user explicitly requests immediate logging without sampling
   if sampled then w.last=w.age;record('frame.enter');flush('frame.enter')end
   return frame_finished(xpcall(run,frame_error,action,...))
  end
 end
 pcall(attach_save);record('installed');flush('installed')
end
