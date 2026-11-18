local work,mode=arg[1],arg[2]
if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')else jit.off()end
local checks=0
local function eq(a,b,m)checks=checks+1;assert(a==b,(m or'check')..': '..tostring(a)..' ~= '..tostring(b))end
local function load(n,env)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,setmetatable(env or{},{__index=_G}));return f end
local function noop()end
local T={};for k,v in pairs(table)do T[k]=v end
load('table_register',{table=T})()
local function copy(v)return T.copy(v,true)end
local function make(story)
 local s={notices={},sys={script_setting={}},hero={},bag={}}
 local env={table=T,Ae冻集={动感格子效果=false,Game_State=0},intable=function(a,k)for _,v in ipairs(a)do if v==k then return true end end;return false end}
 local protect=load('data_protection',env);debug.setupvalue(protect,1,s.sys);s.sys.数据保护=protect
 local config={};local role=load(story==149 and'role_q'or'role_main',env);debug.setupvalue(role,1,config)
 local U={啾啾啵啵=role,人物选择=1,读取人物={},背景音乐={停止=noop},金轮法王=function()return 0 end,胚子考虑=function()return{}end}
 local G={账号信息={账号名称='',唯一标识=''},取控件对象=function()return{}end,鼠标道具=0,转场特效=noop,开始游戏=noop}
 env.Ux雌=U;env.Gly独=G;load('merc_helper',env)(s.sys,{Ux雌=U});env.是否为调试版=function()return true end;env.FXru胃啪={HP=100,等级=50};env.取系统时间=function()return 0 end;env.物品格子18={}
 -- Actual native notice wrapper requests the original one-button modal.
 local ui=assert(loadfile(work..'/modal_fixture.lua'))()(work,env);s.ui=ui
 local notice=load('notice',env)
 G.提示=function(text,...)
  eq(text,'【系统赠送您1瓶祝福油，请查看背包】')
  eq(role().__gm_oil_welcome_v259,true,'claim marker precedes modal')
  s.notices[#s.notices+1]=text
  return notice(text,...)
 end
 env.Sys.run=function(op,f)if op=='adds'then return f()elseif op=='add'then return end;error(op)end
 local water={名称='自然神水_小',分类='道具',子类='消耗品',数量=1,属性={},附加={},资源={},风格提示={}}
 for _,k in ipairs({'最大破坏','最小破坏','最大自然','最小自然','最大灵魂','最小灵魂'})do water.属性[k]=0 end
 local oil=load('oil_template',env)(water);s.oil=oil
 eq(oil.叠加,0);eq(oil.附加.叠加上限,1);eq(oil.附加.快捷物品,0)
 oil.属性=protect(oil.属性,true);oil.附加=protect(oil.附加,true)
 s.sys.游戏道具组={祝福油=oil};s.sys.包裹物品组=s.bag
 s.sys.Hero={背包格子={{32,{},true},{33,{'消耗品'},true},{34,{'武器'},true},{35,{},true},{36,{},true},{37,{},true}}}
 for i=32,37 do s.bag[i]={拿起=false}end
 local free=load('free_slots',env);debug.setupvalue(free,1,s.sys);s.sys.取包裹剩余空位=free;G.取包裹空位=free
 local template=load('template_info',env);debug.setupvalue(template,1,s.sys);G.取道具信息_名称=template
 local add=load('add_item',env);debug.setupvalue(add,1,s.sys);s.sys.增加物品=add
 local glyadd=load('gly_add',env);debug.setupvalue(glyadd,1,s.sys);G.增加物品=glyadd
 s.sys.取包裹指定物品个数=function(name)local n=0;for _,b in pairs(s.bag)do if b.道具 and b.道具.名称==name then n=n+b.道具.数量 end end;return n end
 s.sys.格式化道具属性=function()return''end;s.sys.更新道具属性=noop
 load('stack_install',env)(s.sys)
 s.sys.qs_item_box=noop;s.sys.界面_窗口_数组={};s.sys.脚本关联处理=noop
 local disk={};local stored={名称='角色甲',职业='战士',性别='男'}
 G.读档=function(path)eq(path,'save.dat');return copy(disk.role or stored)end
 G.存档=function(path,r,key)disk.role=copy(r)end
 local cb={配置文件=noop,技能切换=noop}
 local login=load('login_'..story,env);debug.setupvalue(login,1,cb)
 local save=load('save_'..story,env);debug.setupvalue(save,1,cb)
 function s.enter(r)if r then stored=r;disk.role=nil end;login('save.dat');s.hero=role()end
 function s.save()save('存档',1,nil);return disk.role end
 function s.count()return s.sys.取包裹指定物品个数('祝福油')end
 s.G=G;s.env=env;s.disk=disk;s.role=role
 return s
end
for _,story in ipairs({149,179})do
 local s=make(story)
 for _,id in ipairs({32,33,35,36,37})do s.bag[id].道具={名称='占位',数量=1}end
 s.enter();eq(s.count(),0);eq(s.hero.__gm_oil_welcome_v259,nil);eq(#s.notices,0)
 s.save();s.bag[32].道具=nil;s.enter();eq(s.count(),1);eq(s.hero.__gm_oil_welcome_v259,true);eq(#s.notices,1)
 eq(s.ui.box.提示内容,'【系统赠送您1瓶祝福油，请查看背包】');s.ui.update(2.999,'click');eq(s.ui.box.可视,true)
 s.ui.update(3,'click');eq(s.ui.box.可视,false)
 s.save();for i=1,200 do s.enter()end;eq(s.count(),1);eq(#s.notices,1)
 s.bag[32].道具=nil;s.enter();eq(s.count(),0);eq(#s.notices,1)
 s.enter({名称='角色乙',职业='法师',性别='女'});eq(s.count(),1);eq(#s.notices,2)
 local failed=make(story);failed.G.增加物品=function()return false end;failed.enter();eq(failed.hero.__gm_oil_welcome_v259,nil);eq(#failed.notices,0)
 -- Legacy stack remains five; a fresh bottle occupies a separate slot.
 s=make(story);local legacy=copy(s.oil);legacy.数量=5;legacy.叠加=1;legacy.附加.叠加上限=999
 s.bag[32].道具=legacy;s.enter();eq(s.bag[32].道具.数量,5);eq(s.count(),6);eq(#s.notices,1)
 local singles=0;for _,b in pairs(s.bag)do if b.道具 and b.道具.名称=='祝福油'and b.道具~=legacy then eq(b.道具.数量,1);singles=singles+1 end end;eq(singles,1)
 eq(s.sys.增加物品('祝福油',2),true);eq(s.count(),8);eq(legacy.数量,5)
 for _,b in pairs(s.bag)do if b.道具 and b.道具~=legacy then eq(b.道具.数量,1,'every newly added oil is a single bottle')end end
 local items,ids={},{};for id=32,37 do if s.bag[id].道具 then items[#items+1]=copy(s.bag[id].道具);ids[#ids+1]=id end end
 s.sys.__gm_potion_sort_v158(items,s.bag,ids);eq(s.count(),8);eq(legacy.数量,5,'sort does not split/clamp legacy stack')
 -- Actual reload overlay wrapper must retain quantity and disable re-merging.
 local changed;local reset=load('oil_reset',s.env);debug.setupvalue(reset,1,s.sys);debug.setupvalue(reset,2,function(id,c)changed=c;return true end)
 local saved=copy(legacy);reset(32,saved);eq(changed.数量,5);eq(changed.叠加,0);eq(changed.附加.快捷物品,0);eq(saved.叠加,1,'no mutation of caller save overlay')
end
print('GIFT_STACK_V280_PASS '..mode..' checks='..checks..'; native load/add/modal request and legacy-stack preservation, finite UI/file bridges')
