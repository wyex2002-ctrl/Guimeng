local work,mode=arg[1],arg[2]
if mode=='normal'then jit.off()else jit.opt.start('hotloop=1','hotexit=1')end
local checks=0
local function eq(a,b,msg)checks=checks+1;assert(a==b,(msg or'')..' '..tostring(a)..' ~= '..tostring(b))end
local function load(name,env)local f=assert(loadfile(work..'/'..name..'.ljbc'));setfenv(f,env);return f end
local function make(label,story)
 local cfg={};local messages={};local actions={};local state={}
 local E=setmetatable({},{__index=_G})
 E.底部窗口={可视=true};E.底部窗口2={可视=true};E.信息窗口={可视=false};E.信息窗口2={可视=false};E.物品格子18={}
 E.反击选择框={选中=true};E.自动练功选择框={选中=true}
 E.Gly独={镜头缩放=1};E.FXru胃啪={地图格子={x=0,y=0}}
 E.Gly独.事件对象=function(id)return{id=id,HP=100,阵营='敌方',地图格子={x=1,y=0}}end
 E.取两点间距离=function(x,y,a,b)return math.max(math.abs(x-a),math.abs(y-b))end
 E.L常量={键_A=65,键_D=68,键_S=83}
 E.Ux雌={版本选择=story or'来世续缘',技能快捷键=nil,胚子考虑=function()return cfg end,
  托管显示={屏幕提示=function(t,style)messages[#messages+1]={t,style}end},
  窗口相关={窗口开关=function(...)actions[#actions+1]={...}end,技能切换=function()actions[#actions+1]={'skill'}end}}
 local event=load(label,E)();eq(type(event.Main),'function');local f=event.Main
 return{E=E,cfg=cfg,messages=messages,actions=actions,key=f,counter=load('counter',E),settings=load('settings',E)}
end
local old,new=make('old'),make('new')
old.key(9,0);eq(old.E.Ux雌.技能快捷键,0,'previous Tab toggles skill lock');eq(old.E.自动练功选择框.选中,false);eq(old.E.反击选择框.选中,true)
new.key(9,0);eq(new.E.反击选择框.选中,false,'Tab opens original retaliation mode');eq(new.messages[1][1],'自动反击打开');eq(new.messages[1][2],-32768)
eq(new.E.Ux雌.技能快捷键,nil,'no skill lock side effect');eq(new.E.自动练功选择框.选中,true)
new.counter(9);eq(new.E.FXru胃啪.目标,9,'native callback sees enabled mode')
new.key(9,0);eq(new.E.反击选择框.选中,true);eq(new.messages[2][1],'自动反击关闭')
new.counter(10);eq(new.E.FXru胃啪.目标,9,'native callback no longer selects another target')
local f=make('old');f.key(70,0);eq(f.E.反击选择框.选中,false)
local f=make('new');f.key(70,0);eq(f.E.反击选择框.选中,true,'former F binding is removed');eq(#f.messages,0)
-- Representative repeated key events; native engine key-repeat policy unchanged.
for i=1,200 do new.key(9,0);eq(new.E.反击选择框.选中,i%2==0);eq(new.messages[i+2][1],i%2==1 and'自动反击打开'or'自动反击关闭')end
eq(new.E.Ux雌.技能快捷键,nil);eq(new.E.自动练功选择框.选中,true)
new.E.反击选择框.选中=false;new.settings();eq(new.E.反击选择框.选中,true,'existing settings reset remains authoritative');new.key(9,0);eq(new.E.反击选择框.选中,false)
-- Existing event guards still suppress gameplay keys during blocked UI modes.
for _,reason in ipairs({'hidden','zoom','item','modal'})do
 local s=make('new');if reason=='hidden'then s.E.底部窗口.可视=false elseif reason=='zoom'then s.E.Gly独.镜头缩放=2 elseif reason=='item'then s.E.物品格子18.道具={}else s.E.信息窗口.可视=true end
 s.key(9,0);eq(s.E.反击选择框.选中,true,reason);eq(#s.messages,0,reason)
end
-- Independent window shortcuts and the prequel's distinct hero AI are intact.
for _,key in ipairs({66,73,75,77,81,87})do
 local a,b=make('old'),make('new');a.key(key,0);b.key(key,0);eq(#a.actions,#b.actions);for i,row in ipairs(a.actions)do for j,x in ipairs(row)do eq(x,b.actions[i][j])end end
end
for _,label in ipairs({'old','new'})do local s=make(label,'前尘忆梦');s.key(9,0);eq(s.E.反击选择框.选中,true);eq(#s.messages,0)end
print('TAB_V261_PASS',mode,checks,'checks; native key factory/Main and retaliation target callback')
