do
 -- Real full constructor. Only engine/graphics/map and window primitives are
 -- finite. Original public Sys wrapper remains in the path.
 local label
 local GE=setmetatable({table=T,Ae冻集={默认文字_间距=0,默认文字_行距=0,地面道具描边=false},
  Q__={创建动画=function()return{置中心点=noop}end},Q_公用图片库={地面物品闪烁序列图={}},
  Q_地图={逻辑格子到坐标=function(x,y)return x*10,y*10 end,坐标到逻辑格子=function(x,y)return x/10,y/10 end,
   取地图信息_总=function()return{宽度=1000,高度=1000}end,置格子信息=noop},
  Q_文字={取宽度=function(t)return #t*6 end,取高度=function()return 12 end},
  ARGB=function(a,r,g,b)return a*16777216+r*65536+g*256+b end,
  引擎={取随机整数=function(_,lo,hi)return lo end,取随机小数=function(_,lo,hi)return lo end,取运行时间=function()return 0 end}}, {__index=N})
 GE.Sys=load('public_sys',N)({get=function(key)
  if key=='hero'then return h elseif key=='win_tex'then return function()return{置标题=function(...)label={...}end}end end
  error('unexpected native constructor get '..tostring(key))
 end})
 local old,new=load('ground_old',GE),load('ground_new',GE)
 local templates=assert(loadfile(work..'/ground_templates.lua'))()
 local function run(fn,item,qty,outline)
  GE.Ae冻集.地面道具描边=outline;label=nil;local object={};fn(object,item,5,7,qty,0);assert(label);return object,label
 end
 local med,gold=0,0
 for _,item in pairs(templates)do
  local before=item.颜色值
  if item.kind=='medicine'then med=med+1 else gold=gold+1 end
  for _,qty in ipairs({1,9})do for _,outline in ipairs({false,true})do
   local a,x=run(old,item,qty,outline);local b,y=run(new,item,qty,outline)
   eq(y[3],item.kind=='medicine'and -1 or -6240,'ground-only tint')
   for k=1,7 do if k~=3 then eq(y[k],x[k],'ground title/outline/size unchanged')end end
   eq(item.颜色值,before,'item/template tint is never overwritten');eq(b.物品,item);eq(b.数量,a.数量);eq(b.显示内容,a.显示内容)
  end end
 end
 eq(med,22);eq(gold,5)
 for _,item in ipairs({
  {名称='祝福油',显示名='祝福油',分类='道具',子类='消耗品',颜色值=-65536},
  {名称='灵魂神水_小',显示名='灵魂神水',分类='道具',子类='消耗品',颜色值=-26368},
  {名称='疗伤药',显示名='疗伤药',分类='道具',子类='消耗品',颜色值=-5592406},
  {名称='金币卷',显示名='金币卷',分类='特殊',子类='特殊',颜色值=-65536},
  {名称='魔法药_装备',显示名='特殊装备',分类='装备',子类='武器',颜色值=-26368,附加={条数=7}},
  {名称='金创药材',显示名='药材',分类='道具',子类='消耗品',颜色值=-26368},
 })do
  for _,outline in ipairs({false,true})do
   local _,x=run(old,item,1,outline);local _,y=run(new,item,1,outline)
   for k=1,7 do eq(y[k],x[k],'non-target name/rarity remains native')end
  end
 end
 -- R15 native rarity is live after our call. All existing qualities and both
 -- outline modes must retain the exact original tint/outline selection.
 for tier=0,7 do for _,outline in ipairs({false,true})do
  local item={名称='测试装备',显示名='测试装备',分类='装备',子类='武器',颜色值=-26368,附加={条数=tier}}
  local _,x=run(old,item,1,outline);local _,y=run(new,item,1,outline)
  for k=1,7 do eq(y[k],x[k],'live rarity register survived new helper')end
 end end
 local rows={};for _,item in pairs(templates)do rows[#rows+1]=item end
 for i=1,200 do local item=rows[i%#rows+1];local _,label=run(new,item,i%5+1,i%2==0);eq(label[3],item.kind=='medicine'and -1 or -6240)end
 print('GROUND_V252_PASS',mode,med,'medicine variants',gold,'coin variants')
end
