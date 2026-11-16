for _,name in ipairs({'莲月剑法','烈火剑法','翔空剑法','刺杀剑术'})do
 local old,new=visual_scene('old'),visual_scene('new')
 eq(old:cast(name),true);eq(new:cast(name),true);old:step(110);new:step(110)
 local a,b=effect_events(old),effect_events(new);eq(#a,#b)
 eq(#a>0,true,'real configured sword light')
 eq(#times(old,'damage'),#times(new,'damage'))
 for i,t in ipairs(times(old,'damage'))do near(t,times(new,'damage')[i],'damage time preserved')end
 eq(old.hero['属性'].mp,new.hero['属性'].mp,'cost unchanged')
 for i,e in ipairs(a)do
  local f=b[i];near(e.t,f.t,'light onset unchanged');eq(e.args.n,f.args.n)
  for j=1,e.args.n do if j~=13 and j~=8 then eq(e.args[j],f.args[j],'effect argument '..j)end end
  near(f.object['播放速度'],e.object['播放速度']*(name=='莲月剑法'and 1.25 or 1),'interval encodes 80 percent rate')
  local x,y=display_until_gone(old,e),display_until_gone(new,f)
  if name=='莲月剑法'then eq(y>x,true,'slower light lasts longer')else near(x,y,'other light unchanged')end
 end
end
print('LOTUS_V240_PASS',mode)
