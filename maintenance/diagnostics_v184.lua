-- Native engine diagnostics only: no database globals or game-rule changes.
return function(S)
  if S.__gm_detail_v179 then return end
  local core = 核心
  local busy, seq = false, 0
  local recent, important = {}, {}
  local function text(v)
    local ok, s = pcall(tostring, v)
    return ok and string.sub(s,1,1200) or '<unprintable>'
  end
  local function read(path)
    local ok,v=pcall(function() return core.读入文件('Log/'..path) end)
    return ok and type(v)=='string' and v or nil
  end
  local function write(path,data)
    return pcall(function() core.写到文件('Log/'..path,data) end)
  end
  local header='Guimeng v1.184 diagnostics | '..os.date('%Y-%m-%d %H:%M:%S')..'\r\n'
  for _,name in ipairs({'detail','critical'}) do
    local old=read('guimeng_'..name..'_latest.txt')
    if old then write('guimeng_'..name..'_previous.txt',old) end
    write('guimeng_'..name..'_latest.txt',header)
  end
  local function emit(stage,message,critical)
    if busy then return end
    busy=true
    pcall(function()
      seq=seq+1
      local line=os.date('%Y-%m-%d %H:%M:%S')..' #'..seq..' '..text(stage)..' '..text(message)..' state='..text(S.Game_State)..' script='..text(S.sid)
      recent[#recent+1]=line
      if #recent>512 then table.remove(recent,1) end
      write('guimeng_detail_latest.txt',header..table.concat(recent,'\r\n')..'\r\n')
      if critical then
        important[#important+1]=line
        if #important>256 then table.remove(important,1) end
        write('guimeng_critical_latest.txt',header..table.concat(important,'\r\n')..'\r\n')
      end
    end)
    busy=false
  end
  S.__gm_detail_v179=emit
  local function snapshot(v)
    if type(v)~='table' then return 'object='..text(v) end
    local a=v.属性 or {}; local e=a.附加 or {};local p=v.宠物配置 or {}
    local owner=p.主人
    return 'id='..text(v.id)..' name='..text(v.名称)..' faction='..text(v.所属阵营)..' hp='..text(a.hp)..' level='..text(e.等级)..' object_level='..text(v.等级)..' boss='..text(e.BOSS)..' owner='..text(type(owner)=='table' and owner.id or owner)..' owner_id='..text(v.主人id)..' settled='..text(v.__gm_rep_done_v168)
  end
  local function safe_snapshot(stage,v,extra)
    local ok,s=pcall(snapshot,v)
    local live_ok,live=pcall(function()
      local hero=S.Hero;local a=type(hero)=='table' and hero.属性 or nil
      return ' live_hero_level='..text(type(a)=='table' and a.等级)..' checkpoint='..type(S.__gm_diag_checkpoint_v159)
    end)
    emit(stage,(ok and s or 'snapshot.error='..text(s))..' '..(extra or '')..(live_ok and live or ' hero_snapshot.error='..text(live)),true)
  end
  local function pack(...) return {n=select('#',...),...} end
  -- LuaJIT 2.0 supports xpcall's argument forwarding. Cache one handler per
  -- stage and forward varargs directly: no argument/result tables or fresh
  -- closures on successful high-frequency calls. Keep error identity/trace.
  local error_handlers={}
  local function finish(ok,...)
    if not ok then error((...),0) end
    return ...
  end
  local function call(stage,f,...)
    local handler=error_handlers[stage]
    if not handler then
      handler=function(err)
        local trace=text(err)
        if type(debug)=='table' and type(debug.traceback)=='function' then
          local ok,v=pcall(debug.traceback,text(err),2);if ok then trace=v end
        end
        emit(stage..'.error',trace,true)
        return err
      end
      error_handlers[stage]=handler
    end
    return finish(xpcall(f,handler,...))
  end
  local hooked=setmetatable({},{__mode='k'})
  local function hooks(event_class)
    local C=event_class or 类_事件
    if type(C)~='table' or hooked[C] then return end
    local death,damage,callback=C.死亡,C.发生伤害,C.事件回调
    if type(death)~='function' or type(damage)~='function' or type(callback)~='function' then return end
    hooked[C]=true
    S.__gm_hooks_ready_v179=true
    C.死亡=function(v,k,...)
      safe_snapshot('death.enter',v,'killer='..text(k))
      local results=pack(call('death',death,v,k,...))
      safe_snapshot('death.return',v,'killer='..text(k))
      return unpack(results,1,results.n)
    end
    local hits=0
    C.发生伤害=function(v,attacker,amount,...)
      -- Sample ordinary hits; always record potentially lethal hits.
      hits=hits+1
      local ok,lethal=pcall(function()return tonumber(v.属性.hp) and tonumber(amount) and tonumber(v.属性.hp)<=tonumber(amount)end)
      if hits<=5 or hits%100==0 or (ok and lethal) then
        local actor_ok,actor_id=pcall(function()return type(attacker)=='table' and attacker.id or attacker end)
        safe_snapshot('damage.enter',v,'amount='..text(amount)..' attacker='..text(actor_ok and actor_id or '<unavailable>'))
      end
      return call('damage',damage,v,attacker,amount,...)
    end
    C.事件回调=function(v,event,...)
      if event=='死亡' then safe_snapshot('death.callback',v) end
      return call('event.callback',callback,v,event,...)
    end
    emit('hooks.ready','death/damage/event callbacks installed',true)
  end
  local old=S.__gm_diag_checkpoint_v159
  if type(old)=='function' then
    S.__gm_diag_checkpoint_v159=function(stage,msg,...)
      if stage=='diagnostics.attach.v179' then
        local ok,err=pcall(hooks,msg)
        if not ok then emit('hooks.error',err,true)end
        return
      end
      local tag=text(stage)
      local critical=string.find(tag,'reputation',1,true) or string.find(tag,'error',1,true) or string.find(tag,'exit.',1,true) or (string.find(tag,'load.',1,true) and tag~='load.restore.item')
      if critical then emit(stage,msg,true) end
      return old(stage,msg,...)
    end
  end
  local run=S.run
  local attached=false
  local script_calls=0
  if type(run)=='function' then
    S.run=function(...)
      script_calls=script_calls+1
      local sample=script_calls<=8 or script_calls%1000==0
      if sample and not S.__gm_hooks_ready_v179 then pcall(hooks) end
      if not sample then return call('script.run',run,...) end
      if sample then emit('script.run.enter','call='..script_calls..' action='..text(select(1,...)),false) end
      local result=pack(call('script.run',run,...))
      if sample then emit('script.run.return','call='..script_calls..' results='..result.n,false) end
      return unpack(result,1,result.n)
    end
  end
  local errors=S.错误提示
  if type(errors)=='function' then
    S.错误提示=function(...) emit('engine.error',text(select(1,...)),true);return errors(...) end
  end
  local ok,err=pcall(hooks)
  emit('diagnostics.ready','v1.179 hooks='..text(ok)..' attached='..text(S.__gm_hooks_ready_v179 or false)..' error='..text(err)..' original_checkpoint='..type(old)..' class='..type(类_事件),true)
end
