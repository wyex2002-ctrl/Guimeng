local work,mode=assert(arg[1]),arg[2] or 'normal'
if mode=='hot' then require('jit.opt').start('hotloop=1','hotexit=1') end
local count=0
local function eq(a,b,msg)count=count+1;assert(a==b,(msg or 'check')..': '..tostring(a)..' ~= '..tostring(b)) end
local function load(name,env)local f=assert(loadfile(work..'/'..name..'.ljbc'));setfenv(f,env);return f end
local function protect(env)
 local export=load('builtin_exports',_G);eq(export(nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,env),env)
 local sys={script_setting=env,tbl_controls={}}
 for _,name in ipairs({'选择框4','选择框5','选择框6','启动图片','来世续缘','前尘忆梦','动画框4','登录按钮','登录按钮2','版本号标签'})do
  sys.tbl_controls[name]={tbl={['播放']=function()end}}
 end
 local install=load('sandbox_install',_G);debug.setupvalue(install,1,sys);install()
 eq(env.pcall,nil);eq(env.xpcall,nil)
 return sys
end
local labels={[0]='普通',[1]='简单',[2]='困难'}
local function difficulty(disk,which)
 local s={writes=0,reads=0,number=226}
 local U=load('ux_init',_G)();s.U=U
 U['粑粑麻麻']=function(v)if v then s.number=v end;return s.number end
 U['窗口相关']={['人物窗口']=function()end}
 U['背景音乐']={['播放']=function()end}
 U['游戏音效']={['窗口音效']={['播放']=function()end},['按键音效2']={['播放']=function()end}}
 local env={['Ux雌']=U,['Gly独']={['鼠标指针动画']=function()end},
 ['读配置项']=function(path,section,key)eq(path,'Dat/Options.ini');eq(section,'Main');s.reads=s.reads+1;return disk[key] end,
 ['写配置项']=function(path,section,key,value)eq(path,'Dat/Options.ini');eq(section,'Main');disk[key]=tostring(value);s.writes=s.writes+1 end}
 local sys=protect(env);s.env=env;s.sys=sys
 s.ui=load('ui_'..which,env);U['建行卡包']=s.ui
 s.init=load('init_'..which,env)
 function s.register(ver)
  local f=load('register_'..ver,env);local parent={};debug.setupvalue(f,1,parent)
  local config={['游戏难度']=9,unchanged=true};f(parent,config)
  eq(U['胚子考虑'](),config);eq(config.unchanged,true)
  return config
 end
 function s.assertvalue(expected)
  eq(U['__gm_difficulty_v175'],expected)
  for i=0,2 do local field=({[0]='选择框5',[1]='选择框4',[2]='选择框6'})[i];eq(sys.tbl_controls[field].tbl['选中'],i==expected)end
  assert(env['Gly独']['窗口标题']:find(labels[expected],1,true));count=count+1
 end
 return s
end
-- Reproduce the real later callback which used to overwrite saved values.
for _,value in ipairs({1,2})do
 local disk={Ver='来世续缘',GuimengDifficulty=tostring(value)}
 local s=difficulty(disk,'old');s.ui();s.assertvalue(value);s.init(1);s.assertvalue(0);eq(disk.GuimengDifficulty,'0','old callback overwrites saved difficulty')
end
for _,ver in ipairs({'pre','next'})do
 for value=0,2 do
  local disk={Ver=ver=='pre' and '前尘忆梦' or '来世续缘',GuimengDifficulty=tostring(value)}
  local s=difficulty(disk,'new');s.ui();s.assertvalue(value)
  eq(s.U['胚子考虑'],nil,'startup does not require unregistered config getter')
  s.init(1);s.assertvalue(value);eq(disk.GuimengDifficulty,tostring(value))
  local config=s.register(ver);eq(config['游戏难度'],value)
  for choice=0,2 do
   s.ui('来世续缘',labels[choice],'难度选择');s.assertvalue(choice);eq(disk.GuimengDifficulty,tostring(choice));eq(s.U['胚子考虑']()['游戏难度'],choice)
   local fresh=difficulty(disk,'new');fresh.ui();fresh.init(1);fresh.assertvalue(choice)
   eq(fresh.register(ver)['游戏难度'],choice)
  end
  local reads=s.reads;for i=1,10000 do eq(s.U['胚子考虑'](),config) end;eq(s.reads,reads,'getter does not read disk repeatedly')
  local ok=pcall(function()s.env['UNREGISTERED_v180']=true end);eq(ok,false,'original DB global protection remains')
 end
end
for _,bad in ipairs({'', 'garbage','3','-1','nan'})do
 local disk={GuimengDifficulty=bad};local s=difficulty(disk,'new');s.ui();s.init(1);s.assertvalue(0)
end
local missing=difficulty({},'new');missing.ui();missing.init(1);missing.assertvalue(0)
print('DIFFICULTY_PASS',mode,count)
-- Accuracy function executes under the original DB whitelist and protection.
local env={};local skills={};local buff;local adds,deletes=0,0
local U=load('ux_init',_G)();U['啾啾啵啵']=function()return {['技能']=skills}end
env['Ux雌']=U;env['Gly独']={['错误']=error};env['FXru胃啪']={
 ['增加状态']=function(name,time,attrs)eq(name,'增加命中');eq(time,0);buff=attrs['准确几率'];adds=adds+1 end,
 ['删除状态']=function(name)eq(name,'增加命中');buff=nil;deletes=deletes+1 end}
protect(env)
local owner={};local register=load('register_accuracy',env);debug.setupvalue(register,1,owner);register()
local update=owner['命中状态'];eq(type(update),'function')
local learn=load('learn_refresh',env);debug.setupvalue(learn,1,owner)
local login=load('login_refresh',env);debug.setupvalue(login,1,owner)
for lv=0,5 do
 skills={['攻杀剑术']={lv}};update();eq(buff,lv+1,'attack skill level+1')
 for i=1,100 do update();eq(buff,lv+1,'refresh does not accumulate')end
 learn();eq(buff,lv+1,'actual learn/upgrade refresh path')
 login();eq(buff,lv+1,'actual load refresh path')
 skills['基本剑术']={2};update();eq(buff,18+lv+1,'existing basic bonus retained')
 skills['精神力战法']={3};update();eq(buff,18+lv+1,'existing spirit priority retained')
end
skills={};update();eq(buff,nil,'removed skills do not leave stale accuracy')
for _,bad in ipairs({-1,'bad',0/0,math.huge,1.5})do skills={['攻杀剑术']={bad}};update();eq(buff,nil)end
skills={['基本剑术']={0}};update();eq(buff,10,'unrelated basic skill unchanged')
print('ACCURACY_PASS',mode,count)
print('PASS',mode,count)
