local ARG_U, ARG_G = ...
local gm_ok,gm_err=pcall(function()
local S,G,U,E = _G['Sys'],ARG_G,ARG_U,_G['Ae冻集']
if not (S and G and U and E and _G['Q_地图']) then error('游戏拾取接口未就绪') end
local function stopped(reason)
 if U['托管显示'] and U['托管显示']['屏幕提示'] then
  local c=_G['L常量'];U['托管显示']['屏幕提示']('Alt拾取暂不可用：'..reason,c and c['颜色_红'])
 end
end
local mask=E['遮罩信息']
local reason
if not E['屏幕焦点'] then reason='游戏窗口没有焦点'
elseif (E['逻辑暂停'] or 0)>0 or E['逻辑跳过'] or E['游戏暂停'] then reason='游戏正在暂停'
elseif mask and mask['启动'] and mask['触发'] then reason='遮罩正在阻挡操作'
elseif _G['Q_提示框'] and _G['Q_提示框']['可视'] then reason='提示框正在打开' end
if reason then stopped(reason);return end
local windows=S.get('item_box') or {}
for _,w in ipairs(windows) do
 if w['可视'] and type(w['是否有输入框焦点'])=='function' and w['是否有输入框焦点'](w) then stopped('输入框正在输入');return end
end
local hero,bag,control = S.get('hero'),S.get('item_arr'),S.get('控制对象')
local map=_G['Q_地图']['__gm_range_state'];local at=control and control['地图格子']
if not(hero and bag and at and map and map['地面物品组'] and map['到逻辑格子']) then error('角色或地图数据不可用') end
local protect={['青铜斧']=true,['魔法长袍_女']=true,['精灵骸骨']=true,['鹤嘴锄']=true}
local function unproxy(t)
 if type(t)=='table' and type(rawget(t,'__数据'))=='table' then return rawget(t,'__数据') end
 return t
end
local function same(a,b,depth)
 a=unproxy(a); b=unproxy(b)
 if a==b then return true end
 if type(a)~='table' or type(b)~='table' or depth>4 then return false end
 for k,v in pairs(a) do if not same(v,b[k],depth+1) then return false end end
 for k,v in pairs(b) do if a[k]==nil then return false end end
 return true
end
local function short(v)
 local t=type(v)
 if v==nil then return '无' end
 if t=='boolean' then return v and '是' or '否' end
 if t=='number' then return tostring(v) end
 if t=='string' then return '文本' end
 return t
end
local function safe_sell(it)
 if it['分类']~='装备' then return false,'分类:'..tostring(it['分类'] or '无') end
 if protect[it['名称']] then return false,'保护名单' end
 if it['禁止出售'] then return false,'禁止出售:'..short(it['禁止出售']) end
 if it['任务关联'] then return false,'任务关联:'..short(it['任务关联']) end
 if it['剧情关联'] then return false,'剧情关联:'..short(it['剧情关联']) end
 local extra=it['附加']
 if type(extra)~='table' then return false,'附加数据:'..type(extra) end
 if extra['条数']~=nil and extra['条数']~=0 then return false,'词条数:'..short(extra['条数']) end
 if extra['鉴定']~=nil then return false,'鉴定:'..short(extra['鉴定']) end
 if extra['强化装备']~=nil then return false,'强化:'..short(extra['强化装备']) end
 local ref=G['取道具信息_名称'](it['名称'])
 if not ref then return false,'无装备基准' end
 if type(ref['附加'])~='table' then return false,'基准附加:'..type(ref['附加']) end
 local base=ref['附加']
-- The original drop handler attaches a per-item target ID as text. It is not an affix.
if extra['商店目标']~=nil and type(extra['商店目标'])~='string' then return false,'商店目标异常:'..type(extra['商店目标']) end
local skip={['条数']=true,['等级']=true,['卡里钱']=true,['咯扣盘']=true,['商店目标']=true}
 for k,v in pairs(unproxy(extra)) do if not skip[k] and not same(v,base[k],0) then return false,'附加差异:'..tostring(k)..'('..short(v)..'/'..short(base[k])..')' end end
 for k,v in pairs(unproxy(base)) do if not skip[k] and not same(v,extra[k],0) then return false,'基准差异:'..tostring(k)..'('..short(extra[k])..'/'..short(v)..')' end end
 local bonus=U['独角兽下']()['极品数值']; if type(bonus)~='table' then return false,'极品表:'..type(bonus) end
 -- Ground equipment keeps its attributes in a protected nested table. The
-- game's name lookup flattens the base item's attributes into the result.
local attrs=it['属性']
if type(attrs)~='table' then return false,'缺少装备属性数据' end
local keys={};for _,k in ipairs({"最大破坏","最小破坏","最大自然","最小自然","最大灵魂","最小灵魂","最大防御","最小防御","最大魔防","最小魔防","攻火元素","攻冰元素","攻雷元素","攻风元素","攻神元素","攻暗元素","攻幻元素","防火元素","防冰元素","防雷元素","防风元素","防神元素","防暗元素","防幻元素","准确几率","敏捷几率","真伤几率","抵抗真伤","暴击几率","抵抗暴击","暴击伤害","伤害减免","击杀经验","击中回血","击中回蓝","击杀回血","击杀回蓝","红恢复量","蓝恢复量","自动回血","自动回蓝","金币掉落","装备几率","等级降低","武器腕力","穿戴肩力","抵抗几率","物品重量","物品腕力","身体舒适","最大伤害","最小伤害","死亡惩罚","百分伤害","普攻绿毒","元素躲避","背包负重","魔法躲避","毒物躲避","中毒恢复","幸运","经验倍率","装备倍率","极品倍率"}) do keys[k]=true end
for k in pairs(bonus) do keys[k]=true end
for k in pairs(unproxy(attrs)) do keys[k]=true end
local known=0
for k in pairs(keys) do
 local value,baseline=attrs[k],ref[k]
 if value~=nil and baseline~=nil then known=known+1 end
 if not same(value,baseline,0) then return false,'属性差异:'..tostring(k)..'('..short(value)..'/'..short(baseline)..')' end
end
if known==0 then return false,'装备属性数据不完整' end
 if type(it['价格'])~='number' or it['价格']<0 then return false,'价格:'..short(it['价格']) end
 return true,'白板'
end
local function sell(o,it)
 local f=o['拾取']; if type(f)~='function' then return false,'缺少拾取方法' end
 local cb=o['Hero'] and o['Hero']['回调脚本']; cb=cb and cb['拾取']
 if not cb then return false,'缺少拾取回调' end
 if not o['格子'] then return false,'缺少地面格子' end
 if not U['窗口相关'] or type(U['窗口相关']['界面切换'])~='function' then return false,'缺少金币接口' end
 local fields={'名称','显示名','生命值','生命值_百分比','法力值','法力值_百分比','物理伤害','魔法伤害','物理防御','魔法防御','攻击速度','躲避','命中','移动速度','暴击','分类','子类','价格','需要等级','性别要求','职业要求','道具说明','附加','颜色值','格子底图','格子动画','禁止出售','禁止丢弃'}
 local m={};for _,k in ipairs(fields) do m[k]=it[k] end
 m['数量']=o['数量']; m['可叠加']=it['叠加']==1
 local a,b=S.run('fun',cb,{1,o['格子'].x,o['格子'].y,m})
 if a and b then return false,'拾取回调拒绝' end
 local pay=math.ceil(it['价格']/2)*(o['数量'] or 1)
 U['窗口相关']['界面切换'](pay)
 o['已经消失']=true
 return true,'出售执行+'..tostring(pay)..'金币'
end
local function free(it)
 return (G['取包裹空位']('不限制') or 0)+(G['取包裹空位'](it['子类']) or 0)
end
local function capacity(it,n)
 local empty=free(it)
 if it['分类']=='特殊' then return n end
 if it['叠加']==0 then return math.min(n,empty,1) end
 local max=it['附加'] and it['附加']['叠加上限']
 if type(max)~='number' or max<=0 then return 0 end
 local best=0
 for _,slot in ipairs(hero['背包格子'] or {}) do
  if slot[3] then local box=bag[slot[1]];local old=box and box['道具']
   if old and old['名称']==it['名称'] then best=math.max(best,math.max(0,max-(old['数量'] or 0))) end
  end
 end
 if empty>0 then best=math.max(best,max) end
 return math.min(n,best)
end
local incomplete=false
for dy=-5,5 do for dx=-5,5 do
 local x,y=at.x+dx,at.y+dy
 if x>=0 and y>=0 and x<(map['地图格子列数'] or 0) and y<(map['地图格子行数'] or 0) then
  local bucket=map['地面物品组'][map['到逻辑格子'](x,y)]
  if bucket then
   local items={};for _,o in ipairs(bucket) do items[#items+1]=o end
   for _,o in ipairs(items) do
    local it=o['物品'];local n=o['数量'] or 1
    if not o['del__'] and not o['已经消失'] and it then
     local sale_ok=hero.__gm_pickup_sell_v242~=false and safe_sell(it)
     if sale_ok then
      local sold=sell(o,it)
      if not sold then incomplete=true end
     else
      local take=capacity(it,n)
      if take>0 then
       local partial=take<n;local orig=it
       if partial then
        if not table.copy then take=0 else
         local ok,clone=pcall(table.copy,it,true)
         if ok and clone and clone~=it then o['物品']=clone;o['数量']=take else take=0 end
        end
       end
       if take>0 then
        _G['__gm_range_pickup_guard']=true
        local ok,res=pcall(o['拾取'],o,1)
        _G['__gm_range_pickup_guard']=nil
        if partial then
         o['物品']=orig
         if ok and res then
          o['数量']=n-take;o['已经消失']=false
          local label=o['名称标签'];local title=(o['数量']>1) and string.format('%s(%d)',orig['显示名'],o['数量']) or orig['显示名']
          o['显示内容']=title
          if label and label['置标题'] and title then pcall(label['置标题'],title,1,orig['颜色值'],E['地面道具描边'],-16777216,o['显示宽度'],o['显示高度']) end
          items[#items+1]=o
         else o['数量']=n;incomplete=true end
        elseif not ok or not res then incomplete=true end
       else incomplete=true end
      else incomplete=true end
     end
    end
   end
  end
 end
end end
if incomplete and U['托管显示'] and U['托管显示']['屏幕提示'] then
 local c=_G['L常量'];U['托管显示']['屏幕提示']('背包空间不足或部分物品无法处理，剩余物品留在地面',c and c['颜色_红'])
end

end)
_G['__gm_range_pickup_guard']=nil
if not gm_ok then
 local u=ARG_U; local c=_G['L常量']
 if u and u['托管显示'] and u['托管显示']['屏幕提示'] then pcall(u['托管显示']['屏幕提示'],'范围拾取失败：'..tostring(gm_err),c and c['颜色_红']) end
end
