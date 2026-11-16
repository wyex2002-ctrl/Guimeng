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
local api=load('hero_api',N);debug.setupvalue(api,2,owner);local fx=api()
local chat={可视=false};local hints={};local chatInput={内容='keep input'}
local CE=setmetatable({聊天窗口=chat,聊天输入框=chatInput,聊天文本框={内容高度=0,加入文本=function(t)messages[#messages+1]=t end}}, {__index=N})
local message=load('chat_message',CE);debug.setupvalue(message,1,{})
local screenEnv={ARGB=function(a,r,g,b)return a*16777216+r*65536+g*256+b end,FXru胃啪={取状态列表=function()return {信息提醒=true}end,屏幕提示=function(...)hints[#hints+1]={...}end},聊天窗口=chat,Gly独={屏幕高度=600}}
local U={开挖机的={孔爱琴泥=message},托管显示={屏幕提示=load('screen_message',screenEnv)}}
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
eq(E.__gm_luck_line_v244({子类='坐骑',幸运=0},ref),'');eq(E.__gm_luck_line_v244({子类='坐骑',幸运=5},{幸运=2}):find('幸运：5（+3）',1,true)~=nil,true); info.需要等级=1;info.性别要求='不限';info.职业要求='不限'
local early,keptbase=load('compact_early',E)(info,ref);eq(early,'');eq(keptbase,ref,'compact template register survives mount skip')
local oldkind=info.子类;info.子类='戒指';local oldluck=info.幸运;info.幸运=0;local untouched,kept=load('compact_early',E)(info,ref);eq(untouched,'');eq(kept,ref);info.子类=oldkind;info.幸运=oldluck
local a,b=load('compact_tip',E)(info,ref),load('detail_tip',E)(info,ref)
for _,tip in ipairs({a,b})do local at=assert(tip:find('需要等级:1',1,true));local lucky=assert(tip:find(text,1,true));eq(at<lucky,true);eq(tip:sub(lucky),text)end
for i,hint in ipairs(hints)do local expected=messages[i]:gsub('^#c%([%-0-9]+%)',''):gsub('#W$','');eq(hint[1],expected);eq(type(hint[2]),'number');eq(hint[3],0);eq(hint[11],true)end
eq(#hints,#messages);eq(chat.可视,false);eq(chatInput.内容,'keep input')
-- Both original entry windows and the original manual chat toggle.
local function window(visible)local w={可视=visible};w.打开=function()w.可视=true end;w.关闭=function()w.可视=false end;w.开关=function()w.可视=not w.可视 end;return w end
local windows={底部窗口=window(false),快捷窗口=window(false),聊天窗口=window(true)}
local enter=load('entry_windows',windows);local toggle=load('chat_toggle',windows)
for _,story in ipairs({'前尘忆梦','来世续缘'})do
 U.版本选择=story;enter();eq(windows.底部窗口.可视,true);eq(windows.快捷窗口.可视,true);eq(windows.聊天窗口.可视,false)
 toggle();eq(windows.聊天窗口.可视,true);toggle();eq(windows.聊天窗口.可视,false)
 windows.聊天窗口.打开();enter();eq(windows.聊天窗口.可视,false,'reentry closes previous chat')
end
-- Real native rich-text formatter and layout: 2 px before/after, same font.
local function chars(t)local out={};local i=1;while i<=#t do local n=t:byte(i)>127 and 2 or 1;out[#out+1]=t:sub(i,i+n-1);i=i+n end;return out end
local function split(t,sep)local out={};local at=1;while true do local a,b=t:find(sep,at,true);if not a then out[#out+1]=t:sub(at);return out end;out[#out+1]=t:sub(at,a-1);at=b+1 end end
local R=setmetatable({分割文本=split,L常量=setmetatable({},{__index=function()return -1 end}),D2D_精灵={创建=function()return{}end},分割为字符组=chars,Ae冻集={默认文字_间距=0,默认文字_行距=0}}, {__index=N})
load('rich_register',R)()
local original=text:gsub('#p%(0,2%)','')
local tokens=R.丰富文本_格式化(text);local gaps=0
for _,token in ipairs(tokens)do if token.类型=='图片'and token.图片==-1 then eq(token.x,0);eq(token.y,2);gaps=gaps+1 end end
eq(gaps,2)
-- Finite glyph metrics bridge only; formatter/layout and font selection are original.
R.Q_文字={取文字信息=function()return 6,12,0 end,取单个字宽度=function(t)return #t*6 end,取高度=function()return 12 end}
local nativefont=load('font',R)('宋_9_幸运')
local _,oldheight=R.丰富文本_解析(nativefont,'需要等级:1'..original..'\n下一项',600)
local _,height=R.丰富文本_解析(nativefont,'需要等级:1'..text..'\n下一项',600)
eq(height-oldheight,4,'exact two 2-pixel gaps')
local drew={}
local font={取文字信息=function()return 6,12,0 end,取单个字宽度=function(t)return #t*6 end,取高度=function()return 12 end,置颜色=noop,显示=function(x,y,t)drew[#drew+1]={x,y,t}end}
local Render=setmetatable({引擎={画线=noop,取按键事件=function()return false end},Q_文字=font,分割文本=split,分割为字符组=chars,L常量=setmetatable({},{__index=function()return -1 end}),D2D_精灵={创建=function()return{置颜色=noop,显示_范围缩放=noop}end},Ae冻集={默认文字_间距=0,默认文字_行距=-3}}, {__index=_G})
load('rich_register',Render)()

local function render_luck(line,fh,spacing)
 font.取文字信息=function()return 6,fh,0 end;Render.Ae冻集.默认文字_行距=spacing
 local rows,hh=Render.丰富文本_解析(font,'需要等级:1'..line..'\n下一项',240)
 drew={};Render.丰富文本_显示(font,0,0,rows,-1,0,0,false,nil,0,spacing,0)
 local pos={};for _,d in ipairs(drew)do if d[3]=='需'or d[3]=='幸'or d[3]=='下'then pos[d[3]]=d[2]end end
 return pos,hh
end
for _,fh in ipairs({12,16,20})do for _,spacing in ipairs({0,-3})do
 local old,oldh=render_luck(text:gsub('p%(0,2%)','p(0,6)'),fh,spacing)
 local new,newh=render_luck(text,fh,spacing)
 eq(new.需,old.需);eq(new.幸,old.幸-4);eq(new.下,old.下-8);eq(newh,oldh-8)
end end
eq(select(2,text:gsub('\n','')),1,'one normal line break; no blank line')
-- Equipment zero does not suppress independent skill / guild luck.
h.属性.幸运=0;h.属性.属性集.幸运=0
for _,v in ipairs({.149999,.15})do float=v;eq(E.__gm_luck_attack_v244(10,20,{幸运属性=15},fx),v<.15 and 20 or 15)end
for _,v in ipairs({.109999,.11})do float=v;local a=E.__gm_luck_pair_v244(10,20,2,4,{},fx,{行会选中={幸运加持=1}});eq(a,v<.11 and 20 or 15)end
-- Deterministic probability edges preserve floating-point fractions.
actors[10]={id=10,主人id=0,属性={最小防御=2,最大防御=8,最小魔防=3,最大魔防=9}}
actors[11]={id=11,主人id=42,属性=actors[10].属性};actors[42]={id=42,主人id=0};U.佣兵对象=actors[42];actors[12]={id=12,主人id=12,属性=actors[10].属性}
for luck=0,7 do
 h.属性.幸运=luck;h.属性.属性集.幸运=h.属性.幸运;local p=luck>=1 and 1/(10-luck)or 0
 for _,v in ipairs(luck==0 and {0,.05,.999}or {p-1e-9,p,p+1e-9})do
  float=v;local before=float_calls;local a=E.__gm_luck_attack_v244(10,20,{},fx);eq(a,v<p and 20 or 15);eq(float_calls,before+1)
  local before=float_calls;local a,b=E.__gm_luck_defense_v244(actors[10],false);eq(a,v<p and 8 or 5);eq(b,v<p and 9 or 6);eq(float_calls,before+1)
 end
end
h.属性.幸运=5;h.属性.属性集.幸运=h.属性.幸运
for _,v in ipairs({.459999,.46})do float=v;local a,b=E.__gm_luck_pair_v244(10,20,2,4,{幸运属性=15},fx,{行会选中={幸运加持=1}});eq(a,v<.46 and 20 or 15);eq(b,v<.46 and 4 or 3)end
float=.999;eq(E.__gm_luck_attack_v244(10,20,{幸运属性=100},fx),20);float=1;eq(E.__gm_luck_attack_v244(10,20,{幸运属性=100},fx),20)
float=.19;eq(E.__gm_luck_attack_v244(10,20,{},actors[10]),20);h.属性.幸运=0;h.属性.属性集.幸运=h.属性.幸运;eq(E.__gm_luck_attack_v244(10,20,{},actors[10]),15,'live pet sync')
for _,actor in ipairs({actors[12],{id=99},{id=1.5,主人id=0}})do local before=float_calls;eq(E.__gm_luck_attack_v244(10,20,{幸运属性=100},actor),15);eq(float_calls,before,'no hero luck for merc/unowned/cycle')end
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
-- Actual companion aggregate and public actor proxy; never the hero's stats.
local merc={id=42,装备格子={{标识=410,拿起=false}},属性=zero(),宠物配置={主人=h},实时移动速度=1,本次移动速度倍数=1}
merc.属性.属性集=zero();merc.属性.等级=60;merc.属性.绑定成长={};merc.属性.hp=100
owner.屏幕事件组={merc}
local merc_api=load('actor_api',N);debug.setupvalue(merc_api,1,owner);local merc_public=merc_api(merc)
U.佣兵对象=merc_public;actors[42]=merc_public;actors[43]={id=43,主人id=42,属性=actors[10].属性}
local merc_sum=load('merc_gear_sum',N)
merc.属性更新=function()
 local a=zero();local total=merc_sum(merc,a,{幸运=true});merc.属性.属性集.幸运=total.幸运
end
bag[410]={道具=mount(0)};merc:属性更新();eq(merc_public.属性.幸运,0)
local function apply_from(id,v)
 local t=T.copy(oil,true);t.数量=3;bag[id]={道具=t};float=v or .5
 local c={道具CD组={},可用=true,标识=id,格子组=bag,Hero=h,tbl={}};c.消耗=load('consume',N)
 return use(c),bag[id].道具.数量
end
local hero_before=h.属性.属性集.幸运
for level=0,6 do
 for _,outcome in ipairs({{0,math.min(7,level+1)},{.4,level==0 and 1 or level-1},{.7,level==0 and 1 or level}})do
  bag[410].道具=mount(level);merc:属性更新();ok,n=apply_from(333,outcome[1]);eq(ok,true);eq(n,2)
  eq(merc_public.属性.幸运,outcome[2]);eq(h.属性.属性集.幸运,hero_before,'companion use cannot alter hero')
 end
end
bag[410].道具=mount(7);merc:属性更新();ok,n=apply_from(396);eq(ok,false);eq(n,3)
bag[410].道具=nil;merc:属性更新();ok,n=apply_from(333);eq(ok,false);eq(n,3)
-- Companion and pets follow companion luck, hero/pets follow hero luck.
bag[410].道具=mount(0);merc:属性更新();h.属性.属性集.幸运=7;float=.2
eq(E.__gm_luck_attack_v244(10,20,{},fx),20);eq(E.__gm_luck_attack_v244(10,20,{},merc_public),15);eq(E.__gm_luck_attack_v244(10,20,{},actors[43]),15)
bag[410].道具=mount(7);merc:属性更新();h.属性.属性集.幸运=0
float=.2;eq(E.__gm_luck_attack_v244(10,20,{},fx),15);eq(E.__gm_luck_attack_v244(10,20,{},merc_public),20);eq(E.__gm_luck_attack_v244(10,20,{},actors[43]),20)
local da,db=E.__gm_luck_defense_v244(actors[43],false);eq(da,8);eq(db,9)
N.Ae冻集.自定义属性表[#N.Ae冻集.自定义属性表+1]='最小伤害';N.Ae冻集.自定义属性表[#N.Ae冻集.自定义属性表+1]='最大伤害';oil.属性.最小伤害=0;oil.属性.最大伤害=0
-- Actual merc attack span merges its own configured skill, one chance roll.
merc.属性.属性集.最小伤害=0;merc.属性.属性集.最大伤害=0;float=.4
local before=float_calls;local x,y=load('merc_luck',E)(10,20,{幸运属性=15});eq(x,20);eq(y,4);eq(float_calls,before+1)
float=.6;x,y=load('merc_luck',E)(10,20,{幸运属性=15});eq(x,15);eq(y,3)
-- MERC_REGRESSION
-- Shared physical oil moved to hero pack always strengthens the hero.
bag[14].道具=mount(0);refresh();bag[410].道具=mount(6);merc:属性更新()
ok,n=apply_from(32);eq(ok,true);eq(n,2);eq(getter(14).幸运,1);eq(merc_public.属性.幸运,6)
-- No-live-actor companion equipment remains an instance on the persistent UI.
owner.屏幕事件组={};U.佣兵对象=nil
owner.界面_窗口_数组={{名称='佣兵窗口',控件组={{类型=6,格子ID=410,背包格子=false,对象={标识=410,拿起=false}}}}}
bag[410].道具=mount(0);ok,n=apply_from(333);eq(ok,true);eq(n,2);eq(getter(410).幸运,1);eq(getter(14).幸运,1)
owner.界面_窗口_数组={};ok,n=apply_from(333);eq(ok,false);eq(n,3,'no companion mount is not hero fallback')
U.佣兵对象=merc_public;owner.屏幕事件组={merc}
-- Bound native companion outside the screen list still refreshes immediately.
owner.屏幕事件组={};owner.界面_窗口_数组={{名称='佣兵窗口',控件组={{类型=6,格子ID=410,背包格子=false,对象={标识=410,拿起=false,绑定事件={merc}}}}}}
bag[410].道具=mount(0);merc:属性更新();ok,n=apply_from(333);eq(ok,true);eq(n,2);eq(merc_public.属性.幸运,1)
owner.屏幕事件组={merc};owner.界面_窗口_数组={}
-- Saved pre-245 oil is copied, gains the shortcut marker, inputs untouched.
local reset=load('oil_reset',N);debug.setupvalue(reset,1,owner);local changed
owner.游戏道具组.祝福油=oil;local oldprops={叠加上限=999,重量=1};debug.setupvalue(reset,2,function(id,c)changed=c;return true end)
reset(32,{名称='祝福油',附加=oldprops,物品脚本={Main=function()error('old callback')end}});eq(changed.物品脚本,oil.物品脚本);eq(changed.附加.快捷物品,0);eq(oldprops.快捷物品,nil);eq(changed.附加.重量,1)
-- Actual quickslot item event -> original use-by-name -> actual inventory.
local oldrun=run;local event=load('item_event',E)
E.L常量={键_SHIFT=1,颜色_红=-65536};E.物品格子18={}
E.Gly独.取按键状态=function()return false end
E.Gly独.从ID取格子=function(id)return bag[id]end
E.Gly独.取包裹空位=function()return 0 end
U.呦西鸽子=function()return bag end
for _,k in ipairs({'仓库窗口','信息窗口','商店窗口','行会仓库','仓库窗口2','信息窗口2','商店窗口2','行会仓库2','佣兵窗口'})do E[k]={可视=false}end
for _,k in ipairs({'聊天输入框','英雄HP输入框','英雄MP输入框'})do E[k]={焦点=false}end
local original_get=sys.get
local function ui_get(k)
 if k=='win_tex'then return function()return{置标题=noop,销毁=noop}end end
 if k=='item_cd_arr'then return{}end
 if k=='hero'then return h end
 return original_get(k)
end
owner.tbl_controls={}
local native_run=function(op,args,...)
 if op=='qs_item_box'then return true,event(unpack(args))end
 return oldrun(op,args,...)
end
N.Sys=load('public_sys',N)({get=ui_get,run=native_run,add=function(kind,name,v)eq(kind,'tbl_controls');owner.tbl_controls[name]=v end})
N.Q_文字.取高度=function()return 12 end;N.D2D_包围盒={创建=function()return{}end}
N.Ae冻集.快捷事件组={};N.Ae冻集.控件名称组={};N.Ae冻集.包裹物品数=500
N.class=function()local C={};C.创建=function(...)local obj=setmetatable({},{__index=C});C.初始化(obj,...);return obj end;return C end
load('inventory_class',N)()
local add=load('add_control',N);local bind=load('bind_control',N)
local byname=load('use_by_name',N);debug.setupvalue(byname,1,owner);E.Gly独.使用物品=byname
local quantity=load('quantity',N);debug.setupvalue(quantity,1,owner);E.Gly独.取物品数量=quantity
for _,case in ipairs({{'前尘忆梦',1,7},{'来世续缘',21,32}})do
 U.版本选择=case[1];local qid,bid=case[2],case[3]
 h.背包格子={};local win={名称='背包窗口',可视=false,控件组={},坐标={x=0,y=0},闭包=bind}
 add(win,6,'物品格子'..qid,0,0,32,32,qid,nil,false,false,0,false,false)
 add(win,6,'物品格子'..bid,0,0,32,32,bid,nil,false,true,0,false,false)
 local qcontrol=win.控件组[1].对象;owner.界面_窗口_数组={win}
 local placeholder=protected(T.copy(oil,true));placeholder.数量=1
 eq(placeholder.附加.快捷物品,0,'normal shortcut marker')
 bag[qid]={道具=placeholder};local real=protected(T.copy(oil,true));real.数量=3;bag[bid]={道具=real}
 local stop=event(6,qid,'祝福油',bid);eq(stop~=true,true,'native placement allowed')
 bag[14].道具=mount(0);refresh();bag[410].道具=mount(4);merc:属性更新()
 eq(qcontrol:使用物品(),false,'native shortcut stops placeholder consumption')
 eq(bag[bid].道具.数量,2);eq(bag[qid].道具.数量,1);eq(getter(14).幸运,1);eq(merc_public.属性.幸运,4)
 bag[14].道具=mount(7);refresh();qcontrol:使用物品();eq(bag[bid].道具.数量,2);eq(bag[qid].道具.数量,1)
 bag[14].道具=nil;refresh();qcontrol:使用物品();eq(bag[bid].道具.数量,2)
 bag[14].道具=mount(0);refresh();bag[bid].道具=nil
 qcontrol:使用物品();eq(getter(14).幸运,0,'empty bag cannot use placeholder as free oil');eq(bag[qid].道具.数量,1)
end
-- The companion bag also runs the real original item event while visible.
local mw={名称='佣兵窗口',可视=true,控件组={},坐标={x=0,y=0},闭包=bind}
add(mw,6,'物品格子333',0,0,32,32,333,nil,false,false,0,false,false)
owner.界面_窗口_数组={mw};E.佣兵窗口.可视=true
local real=protected(T.copy(oil,true));real.数量=3;bag[333]={道具=real}
bag[410].道具=mount(0);merc:属性更新();local hb=getter(14).幸运
mw.控件组[1].对象:使用物品();eq(bag[333].道具.数量,2);eq(merc_public.属性.幸运,1);eq(getter(14).幸运,hb)
-- Companion aggregate includes its own other gear once, not hero gear.
merc.装备格子[2]={标识=411,拿起=false};bag[411]={道具={子类='戒指',属性=attrs(1)}}
bag[410].道具=mount(5);merc:属性更新();eq(merc_public.属性.幸运,6)
local kept=T.copy(bag[410].道具,true);bag[410].道具=mount(2);merc:属性更新();eq(merc_public.属性.幸运,3)
bag[410].道具=nil;merc:属性更新();eq(merc_public.属性.幸运,1)
bag[410].道具=protected(kept);merc:属性更新();eq(merc_public.属性.幸运,6,'companion mount field roundtrip')
eq(E.__gm_oil_event_v245(3,333),true);eq(E.__gm_oil_event_v245(6,333),false);eq(E.__gm_oil_event_v245(3,32),false);bag[334]={道具={名称='金创药_小'}};eq(E.__gm_oil_event_v245(3,334),false)
-- Strong direct call guard on quick references, separate from source bag use.
float=0;eq(E.__gm_luck_use_v244(21),false);eq(E.Sys,nil);eq(E._G,nil)

print('LUCK_V248_PASS',mode,checks)
