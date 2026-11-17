-- Game-local diagnostics only. No OS event service, registry or native hook.
return function(S)
 local core=核心
 if not core or type(core.写到文件)~='function' or type(os)~='table' or type(os.exit)~='function' then return end
 local prior=os.__gm_exit_watch_v270
 if type(prior)=='table' and prior.wrapper==os.exit then
  prior.sys=S;S.__gm_exit_watch_v270=prior;return
 end
 local original=os.exit
 local w={sys=S,requests=0,busy=false}
 local function safe(v)
  local ok,s=pcall(tostring,v)
  return ok and string.sub(s,1,240) or '<unprintable>'
 end
 local function write(stage,...)
  local s=w.sys;local native=s.__gm_native_watch_v268
  local lines={'Guimeng v1.274 game exit watch | '..(type(os.date)=='function'and os.date('%Y-%m-%d %H:%M:%S')or'unavailable')..'',
   'stage='..stage..' requests='..w.requests..' game='..safe(s.Game_State)..' sid='..safe(s.sid),
   'frame='..safe(type(native)=='table' and native.frame)..' phase='..safe(type(native)=='table' and native.phase),
   'save='..safe(type(native)=='table' and native.save),
   'This records script os.exit requests, not native faults or a confirmed crash cause.'}
  if stage=='exit.enter' then
   lines[#lines+1]='argc='..select('#',...)
   for i=1,math.min(select('#',...),8)do lines[#lines+1]='arg'..i..'='..safe(select(i,...))end
   if type(debug)=='table' and type(debug.traceback)=='function' then
    local ok,stack=pcall(debug.traceback,'game exit requested',2)
    if ok and type(stack)=='string'then lines[#lines+1]=string.sub(stack,1,16384)end
   end
  end
  core.写到文件('Log/guimeng_exit_latest.txt',table.concat(lines,'\r\n')..'\r\n')
 end
 local function emit(...)
  if w.busy then return end
  w.busy=true;pcall(write,'exit.enter',...);w.busy=false
 end
 w.wrapper=function(...)
  w.requests=w.requests+1
  emit(...)
  return original(...)
 end
 -- Rotate only at installation, before any request. Never append unboundedly.
 if type(core.读入文件)=='function'then
  local ok,data=pcall(core.读入文件,'Log/guimeng_exit_latest.txt')
  if ok and type(data)=='string'then pcall(core.写到文件,'Log/guimeng_exit_previous.txt',data)end
 end
 os.__gm_exit_watch_v270=w;S.__gm_exit_watch_v270=w;os.exit=w.wrapper
 pcall(write,'installed')
end
