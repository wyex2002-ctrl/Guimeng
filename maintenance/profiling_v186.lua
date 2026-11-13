-- Native-only, bounded, low-frequency timing. No database/global API additions.
return function(S)
  if S.__gm_perf_v185 then return end
  local emit=S.__gm_detail_v179
  local clock=type(os)=='table' and os.clock
  if type(emit)~='function' or type(clock)~='function' then return end
  local wall=type(os.time)=='function' and os.time or clock
  local window=wall()
  local updates,update_total,update_max,gap_max,last_start=0,0,0,0,nil
  local callbacks,callback_total,callback_max,slow_sid,slow_label=0,0,0,nil,nil
  local checkpoints,checkpoint_total,checkpoint_max=0,0,0
  local reporting=false
  local phase_names={'prepare','input','effects_update','actors_update','map_update','hero_update','bulk_sale','alt_pickup','windows_order','world_render','map_draw','world_overlay','tooltip','bubbles','scene_composite','mask_draw','windows_draw','labels_effects','sprite_update','final_ui','timers','debug','http_queue'}
  local allowed={};for _,name in ipairs(phase_names)do allowed[name]=true end
  local phase_time,phase_peak={},{}
  local phase_name,phase_started=nil,0
  local report_write_ms=0
  local function charge_phase(now)
    if phase_name then
      local dt=now-phase_started
      phase_time[phase_name]=(phase_time[phase_name] or 0)+dt
      if dt>(phase_peak[phase_name] or 0)then phase_peak[phase_name]=dt end
      phase_started=now
    end
  end
  S.__gm_perf_phase_v186=function(name)
    local now=clock()
    if name=='prepare' then phase_name=nil else charge_phase(now)end
    phase_name=allowed[name] and name or nil
    phase_started=now
  end
  local first_update_entered,first_update_returned=false,false
  S.__gm_perf_v185=true
  local function report(force)
    if reporting or S.Game_State~=1 then return end
    local now=wall();local elapsed=now-window
    if not force and elapsed<2 then return end
    reporting=true
    charge_phase(clock())
    local parts={};local peak_name,peak= '<none>',0
    for _,name in ipairs(phase_names)do
      local total=phase_time[name]or 0
      if total>0 then parts[#parts+1]=name..':'..math.floor(total*1000)end
      if (phase_peak[name]or 0)>peak then peak_name,peak=name,phase_peak[name]end
    end
    local function size(name)local t=S[name];return type(t)=='table' and #t or 0 end
    local msg='window_seconds='..tostring(elapsed)..' updates='..updates
      ..' update_total_ms='..math.floor(update_total*1000)
      ..' update_max_ms='..math.floor(update_max*1000)
      ..' update_gap_max_ms='..math.floor(gap_max*1000)
      ..' callbacks='..callbacks..' callback_total_ms='..math.floor(callback_total*1000)..' callback_max_ms='..math.floor(callback_max*1000)
      ..' slow_sid='..tostring(slow_sid)..' slow_label='..tostring(slow_label)
      ..' checkpoints='..checkpoints..' checkpoint_total_ms='..math.floor(checkpoint_total*1000)
      ..' checkpoint_max_ms='..math.floor(checkpoint_max*1000)
      ..' phase_peak='..peak_name..' phase_peak_ms='..math.floor(peak*1000)
      ..' phases_ms='..table.concat(parts,',')
      ..' actors='..size('屏幕事件组')..' particles='..size('屏幕粒子组')
      ..' effects='..size('屏幕特效组')..' sprites='..size('动画精灵组')
      ..' prior_report_write_ms='..report_write_ms
      ..' timings=inclusive_clock window='..(wall==clock and 'clock' or 'os.time')
    local write_start=clock()
    pcall(emit,'perf.frame',msg,true)
    report_write_ms=math.floor((clock()-write_start)*1000)
    window=now
    updates,update_total,update_max,gap_max=0,0,0,0
    callbacks,callback_total,callback_max,slow_sid,slow_label=0,0,0,nil,nil
    checkpoints,checkpoint_total,checkpoint_max=0,0,0
    phase_time,phase_peak={},{}
    if phase_name then phase_started=clock()end
    reporting=false
  end
  local checkpoint=S.__gm_diag_checkpoint_v159
  if type(checkpoint)=='function' then
    local function finished(start,...)
      local dt=clock()-start;checkpoints=checkpoints+1
      checkpoint_total=checkpoint_total+dt
      if dt>checkpoint_max then checkpoint_max=dt end
      return ...
    end
    S.__gm_diag_checkpoint_v159=function(...)
      return finished(clock(),checkpoint(...))
    end
  end
  local fun=S.fun
  if type(fun)=='function' then
    local function finished(start,f,...)
      local dt=clock()-start;callbacks=callbacks+1;callback_total=callback_total+dt
      if dt>callback_max then
        callback_max=dt
        -- Resolve names only for a new slow maximum; keep one bounded record.
        local meta=type(S.shelp)=='table' and S.shelp[tostring(f)]
        slow_sid=type(meta)=='table' and meta.sid or nil
        slow_label=type(meta)=='table' and string.sub(tostring(meta.msg),1,160) or '<unregistered>'
      end
      -- Summaries run after the native update returns, never inside a callback.
      return ...
    end
    S.fun=function(f,...)return finished(clock(),f,fun(f,...))end
  end
  local run=S.run
  if type(run)=='function' then
    local function finished(start,...)
      local dt=clock()-start;updates=updates+1;update_total=update_total+dt
      if first_update_entered and not first_update_returned then
        first_update_returned=true
        pcall(emit,'perf.play.return','first_update_ms='..math.floor(dt*1000),true)
      end
      if dt>update_max then update_max=dt end
      report(false)
      return ...
    end
    S.run=function(action,...)
      if action~=nil then return run(action,...) end
      if S.Game_State==1 and not first_update_entered then
        first_update_entered=true
        pcall(emit,'perf.play.enter','first active native update; no player input required',true)
      end
      local start=clock()
      if last_start and start-last_start>gap_max then gap_max=start-last_start end
      last_start=start
      return finished(start,run(action,...))
    end
  end
  local exit=S.__gm_diag_exit_v164
  if type(exit)=='function' then
    S.__gm_diag_exit_v164=function(force,...)
      if force then report(true)end
      return exit(force,...)
    end
  end
end
