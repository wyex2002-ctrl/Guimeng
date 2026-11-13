local work,mode=arg[1],arg[2]
if mode=='hot' then require('jit.opt').start('hotloop=1','hotexit=1')end
local function execute(version,phase)
 local events,logs={},{};local tick,elapsed=0,0
 local function op(name)return function(...)events[#events+1]=name end end
local E={['游戏进度']=1,['逻辑暂停']=0,['屏幕焦点']=true,['最后按键']=0,['界面可视']=true,['游戏暂停']=false,
 ['屏幕震动时间']=0,['屏幕宽度']=800,['屏幕高度']=600,['屏幕缩放']=1,['画面偏移']={x=0,y=0},
 ['鼠标_屏幕坐标']={x=0,y=0},['鼠标_地图坐标']={x=0,y=0},['鼠标_地图格子']={x=0,y=0},['遮罩信息']={['启动']=false}}
local S={Game_State=1,['控制对象']={},['Hero']={['更新']=op('hero.update'),['属性']={hp=100}},['script_setting']={['Ux雌']={},['Gly独']={}}}
for _,name in ipairs({'游戏技能组','道具CD信息组','屏幕特效组','屏幕锁链组','屏幕粒子组','屏幕事件组','屏幕子弹组','界面_窗口_数组','屏幕提示组','屏幕气泡组','Plug','动画精灵组','剧情对话框','剧情资源表','time_table','创建窗口组'})do S[name]={}end
for _,name in ipairs({'取鼠标所在窗口','状态图标显示控制','状态图标显示提示','焦点触发'})do S[name]=op(name)end
S.temp_spr={['置混合模式']=op('composite.blend'),['显示_范围缩放']=op('composite.draw')}
S['banner']={show=op('banner')};S['黑边特效']={show=op('letterbox')}
S.get=function(key)if key=='item_box'then return{}end end
S.Hero['焦点触发']=op('hero.focus')
S['中间提示组']={};S['中间遮罩']={['可视']=false};S['气泡提示组']={}
for i=0,9 do S['气泡提示组'][i]={['可视']=false}end
local env={['Ae冻']={},['Ae冻集']=E,dt=0.016,Sys=S,['丰富文本_动画更新显示']=op('richtext'),['Q_公用动画库']={},['Q_提示框']={['可视']=false},
 ['Q_鼠标']={},['Q_地图']={['更新']=op('map.update'),['显示']=function()op('map.draw')();tick=tick+0.300 end},['Q_文字']={['显示']=op('text')},
 ['引擎']={['取按键按下']=function()return false end,['取按键弹起']=function()return false end,['调整屏幕']=op('camera')},
 ['L常量']={},['核心']={http_url_get=function()return {['总数']=0}end}}
env._G=env;env.loadstring=function(src)local f,e=loadstring(src);if f then setfenv(f,env)end;return f,e end
env.os={clock=function()return tick end,time=function()return math.floor(elapsed)end};S.__gm_detail_v179=function(tag,msg) logs[#logs+1]=tag..' '..msg;tick=tick+0.007 end
setmetatable(env,{__index=function(_,k)if k=='__gm_bulk_sale_tick_v177' or k=='__gm_info_tick_v137' then return nil end;if _G[k]~=nil then return _G[k]end;error('MISSING GLOBAL '..tostring(k))end})

 S['屏幕事件组']={{id=17,['名称']='慢对象',['临时焦点触发']=op('actor.focus'),['更新']=function()op('actor.update')();tick=tick+0.564;S['屏幕事件组'][1]=nil end}}
 local f=assert(loadfile(work..'/frame_'..version..'.ljbc'));setfenv(f,env);debug.setupvalue(f,1,S);debug.setupvalue(f,2,{})
 S.run=f
 if phase=='installed' then local install=assert(loadfile(work..'/profile_only.ljbc'));setfenv(install,env);install(S)
 else S.__gm_perf_phase_v186=phase end
 for i=1,20 do S.run();elapsed=elapsed+0.3 end
 if phase=='installed' then
  local text=table.concat(logs,'\n')
  for _,key in ipairs({'perf.play.enter','perf.play.return','phase_peak=actors_update','phases_ms=','map_draw:','actor_max_ms=564','slow_actor=id=17/name=慢对象','callback_total_ms=0','prior_report_write_ms=7','actors=0','timings=inclusive_clock'})do assert(text:find(key,1,true),key..' missing: '..text)end
  assert(text:match('phase_peak_ms=56[34]'),text)
 end
 return table.concat(events,','),S.Hero['属性'].hp
end
local original,hp=execute('old',nil)
for _,phase in ipairs({false,true,'installed'})do
 local events,h=execute('new',phase);assert(events==original,'native frame call order changed');assert(h==hp)
end
-- Also verify absent optional timing hook follows the entire original frame.
local events,h=execute('new',nil);assert(events==original and h==hp)
print('FULL_NATIVE_FRAME_PHASE_PASS',mode,'zero-input; original frame call order; absent/nonfunction hooks; controlled actor update 564ms and map draw 300ms')
