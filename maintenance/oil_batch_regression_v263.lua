local work,mode=arg[1],arg[2]
if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')else jit.off()end
local oil_weights={{1,0,0},{.70,.10,.20},{.55,.15,.30},{.40,.20,.40},{.20,.32,.48},{.09,.39,.52},{.03,.46,.51}}
local function b3(x)x=math.min(9,math.max(0,x));return x<1 and 0 or math.min(1,1/(10-x)+.10*x/7+.08*(x/7)^2)end
local checks=0;local function eq(a,b,m)checks=checks+1;assert(a==b,(m or'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function load(n,env)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,env);return f end
local function noop()end
local N=setmetatable({},{__index=_G});N.math=setmetatable({round=function(n)return math.floor(n+.5)end},{__index=math});local T={};for k,v in pairs(table)do T[k]=v end;N.table=T;load('table_register',N)()
local function zero()return setmetatable({},{__index=function()return 0 end})end
local props={'物理伤害','魔法伤害','物理防御','魔法防御','生命值','法力值','命中','躲避','暴击','移动速度','攻击速度','最大破坏','最小破坏','最大自然','最小自然','最大灵魂','最小灵魂','最大防御','最小防御','最大魔防','最小魔防','幸运'}
N.Ae冻集={自定义属性表=props}
local function attrs(luck)local a={};for _,k in ipairs(props)do a[k]=0;a[k..'_百分比']=0 end;a.幸运=luck or 0;return a end
local messages,actors={},{};local float=.5;local float_calls,integer_calls=0,0;local length=5;local samples;local sample_index=0
N.引擎={取随机小数=function(_,lo,hi)eq(lo,0);eq(hi,1);float_calls=float_calls+1;sample_index=sample_index+1;return samples and samples[sample_index]or float end,取随机整数=function(_,lo,hi)eq(lo,5);eq(hi,10);integer_calls=integer_calls+1;return length end}
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
E.__gm_stat_v162=nil
local install=load('install',N);debug.setupvalue(install,1,owner);install(E);eq(owner.script_setting,E);eq(E.pcall,nil);eq(E._G,nil);eq(E.Sys,nil)
local sys={get=function(k)if k=='item_arr'then return bag end end}
local run=function(op,func,...)
 if op=='fun'then return true,func(unpack((...)))end
 if op=='adds'then setfenv(func,E);return func()elseif op=='add'then return end
 if op=='qs_item_box'then return true,false end
 if op=='创建时钟'then return true end
 error('unexpected '..op)
end
N.Sys=load('public_sys',N)({get=sys.get,run=run});N.Q_鼠标={格子标识=0,物品来源={}}
local function refresh()h.refreshes=(h.refreshes or 0)+1 end
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
local function apply(v,source,quantity)
 local t=T.copy(oil,true);t.数量=quantity or 3;source=source or 32;bag[source]={道具=t};float=v or .5;sample_index=0
 control.标识=source;local oilref=bag[source].道具;local ok=use(control);return ok,oilref.数量
end
local key='__gm_oil_batch_v263'
local function batch(item)return item.附加[key]end
local function reload(item)
 local saved=load('save_item',N)(item)
 local text=T.tostring(T.copy(saved,true))
 local restored=T.loadstring(text)
 -- Native item reset applies the saved overlay to a fresh template.
 local reset=load('reset_item',N);debug.setupvalue(reset,1,owner)
 owner.更新道具属性=function(id,fields)
  for k,v in pairs(fields)do bag[id].道具[k]=type(v)=='table'and proxy(v,true)or v end
 end
 local c={格子ID=14,对象={物品进入=noop,计算属性=false}}
 bag[14].道具=nil
 assert(reset(c,saved.名称,saved.数量,false,restored,false))
 return bag[14].道具,text
end
local ok,n=apply();eq(ok,false);eq(n,3);eq(integer_calls,0);eq(float_calls,0)
-- Exact lengths, all outcomes consuming once including the guaranteed 0->1.
for _,size in ipairs({5,6,7,8,9,10})do
 length=size;samples=nil;bag[14].道具=mount(0)
 local fc,ic=float_calls,integer_calls
 ok,n=apply(.9876543210123456);eq(ok,true);eq(n,2)
 local m=bag[14].道具;eq(m.属性.幸运,1);eq(batch(m).length,size);eq(batch(m).next,2);eq(float_calls,fc+size);eq(integer_calls,ic+1)
 eq(tonumber(batch(m).values[1]),.9876543210123456,'full-precision sample')
 if size==5 then m=reload(m);eq(tonumber(batch(m).values[2]),.9876543210123456,'native save preserves pending sample precision')end
 for i=2,size do
  m.属性.幸运=1;ok,n=apply(0);eq(ok,true);eq(n,2);eq(m.属性.幸运,1,'fixed high roll remains unchanged');eq(batch(m).next,i+1)
 end
 eq(integer_calls,ic+1,'no pre-generation at final element');eq(float_calls,fc+size)
 m.属性.幸运=1;ok,n=apply(0);eq(ok,true);eq(n,2);eq(m.属性.幸运,2);eq(batch(m).next,2);eq(integer_calls,ic+2);eq(float_calls,fc+2*size)
end
-- Every original probability boundary still uses CURRENT level, not batch-time.
for level=0,6 do
 local weights=oil_weights[level+1]
 local rolls=level==0 and {0,.999999}or {0,weights[1]-1e-9,weights[1],weights[1]+weights[2]-1e-9,weights[1]+weights[2],.999999}
 for _,v in ipairs(rolls)do
  length=5;samples=nil;bag[14].道具=mount(level);ok,n=apply(v);eq(ok,true);eq(n,2)
  local expected=v<weights[1]and level+1 or v<weights[1]+weights[2]and level-1 or level
  eq(bag[14].道具.属性.幸运,expected);eq(batch(bag[14].道具).next,2)
 end
end
-- Invalid/non-consuming uses never generate or advance anything.
bag[14].道具=mount(7);local fc,ic=float_calls,integer_calls
ok,n=apply();eq(ok,false);eq(n,3);eq(batch(bag[14].道具),nil);eq(float_calls,fc);eq(integer_calls,ic)
bag[14].道具=mount(1);apply(.9);local m=bag[14].道具;local at=batch(m).next
m.属性.幸运=7;ok,n=apply();eq(ok,false);eq(n,3);eq(batch(m).next,at)
m.属性.幸运=1;h.装备格子[1].拿起=true;ok,n=apply();eq(ok,false);eq(n,3);eq(batch(m).next,at);h.装备格子[1].拿起=false
ok,n=apply(.5,32,0);eq(ok,false);eq(n,0);eq(batch(m).next,at)
-- Other engine RNG and combat rolls cannot alter an existing batch.
local before=T.tostring(T.copy(batch(m),true));float=.001;E.__gm_luck_attack_v244(1,2,{幸运属性=25},fx)
N.引擎:取随机小数(0,1);eq(T.tostring(T.copy(batch(m),true)),before)
-- Save snapshot after batch creation, full-precision serializer/readback, S/L.
length=5;samples={.1,.75,.9,.2,.99};bag[14].道具=mount(1);apply();m=bag[14].道具
local reloaded,text=reload(m);eq(batch(reloaded).next,2);eq(tonumber(batch(reloaded).values[2]),.75)
local snapshot=T.copy(reloaded,true)
for i=1,200 do
 bag[14].道具=protected(T.loadstring(T.tostring(snapshot)))
 samples=nil;float=(i-.5)/200
 local fc,ic=float_calls,integer_calls;ok,n=apply(float);eq(ok,true);eq(n,2)
 eq(bag[14].道具.属性.幸运,2,'same saved roll gives same unchanged result from luck2');eq(batch(bag[14].道具).next,3)
 eq(float_calls,fc);eq(integer_calls,ic)
end
-- Same saved sample .75 uses the CURRENT luck1 -> loss0, not luck2 -> unchanged2.
bag[14].道具=protected(T.copy(snapshot,true));bag[14].道具.属性.幸运=1;apply(.001);eq(bag[14].道具.属性.幸运,0)
-- At exhausted-save boundary the next batch may intentionally be rerolled.
bag[14].道具=protected(T.copy(snapshot,true));m=bag[14].道具;batch(m).next=6;local exhausted=T.copy(m,true)
for _,v in ipairs({0,.9})do
 bag[14].道具=protected(T.copy(exhausted,true));apply(v);eq(batch(bag[14].道具).next,2);eq(bag[14].道具.属性.幸运,v==0 and 3 or 2)
end
-- True independent mounts, including an absent companion actor's equipment.
local merc={id=42,装备格子={{标识=410,拿起=false}},属性更新=refresh};owner.屏幕事件组={merc};U.佣兵对象={id=42}
local first=protected(T.copy(snapshot,true));bag[14].道具=first;bag[410]={道具=mount(1)};apply(.9,333)
local second=bag[410].道具;eq(batch(first).next,2);eq(batch(second).next,2);eq(second.属性.幸运,1)
apply(.1,32);eq(batch(first).next,3);eq(batch(second).next,2)
apply(.1,333);eq(batch(first).next,3);eq(batch(second).next,3);eq(second.属性.幸运,1)
-- Native drag/swap/place covers unequip, bag rearrange, warehouse slots,
-- companion transfer and re-equip: no item identity-dependent sequence state.
local take,swap,place=load('take',N),load('swap',N),load('place',N)
local function ctl(id)
 bag[id]=bag[id]or{}
 return{标识=id,格子组=bag,能否放下=function()return true end,主角纸娃娃更新=noop,弹簧效果刷新=noop,放下物品=place}
end
local expected=T.tostring(T.copy(batch(first),true));bag[14].道具=first;bag[410].道具=nil
for _,pair in ipairs({{14,40},{40,41},{41,200},{200,201},{201,410},{410,14}})do
 local a,b=ctl(pair[1]),ctl(pair[2]);take(a);swap(b);place(b)
 eq(bag[pair[2]].道具,first);eq(T.tostring(T.copy(batch(first),true)),expected)
end
m=reload(first);eq(T.tostring(T.copy(batch(m),true)),expected,'transferred item native capture/reset retains sequence')
-- Exceptions before consume leave ALL persistent values untouched; subsequent
-- use clears the aborted slot transaction. Exceptions after commit retain all.
bag[14].道具=mount(1);m=bag[14].道具;local oldbuff=h.BUFF状态更新
h.BUFF状态更新=function()error('before consume')end
local pass,err=pcall(apply,.1);eq(pass,false);assert(tostring(err):find('before consume',1,true));eq(m.属性.幸运,1);eq(batch(m),nil);eq(bag[32].道具.数量,3)
h.BUFF状态更新=oldbuff;apply(.9);eq(m.属性.幸运,1);eq(batch(m).next,2)
local oldrefresh=h.属性更新;h.属性更新=function()error('after commit')end
pass,err=pcall(apply,.1);eq(pass,false);assert(tostring(err):find('after commit',1,true));eq(m.属性.幸运,1);eq(batch(m).next,3);eq(bag[32].道具.数量,2)
h.属性更新=oldrefresh
-- Last bottle clears its slot once, ordinary consumables retain native consume.
ok,n=apply(.1,32,1);eq(ok,true);eq(n,0);eq(bag[32].道具,nil);eq(batch(m).next,4)
local plain=T.copy(oil,true);plain.名称='普通消耗品';plain.物品脚本.Main=function()return true end;plain.数量=2;bag[32]={道具=plain};control.标识=32
ok=use(control);eq(ok,true);eq(bag[32].道具.数量,1)
-- Template and unrelated fields remain intact; no batch is attached to oil.
eq(base.附加[key],nil);eq(oil.附加[key],nil);eq(owner.游戏道具组.测试坐骑.属性.幸运,0)
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
N.Q_文字={};N.Q_文字.取高度=function()return 12 end;N.D2D_包围盒={创建=function()return{}end}
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
 bag[14].道具=mount(0);refresh();bag[410].道具=mount(4);refresh()
 eq(qcontrol:使用物品(),false,'native shortcut stops placeholder consumption')
 eq(bag[bid].道具.数量,2);eq(bag[qid].道具.数量,1);eq(bag[14].道具.属性.幸运,1);eq(bag[410].道具.属性.幸运,4);eq(batch(bag[14].道具).next,2)
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
bag[410].道具=mount(0);refresh();local hb=getter(14).幸运
mw.控件组[1].对象:使用物品();eq(bag[333].道具.数量,2);eq(bag[410].道具.属性.幸运,1);eq(batch(bag[410].道具).next,2);eq(getter(14).幸运,hb)

print('v263 oil batches native regression OK '..mode..' checks='..checks..'; controlled save/reload and native transfers; no Windows client IO')
