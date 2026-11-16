local work,mode=arg[1],arg[2]
if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')else jit.off()end
local checks=0;local function eq(a,b,m)checks=checks+1;assert(a==b,(m or'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function load(n,env)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,env);return f end
local function noop()end
local N=setmetatable({},{__index=_G});N.math=setmetatable({round=function(n)return math.floor(n+.5)end},{__index=math});local T={};for k,v in pairs(table)do T[k]=v end;N.table=T;load('table_register',N)()
local function zero()return setmetatable({},{__index=function()return 0 end})end
local props={'物理伤害','魔法伤害','物理防御','魔法防御','生命值','法力值','命中','躲避','暴击','移动速度','攻击速度','最大破坏','最小破坏','最大自然','最小自然','最大灵魂','最小灵魂','最大防御','最小防御','最大魔防','最小魔防','幸运'}
N.Ae冻集={自定义属性表=props}
local function attrs(luck)local a={};for _,k in ipairs(props)do a[k]=0;a[k..'_百分比']=0 end;a.幸运=luck or 0;return a end
local messages,actors={},{};local float=.5;local float_calls,integer_calls=0,0
N.引擎={取随机小数=function(_,lo,hi)eq(lo,0);eq(hi,1);float_calls=float_calls+1;return float end}
local bag={};local h={id=0,装备格子={{标识=14,拿起=false},{标识=15,拿起=false}},自定义属性表={幸运=true},属性=zero()}
h.本次移动速度倍数=1;h.实时移动速度=1;h.属性.属性集={幸运=0};h.属性.附加_幸运=0;h.BUFF状态更新=noop;h.属性.等级=60;h.回调脚本={系统反馈=noop};local owner={Hero=h,包裹物品组=bag,游戏道具组={}};owner.script_setting={Gly独={错误=function(s)error(s)end}}
local proxy=load('proxy',N);debug.setupvalue(proxy,1,owner);owner.数据保护=proxy
owner.包裹物品组=proxy(bag,true);bag=owner.包裹物品组
local getter=load('metadata',N);debug.setupvalue(getter,1,owner)
local baseget=load('template_info',N);debug.setupvalue(baseget,1,owner)
local api=load('hero_api',N);debug.setupvalue(api,2,owner);local fx=api();local U={开挖机的={孔爱琴泥=function(text,channel)eq(channel,1);messages[#messages+1]=text end}}
local E={Ux雌=U,FXru胃啪=fx,type=type,tonumber=tonumber,math=math,table=T,string=string,pairs=pairs,ipairs=ipairs,unpack=unpack,分割文本=function()return{}end}
E.Gly独={事件对象=function(id)return id==0 and fx or actors[id]end,取随机数=function(lo,hi)integer_calls=integer_calls+1;return math.floor((lo+hi)/2)end,取道具信息_格子=getter,取道具信息_名称=baseget}
E.__gm_stat_v162=load('stat',N)()
local install=load('install',N);debug.setupvalue(install,1,owner);install(E);eq(owner.script_setting,E);eq(E.pcall,nil);eq(E._G,nil);eq(E.Sys,nil)
local sum=load('gear_sum',N);local sys={get=function(k)if k=='item_arr'then return bag end end}
local run=function(op,func,...)
 if op=='fun'then return true,func(unpack((...)))end
 if op=='adds'then setfenv(func,E);return func()elseif op=='add'then return end
 if op=='qs_item_box'then return true,false end
 error('unexpected '..op)
end
N.Sys=load('public_sys',N)({get=sys.get,run=run});N.Q_鼠标={格子标识=0,物品来源={}}
local function refresh()
 local a=zero();for _,k in ipairs({'物理伤害','魔法伤害','物理防御','魔法防御','命中','躲避','暴击','maxhp','maxmp','移动速度倍数','攻击速度倍数','生命值_百分比','法力值_百分比','物理伤害_百分比','魔法伤害_百分比','物理防御_百分比','魔法防御_百分比','命中_百分比','躲避_百分比','暴击_百分比','移动速度_百分比','攻击速度_百分比','幸运','幸运_百分比'})do a[k]=0 end
 local total=sum(h,a);h.属性.幸运=total.幸运;h.属性.属性集.幸运=h.属性.幸运
end
h.属性更新=function()refresh()end
local base={数量=1,名称='测试坐骑',显示名='测试坐骑',子类='坐骑',分类='装备',属性=attrs(),附加={},资源={},风格提示={}}
owner.游戏道具组.测试坐骑=base
local function protected(t)t.属性=proxy(t.属性,true);t.附加=proxy(t.附加 or{},true);return proxy(t)end
local function mount(luck)local t=T.copy(base,true);t.属性.幸运=luck;return protected(t)end
bag[14]={道具=nil};bag[15]={道具=nil}
local oil_base={名称='自然神水_小',显示名='自然神水',子类='消耗品',分类='道具',数量=3,属性=attrs(),附加={},资源={},风格提示={},任务关联=false,剧情关联=false,性别要求='不限',职业要求='不限',需要等级=1}
local oil=load('oil_template',N)(oil_base);eq(oil.名称,'祝福油');eq(oil.颜色值,-65536)
local control={道具CD组={},可用=true,标识=32,格子组=bag,Hero=h,tbl={}}
control.消耗=load('consume',N);local use=load('inventory_use',N)
local function apply(v)
 local t=T.copy(oil,true);t.数量=3;bag[32]={道具=t};float=v or .5
 return use(control),bag[32].道具.数量
end
local ok,n=apply();eq(ok,false);eq(n,3);eq(messages[#messages],'请先装备坐骑后再使用祝福油。')
bag[14].道具=proxy(mount(nil));ok,n=apply();eq(ok,true);eq(n,2);eq(bag[14].道具.属性.幸运,1,'mount after first oil');eq(h.属性.幸运,1,'native gear sum after first oil');eq(base.属性.幸运,0,'template untouched')
eq(messages[#messages],'#c(-13465000)祝福油使用成功，坐骑幸运提升至 +1！#W')
for _,v in ipairs({{.399999,2,'success'},{.4,1,'loss'},{.7,1,'same'},{0,2,'success'},{.999,2,'same'}})do ok,n=apply(v[1]);eq(ok,true);eq(n,2);eq(bag[14].道具.属性.幸运,v[2]);eq(h.属性.幸运,v[2])end
bag[14].道具.属性.幸运=7;refresh();ok,n=apply();eq(ok,false);eq(n,3);eq(h.属性.幸运,7)
bag[14].道具.属性.幸运=1;refresh();ok,n=apply(.5);eq(ok,true);eq(n,2);eq(h.属性.幸运,0)
for level=1,6 do
 for _,outcome in ipairs({{0,level+1},{.4,level-1},{.7,level}})do
  bag[14].道具=mount(level);refresh();ok,n=apply(outcome[1]);eq(ok,true);eq(n,2);eq(bag[14].道具.属性.幸运,outcome[2])
 end
end
h.装备格子[1].拿起=true;ok,n=apply();eq(ok,false);eq(n,3);h.装备格子[1].拿起=false
bag[14].道具.属性.幸运=0/0;ok,n=apply();eq(ok,false);eq(n,3)
bag[14].道具=mount(5);refresh()
-- No transfer between instances; original gear sum adds other gear once.
local saved=T.copy(bag[14].道具,true);bag[14].道具=proxy(mount(5));bag[15].道具=proxy({子类='戒指',属性=attrs(1)});refresh();eq(h.属性.幸运,6)
local first=bag[14].道具;bag[14].道具=proxy(mount(2));refresh();eq(h.属性.幸运,3);eq(first.属性.幸运,5)
bag[14].道具=nil;refresh();eq(h.属性.幸运,1);bag[14].道具=protected(T.copy(first,true));refresh();eq(h.属性.幸运,6,'field export/reload')
-- Outline alias invokes the real native renderer closure with unchanged args.
local outline;N.Q_文字={显示=function(...)outline=select(6,...)end};local font=load('font',N)('宋_9_幸运');font.显示(1,2,'幸运',0,-1720246,0,0,0);eq(outline,-11979495)
owner.游戏道具组.测试坐骑=protected(T.copy(base,true));local info=getter(14);local ref=baseget('测试坐骑')
local text=E.__gm_luck_line_v244(info,ref);eq(text:find('幸运：5（+5）',1,true)~=nil,true);eq(text:find('#c(-1720246)',1,true)~=nil,true)
eq(E.__gm_luck_line_v244({子类='坐骑',幸运=0},ref),'');eq(E.__gm_luck_line_v244({子类='坐骑',幸运=5},{幸运=2}):find('幸运：5（+3）',1,true)~=nil,true);eq(load('compact_tip',E)(info,ref),text);eq(load('detail_tip',E)(info,ref),text)
-- Deterministic probability edges preserve floating-point fractions.
actors[10]={id=10,主人id=0,属性={最小防御=2,最大防御=8,最小魔防=3,最大魔防=9}}
actors[11]={id=11,主人id=42,属性=actors[10].属性};actors[42]={id=42,主人id=0};U.佣兵对象=actors[42];actors[12]={id=12,主人id=12,属性=actors[10].属性}
for luck=0,7 do
 h.属性.幸运=luck;h.属性.属性集.幸运=h.属性.幸运;local p=1/(10-luck)
 for _,v in ipairs({p-1e-9,p,p+1e-9})do
  float=v;local before=float_calls;local a=E.__gm_luck_attack_v244(10,20,{},fx);eq(a,v<p and 20 or 15);eq(float_calls,before+1)
  local before=float_calls;local a,b=E.__gm_luck_defense_v244(actors[10],false);eq(a,v<p and 8 or 5);eq(b,v<p and 9 or 6);eq(float_calls,before+1)
 end
end
h.属性.幸运=5;h.属性.属性集.幸运=h.属性.幸运
for _,v in ipairs({.459999,.46})do float=v;local a,b=E.__gm_luck_pair_v244(10,20,2,4,{幸运属性=15},fx,{行会选中={幸运加持=1}});eq(a,v<.46 and 20 or 15);eq(b,v<.46 and 4 or 3)end
float=.999;eq(E.__gm_luck_attack_v244(10,20,{幸运属性=100},fx),20);float=1;eq(E.__gm_luck_attack_v244(10,20,{幸运属性=100},fx),20)
float=.19;eq(E.__gm_luck_attack_v244(10,20,{},actors[10]),20);h.属性.幸运=0;h.属性.属性集.幸运=h.属性.幸运;eq(E.__gm_luck_attack_v244(10,20,{},actors[10]),15,'live pet sync')
for _,actor in ipairs({actors[11],actors[12],actors[42],{id=99},{id=1.5,主人id=0}})do local before=float_calls;eq(E.__gm_luck_attack_v244(10,20,{幸运属性=100},actor),15);eq(float_calls,before,'no hero luck for merc/unowned/cycle')end
-- Independent attack/defense rolls; one merged attack roll, no residual old rolls.
h.属性.幸运=5;h.属性.属性集.幸运=h.属性.幸运;float=.19;eq(E.__gm_luck_attack_v244(10,20,{},fx),20);float=.21;local a,b=E.__gm_luck_defense_v244(actors[10],false);eq(a,5);eq(b,6)
local hit=0;for i=1,200 do float=(i-.5)/200;if E.__gm_luck_attack_v244(10,20,{},fx)==20 then hit=hit+1 end end;eq(hit,40,'200 deterministic bins at luck5')
float=.45;local before=float_calls;local a,b=load('hero_luck',E)(10,20,{幸运属性=15},{行会选中={幸运加持=1}});eq(a,20);eq(b,4);eq(float_calls,before+1)
-- Every registered creature callback executes its complete native body.
local skill={显示名='普通攻击',冷却时间=1,幸运属性=15}
E.Gly独.取出技能信息=function()return skill end
U.胚子考虑=function()return{行会选中={}}end;U.啾啾啵啵=function()return{技能={}}end
for _,key in ipairs({'主角抵抗几率','主角抵抗暴击','主角抵抗真伤','主角敏捷几率','主角元素躲避','主角伤害减免','主角最小防御','主角最小魔防','主角最大防御','主角最大魔防'})do U[key]=0 end
U.主角最小防御=2;U.主角最小魔防=3;U.主角最大防御=8;U.主角最大魔防=9
local function actor(id,parent,growth)
 local a=zero();a.附加={};a.最小破坏=10;a.最大破坏=20;a.准确几率=100;a.成长=growth or'战士';a.最小防御=2;a.最大防御=8;a.最小魔防=3;a.最大魔防=9
 return{id=id,主人id=parent,属性=a,HP=100,等级=60,附加=a.附加}
end
actors[70]=actor(70,nil);actors[71]=actor(71,0);actors[72]=actor(72,0,'刺客')
local fns={};h.属性.幸运=5;h.属性.属性集.幸运=h.属性.幸运;float=.34
for _,id in ipairs(assert(loadfile(work..'/callbacks.lua'))())do
 local f=load('creature'..id,E);debug.setupvalue(f,1,{对象=actors[71]})
 local before=float_calls;local result=f(70,'普通攻击',1);eq(type(result),'table');eq(float_calls,before+1,'one pet attack roll in callback '..id)
 fns[#fns+1]=f
end
-- Wild attacker -> pet random defense and hero combined defense: own roll only.
local f=fns[1];debug.setupvalue(f,1,{对象=actors[70]});local before=float_calls;f(72,'普通攻击',1);eq(float_calls,before+1)
before=float_calls;f(0,'普通攻击',1);eq(float_calls,before+1)
local old=load('creature_old',E);debug.setupvalue(old,1,{对象=actors[70]});debug.setupvalue(f,1,{对象=actors[70]});before=float_calls
local old_result,new_result=old(70,'普通攻击',1),f(70,'普通攻击',1);for i=1,3 do eq(new_result[i],old_result[i],'wild combat baseline')end;eq(float_calls,before)
-- Both sides are pets: attack and defense are independent, two rolls total.
debug.setupvalue(f,1,{对象=actors[71]});before=float_calls;f(72,'普通攻击',1);eq(float_calls,before+2)
print('LUCK_V244_PASS',mode,checks)
