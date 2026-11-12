local work,mode=assert(arg[1]),arg[2] or 'normal'
if mode=='hot' then require('jit.opt').start('hotloop=1','hotexit=1') end
local count=0
local function check(x,msg) count=count+1;assert(x,msg) end
local function make(fail,late)
 local files={['Log/guimeng_detail_latest.txt']='old details',['Log/guimeng_critical_latest.txt']='old critical'}
 local S={Game_State=1,sid=5,save_info={}}
 S.run=function(...) return nil,select('#',...),... end
 local C={}
 C['死亡']=function(v,k) v.dead=true;v['属性'].hp=0;return nil,k,false end
 C['发生伤害']=function(v,a,amount) v['属性'].hp=v['属性'].hp-amount;return nil,amount end
 C['事件回调']=function(v,event)return event,nil,false end
 local env=setmetatable({['核心']={['读入文件']=function(p)return files[p]end,['写到文件']=function(p,d)
  assert(not p:find('log/log',1,true));if fail then error('disk unavailable')end;files[p]=d;return true
 end},Sys=S,['类_事件']=late and nil or C},{__index=_G})
 local f=assert(loadfile(work..'/installer178.ljbc'));setfenv(f,env);f(S)
 return S,C,files,env
end
local v=function()return {id=5,['名称']='多钩猫',['所属阵营']='敌方',['属性']={hp=40,['附加']={['等级']=7}},['宠物配置']={}}end
for _,failure in ipairs({false,true}) do
 local S,C,files=make(failure)
 check(type(S.__gm_detail_v178)=='function','installer must attach detail logger')
 local object=v();local a,b,c=C['死亡'](object,42)
 check(a==nil and b==42 and c==false and object.dead,'death return semantics')
 a,b=C['发生伤害'](v(),{id=0},41);check(a==nil and b==41,'damage result')
 local hostile=setmetatable({},{__index=function()error('diagnostic field unavailable')end})
 a,b=C['发生伤害'](v(),hostile,41);check(a==nil and b==41,'diagnostic accessor failure isolated')
 local err={message='same error object'}
 local ok,value=pcall(S.run,'test');check(ok,'run works')
 S.__gm_diag_checkpoint_v159('reputation.v177','skip ordinary: test')
 if not failure then
  check(files['Log/guimeng_detail_previous.txt']=='old details','detail rotation')
  check(files['Log/guimeng_critical_previous.txt']=='old critical','critical rotation')
  local log=files['Log/guimeng_critical_latest.txt']
  for _,stage in ipairs({'hooks.ready','death.enter','death.return','damage.enter','reputation.v177'})do check(log:find(stage,1,true),'missing '..stage)end
  check(log:find('killer=42',1,true),'killer context')
  for i=1,600 do S.__gm_detail_v178('ordinary',i,false) end
  check(files['Log/guimeng_critical_latest.txt']:find('death.enter',1,true),'critical survives ordinary traffic')
  check(#files['Log/guimeng_detail_latest.txt']<700000,'bounded log')
 end
end
local S,C,files,env=make(false,true)
env['类_事件']=C
local a,b,c,d=S.run('foo',nil,false)
check(a==nil and b==3 and c=='foo' and d==nil,'run nil returns and args preserved')
C['死亡'](v(),0);check(files['Log/guimeng_critical_latest.txt']:find('death.enter',1,true),'late class hooks')
-- Real installer plus diagnostic wrappers: original errors retain their identity.
local E={tag='original error'}
local raw=assert(loadfile(work..'/installer178.ljbc'))
local errorS={run=function()error(E)end,Game_State=1}
local e=setmetatable({Sys=errorS,['核心']={['读入文件']=function()end,['写到文件']=function(p,s)files[p]=s end}}, {__index=_G})
setfenv(raw,e);raw(errorS)
local ok,err=pcall(errorS.run)
check(not ok and err==E,'error identity preserved')
check(files['Log/guimeng_critical_latest.txt']:find('script.run.error',1,true),'error logged')
print('DIAGNOSTICS_PASS',mode,count)
