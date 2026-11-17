local work,mode=arg[1],arg[2]
if mode=='normal'then jit.off()else jit.opt.start('hotloop=1','hotexit=1')end
local checks=0
-- Register the actual native table.copy/proxy helpers, not a clone substitute.
local native_table={};for k,v in pairs(table)do native_table[k]=v end
local table_env=setmetatable({table=native_table},{__index=_G})
local reg=assert(loadfile(work..'/table_register.ljbc'));setfenv(reg,table_env);reg()
table=native_table
local protected_mode=false
local function eq(a,b,msg)checks=checks+1;assert(a==b,(msg or'')..' '..tostring(a)..' ~= '..tostring(b))end
local function noop()end
local function load(n,e)local f=assert(loadfile(work..'/'..n..'.ljbc'));setfenv(f,e);return f end
local function scene(label,id,owner,opts)
 opts=opts or{};local env=setmetatable({class=function()return{}end,Ae冻集={游戏暂停=false},dt=1/60},{__index=_G})
 local E={Ux雌={佣兵对象={id=7}},Gly独={事件对象=function(id)return{id=id,主人id=id==8 and 0 or nil}end}}
 load('mode',env)({},E);load('class_'..label,env)()
 local C=env.类_事件
 local update,reverse,reset=load('anim_update',env),load('anim_reverse',env),load('anim_reset',env)
 local function part()
  local anim={停止=false,时间累积=0,全局计次=0,动画帧=0,首动作='停止',总帧数=4,可视=true,
   更新=update,反向更新=reverse,重置=reset,置中心点=noop,置翻转=noop,置混合模式=noop,动画资源={PAK信息组={{图片=1,精灵={}},{图片=1,精灵={}},{图片=1,精灵={}},{图片=1,精灵={}}},图层信息组={}}}
  local actions={}
  for _,name in ipairs({'攻击','战斗准备','停止','受伤','走','跑','死亡'})do
   actions[name]={帧数组={{1,2,3,4}},帧率=10,混合组={false},翻转组={false},锚点x=0,锚点y=0}
  end
  return{动画=anim,动作组=actions,动画翻转=false}
 end
 local a=setmetatable({id=id,宠物配置=owner and{主人={id=owner}}or{},主人id=owner,属性={hp=100,攻击速度倍数=10},
  当前状态=0,上次状态=0,动作='停止',动画暂停=false,本次攻击动作='攻击',本次动作反向=false,本次动作残影=false,
  本次移动速度倍数=1,施法速度=1,方向=1,资源动画={},动作转移={},键盘移动=false,自动寻路=nil,动态帧组={},
  动画组={part(),part()},可视=false,释放技能组={},击退信息={},巡逻动作='走',跑动动作='跑',僵直效果=true,攻击速度_计次=123,
  事件回调=noop,移动音效间隔=0}, {__index=C})
 if protected_mode then
  local state={script_setting={Gly独={错误=function(msg)error(msg)end}}}
  local protect=load('data_protection',env);debug.setupvalue(protect,1,state);state.数据保护=protect
  a.属性=protect(a.属性,true)
  eq(type(a.属性.__p),'table','actual protected attributes')
  eq(table.copy(a.属性,true).hp,100,'actual proxy-aware copy')
  if owner then
   local raw={id=owner,属性={hp=100},地图格子={x=0,y=0}}
   local public=load('public_actor',env);debug.setupvalue(public,1,state)
   a.宠物配置={主人=public(raw)};a.主人id=nil
   eq(a.宠物配置.主人.id,owner,'actual public owner proxy')
  end
 end
 local finish=load('finish_'..label,env)
 local s={a=a,env=env,E=E,finish=finish}
 function s.attack()
  a:改变动作_(3);a:动作更新()
 end
 function s.endattack()
  for i=1,100 do if a:本次动作结束()then break end;a:动作更新()end
  eq(a:本次动作结束(),true,'original finish predicate reached')
  finish(a)

 end
 return s
end
for _,pair in ipairs({{7},{8,0},{10,7},{11,8}})do
 local old,new=scene('old',pair[1],pair[2]),scene('new',pair[1],pair[2])
 old.attack();new.attack();old.endattack();new.endattack()
 eq(old.a.当前状态,99);eq(new.a.当前状态,99);eq(old.a.动画暂停,true);eq(new.a.动画暂停,true)
 local frames={};for i=1,30 do old.a:动作更新();new.a:动作更新();frames[new.a.动画组[1].动画.当前帧 or 0]=true end
 eq(old.a.动作,'战斗准备','baseline waiting pose preserved');eq(old.a.动画暂停,false)
 eq(new.a.动作,'战斗准备');eq(new.a.动画暂停,false);eq(new.a.当前状态,99);eq(new.a.攻击速度_计次,old.a.攻击速度_计次)
 local n=0;for _ in pairs(frames)do n=n+1 end;assert(n>2,'original animation update visibly progresses')
end
for _,kind in ipairs({'idle','single','missing','active','pause','script','death','knock','moving','hurt','plain99','enemy','hero'})do
 local id=kind=='enemy'and 90 or kind=='hero'and 0 or 7
 local s=scene('new',id);local a=s.a;s.attack();s.endattack()
 if kind=='idle'then for _,p in ipairs(a.动画组)do p.动作组.战斗准备=nil end
 elseif kind=='single'then for _,p in ipairs(a.动画组)do p.动作组.战斗准备.帧数组[1]={1};p.动作组.停止.帧数组[1]={1}end
 elseif kind=='missing'then a.动画组[2].动作组.战斗准备=nil;a.动画组[2].动作组.停止=nil
 elseif kind=='active'then a.释放技能组={ {刷新=noop} }
 elseif kind=='pause'then s.env.Ae冻集.游戏暂停=true
 elseif kind=='script'then a.播放动作=true;a.指定动作='攻击'
 elseif kind=='death'then a.属性.hp=0
 elseif kind=='knock'then a.击退信息={击退中=true,冲刺模式=false}
 elseif kind=='moving'then a:改变动作_(1)
 elseif kind=='hurt'then a:改变动作_(4)
 elseif kind=='plain99'then a.__gm_party_wait_v262=nil end
 a:动作更新()
 if kind=='idle'then eq(a.动作,'停止');eq(a.动画暂停,false)
 elseif kind=='moving'then eq(a.动作,'走')
 elseif kind=='hurt'then eq(a.动作,'受伤')
 else eq(a.动作,'攻击',kind..' protected');eq(a.动画暂停,true,kind)end
 if kind=='active'then a.释放技能组={};a:动作更新();eq(a.动作,'战斗准备','wait until all skills finish')end
end
local s=scene('new',7)
for i=1,200 do s.attack();s.endattack();s.a:动作更新();eq(s.a.当前状态,99);eq(s.a.动画暂停,false);eq(s.a.攻击速度_计次,0)end
-- Same native bodies with the dump's protected attributes and public owner.
protected_mode=true
for _,pair in ipairs({{7},{50063,0},{10,7}})do
 local s=scene('new',pair[1],pair[2])
 for i=1,200 do
  s.a:改变动作_(1);eq(s.a.动作,'走')
  s.a:改变动作_(2,true);eq(s.a.动作,'跑')
  s.attack();s.endattack();s.a:动作更新()
  eq(s.a.当前状态,99);eq(s.a.动作,'战斗准备');eq(s.a.动画暂停,false)
 end
end
if mode=='hot'then eq(jit.status(),true,'global JIT remains enabled')end
print('PARTY_WAIT_V277_PASS',mode,checks,'checks; actual class/motion/reset/animation, protected attributes/public owners and native copy')
