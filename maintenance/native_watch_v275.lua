-- Diagnostic-only native installation. Never exported to DB or serialized.
return function(S)
 if S.__gm_native_watch_v268 then return end
 local core=核心
 if not core or type(core.写到文件)~='function'then return end
 local ring={};for i=1,256 do ring[i]={}end
 local w={seq=0,frame=0,age=0,last=-1,phase='init',busy=false,depth=0,event_seq=0}
 S.__gm_native_watch_v268=w
 local flush
 local counts={}
 local events={};for i=1,128 do events[i]={}end
 local observed=setmetatable({},{__mode='k'})
 local target_fields={'攻击目标','远程目标','待选目标','__gm_queued_target_v155'}
 local function record(kind,actor,callback,detail)
  w.seq=w.seq+1;local r=ring[(w.seq-1)%256+1]
  r.seq=w.seq;r.frame=w.frame;r.kind=kind;r.phase=w.phase;r.actor=actor;r.callback=callback;r.sid=S.sid;r.action=w.action
  r.detail=detail;counts[kind]=(counts[kind]or 0)+1
 end
 local function text(v)
  local ok,s=pcall(tostring,v);return ok and string.sub(s,1,180)or'<unprintable>'
 end
 -- These event strings are frozen at the observation point. They do not retain
 -- entity references, and ordinary update traffic cannot evict this event ring.
 local function event(kind,msg)
  w.event_seq=w.event_seq+1;local r=events[(w.event_seq-1)%128+1]
  r.seq=w.event_seq;r.frame=w.frame;r.phase=w.phase;r.sid=S.sid;r.kind=kind;r.msg=msg
 end
 local function describe_raw(a)
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
   ..' valid='..text(a.是否有效)..' gone='..text(a.已经消失)..' dead='..text(a.已经死亡)
 end
 local function describe(a)
  local ok,msg=pcall(describe_raw,a)
  return ok and msg or('<entity context unavailable: '..text(msg)..'>')
 end
 local function observe_target(a,last,key,source)
  local t=a[key]
  local tid,thp,tv,tg,td
  if type(t)=='table'then
   tid=t.id;local at=t.属性
   if type(at)=='table'then thp=at.hp end
   tv=t.是否有效;tg=t.已经消失;td=t.已经死亡
  else tid=t end
  if last.ref~=t or last.hp~=thp or last.valid~=tv or last.gone~=tg or last.dead~=td then
   event('target.change','at='..source..' actor='..text(a.id)..' field='..key
    ..' old_id='..text(last.id)..' old_hp='..text(last.hp)..' old_valid='..text(last.valid)..' old_gone='..text(last.gone)..' old_dead='..text(last.dead)
    ..' new_id='..text(tid)..' new_hp='..text(thp)..' new_valid='..text(tv)..' new_gone='..text(tg)..' new_dead='..text(td))
   last.ref=t;last.id=tid;last.hp=thp;last.valid=tv;last.gone=tg;last.dead=td
  end
 end
 local function observe(a,source)
  if type(a)~='table'then return end
  local p=type(a.属性)=='table'and a.属性 or{}
  local old=observed[a]
  if not old then old={targets={{},{},{},{}}};observed[a]=old end
  local hp,valid,gone,dead=p.hp,a.是否有效,a.已经消失,a.已经死亡
  if not old.seen or old.hp~=hp or old.valid~=valid or old.gone~=gone or old.dead~=dead then
   event('actor.life','at='..source..' old_hp='..text(old.hp)..' old_valid='..text(old.valid)..' old_gone='..text(old.gone)..' '..describe(a))
   old.hp=hp;old.valid=valid;old.gone=gone;old.dead=dead;old.seen=true
  end
  local owner=type(a.宠物配置)=='table'and a.宠物配置.主人
  if a~=S.Hero and owner==nil and a.主人id==nil and a.所属阵营~='友方'then return end
  -- Four fixed fields: keep this boundary free of an inner iterator. The
  -- iterator version reproduced a LuaJIT 2.0 continuation failure when called
  -- from the real native phase hook (see the full-frame hot regression).
  observe_target(a,old.targets[1],target_fields[1],source)
  observe_target(a,old.targets[2],target_fields[2],source)
  observe_target(a,old.targets[3],target_fields[3],source)
  observe_target(a,old.targets[4],target_fields[4],source)
  local n=type(a.释放技能组)=='table'and #a.释放技能组
  if old.state~=a.当前状态 or old.next~=a.下次技能 or old.queued~=a.__gm_queued_skill_v155 or old.releases~=n then
   event('skill.state','at='..source..' '..describe(a)..' queued='..text(a.__gm_queued_skill_v155))
   old.state=a.当前状态;old.next=a.下次技能;old.queued=a.__gm_queued_skill_v155;old.releases=n
  end
 end
 local function watch(a,source)
  local ok=pcall(observe,a,source)
  if not ok then w.observation_failures=(w.observation_failures or 0)+1 end
 end
 local function callback_label(f)
  local meta=type(S.shelp)=='table'and S.shelp[text(f)]
  return type(meta)=='table'and text(meta.msg)or text(f)
 end
 local function output(reason)
  local jitstate=type(jit)=='table'and type(jit.status)=='function'and jit.status()or'unknown'
  local lines={'Guimeng v1.275 native watch | '..os.date('%Y-%m-%d %H:%M:%S'),
   'reason='..text(reason)..' frame='..w.frame..' phase='..text(w.phase)..' game='..text(S.Game_State)..' sid='..text(S.sid)..' jit='..text(jitstate),
   'hero '..describe(S.Hero),'current_actor '..describe(w.actor),'current_callback '..callback_label(w.callback),
   'action='..text(w.action)..' save='..text(w.save)..' (sampled disk snapshots; actor history uses current referenced state)'}
  lines[#lines+1]='hooks checkpoint='..text(w.checkpoint_attached)..' detail='..text(w.detail_attached)..' projectile='..text(w.projectile_attached)..' observation_failures='..text(w.observation_failures or 0)
  if w.projectile then lines[#lines+1]='projectile '..text(w.projectile.id)..' operation='..text(w.projectile_operation)..' skill='..text(w.projectile.skill)..' owner '..describe(w.projectile.actor)..' launch_target '..describe(w.projectile.target)end
  if w.fault then lines[#lines+1]='FIRST_LUA_FAULT '..w.fault end
  if reason~='frame.enter'and reason~='frame.return'and type(debug)=='table'and type(debug.traceback)=='function'then
   local ok,stack=pcall(debug.traceback,'live operation',2)
   if ok and type(stack)=='string'then lines[#lines+1]=string.sub(stack,1,16384)end
  end
  local context={}
  for _,key in ipairs({'屏幕事件组','屏幕子弹组','屏幕粒子组','屏幕特效组','动画精灵组','界面_窗口_数组','time_table','创建窗口组'})do
   local v=S[key];context[#context+1]=key..'='..(type(v)=='table'and #v or -1)
  end
  lines[#lines+1]='collections '..table.concat(context,' ')
  local totals={};for key,value in pairs(counts)do totals[#totals+1]=key..'='..value end
  table.sort(totals);lines[#lines+1]='totals '..table.concat(totals,' ')
  if type(collectgarbage)=='function'then local ok,kb=pcall(collectgarbage,'count');if ok then lines[#lines+1]='lua_heap_kib='..text(kb)end end
  lines[#lines+1]='FROZEN_EVENTS (observed changes, not proof of a selection decision or native fault)'
  for n=math.max(1,w.event_seq-127),w.event_seq do
   local r=events[(n-1)%128+1]
   lines[#lines+1]='@'..r.seq..' frame='..r.frame..' phase='..text(r.phase)..' sid='..text(r.sid)..' '..r.kind..' '..r.msg
  end
  for n=math.max(1,w.seq-255),w.seq do
   local r=ring[(n-1)%256+1]
   lines[#lines+1]='#'..r.seq..' frame='..r.frame..' '..text(r.kind)..' phase='..text(r.phase)..' sid='..text(r.sid)..' action='..text(r.action)..' detail='..text(r.detail)
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
 local function fault_text(stage,err)
  local msg=text(err)
  if type(debug)=='table'and type(debug.traceback)=='function'then
   local ok,t=pcall(debug.traceback,msg,2);if ok then msg=t end
  end
  return stage..' action='..text(w.action)..' callback='..callback_label(w.callback)..' actor '..describe(w.actor)
   ..' projectile='..text(w.projectile and w.projectile.id)..' operation='..text(w.projectile_operation)
   ..' skill='..text(w.projectile and w.projectile.skill)..' projectile_owner '..describe(w.projectile and w.projectile.actor)
   ..' launch_target '..describe(w.projectile and w.projectile.target)..'\r\n'..msg
 end
 local function emit_fault(stage,msg)
  local emit=S.__gm_detail_v179
  if type(emit)=='function'then pcall(emit,stage,msg,true)end
 end
 local function trace(stage,err)
  if w.fault then return err end
  local ok,msg=pcall(fault_text,stage,err)
  w.fault=ok and msg or(stage..' error='..text(err)..' (context unavailable)')
  record(stage,w.actor,w.callback);flush(stage)
  pcall(emit_fault,stage,w.fault)
  return err
 end
 local function begin()
  if w.depth==0 then w.fault=nil end
  w.depth=w.depth+1
 end
 local function save_error(err)return trace('native.save.error',err)end
 local function save_finished(ok,...)
  w.save=ok and'returned'or'error';record('save.'..w.save);flush('save.'..w.save)
  w.depth=w.depth-1
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
   begin()
   w.save='entered';record('save.enter');flush('save.enter')
   return save_finished(xpcall(original,save_error,...))
  end
  g.存档=saved_wrapper
 end
 local phase=S.__gm_perf_phase_v186
 if type(phase)=='function'then
  S.__gm_perf_phase_v186=function(name)
   if w.phase=='hero_update'then watch(S.Hero,'hero.update.return')end
   w.phase=name;record('phase')
   if name=='hero_update'then watch(S.Hero,'hero.update.enter')end
   return phase(name)
  end
 end
 local actor=S.__gm_perf_actor_v189
 if type(actor)=='function'then
  S.__gm_perf_actor_v189=function(start,v)
   if start then w.actor=v;watch(v,'actor.enter');record('actor.enter',v)else watch(w.actor,'actor.return');record('actor.return',w.actor);w.actor=nil end
   return actor(start,v)
  end
 end
 local fun=S.fun
 if type(fun)=='function'then
  local function callback_error(err)return trace('native.callback.error',err)end
  local function returned(previous,ok,...)
   record(ok and'callback.return'or'callback.failed',nil,w.callback)
   w.callback=previous;w.depth=w.depth-1
   if not ok then error((...),0)end
   return ...
  end
  S.fun=function(f,...)
   begin();local previous=w.callback;w.callback=f;record('callback.enter',nil,f)
   return returned(previous,xpcall(fun,callback_error,f,...))
  end
 end
 -- Fixed per-instance wrappers; no new closure or argument table per frame.
 local projectile_id=0
 local function projectile_error(err)return trace('native.projectile.error',err)end
 local function projectile_result(meta,key,value)
  if key=='已经消失'and value and not meta.gone then
   meta.gone=true;event('projectile.gone','id='..meta.id..' skill='..text(meta.skill))
  elseif key=='取命中对象'and meta.hit~=value then
   meta.hit=value;event('projectile.hit','id='..meta.id..' skill='..text(meta.skill)..' target='..text(type(value)=='table'and value.id or value))
  end
 end
 local function wrap_projectile_method(original,key,meta)
  local function finished(previous,operation,ok,...)
   record(ok and'projectile.return'or'projectile.failed',nil,nil,key)
   if ok then pcall(projectile_result,meta,key,(...))end
   w.projectile=previous;w.projectile_operation=operation;w.depth=w.depth-1
   if not ok then error((...),0)end
   return ...
  end
  return function(...)
   begin();local previous,operation=w.projectile,w.projectile_operation
   w.projectile=meta;w.projectile_operation=key;record('projectile.enter',nil,nil,key)
   if key=='销毁'then event('projectile.destroy','id='..meta.id..' skill='..text(meta.skill))end
   return finished(previous,operation,xpcall(original,projectile_error,...))
  end
 end
 local function attach_projectile(object,meta)
  if type(object)~='table'then return end
  for _,key in ipairs({'更新','显示','销毁','已经消失','取命中对象'})do
   local original=object[key]
   if type(original)=='function'then object[key]=wrap_projectile_method(original,key,meta)end
  end
 end
 local function projectile_created(meta,info)
  if type(info)=='table'then meta.skill=info.技能名称 end
  event('projectile.create','id='..meta.id..' skill='..text(meta.skill)..' owner='..text(type(meta.actor)=='table'and meta.actor.id)..' target='..text(type(meta.target)=='table'and meta.target.id))
 end
 local function projectile_before(actor,target,info)
  begin();projectile_id=projectile_id+1
  local meta={id=projectile_id,actor=actor,target=target,previous=w.projectile,operation=w.projectile_operation}
  w.projectile=meta;w.projectile_operation='create'
  pcall(projectile_created,meta,info)
  return meta
 end
 local function projectile_after(meta,ok,...)
  if ok then pcall(attach_projectile,(...),meta)end
  w.projectile=meta.previous;w.projectile_operation=meta.operation
  meta.previous=nil;meta.operation=nil;w.depth=w.depth-1
  if not ok then error((...),0)end
  return ...
 end
 -- Small synchronous skill breadcrumbs, separate from the large sampled
 -- snapshot. At most 12 frozen lines; never emitted by ordinary actor updates.
 local steps={};local step_seq=0;local step_busy=false;local step_active=false;local step_age=-1
 local step_stages={['skill.event.enter']=true,['skill.dispatch.begin']=true,['skill.dispatch.return']=true,
  ['skill.selector.enter']=true,['skill.selector.target']=true,['skill.selector.native_path']=true,
  ['skill.slot.enter']=true,['skill.slot.call_hero']=true,['skill.slot.return']=true,['skill.slot.error']=true,
  ['skill.hero.enter']=true,['skill.hero.range.begin']=true,['skill.hero.range.return']=true}
 if type(core.读入文件)=='function'then
  local ok,data=pcall(core.读入文件,'Log/guimeng_skill_steps_latest.txt')
  if ok and type(data)=='string'then pcall(core.写到文件,'Log/guimeng_skill_steps_previous.txt',data)end
 end
 local function step_write(stage,msg)
  step_seq=step_seq+1
  steps[#steps+1]='#'..step_seq..' '..os.date('%H:%M:%S')..' frame='..w.frame..' phase='..text(w.phase)
   ..' sid='..text(S.sid)..' stage='..stage..' value='..text(msg)..' '..describe(S.Hero)
  if #steps>12 then table.remove(steps,1)end
  core.写到文件('Log/guimeng_skill_steps_latest.txt','Guimeng v1.275 skill steps | '..os.date('%Y-%m-%d %H:%M:%S')
   ..'\r\nSampled skill attempts (0.25s gate), synchronous checkpoints; not proof of a native fault.\r\n'..table.concat(steps,'\r\n')..'\r\n')
 end
 local function step(stage,msg)
  if stage=='skill.event.enter'then
   step_active=w.age-step_age>=.25
   if step_active then step_age=w.age end
  end
  if not step_active or w.age-step_age>1.5 or not step_stages[stage]or step_busy then return end
  step_busy=true;pcall(step_write,stage,msg);step_busy=false
  if stage=='skill.slot.return'or stage=='skill.slot.error'then step_active=false end
 end
 local detail_wrapper,checkpoint_wrapper
 local function attach_sources()
  local diagnostic=S.__gm_detail_v179
  if type(diagnostic)=='function'and diagnostic~=detail_wrapper then
   detail_wrapper=function(stage,msg,...)
    record('diagnostic',nil,nil,text(stage)..' '..text(msg))
    if type(stage)=='string'and(stage:find('error',1,true)or stage:find('exit',1,true))then flush('critical '..text(stage))end
    return diagnostic(stage,msg,...)
   end
   S.__gm_detail_v179=detail_wrapper;w.detail_attached=true
  end
  local checkpoint=S.__gm_diag_checkpoint_v159
  if type(checkpoint)=='function'and checkpoint~=checkpoint_wrapper then
   checkpoint_wrapper=function(stage,msg,...)
    step(stage,msg)
    if type(stage)=='string'and(stage:find('skill.selector.',1,true)or stage=='skill.hero.enter'or stage:find('error',1,true))then
     event('checkpoint',text(stage)..' '..text(msg));watch(S.Hero,'checkpoint:'..stage)
    end
    return checkpoint(stage,msg,...)
   end
   S.__gm_diag_checkpoint_v159=checkpoint_wrapper;w.checkpoint_attached=true
  end
  local env=getfenv(1);local factory=env.子弹类
  if type(factory)=='function'then
   local state=rawget(env,'__gm_projectile_watch_v274')
   if type(state)~='table'or factory~=state.wrapper then
    state={original=factory}
    state.wrapper=function(...)
     local a,b,c,d,e,actor,target,h,i,j,k,l,m,n,o,info=...
     local meta=state.before(actor,target,info)
     return state.after(meta,xpcall(state.original,state.onerror,...))
    end
    env.__gm_projectile_watch_v274=state;env.子弹类=state.wrapper
   end
   state.before=projectile_before;state.after=projectile_after;state.onerror=projectile_error
   w.projectile_attached=true
  end
 end
 local run=S.run
 if type(run)=='function'then
  local sampled=false
  local function frame_error(err)return trace('native.frame.error',err)end
  local function frame_finished(ok,...)
   watch(S.Hero,'frame.return')
   record('frame.return',w.actor,w.callback)
   if sampled then flush(ok and'frame.return'or'frame.error')end
   w.depth=w.depth-1
   if not ok then error((...),0)end
   return ...
  end
  local function action_error(err)return trace('native.action.error',err)end
  local function action_finished(previous,ok,...)
   if w.action=='qs_skill_drop'then watch(S.Hero,'skill.dispatch.return')end
   record(ok and'action.return'or'action.failed',w.actor,w.callback);w.action=previous;w.depth=w.depth-1
   pcall(attach_save);pcall(attach_sources)
   if not ok then error((...),0)end
   return ...
  end
  S.run=function(action,...)
   begin()
   if action~=nil then
    local previous=w.action;w.action=action;record('action.enter',w.actor,w.callback)
    return action_finished(previous,xpcall(run,action_error,action,...))
   end
   w.frame=w.frame+1;w.actor=nil;w.callback=nil;w.phase='frame.begin'
   watch(S.Hero,'frame.enter')
   local delta=dt
   if type(delta)=='number'and delta==delta and delta>0 then w.age=w.age+math.min(delta,1)end
   sampled=w.age-w.last>=.5
   if sampled then w.last=w.age;record('frame.enter');flush('frame.enter')end
   return frame_finished(xpcall(run,frame_error,action,...))
  end
 end
 pcall(attach_save);pcall(attach_sources);record('installed');flush('installed')
end
