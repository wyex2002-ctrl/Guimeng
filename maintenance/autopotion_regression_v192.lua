local work,mode=arg[1],arg[2]or'normal'
if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end
local checks=0
local function eq(a,b,label)checks=checks+1;assert(a==b,(label or'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function load(name,env)local f=assert(loadfile(work..'/'..name..'.ljbc'));setfenv(f,env or _G);return f end
local function bind(name,S,env)local f=load(name,env);debug.setupvalue(f,1,S);return f end
local function copy(t)
 if type(t)~='table'then return t end
 if rawget(t,'__p')~=nil then t=t()end
 local n={};for k,v in pairs(t)do n[k]=copy(v)end;return n
end
local T={};for k,v in pairs(table)do T[k]=v end;T.copy=copy

local templates=assert(loadfile(work.."/templates.lua"))()
-- class(), text and rectangle creation are unavailable engine primitives.
-- Only these are finite facades. All game class registrations, initializer,
-- inventory use, consumption, native control construction and DB callbacks
-- below are the actual resource bytecode, not handwritten item methods.
local function inventory_trial(story,visible,mp,quick,broken,name,bagid,version)
 bagid=bagid or 32;version=version or "aux"
 local id=story=='前尘忆梦'and 1 or 21
 local item=copy(templates[name]);item['数量']=3;item['属性']={}
 local names={'生命值','法力值','生命值_百分比','法力值_百分比','物理伤害','魔法伤害','魔法防御','物理防御','命中','躲避','暴击','移动速度','攻击速度'}
 for _,k in ipairs(names)do item['属性'][k]=item[k]or 0 end
 local req={};local function request(v,kind)req[kind or 2]=(req[kind or 2]or 0)+v end
 local slots={};for i=1,150 do slots[i]={}end
 slots[bagid]={['道具']=item}
 if quick then
  local q=copy(item);q['附加']['快捷物品']=true;q['数量']=1
  q['物品脚本']={} -- shortcut never performs default consumption
  slots[id]={['道具']=q}
 end
 local hp,blue,hp_calls,mp_calls=5,5,0,0
 local hero={['背包格子']={},['装备格子']={},['属性']={['等级']=21,['性别']='男',['职业']='战士',maxhp=100,maxmp=100},['BUFF状态更新']=function()end,
 ['HP改变']=function(_,v)hp=hp+v;hp_calls=hp_calls+1 end,['MP改变']=function(_,v)blue=blue+v;mp_calls=mp_calls+1 end}
 local S={Game_State=1,['Hero']=hero,['包裹物品组']=slots,sid=0,shelp={},script_setting={}}
 S['数据保护']=bind('proxy',S);S['包裹物品组']=S['数据保护'](slots,true)
 slots=S['包裹物品组']
 local native_use=bind('use',S)
 local G={['取包裹空位']=function()return 100 end,['使用物品']=native_use,['从ID取格子']=function(i)return slots[i]end,['取按键状态']=function()return false end,
 ['取物品数量']=function(n)return slots[bagid]['道具']and slots[bagid]['道具']['数量']or 0 end}
 local U={['版本选择']=story,['主角HP']=mp and 100 or hp,['主角MAXHP']=100,['主角MP']=mp and blue or 100,['主角MAXMP']=100,['人物选择']=1,['托管显示']={['屏幕提示']=function()error('unexpected gameplay gate')end}}
 local owner={['角色组']={['法治观念']=true,['技能']={}},['配置']={['主角格子']={}},['游戏格子']=slots}
 for key,name in pairs({['啾啾啵啵']=story=='前尘忆梦'and'role_a'or'role_b',['胚子考虑']=story=='前尘忆梦'and'config_a'or'config_b'})do U[key]=bind(name,owner,{['Ux雌']=U})end
 U['呦西鸽子']=bind('slots_get',owner)
 local getter=bind('public_get',S);S.get=getter
 local public=load('public_sys')(S)
 local env={type=type,['Ux雌']=U,['Gly独']=G,['物品格子18']={},['FXru胃啪']={HP=100,['取状态列表']=function()return{}end},['L常量']={},['仓库窗口2']={['可视']=false},['信息窗口2']={['可视']=false},['商店窗口2']={['可视']=false},['行会仓库2']={['可视']=false},['聊天输入框']={['焦点']=false},['英雄HP输入框']={['焦点']=false},['英雄MP输入框']={['焦点']=false}}
 S.script_setting=env;S.tbl_controls={}

 for _,s in ipairs({'红','蓝'})do env['加'..s..'选择框']={['选中']=false};env['加'..s..'滑块条']={['位置']=50}end
 for _,name in ipairs({'仓库窗口','佣兵窗口','商店窗口','行会仓库','信息窗口'})do env[name]={['可视']=false}end
 U['主角红恢复量']=0;U['主角蓝恢复量']=0
 U['窗口相关']={['加血加蓝']=request}
 env.math=math;env['分割文本']=function(text,sep)
  local r={};local i=1;while true do local a,b=text:find(sep,i,true);if not a then r[#r+1]=text:sub(i);break end;r[#r+1]=text:sub(i,a-1);i=b+1 end;return r
 end
 env['FXru胃啪']['增加状态']=function()end
 G['取道具信息_格子']=function(i)return slots[i]and slots[i]['道具']end
 G['取随机数']=function(a,b)eq(a,1);eq(b,4);return 1 end
 item['物品脚本']=load('script_'..(name:gsub('.',function(c)return string.format('%02x',string.byte(c))end)),env)()
 if quick then slots[id]['道具']['物品脚本']=item['物品脚本']end
 local event=load('item_event',env);S.shelp[tostring(event)]={sid=5,msg='real item event'}
 local original_error;G['错误']=function(e)original_error=e end
 local dispatch=bind('dispatch',S);S.fun=dispatch
 local aux=load(version,env);U['窗口相关']['辅助窗口']=aux;debug.setupvalue(aux,1,U['窗口相关'])
 local log={};S.__gm_detail_v179=function(tag,msg)log[#log+1]=tag..' '..msg end
 local cd={};local tex=function()return{}end
 local engine_run=function(action,a,b)
  if action=='qs_item_box'then
   local ok,r=dispatch(event,a,0);assert(ok,original_error or r);return ok,r
  elseif action=='fun'then return true,a(unpack(b))
  else error('unexpected engine action '..tostring(action))end
 end
 S.run=engine_run
 -- Sys.get uses the original explicit fields below, not a dynamic fake API.
 S['文字标签类']=nil
 local uiSys={get=function(key)
  if key=='hero'then return hero elseif key=='item_arr'then return slots elseif key=='item_cd_arr'then return cd elseif key=='win_tex'then return tex else error('unexpected ui engine key '..tostring(key))end
 end,run=engine_run,add=function(key,name,value)eq(key,'tbl_controls');S.tbl_controls=S.tbl_controls or{};S.tbl_controls[name]=value end}
 local ui={class=function()
  local C={};C['创建']=function(...)local o=setmetatable({},{__index=C});C['初始化'](o,...);return o end;return C
 end,math=math,table=table,select=select,setmetatable=setmetatable,['Sys']=load('public_sys')(uiSys),['Q_文字']={['取高度']=function()return 12 end},['Q_鼠标']={['格子标识']=0},['D2D_包围盒']={['创建']=function()return{}end},['Ae冻集']={['快捷事件组']={},['控件名称组']={},['包裹物品数']=150,['自定义属性表']={}}}
 setmetatable(ui,{__index=_G}) -- native module environment, not the DB sandbox
 load('inventory_class',ui)()
 local bind_control=load('bind_control',ui)
 local win={['名称']='背包窗口',['可视']=visible,['控件组']={},['坐标']={x=0,y=0},['闭包']=bind_control}
 local add=load('add_control',ui)
 for qid=id,id+5 do add(win,6,'物品格子'..qid,0,0,32,32,qid,nil,false,false,0,false,false)end
 add(win,6,'物品格子'..bagid,0,0,32,32,bagid,nil,false,true,0,false,false)
 local obj=win['控件组'][#win['控件组']]['对象']
 eq(type(obj['使用物品']),'function');eq(obj['标识'],bagid);eq(obj['格子组'],slots);eq(#hero['背包格子'],1)
 if broken then table.insert(win['控件组'],1,{['名称']='过期同ID格子',['类型']=6,['格子ID']=bagid,['对象']={}})end
 S['界面_窗口_数组']={win};load('profile',ui)(S)
 eq(public.get('__gm_item_control_v189'),nil);eq(public.get('__gm_item_seq_v189'),nil)
 -- Execute the original load loop (12/179 PC456..497), including
 -- table.insert and public controls returned by real 48/23 bindings.
 bind('sandbox_install',S,_G)();eq(env.Sys,nil,'event environment has no Sys');eq(env.pcall,nil);eq(env._G,nil)
 local factory=load('gly_factory',_G);debug.setupvalue(factory,2,S)
 local exported=factory();G['取控件对象']=exported['取控件对象'];eq(type(G['取控件对象']),'function')
 local init=load('initialize_controls',{['Gly独']=G,['Ux雌']=U,table=table});init()
 eq(#owner['配置']['主角格子'],7,'real initialization creates dense list')
 eq(owner['配置']['主角格子'][bagid],nil,'list index differs from native slot ID')
 eq(env.Sys,nil,'native getter is deliberately unavailable to the event')
 eq(env.pcall,nil);eq(env._G,nil)
 -- Compare automation to an actual manual invocation of the same
 -- original drug script. Effect ticks belong to the absent client engine.
 eq(obj['使用物品'](obj),true,'manual reference');eq(item['数量'],2)
 local reference=copy(req);req={};item['数量']=3
 local function check_request()
  eq(req[1]or 0,reference[1]or 0,'same HP request as real manual use')
  eq(req[2]or 0,reference[2]or 0,'same MP request as real manual use')
 end
 local periodic=load('periodic',env);S.shelp[tostring(periodic)]={sid=13,msg='real hero periodic potion slice'}
 local function invoke()local ok,r=dispatch(periodic,{});assert(ok,original_error or r)end
 if version=='aux_old'then
  local ok,err=dispatch(periodic,{});eq(ok,false,'v191 actual event failure reproduced');err=original_error or err
  eq(item['数量'],3,'old dense-list bug reproduced');eq(next(req),nil)
  eq(tostring(err):find("global 'Sys'",1,true)~=nil,true,'exact uploaded v191 error: '..tostring(err))
  return checks
 end
 invoke()
 eq(item['数量'],2,'exactly one genuine consumption');check_request()
 for i=1,200 do
  item['数量']=3;req={}
  invoke()
  eq(item['数量'],2,'repeated auxiliary consumption');check_request()
 end
 if quick then eq(slots[id]['道具']['数量'],1,'shortcut never consumes its placeholder')end
 -- Missing UI bindings are a safe no-op, including bag-capacity fallback.
 local controls=S.tbl_controls;S.tbl_controls={};item['数量']=3;req={}
 invoke();eq(item['数量'],3,'missing controls skipped');eq(next(req),nil);S.tbl_controls=controls
 -- Threshold and non-medicine slots must not trigger consumption.
 local field=mp and'主角MP'or'主角HP';U[field]=100;item['数量']=3;req={}
 invoke();eq(item['数量'],3,'above threshold');eq(next(req),nil);U[field]=5
 local original_flags=item['附加'];item['附加']={};req={}
 -- Empty quick slot removes the shortcut's independent selector flags.
 local savedquick=slots[id]['道具'];slots[id]['道具']=nil
 invoke();eq(item['数量'],3,'non-medicine skipped');eq(next(req),nil)
 item['附加']=original_flags;slots[id]['道具']=savedquick
 -- Empty quick/ordinary cells do not reuse depleted potions.
 item['数量']=2;eq(obj['使用物品'](obj),true);eq(item['数量'],1)
 eq(obj['使用物品'](obj),true);eq(slots[bagid]['道具'],nil)
 eq(obj['使用物品'](obj),false,'empty cell safe');invoke()
 return checks
end
for _,story in ipairs({'前尘忆梦','来世续缘'})do
 for _,visible in ipairs({false,true})do
  for _,name in ipairs({'金创药_小','魔法药_小','太阳水','强效太阳水','万年雪霜'})do
   for _,mp in ipairs({false,true})do
    if templates[name]['附加'][mp and'加蓝'or'加血']~=nil then
     inventory_trial(story,visible,mp,false,true,name,32,'aux_old')
     for _,quick in ipairs({false,true})do
      for _,bag in ipairs({31,32,80,126})do inventory_trial(story,visible,mp,quick,true,name,bag)end
     end
    end
   end
  end
 end
end
print('AUTOPOTION_V192_PASS',mode,checks)
