local function input_scene(version,opts)
 local s=scene(version,opts);local h,env=s.hero,s.env
 s.target['地图格子'].x=0;s.target['地图格子'].y=-1;s.target['地图坐标'].x=0;s.target['地图坐标'].y=-1
 h['当前状态']=3;eq(s:cast('刺杀剑术'),false)
 h['当前状态']=0;h['下次技能']=nil;h['攻击目标']=nil;h['远程目标']=nil
 for i=#s.events,1,-1 do table.remove(s.events,i)end
 env.setmetatable=setmetatable;env.rawget=rawget;env.rawset=rawset
 local f=load('hero_api',env);debug.setupvalue(f,2,{Hero=h,['屏幕事件组']={s.target}})
 local api=f()
 env['FXru胃啪']={['释放技能']=api['释放技能'],['取状态列表']=api['取状态列表'],['删除状态']=noop,['增加状态']=function(name)eq(name,'禁足')end}
 env['Ux雌']['啾啾啵啵']=function()return{['技能']={['刺杀剑术']={0}}}end
 env['L常量']['键_SHIFT']=16;env['L常量']['键_鼠标左']=1
 s.keys={[16]=true,[1]=true}
 env['引擎']['取按键事件']=function(a,b)local key=b or a;return s.keys[key]or false end
 env['引擎']['取按键按下']=function()return false end
 local register=load('shift_registration',env);debug.setupvalue(register,1,{})
 env['Ae冻']=env['Ux雌'];env['Ae冻']['窗口相关']=register()
 eq(type(env['Ae冻']['窗口相关']['刺杀剑术']),'function','real original callback registration')
 env['Ae冻集']['新时钟计次']=0;env['Ae冻集']['镜头ID']=h.id;env['Ae冻集']['遮罩信息']['触发']=true
 h['主角配置']['左键步距']=0;h['快捷事件组']={};env['Ae冻集']['快捷事件组']={}
 local owner={time_table={}}
 local factory=load('timer_factory',env);debug.setupvalue(factory,1,owner)
 local polls={}
 factory(100,function()polls[#polls+1]=s.now();if version=='previous'then env['Ae冻']['窗口相关']['刺杀剑术']()end end)
 local loop=load('timer_loop',env);debug.setupvalue(loop,1,owner)
 s.input=function()h['输入控制'](h)end
 s.timer=loop;s.polls=polls
 return s
end
for _,opts in ipairs({{dt=.01},{dt=1/60},{dt=1/15},{dt=.01,speed=25},{dt=.01,speed=5}})do
 local old,new=input_scene('previous',opts),input_scene('new',opts)
 old.input();new.input()
 for i=1,20000 do
  old:step();new:step();old.timer();new.timer();old.input();new.input()
  if #times(old,0)>=(opts.dt==.01 and not opts.speed and 200 or 5) and #times(new,0)>=(opts.dt==.01 and not opts.speed and 200 or 5)then break end
 end
 local a,b=times(old,0),times(new,0)
 eq(b[1],0,'first Shift request in the same input update');eq(a[1]>0,true,'old waits for native timer')
 print('INPUT',opts.dt,opts.speed or 10,'starts',a[1],b[1],a[2],b[2],a[3],b[3],'counts',#a,#b,'diff',a[2]-a[1],b[2]-b[1])
 for i=3,math.min(#a,#b)do near(a[i]-a[2],b[i]-b[2],'held Shift steady cadence '..i)end
end

-- Release, right-click, focus, modal/UI, pause and unlearned/disabled states.
for _,kind in ipairs({'release','right','focus','ui','pause','modal','story','camera','dead','unlearned','paralyzed','missing_callback'})do
 local s=input_scene('new');local h,env=s.hero,s.env
 if kind=='release'then s.keys[16]=false
 elseif kind=='right'then s.keys[2]=true
 elseif kind=='focus'then env['Ae冻集']['屏幕焦点']=false
 elseif kind=='ui'then env['Ae冻集']['UI焦点']=true
 elseif kind=='pause'then env['Ae冻集']['游戏暂停']=true
 elseif kind=='modal'then env['Q_提示框']['可视']=true
 elseif kind=='story'then h['剧情表']={true}
 elseif kind=='camera'then env['Ae冻集']['镜头ID']=99
 elseif kind=='dead'then h['属性'].hp=0
 elseif kind=='unlearned'then env['Ux雌']['啾啾啵啵']=function()return{['技能']={}}end
 elseif kind=='paralyzed'then env['FXru胃啪']['取状态列表']=function()return{['麻痹']={}}end
 elseif kind=='missing_callback'then env['Ae冻']['窗口相关']['刺杀剑术']=nil end
 s.input();eq(#times(s,0),0,kind..' cannot launch attack')
end
-- Releasing/repressing between polls never bypasses the prior attack's gate.
do
 local s=input_scene('new');s.input()
 for i=1,200 do s.keys[1]=i%2==0;s:step();s.timer();s.input()end
 local starts=times(s,0);eq(#starts>=2,true)
 for i=2,#starts do eq(starts[i]-starts[i-1]>=.89-1e-8,true,'repress does not bypass recovery')end
end
print('INPUT_PASS' ,mode,checks)
