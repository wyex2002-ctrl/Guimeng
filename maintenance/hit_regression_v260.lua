local work,mode=arg[1],arg[2]
if mode=='normal'then jit.off()else jit.opt.start('hotloop=1','hotexit=1')end
local checks=0
local function eq(a,b,msg)checks=checks+1;assert(a==b,(msg or'')..' '..tostring(a)..' ~= '..tostring(b))end
local function near(a,b)checks=checks+1;assert(math.abs(a-b)<1e-8,tostring(a)..' ~= '..tostring(b))end
local function load(n,env)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,env);return f end
local native=setmetatable({},{__index=_G});local db=setmetatable({},{__index=_G})
local rows=assert(loadfile(work..'/hit_meta.lua'))()
local raw={}
local function actor(id,faction,owner)
 local a={id=id,所属阵营=faction,属性={hp=100},宠物配置={},被击中=function()end}
 raw[id]=a;if owner~=nil then a.宠物配置.主人=raw[owner];a.主人id=owner end;return a
end
local hero=actor(0,'友方');local merc=actor(7,'友方');local pet=actor(8,'友方',0);local mpet=actor(10,'友方',7)
local monster=actor(9,'敌方');local stranger=actor(11,'友方');local cycle=actor(12,'敌方');cycle.宠物配置.主人=cycle;cycle.主人id=12
local nested=actor(13,'友方',8)
local factory=load('hit_public_actor',native);debug.setupvalue(factory,1,{})
local public={};for id,a in pairs(raw)do public[id]=factory(a)end
local E={Ux雌={佣兵对象=public[7]},Gly独={事件对象=function(id)return public[id]end}}
load('hit_mode',native)({},E)
db.__gm_hit_factor_v260=E.__gm_hit_factor_v260;db.Ux雌=E.Ux雌
local roll,calls=70,0
local function random(lo,hi)eq(lo,1);eq(hi,100);calls=calls+1;return roll end
db.Gly独={取随机数=random};native.引擎={取随机整数=function(_,lo,hi)return random(lo,hi)end}
local factor=native.__gm_hit_factor_v260
for _,a in ipairs({hero,merc,pet,mpet,nested})do
 eq(factor(a,monster),2.5);eq(factor(public[a.id],public[9]),2.5);eq(factor(a.id,9),2.5)
 eq(factor(monster,a),1);eq(factor(public[9],public[a.id]),1)
 eq(factor(a,hero),1);eq(factor(a,stranger),1)
end
eq(factor(stranger,monster),1);eq(factor(monster,monster),1);eq(factor(cycle,monster),1)
eq(factor(nil,monster),1);eq(factor(hero,nil),1);eq(factor(9999,9),1)
raw[8].宠物配置.主人=monster;raw[8].主人id=9;eq(factor(public[8],public[9]),1,'pet ownership changes immediately');raw[8].宠物配置.主人=hero;raw[8].主人id=0
local function args(row,A,D,source,target,absolute)
 local name,kind,n,ar,dr,den=unpack(row);local t={}
 t[ar+1]=A;t[dr+1]=D;if den~=ar then t[den+1]=A end
 t[1]=kind=='hero'or kind=='merc'or kind=='monster'and target.id or source
 if kind=='hero'or kind=='merc'or kind=='monster'then t[1]=target.id else t[2]=target end
 if kind=='merc'then t[5]={行会选中={}}end
 if kind=='monster'then t[5]={准确几率=A}end
 if kind=='native_monster'then t[22]={命中=A};t[24]={躲避=D};t[11]={绝对命中=absolute or 0}end
 if kind=='native_hero'then t[14]={命中=A};t[15]={躲避=D};t[9]={绝对命中=absolute or 0}end
 return t,n
end
local cached={};local kinds={}
for _,row in ipairs(rows)do
 local name,kind=row[1],row[2];local env=(kind=='basic'or kind=='native_monster'or kind=='native_hero')and native or db
 local ratio=load(name..'_new_ratio',env);local old=load(name..'_old_ratio',env);local decision=load(name..'_new_decision',env)
 if kind=='monster'then for _,f in ipairs({ratio,old,decision})do debug.setupvalue(f,1,{对象=public[8]})end end
 local source=kind=='hero'and hero or kind=='merc'and merc or pet
 local t,n=args(row,20,20,source,monster);near(ratio(unpack(t,1,n)),100*20/(20+20/2.5))
 if not kinds[kind]then
  kinds[kind]=true;cached[kind]={row,decision}
  for _,pair in ipairs({{hero,monster},{merc,monster},{pet,monster},{mpet,monster},{monster,hero},{monster,merc},{monster,pet},{monster,mpet},{monster,monster},{hero,stranger}})do
   local a,b=unpack(pair)
   -- Fixed hero/merc callback sources come from their original globals.
   if kind=='hero'then a=hero elseif kind=='merc'then a=merc end
   if kind=='monster'then for _,f in ipairs({ratio,old,decision})do debug.setupvalue(f,1,{对象=public[a.id]})end end
   local fct=factor(a,b)
   for _,v in ipairs({{20,20},{10,20},{0,20},{20,0},{0,0},{1,1000},{1e300,1e300}})do
    local A,D=unpack(v);local expected=A+D/fct==0 and 0 or 100*A/(A+D/fct)
    local t,n=args(row,A,D,a,b);near(ratio(unpack(t,1,n)),expected)
    for _,r in ipairs({50,51,71,72})do roll=r;calls=0
     eq(type(decision(unpack(t,1,n)))=='number',r<=expected,kind..' hit boundary');eq(calls,1,'one draw')
    end
   end
  end
  if kind=='native_monster'or kind=='native_hero'then
   local t,n=args(row,0,100,monster,hero,1);calls=0;eq(type(decision(unpack(t,1,n))),'number');eq(calls,0,'absolute hit retains no random draw')
  end
 end
end
eq(#rows,252)
for i=1,200 do
 local row,decision=unpack(cached.hero);local t,n=args(row,20,20,hero,monster);roll=(i-1)%100+1;calls=0
 eq(type(decision(unpack(t,1,n)))=='number',roll<=71);eq(calls,1)
end
-- Actual native outer entry consumes a script result once, without rerolling.
for _,kind in ipairs({'hero','monster'})do
 local row,decision=unpack(cached[kind]);local source=kind=='hero'and hero or monster;local target=kind=='hero'and monster or hero
 if kind=='monster'then debug.setupvalue(decision,1,{对象=public[9]})end
 local t,n=args(row,20,20,source,target)
 local function scripted()return type(decision(unpack(t,1,n)))=='number'and{10,0,0}or{0,-1,0}end
 local output;local a={回调脚本={发生伤害='script'},事件回调=function()return true,scripted()end}
 local b={id=target.id,属性={hp=100},被击中=function(_,_,damage)output=damage end}
 local env=setmetatable({Sys={get=function()return{击退距离=0}end,run=function()return true,scripted()end}}, {__index=native})
 local full=load(kind=='hero'and'hit_full_hero'or'hit_full_monster',env)
 roll=70;calls=0;full(a,b,'skill',1,nil,false,false,false);eq(calls,1);eq(output,kind=='hero'and 10 or -1)
end
print('HIT_V260_PASS',mode,checks,'checks',#rows,'sites; party-to-monster only')
