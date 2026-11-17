local work,mode=assert(arg[1]),arg[2]
if mode=='hot'then jit.opt.start('hotloop=1','hotexit=1')else jit.off()end
local checks,calls=0,0
local function eq(a,b)checks=checks+1;assert(a==b,tostring(a)..' ~= '..tostring(b))end
local function load(name,env)
 local f=assert(loadfile(work..'/'..name..'.ljbc'));setfenv(f,env);return f
end
for _,idx in ipairs({89,97})do
 local expected_actor,expected_state
 local helper=function(actor,state)
  calls=calls+1;eq(actor,expected_actor);eq(state,expected_state)
  return false,nil,'discarded',actor
 end
 local env={__gm_party_wait_v262=helper}
 local entry=load('abi_'..idx,env)
 for i=1,200 do
  local actor={id=i};expected_actor=actor
  if idx==89 then
   local state=i%6;local a;local b={i}
   if i%2==0 then a=false end
   if i%3==0 then b=false elseif i%3==1 then b=nil end
   expected_state=state
   local r0,r1,r2,r3=entry(actor,state,a,b)
   eq(r0,actor);eq(r1,state);eq(r2,a);eq(r3,b)
  else
   expected_state=nil
   local second=i/100;if i%2==0 then second=false end
   local r0,r1=entry(actor,second);eq(r0,actor);eq(r1,second)
  end
 end
 local sentinel={};env.__gm_party_wait_v262=function()error(sentinel)end
 local ok,err=pcall(entry,{},false,nil,true);eq(ok,false);eq(err,sentinel)
end
eq(calls,400)
if mode=='hot'then eq(jit.status(),true)end
print('ENTRY_ABI_V277_PASS',mode,checks,'checks; all original parameters, ignored helper returns, error identity')
