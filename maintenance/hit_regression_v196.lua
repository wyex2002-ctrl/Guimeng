local work,mode=arg[1],arg[2]or'normal'
if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end
local checks=0
local function eq(a,b,label)checks=checks+1;assert(a==b,(label or'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function near(a,b)checks=checks+1;assert(math.abs(a-b)<1e-9,tostring(a)..' ~= '..tostring(b))end
local function load(n,env)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,env or _G);return f end
local layouts=assert(loadfile(work..'/metadata.lua'))()
local monster_ids=assert(loadfile(work..'/monsters.lua'))()
local roll,calls=70,0
local function random(a,b)eq(a,1);eq(b,100);calls=calls+1;return roll end
local engine={['取随机整数']=function(_,a,b)return random(a,b)end}
local db={['Gly独']={['取随机数']=random}}
local install=load('sandbox_install');debug.setupvalue(install,1,{script_setting=db,tbl_controls={}});install();eq(db.Sys,nil);eq(db._G,nil);eq(db.pcall,nil)
local native={['引擎']=engine}
local function env(name)return(name=='basic'or name=='native_monster'or name=='native_hero')and native or db end
local function args(info,A,D,absolute)
 local name,n,ar,dr,den=unpack(info);local t={}
 t[ar+1]=A;t[dr+1]=D
 if name=='basic'or name=='native_monster'or name=='native_hero'then t[2]={['被击中']=function()end}end
 -- The old denominator may contain a second copy of A; initialize inputs
 -- without changing the actual field fetches in each decision fragment.
 if den~=ar then t[den+1]=A end
 if name=='merc'then t[5]={['行会选中']={}}end
 if name=='monster'then t[5]={['准确几率']=A}end
 if name=='native_monster'then t[22]={['命中']=A};t[24]={['躲避']=D};t[11]={['绝对命中']=absolute or 0}end
 if name=='native_hero'then t[14]={['命中']=A};t[15]={['躲避']=D};t[9]={['绝对命中']=absolute or 0}end
 return t,n
end
local cases={{20,20,71.42857142857143},{10,20,55.55555555555556},{40,20,83.33333333333333},{80,20,90.9090909090909},{0,20,0},{20,0,100},{1,1000,0.24937655860349128},{0.5,0.25,83.33333333333333},{1e300,1e300,71.42857142857143}}
local cached={}
for _,info in ipairs(layouts)do
 local name=info[1];local new=load(name..'_new_ratio',env(name));local old=load(name..'_old_ratio',env(name));local decision=load(name..'_new_decision',env(name));local previous=load(name..'_old_decision',env(name));cached[name]={info,decision}
 for _,c in ipairs(cases)do
  local t,n=args(info,c[1],c[2]);near(new(unpack(t,1,n)),c[3]);near(old(unpack(t,1,n)),100*c[1]/(c[1]+c[2]))
  -- Exact predicate on either side of the theoretical probability.
  for _,r in ipairs({math.max(1,math.floor(c[3])),math.min(100,math.floor(c[3])+1)})do
   roll=r;calls=0;local value=decision(unpack(t,1,n));eq(type(value)=='number',r<=c[3],name..' boundary');eq(calls,1,name..' single draw')
  end
 end
 local t,n=args(info,20,20);roll=70;calls=0;eq(type(previous(unpack(t,1,n))),'table','baseline 50% misses 70');eq(type(decision(unpack(t,1,n))),'number','new formula hits 70');eq(calls,2)
 t,n=args(info,0,0);roll=1;eq(type(decision(unpack(t,1,n))),'table','zero/zero safely misses without division')
 if name=='native_monster'or name=='native_hero'then
  t,n=args(info,0,100,1);calls=0;eq(type(decision(unpack(t,1,n))),'number','absolute hit retained');eq(calls,0,'absolute hit does not draw')
 end
end
-- Each registered monster uses its own actual relocated bytecode.
local info=cached.monster[1];local t,n=args(info,20,20);roll=70
for _,i in ipairs(monster_ids)do local f=load('monster_'..i,db);calls=0;eq(type(f(unpack(t,1,n))),'number');eq(calls,1)end
-- One representative repeat scenario, 200 total, not per layout/monster.
local info,f=unpack(cached.hero);local t,n=args(info,20,20)
for i=1,200 do roll=(i-1)%100+1;calls=0;eq(type(f(unpack(t,1,n)))=='number',roll<=71);eq(calls,1)end
-- Execute complete native damage entry points with a real script decision
-- returning a damage table. Native fallback must not roll for hit again.
for _,name in ipairs({'full_hero','full_monster'})do
 local selected=name=='full_hero'and cached.hero or cached.monster
 local info,decision=unpack(selected);local t,n=args(info,20,20)
 local result;local hit_calls=0
 local skill={['击退距离']=0}
 local function scripted()
  local value=decision(unpack(t,1,n));return type(value)=='number'and{10,0,0}or{0,-1,0}
 end
 local sys={get=function(kind)eq(kind,'skill');return skill end,run=function(kind)eq(kind,'fun');return true,scripted()end}
 local attacker={['回调脚本']={['发生伤害']='controlled callback'},['事件回调']=function()return true,scripted()end}
 local target={id=2,['属性']={hp=100},['被击中']=function(_,_,damage)hit_calls=hit_calls+1;result=damage end}
 local full=load(name,{Sys=sys,type=type,math=math,['引擎']=engine})
 for _,r in ipairs({70,90})do
  roll=r;calls=0;hit_calls=0;local v=full(attacker,target,'controlled skill',1,nil,false,false,false)
  eq(calls,1,'script and native do not double-roll');eq(hit_calls,1);eq(result,r==70 and 10 or -1);eq(v[1],result)
 end
end
print('HIT_V196_PASS',mode,'checks',checks,'hit_sites',252)
