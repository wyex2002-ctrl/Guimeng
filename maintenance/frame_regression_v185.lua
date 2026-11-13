local work,mode=assert(arg[1]),arg[2] or 'normal'
if mode=='hot' then require('jit.opt').start('hotloop=1','hotexit=1')end
local count=0
local function eq(a,b,msg)count=count+1;assert(a==b,(msg or 'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function pack(...)return {n=select('#',...),...}end
local function load(name,env)local f=assert(loadfile(work..'/'..name..'.ljbc'));setfenv(f,env);return f end
local function make(version,broken)
 local files={};local writes,readbacks,writebytes,frames,skills=0,0,0,0,0
 local tick=0;local elapsed=0
 local clock=function()return tick end
 local S={Game_State=1,sid=0,shelp={},save_info={}}
 local env={os={date=os.date,clock=clock,time=function()return math.floor(elapsed)end}}
 env['核心']={['读入文件']=function(p)readbacks=readbacks+1;return files[p]end,['写到文件']=function(p,s)
  writes=writes+1;writebytes=writebytes+#s
  -- Explicit deterministic I/O-cost model, not a Windows timing claim.
  tick=tick+0.005;elapsed=elapsed+0.005
  if broken then error('disk unavailable')end
  files[p]=s;return true
 end}
 setmetatable(env,{__index=_G})
 S['错误提示']=function(e)return e end
 S.script_setting={['Gly独']={['错误']=function(e)return S['错误提示'](e)end}}
 local dispatch=load('dispatch',env);debug.setupvalue(dispatch,1,S);S.fun=dispatch
 local getter=load('public_get',env);debug.setupvalue(getter,1,S);S.get=getter
 S.run=function(action,...)
  if action=='fun' then return S.fun(...)end
  if action=='qs_skill_drop' then skills=skills+1;return true,false end
  if action==nil then frames=frames+1;tick=tick+0.001;elapsed=elapsed+0.016;return nil,false,7,nil end
  return nil,select('#',...),...
 end
 local install=load('installer_'..version,env);install(S)
 local exporter=load('native_exports',env);debug.setupvalue(exporter,5,load('public_sys',_G))
 local public=exporter(S);eq(public.run,S.run,'actual constructor exports installed run')
 local gameenv=setmetatable({Sys=public,['Ae冻集']={['鼠标_地图坐标']={x=1,y=2}}},{__index=_G})
 local hero={['属性']={['禁攻击']=true},['硬直']=0,['技能信息']={['灵魂火符']={['可用']=true}}}
 hero['技能释放']=load('hero_skill',gameenv)
 local slot={Hero=hero,['绑定技能']='灵魂火符'}
 local release=load('skill_slot',gameenv);S.shelp[tostring(release)]={sid=77,msg='actual skill slot'}
 return {S=S,public=public,hero=hero,slot=slot,release=release,files=files,env=env,
  advance=function(cpu,wall)tick=tick+cpu;elapsed=elapsed+wall end,
  stats=function()return writes,readbacks,writebytes,frames,skills,tick end}
end
local results={}
for _,version in ipairs({'old','new'})do
 local s=make(version);local before=s.stats()
 for i=1,600 do
  local r=pack(s.S.run('fun',s.release,{s.slot}));eq(r[1],true);eq(r[2],false)
  eq(s.hero['下次技能'],nil,'real forbidden-attack gate preserved')
 end
 local w,r,b,f,sk,t=s.stats();eq(sk,600)
 results[version]={writes=w-before,bytes=b,modeled_seconds=t}
 -- Force an actual native error/exit path while routine skill messages remain
 -- buffered; all recent context must survive and critical events stay immediate.
 s.S.__gm_diag_checkpoint_v159('skill.hero.enter','last-pending-skill')
 s.S.__gm_diag_checkpoint_v159('skill.slot.error','test original skill error')
 eq(s.files['Log/guimeng_critical_latest.txt']:find('skill.slot.error',1,true)~=nil,true)
 s.S['错误提示']('actual skill failure')
 local errorlog=s.files['Log/guimeng_error_latest.txt']
 eq(errorlog:find('last%-pending%-skill')~=nil,true)
 eq(errorlog:find('stack traceback',1,true)~=nil,true)
 local n=s.stats();s.S.__gm_diag_checkpoint_v159('reputation.v179','ordinary roll=22 hit=false')
 eq(s.stats()>n,true,'reputation remains immediate')
 eq(s.files['Log/guimeng_critical_latest.txt']:find('ordinary roll=22',1,true)~=nil,true)
 s.S.__gm_diag_exit_v164(true);eq(s.files['Log/guimeng_critical_latest.txt']:find('exit.requested',1,true)~=nil,true)
end
print('REAL_SKILL_IO',mode,results.old.writes,results.new.writes,results.old.bytes,results.new.bytes)
eq(results.new.writes<results.old.writes/20,true,'real skill traffic write reduction')
-- Real nil-action frame entry, original callback dispatcher and public API;
-- timing values are controlled, so slow callback identification is testable.
do
 local s=make('new');local S=s.S
 local slow=function(x)s.advance(0.045,0.045);return nil,x,false,nil end
 S.shelp[tostring(slow)]={sid=42,msg='slow test callback'}
 local r=pack(S.fun(slow,{99},0));eq(r[1],true);eq(r[2],nil);eq(r[3],99);eq(r[4],false)
 for i=1,12 do local q=pack(S.run());eq(q.n,4);eq(q[1],nil);eq(q[2],false);eq(q[3],7);eq(q[4],nil)end
 s.advance(0.01,3);S.run()
 local text=s.files['Log/guimeng_critical_latest.txt']
 for _,key in ipairs({'perf.frame','update_total_ms=','checkpoint_total_ms=','slow_sid=42','slow test callback','timings=inclusive_clock'})do
  eq(text:find(key,1,true)~=nil,true,key)
 end
 -- The clock key is native-only and must not leak through the public getter.
 eq(S.get('__gm_perf_v185'),nil)
end
-- Repeated timing windows remain bounded, and reinstallation is idempotent.
do
 local s=make('new');local S=s.S;local f=S.run
 load('profile_only',s.env)(S);eq(f,S.run)
 for i=1,400 do s.advance(0.001,3);S.run()end
 eq(#s.files['Log/guimeng_critical_latest.txt']<250000,true,'bounded summaries')
 local no={run=function()return 'unchanged' end};local env={os={}}
 setmetatable(env,{__index=_G});load('profile_only',env)(no);eq(no.run(),'unchanged')
end
-- Zero player input: only native update ticks; no skill or action injection
-- is needed for activation markers and periodic timing summaries.
do
 local s=make('new');local _,_,_,before_frames,before_skills=s.stats()
 for i=1,400 do local r=pack(s.public.run());eq(r.n,4);eq(r[1],nil);eq(r[2],false);eq(r[3],7);eq(r[4],nil)end
 local _,_,_,frames,skills=s.stats();eq(frames-before_frames,400);eq(skills-before_skills,0)
 local text=s.files['Log/guimeng_critical_latest.txt']
 for _,key in ipairs({'perf.play.enter','perf.play.return','perf.frame','update_max_ms=','checkpoints='})do eq(text:find(key,1,true)~=nil,true,key)end
end
-- Disk failures never turn a valid game callback into an error.
do
 local s=make('new',true)
 for i=1,100 do local r=pack(s.S.run('fun',s.release,{s.slot}));eq(r[1],true);eq(r[2],false);s.advance(0.001,3);s.S.run()end
 s.S.__gm_diag_exit_v164(true)
end
print('FRAME_AND_SKILL_PASS',mode,count)
