do
 local function near(a,b,why)checks=checks+1;assert(math.abs(a-b)<1e-9,(why or'near')..': '..tostring(a)..' ~= '..tostring(b))end
 local rules=assert(loadfile(work..'/rules.lua'))()
 local expected={0,.12702947845804988,.16010204081632654,.20040816326530614,.24993197278911564,.3122448979591837,.39448979591836736,.5133333333333333,.7187755102040816,1}
 for x=0,9 do near(rules.equipment({luck=x}),expected[x+1],'B3 exact probability '..x)end
 for _,bad in ipairs({-10,-1,.5,10,100,1e9,math.huge,-math.huge,0/0,'bad','3'})do
  local n=tonumber(bad);local want
  if not n or n~=n or n==math.huge or n==-math.huge then want=0 else want=b3(n)end
  near(rules.equipment({luck=bad}),want,'safe formula input')
 end
 -- Exact recurrence for a birth/death/stay chain, not a Monte Carlo estimate.
 local delta,total=0,0
 for x=0,6 do
  local success,loss,same=rules.enhancement({luck=x})
  near(success,oil_weights[x+1][1]);near(loss,oil_weights[x+1][2]);near(same,oil_weights[x+1][3]);near(success+loss+same,1)
  delta=(1+loss*delta)/success;total=total+delta
 end
 near(total,10377016/10395,'Markov expectation 998.2699374699374 oils; no guarantee')
 -- Native use / consumption at every tier threshold, one roll from PRE-use luck.
 for level=1,6 do
  local a,b=rules.enhancement({luck=level})
  for _,case in ipairs({{0,level+1},{a-1e-10,level+1},{a,level-1},{a+b-1e-10,level-1},{a+b,level},{.999999999,level}})do
   bag[14].道具=mount(level);refresh();local before=float_calls;local ok,qty=apply(case[1])
   eq(ok,true);eq(qty,2);eq(getter(14).幸运,case[2]);eq(float_calls,before+1,'exactly one enhancement roll')
  end
 end
 bag[14].道具=mount(0);refresh();local before=float_calls;local ok,qty=apply(.999);eq(ok,true);eq(qty,2);eq(getter(14).幸运,1);eq(float_calls,before,'zero oil tier is certain, no extra roll')
 bag[14].道具=mount(7);refresh();before=float_calls;ok,qty=apply(0);eq(ok,false);eq(qty,3);eq(float_calls,before,'cap cannot consume or roll')
 -- Read the ACTUAL native skill-tier rows; never borrow another active skill.
 local skill_rules=load('skill_rules',E)()
 local fire=skill_rules.烈火剑法;eq(type(fire),'table')
 local trained=fire[6];eq(type(trained),'table');eq(trained.幸运属性,25,'original level-5 fire luck')
 h.属性.属性集.幸运=7
 local chance=b3(7)+trained.幸运属性/100
 for _,v in ipairs({chance-1e-10,chance})do float=v;local a,b=load('hero_luck',E)(10,20,trained,{行会选中={}});eq(a,v<chance and 20 or 15);eq(b,v<chance and 4 or 3)end
 local combined=chance+.11
 for _,v in ipairs({combined-1e-10,combined})do
  float=v;local n=float_calls;local a=load('hero_luck',E)(10,20,trained,{行会选中={幸运加持=true}})
  eq(a,v<combined and 20 or 15);eq(float_calls,n+1,'single combined skill + status + B3 roll')
 end
 -- Only current equipment totals count, including values >7 from OTHER gear.
 for _,value in ipairs({8,9,10,100,-3,0/0,math.huge,-math.huge})do
  h.属性.属性集.幸运=value
  local p=(value~=value or value==math.huge or value==-math.huge)and 0 or b3(value)
  float=.70;eq(E.__gm_luck_attack_v244(10,20,{},fx),.70<p and 20 or 15)
 end
 -- Real original gear aggregation, not a second mount contribution.
 local kept_mount,kept_ring=bag[14].道具,bag[15].道具
 bag[14].道具=mount(7);bag[15].道具=protected({子类='戒指',属性=attrs(1)});refresh()
 eq(fx.属性.幸运,8);float=.71;eq(E.__gm_luck_attack_v244(10,20,{},fx),20)
 bag[15].道具=protected({子类='戒指',属性=attrs(2)});refresh();eq(fx.属性.幸运,9)
 float=.999999;eq(E.__gm_luck_attack_v244(10,20,{},fx),20);eq(getter(14).幸运,7,'no mount +8 or +9 opened')
 local ok,qty=apply(0);eq(ok,false);eq(qty,3,'other equipment luck cannot bypass mount +7 cap')
 bag[14].道具=kept_mount;bag[15].道具=kept_ring;refresh()
 -- Count forced maxima with a finite midpoint ordinary roll (never max), so
 -- ordinary lucky top rolls cannot inflate this deterministic trigger count.
 for _,value in ipairs({0,1,3,5,6,7})do
  h.属性.属性集.幸运=value;local hits=0
  for i=1,200 do float=(i-.5)/200;if E.__gm_luck_attack_v244(10,20,{},fx)==20 then hits=hits+1 end end
  eq(hits,math.floor(b3(value)*200+.5),'B3-only deterministic trigger bins '..value)
 end
 -- Hero and companion formulas remain separate, with live summon ownership.
 h.属性.属性集.幸运=7;merc.属性.属性集.幸运=7;float=.4
 eq(E.__gm_luck_attack_v244(10,20,{},fx),20);eq(E.__gm_luck_attack_v244(10,20,{},actors[71]),20)
 eq(E.__gm_luck_attack_v244(10,20,{},merc_public),15);eq(E.__gm_luck_attack_v244(10,20,{},actors[43]),15)
 local a,b=E.__gm_luck_defense_v244(actors[71],false);eq(a,8);eq(b,9)
 local a,b=E.__gm_luck_defense_v244(actors[43],false);eq(a,5);eq(b,6)
 h.属性.属性集.幸运=0;eq(E.__gm_luck_attack_v244(10,20,{},actors[71]),15,'existing summon immediately loses equipment effect')
 h.属性.属性集.幸运=7;eq(E.__gm_luck_attack_v244(10,20,{},actors[71]),20,'existing summon immediately gains B3')
 float=.55;local a,b=E.__gm_luck_defense_v244(actors[71],false);eq(a,5);eq(b,6,'attack success does not force defense success')
 -- Base luck vs blessing increment is displayed separately, no template edits.
 eq(E.__gm_luck_line_v244({子类='坐骑',幸运=5},{幸运=2}):find('幸运：5（+3）',1,true)~=nil,true)
 eq(E.__gm_luck_line_v244({子类='坐骑',幸运=0},{幸运=0}),'')
 -- Leave later original inventory/shortcut cases in their original fixture state.
 bag[14].道具=mount(0);refresh();bag[410].道具=mount(7);merc:属性更新()
 print('B3_V249_PASS',mode,'expected_oils',total,'hero7_probability',b3(7),'equipment0_probability',b3(0))
end
