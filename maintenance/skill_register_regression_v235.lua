-- Execute the actual damage callback directly across hot trace exits, retaining
-- the original result table and non-target outcomes. Damage/world effects are finite.
do
 local E={type=type,table=table,math=math}
 local function target(x,hp)return{属性={hp=hp or 100},地图格子={x=x,y=0}}end
 local calls={}
 local caster={地图格子={x=0,y=0},发生伤害=function(self,victim,skill,power)
  calls[#calls+1]=skill;return{true,power,0}
 end}
 local state={施法者=caster,技能信息={对象={名称='月魂灵波',类型=1}}}
 local f=load('damage_helper',E);debug.setupvalue(f,1,state);debug.setupvalue(f,2,nil)
 for i=1,200 do
  local names={'月魂灵波','雷电术','刺杀剑术','普通攻击'}
  local name=names[(i-1)%4+1];state.技能信息.对象.名称=name
  local victim=target(i%3==0 and 'invalid' or i%2+1)
  state.命中目标组={{victim,100},{target(2,0),100}};state.伤害进度={1}
  local before=#calls;local result=f()
  eq(type(result),'table','native damage result retained');eq(#result,2,'live/dead result slots')
  eq(#calls,before+1,'one live target damage request')
  if name=='刺杀剑术'and type(victim.地图格子.x)=='number'and victim.地图格子.x<=1 then
   eq(calls[#calls],'普通攻击','original adjacent thrust conversion')
  else eq(calls[#calls],name,'preserve non-adjacent/non-thrust skill')end
 end
 print('SKILL_REGISTERS_V235_PASS '..mode..' native damage callback: result table, live/dead targets, thrust/fallback, hot exits')
end

do
 local c=scene('new',{convert='攻杀剑术'});local h,e=c.hero,c.env
 local get=load('getter',e);debug.setupvalue(get,1,{Hero=h,游戏技能组=c.skills,屏幕事件组={c.target}});e.Sys.get=get
 local t=c.target;t.地图格子={x=2,y=0};t.地图坐标={x=2,y=0};t.可视=true;t.屏幕可视=true;t.属性.可视=true;t.属性.透明度=255
 e.Ae冻集.屏幕宽度=800;e.Ae冻集.屏幕高度=600
 local accepted=h:技能释放('普通攻击',true,t,nil,false)
 assert(accepted,'native selector conversion accepts')
 local state=upstate(c)
 eq(state.技能信息.对象.名称,'刺杀剑术','two-grid selected attack')
 eq(state.__gm_training_skill_v169,'攻杀剑术','captured training name survives original calls')
 print('SELECTOR_REGISTERS_V235_PASS '..mode)
end
