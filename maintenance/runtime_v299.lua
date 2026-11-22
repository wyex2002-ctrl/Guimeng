-- Guimeng v1.299 runtime helper (compiled once via loadstring at module 14 init).
-- Scope: All new v1.299 features apply ONLY to 「来世续缘」.
-- 「前尘忆梦」 keeps original manual Alt pickup and untouched mount/shop/UI logic.
local S=...
local G_ROOT=_G
if type(S)~='table' then return end
if S.__gm_runtime_v299_installed then return end
S.__gm_runtime_v299_installed=true

 local BATCH_KEY='__gm_oil_batch_v263'
 local BATCH_MAX=50
 local MAX_ROLL=1-2^-53

 local function get_U()
  local ss=S.script_setting
  if type(ss)=='table' and type(ss.Ux雌)=='table' then return ss.Ux雌 end
  if type(G_ROOT.Ux雌)=='table' then return G_ROOT.Ux雌 end
  return nil
 end

 local function is_laishi()
  local U=get_U()
  return type(U)=='table' and U.版本选择=='来世续缘'
 end

 local function finite(v)
  local n=tonumber(v)
  if type(n)~='number' or n~=n or n==math.huge or n==-math.huge then return nil end
  return n
 end

 local function unproxy(t)
  if type(t)~='table' then return t end
  local inner=rawget(t,'__数据')
  if type(inner)=='table' then return inner end
  return t
 end

 local function deep_copy(t)
  if type(table)=='table' and type(table.copy)=='function' then
   return table.copy(t,true)
  end
  local function rec(v,depth)
   local u=unproxy(v)
   if type(u)~='table' or depth>8 then return u end
   local out={}
   for k,val in pairs(u) do out[k]=rec(val,depth+1) end
   return out
  end
  return rec(t,0)
 end

 local function protect_table(t)
  if type(S.数据保护)=='function' then
   return S.数据保护(t,true)
  end
  return t
 end

 local function random_unit()
  local eng=G_ROOT.引擎
  local v=eng and eng:取随机小数(0,1)
  local n=finite(v) or 0
  if n<0 then n=0 elseif n>MAX_ROLL then n=MAX_ROLL end
  return n
 end

 local function new_oil_batch()
  local eng=G_ROOT.引擎
  local raw_n=eng and eng:取随机整数(1,BATCH_MAX)
  local n=finite(raw_n)
  if not n or n%1~=0 or n<1 or n>BATCH_MAX then
   error('invalid oil batch length')
  end
  local values={}
  for i=1,n do
   values[i]=string.format('%.17g',random_unit())
  end
  return {version=1,length=n,next=1,values=values}
 end

 local function validate_oil_batch(batch)
  if type(batch)~='table' then return false,'not_table' end
  local raw=unproxy(batch)
  if type(raw)~='table' then return false,'unproxy_fail' end
  if rawget(raw,'version')~=1 then return false,'bad_version' end
  local n=finite(rawget(raw,'length'))
  local nxt=finite(rawget(raw,'next'))
  if not n or n%1~=0 or n<1 or n>BATCH_MAX then return false,'bad_length' end
  -- Exhausted batch (next == length + 1) is valid and must be preserved as-is.
  if not nxt or nxt%1~=0 or nxt<1 or nxt>n+1 then return false,'bad_next' end
  local vals=unproxy(rawget(raw,'values'))
  if type(vals)~='table' then return false,'values_not_table' end
  for j=1,n do
   local v=finite(rawget(vals,j))
   if not v or v<0 or v>=1 then return false,'bad_value_'..tostring(j) end
  end
  return true,nil
 end

 local function record_anomaly(reason,detail,item)
  local log=S.__gm_mount_batch_anomalies_v299
  if type(log)~='table' then log={}; S.__gm_mount_batch_anomalies_v299=log end
  local name=type(item)=='table' and item.名称 or ''
  local entry={reason=reason,detail=detail,name=name}
  if #log<100 then log[#log+1]=entry end
  if type(S.__gm_diag_checkpoint_v159)=='function' then
   pcall(S.__gm_diag_checkpoint_v159,'mount.batch.anomaly',tostring(reason)..':'..tostring(detail)..':'..tostring(name))
  end
 end

 local function is_shared_template(item)
  local templates=S.游戏道具组
  if type(templates)~='table' then return false end
  local name=item.名称
  if name==nil then return false end
  local tmpl=templates[name]
  if type(tmpl)~='table' then return false end
  if item==tmpl then return true end
  local ri,rt=unproxy(item),unproxy(tmpl)
  return type(ri)=='table' and ri==rt
 end

 local function ensure_mount_batch(item,source)
  if not is_laishi() then return 'skip_story' end
  if type(item)~='table' then return 'skip_type' end
  if item.子类~='坐骑' then return 'skip_not_mount' end
  if is_shared_template(item) then return 'skip_template' end
  local extra=item.附加
  if extra~=nil and type(extra)~='table' then
   record_anomaly(source or 'unknown','extra_not_table',item)
   return 'anomaly_extra'
  end
  local raw_extra=type(extra)=='table' and unproxy(extra) or nil
  local existing=type(raw_extra)=='table' and rawget(raw_extra,BATCH_KEY) or nil
  if existing~=nil then
   local ok,why=validate_oil_batch(existing)
   if ok then return 'keep_valid' end
   record_anomaly(source or 'unknown',why or 'invalid_batch',item)
   return 'anomaly_preserved'
  end
  local ok_gen,batch=pcall(new_oil_batch)
  if not ok_gen or type(batch)~='table' then
   record_anomaly(source or 'unknown','rng_failed',item)
   return 'rng_error'
  end
  local next_extra=type(extra)=='table' and deep_copy(extra) or {}
  next_extra[BATCH_KEY]=batch
  item.附加=protect_table(next_extra)
  return 'initialized'
 end

 S.__gm_ensure_mount_batch_v299=function(item,source)
  local ok,res=pcall(ensure_mount_batch,item,source)
  if ok then return res end
  record_anomaly(source or 'unknown','exception:'..tostring(res),item)
  return 'error'
 end

 S.__gm_on_slot_item_v299=function(slot_id,source)
  if S.__gm_loading_save_v299 then return 'deferred_load' end
  if not is_laishi() then return 'skip_story' end
  local bag=S.包裹物品组
  if type(bag)~='table' or slot_id==nil then return 'skip_slot' end
  local cell=bag[slot_id]
  if type(cell)~='table' then return 'skip_cell' end
  return S.__gm_ensure_mount_batch_v299(cell.道具,source)
 end

 local function migrate_mounts_once()
  if not is_laishi() then return {skipped=true} end
  local seen={}
  local stats={scanned=0,initialized=0,kept=0,anomalies=0,errors=0}
  local function visit_item(it,src)
   if type(it)~='table' then return end
   local key=unproxy(it)
   if type(key)~='table' or seen[key] then return end
   seen[key]=true
   if it.子类~='坐骑' then return end
   stats.scanned=stats.scanned+1
   local res=S.__gm_ensure_mount_batch_v299(it,src)
   if res=='initialized' then stats.initialized=stats.initialized+1
   elseif res=='keep_valid' then stats.kept=stats.kept+1
   elseif res=='anomaly_preserved' or res=='anomaly_extra' then stats.anomalies=stats.anomalies+1
   elseif res=='error' or res=='rng_error' then stats.errors=stats.errors+1 end
  end
  -- 1. Primary unified container: 包裹物品组 (hero equip 1..20, quickbar 21..26,
  -- hero bags 27..126, warehouse 127..226, guild warehouse 227..326,
  -- extra slots 327..332, merc bag 333..396, merc equip 397..417 including unsummoned).
  local bag=S.包裹物品组
  if type(bag)=='table' then
   for _,cell in pairs(bag) do
    if type(cell)=='table' and type(cell.道具)=='table' then
     visit_item(cell.道具,'load_bag')
    end
   end
  end
  -- 2. Window slot controls (catch any slot control holding an item directly).
  local wins=S.界面_窗口_数组
  if type(wins)=='table' then
   for i=1,#wins do
    local w=wins[i]
    local ctrls=type(w)=='table' and w.控件组
    if type(ctrls)=='table' then
     for j=1,#ctrls do
      local c=ctrls[j]
      local obj=type(c)=='table' and c.对象
      if type(obj)=='table' and type(obj.道具)=='table' then
       visit_item(obj.道具,'load_window')
      end
     end
    end
   end
  end
  -- 3. Additional player/merc slot references if populated.
  local U=get_U()
  if type(U)=='table' then
   if type(U.佣兵背包)=='table' then
    for _,cell in pairs(U.佣兵背包) do
     if type(cell)=='table' and type(cell.道具)=='table' then
      visit_item(cell.道具,'load_merc_bag')
     end
    end
   end
   if type(U.胚子考虑)=='function' then
    local ok_p,cfg=pcall(U.胚子考虑)
    if ok_p and type(cfg)=='table' and type(cfg.主角格子)=='table' then
     for _,cell in pairs(cfg.主角格子) do
      if type(cell)=='table' and type(cell.道具)=='table' then
       visit_item(cell.道具,'load_hero_slots')
      end
     end
    end
   end
  end
  -- 4. Hero equip table and mouse-held item if any.
  local hero=S.Hero
  if type(hero)=='table' and type(hero.装备)=='table' then
   for _,it in pairs(hero.装备) do
    if type(it)=='table' then visit_item(it,'load_hero_equip') end
   end
  end
  local mouse=G_ROOT.Q_鼠标
  if type(mouse)=='table' and type(mouse.道具)=='table' then
   visit_item(mouse.道具,'load_mouse')
  end
  S.__gm_mount_migrate_last_v299=stats
  return stats
 end

 S.__gm_migrate_mounts_v299=migrate_mounts_once

 S.__gm_load_state_v299=function(loading,run_migrate)
  S.__gm_loading_save_v299=loading==true
  if not loading and run_migrate then
   pcall(migrate_mounts_once)
  end
 end

 -- ========================================================================
 -- Auto-pickup toggle button (Window 539, left of 【仓库】) & 1s pre-check
 -- ========================================================================
 G_ROOT.__gm_auto_pickup_on_v299=false
 local auto_state={
  active=false,
  last_ms=nil,
  last_map=nil,
  full_notified=false,
  btn_installed=false,
 }
 local pickup_stats={
  prechecks=0,
  precheck_hits=0,
  precheck_empty=0,
  precheck_items_inspected=0,
  full_runs=0,
  manual_runs=0,
  suppressed_full_msgs=0,
 }
 S.__gm_autopickup_stats_v299=pickup_stats
 S.__gm_autopickup_state_v299=auto_state

 local function now_ms()
  local eng=G_ROOT.引擎
  if not (eng and type(eng.取运行时间)=='function') then return nil end
  local s=tonumber(eng:取运行时间())
  if type(s)~='number' or s~=s then return nil end
  return s*1000
 end

 local function set_auto_pickup(enabled,silent)
  local on=enabled==true
  G_ROOT.__gm_auto_pickup_on_v299=on
  auto_state.full_notified=false
  auto_state.last_ms=nil
  if not silent then
   local U=get_U()
   if U and U.托管显示 and U.托管显示.屏幕提示 then
    local c=G_ROOT.L常量
    local col=on and (c and c.颜色_黄) or -4210753
    U.托管显示.屏幕提示(on and '自动拾取已开启' or '自动拾取已关闭',col)
   end
  end
 end
 S.__gm_set_auto_pickup_v299=set_auto_pickup

 local function install_autopickup_btn()
  if not is_laishi() then return false end
  if type(S.取窗口对象)~='function' then return false end
  local win=S.取窗口对象(539)
  if type(win)~='table' or type(win.控件组)~='table' then return false end
  local name='自动拾取按钮_v299'
  for i=1,#win.控件组 do
   local c=win.控件组[i]
   if c and c.名称==name then
    auto_state.btn_installed=true
    return true
   end
  end
  if type(G_ROOT.__Res)~='function' or type(G_ROOT.Q__)~='table' then return false end
  local font=G_ROOT.__Res(2,'400132927.img')
  local image=G_ROOT.__Res(1,'-1657209002.img',0)
  if not (font and image) then return false end
  local text='自动拾取'
  local tw,th=font.取宽度(text,0),font.取高度(text,0)
  local height=math.floor(17*1.3+0.5) -- 22, identical to 【仓库】
  local wh_w=math.floor(math.floor(math.max(42,math.ceil(font.取宽度('仓库'))+16)*1.3+0.5)*0.8+0.5)
  local wh_x=235-5-wh_w-6 -- 180
  local gap=4
  local width=math.min(68,math.max(58,math.ceil(tw)+18))
  local bx=wh_x-gap-width
  if bx<108 then
   bx=108
   width=wh_x-gap-bx
  end
  local by=15+(26-height)/2+3 -- 20, aligned with 【仓库】
  local function on_toggle_click()
   if not is_laishi() then return end
   local U=get_U()
   if U and U.游戏音效 and U.游戏音效.按键音效1 and U.游戏音效.按键音效1.播放 then
    U.游戏音效.按键音效1.播放()
   end
   set_auto_pickup(G_ROOT.__gm_auto_pickup_on_v299~=true,false)
  end
  local function factory()
   local self={id=name}
   return {
    getself=function() return self end,
    Main=function() return on_toggle_click() end,
    鼠标焦点=function() end,
   }
  end
  win:增加控件(10,name,bx,by,0,width,height,'',image,
   '[控件]\n按下效果=0\n按钮类型=1\n像素检测=假\n透明色=0\n',{factory})
  local control=win.控件组[#win.控件组]
  local object=control and control.对象
  if type(object)~='table' then return false end
  local original=object.显示
  local destroy=object.销毁
  local left=G_ROOT.Q__.创建精灵(image,0,0,6,17)
  local middle=G_ROOT.Q__.创建精灵(image,6,0,1,17)
  local right=G_ROOT.Q__.创建精灵(image,28,0,6,17)
  local dot_bg=G_ROOT.Q__.创建精灵(0,0,0,1,1)
  local dot_fg=G_ROOT.Q__.创建精灵(0,0,0,1,1)
  local layout=font.解析(text,0,0)
  object.销毁=function()
   left.销毁(); middle.销毁(); right.销毁()
   dot_bg.销毁(); dot_fg.销毁()
   if type(destroy)=='function' then destroy() end
  end
  object.显示=function(x,y,sx,sy,angle,color,alpha)
   if not is_laishi() then return end
   if type(original)=='function' then original(x,y,sx,sy,angle,0,0) end
   sx=sx or 1; sy=sy or 1
   local on=G_ROOT.__gm_auto_pickup_on_v299==true
   local hovered=type(object.是否有焦点)=='function' and object.是否有焦点()
   local eng=G_ROOT.引擎
   local L=G_ROOT.L常量
   local pressed=hovered and eng and L and eng:取按键事件(L.键_鼠标左)
   if pressed then y=y+sy end
   local shade
   if on then
    shade=(hovered and not pressed) and -8658802 or -9910150 -- emerald green ON
   else
    shade=(hovered and not pressed) and -4671304 or -5723992 -- neutral stone OFF
   end
   local a_byte=math.floor(255*(alpha or 1))
   local skin=type(G_ROOT.SETA)=='function' and G_ROOT.SETA(shade,a_byte) or shade
   left.置颜色(skin); middle.置颜色(skin); right.置颜色(skin)
   for row=1,3 do
    local sourceY,sourceH,dy,targetH=0,3,0,3
    if row==2 then sourceY=3; sourceH=11; dy=3; targetH=height-6 end
    if row==3 then sourceY=14; sourceH=3; dy=height-3; targetH=3 end
    left.置显示区域(0,sourceY,6,sourceH)
    middle.置显示区域(6,sourceY,1,sourceH)
    right.置显示区域(28,sourceY,6,sourceH)
    left.显示_高级(x,y+dy*sy,angle or 0,sx,sy*targetH/sourceH)
    middle.显示_高级(x+6*sx,y+dy*sy,angle or 0,(width-12)*sx,sy*targetH/sourceH)
    right.显示_高级(x+(width-6)*sx,y+dy*sy,angle or 0,sx,sy*targetH/sourceH)
   end
   -- Status indicator dot on the left inside the button
   local dot_x=x+5*sx
   local dot_y=y+(height-6)*sy/2
   dot_bg.置颜色(type(G_ROOT.SETA)=='function' and G_ROOT.SETA(-14671840,a_byte) or -14671840)
   dot_bg.显示_高级(dot_x,dot_y,angle or 0,6*sx,6*sy)
   local dot_col=on and -13369549 or -8355712 -- bright green ON vs dim grey OFF
   dot_fg.置颜色(type(G_ROOT.SETA)=='function' and G_ROOT.SETA(dot_col,a_byte) or dot_col)
   dot_fg.显示_高级(dot_x+sx,dot_y+sy,angle or 0,4*sx,4*sy)
   local text_col=on and (color or -1) or -4210753
   local text_x=x+12*sx+(width-14-tw)*sx/2
   local text_y=y+(height-th)*sy/2-sy
   font.显示配置(layout,text_x,text_y,text_col,-15724528)
  end
  auto_state.btn_installed=true
  return true
 end
 S.__gm_install_autopickup_btn_v299=install_autopickup_btn

 -- Constant tables hoisted once (zero per-call allocation)
 local PROTECT_ITEMS={['青铜斧']=true,['魔法长袍_女']=true,['精灵骸骨']=true,['鹤嘴锄']=true}
 local SKIP_EXTRA={['条数']=true,['等级']=true,['卡里钱']=true,['咯扣盘']=true,['商店目标']=true}
 local KNOWN_ATTR_KEYS={
  '最大破坏','最小破坏','最大自然','最小自然','最大灵魂','最小灵魂',
  '最大防御','最小防御','最大魔防','最小魔防',
  '攻火元素','攻冰元素','攻雷元素','攻风元素','攻神元素','攻暗元素','攻幻元素',
  '防火元素','防冰元素','防雷元素','防风元素','防神元素','防暗元素','防幻元素',
  '准确几率','敏捷几率','真伤几率','抵抗真伤','暴击几率','抵抗暴击','暴击伤害',
  '伤害减免','击杀经验','击中回血','击中回蓝','击杀回血','击杀回蓝',
  '红恢复量','蓝恢复量','自动回血','自动回蓝','金币掉落','装备几率','等级降低',
  '武器腕力','穿戴肩力','抵抗几率','物品重量','物品腕力','身体舒适',
  '最大伤害','最小伤害','死亡惩罚','百分伤害','普攻绿毒','元素躲避',
  '背包负重','魔法躲避','毒物躲避','中毒恢复','幸运','经验倍率','装备倍率','极品倍率'
 }

 local function same_val(a,b,depth)
  a=unproxy(a); b=unproxy(b)
  if a==b then return true end
  if type(a)~='table' or type(b)~='table' or depth>4 then return false end
  for k,v in pairs(a) do if not same_val(v,b[k],depth+1) then return false end end
  for k,v in pairs(b) do if a[k]==nil then return false end end
  return true
 end

 local function short_val(v)
  local t=type(v)
  if v==nil then return '无' end
  if t=='boolean' then return v and '是' or '否' end
  if t=='number' then return tostring(v) end
  if t=='string' then return '文本' end
  return t
 end

 local function run_range_pickup(ARG_U,ARG_G,is_auto)
  if auto_state.active or G_ROOT['__gm_range_pickup_guard'] then return false end
  auto_state.active=true
  local saleCount, saleGold = 0, 0
  local picked = 0
  if is_auto then pickup_stats.full_runs=pickup_stats.full_runs+1
  else pickup_stats.manual_runs=pickup_stats.manual_runs+1 end
  local gm_ok,gm_err=pcall(function()
  local SYS,G,U,E = G_ROOT['Sys'],ARG_G,ARG_U,G_ROOT['Ae冻集']
  if not (SYS and G and U and E and G_ROOT['Q_地图']) then
   if is_auto then return end
   error('游戏拾取接口未就绪')
  end
  local function stopped(reason)
   if is_auto then return end
   if U['托管显示'] and U['托管显示']['屏幕提示'] then
    local c=G_ROOT['L常量'];U['托管显示']['屏幕提示']('Alt拾取暂不可用：'..reason,c and c['颜色_红'])
   end
  end
  local mask=E['遮罩信息']
  local reason
  if not E['屏幕焦点'] then reason='游戏窗口没有焦点'
  elseif (E['逻辑暂停'] or 0)>0 or E['逻辑跳过'] or E['游戏暂停'] then reason='游戏正在暂停'
  elseif mask and mask['启动'] and mask['触发'] then reason='遮罩正在阻挡操作'
  elseif G_ROOT['Q_提示框'] and G_ROOT['Q_提示框']['可视'] then reason='提示框正在打开' end
  if reason then stopped(reason);return end
  local windows=SYS.get('item_box') or {}
  for _,w in ipairs(windows) do
   if w['可视'] and type(w['是否有输入框焦点'])=='function' and w['是否有输入框焦点'](w) then stopped('输入框正在输入');return end
  end
  local hero,bag,control = SYS.get('hero'),SYS.get('item_arr'),SYS.get('控制对象')
  local map=G_ROOT['Q_地图']['__gm_range_state'];local at=control and control['地图格子']
  if not(hero and bag and at and map and map['地面物品组'] and map['到逻辑格子']) then
   if is_auto then return end
   error('角色或地图数据不可用')
  end
  if is_auto and (hero['del__'] or hero['已经死亡'] or control['del__'] or control['已经死亡']) then return end
  local function safe_sell(it)
   if it['分类']~='装备' then return false,'分类:'..tostring(it['分类'] or '无') end
   if PROTECT_ITEMS[it['名称']] then return false,'保护名单' end
   if it['禁止出售'] then return false,'禁止出售:'..short_val(it['禁止出售']) end
   if it['任务关联'] then return false,'任务关联:'..short_val(it['任务关联']) end
   if it['剧情关联'] then return false,'剧情关联:'..short_val(it['剧情关联']) end
   local extra=it['附加']
   if type(extra)~='table' then return false,'附加数据:'..type(extra) end
   if extra['条数']~=nil and extra['条数']~=0 then return false,'词条数:'..short_val(extra['条数']) end
   if extra['鉴定']~=nil then return false,'鉴定:'..short_val(extra['鉴定']) end
   if extra['强化装备']~=nil then return false,'强化装备:'..short_val(extra['强化装备']) end
   local ref=G['取道具信息_名称'](it['名称'])
   if not ref then return false,'无装备基准' end
   if type(ref['附加'])~='table' then return false,'基准附加:'..type(ref['附加']) end
   local base=ref['附加']
   if extra['商店目标']~=nil and type(extra['商店目标'])~='string' then return false,'商店目标异常:'..type(extra['商店目标']) end
   for k,v in pairs(unproxy(extra)) do if not SKIP_EXTRA[k] and not same_val(v,base[k],0) then return false,'附加差异:'..tostring(k)..'('..short_val(v)..'/'..short_val(base[k])..')' end end
   for k,v in pairs(unproxy(base)) do if not SKIP_EXTRA[k] and not same_val(v,extra[k],0) then return false,'基准差异:'..tostring(k)..'('..short_val(extra[k])..'/'..short_val(v)..')' end end
   local bonus=U['独角兽下']()['极品数值']; if type(bonus)~='table' then return false,'极品表:'..type(bonus) end
   local attrs=it['属性']
   if type(attrs)~='table' then return false,'缺少装备属性数据' end
   local keys={}
   for i=1,#KNOWN_ATTR_KEYS do keys[KNOWN_ATTR_KEYS[i]]=true end
   for k in pairs(bonus) do keys[k]=true end
   for k in pairs(unproxy(attrs)) do keys[k]=true end
   local known=0
   for k in pairs(keys) do
    local value,baseline=attrs[k],ref[k]
    if value~=nil and baseline~=nil then known=known+1 end
    if not same_val(value,baseline,0) then return false,'属性差异:'..tostring(k)..'('..short_val(value)..'/'..short_val(baseline)..')' end
   end
   if known==0 then return false,'装备属性数据不完整' end
   if type(it['价格'])~='number' or it['价格']<0 then return false,'价格:'..short_val(it['价格']) end
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
   local a,b=SYS.run('fun',cb,{1,o['格子'].x,o['格子'].y,m})
   if a and b then return false,'拾取回调拒绝' end
   local pay=math.ceil(it['价格']/2)*(o['数量'] or 1)
   U['窗口相关']['界面切换'](pay,nil,'__gm_alt_sale_v283')
   o['已经消失']=true
   saleCount, saleGold = saleCount+1, saleGold+pay
   return true
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
  local aborted=false
  for dy=-5,5 do
   if aborted then break end
   for dx=-5,5 do
    if hero['del__'] or hero['已经死亡'] or (G_ROOT['Q_地图'] and G_ROOT['Q_地图']['__gm_range_state'])~=map then
     aborted=true; break
    end
    local x,y=at.x+dx,at.y+dy
    if x>=0 and y>=0 and x<(map['地图格子列数'] or 0) and y<(map['地图格子行数'] or 0) then
     local bucket=map['地面物品组'][map['到逻辑格子'](x,y)]
     if bucket then
      local items={};for _,o in ipairs(bucket) do items[#items+1]=o end
      for _,o in ipairs(items) do
       if hero['del__'] or hero['已经死亡'] or (G_ROOT['Q_地图'] and G_ROOT['Q_地图']['__gm_range_state'])~=map then
        aborted=true; break
       end
       local it=o['物品'];local n=o['数量'] or 1
       if not o['del__'] and not o['已经消失'] and it then
        local sale_ok=safe_sell(it)
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
           G_ROOT['__gm_range_pickup_guard']=true
           local ok,res=pcall(o['拾取'],o,1)
           G_ROOT['__gm_range_pickup_guard']=nil
           if partial then
            o['物品']=orig
            if ok and res then
             picked=picked+1
             o['数量']=n-take;o['已经消失']=false
             local label=o['名称标签'];local title=(o['数量']>1) and string.format('%s(%d)',orig['显示名'],o['数量']) or orig['显示名']
             o['显示内容']=title
             if label and label['置标题'] and title then
              local color=o['__gm_ground_label_color_v287'] or orig['颜色值']
              pcall(label['置标题'],title,1,color,E['地面道具描边'],-16777216,o['显示宽度'],o['显示高度'])
             end
             items[#items+1]=o
            else o['数量']=n;incomplete=true end
           elseif not ok or not res then incomplete=true else picked=picked+1 end
          else incomplete=true end
         else incomplete=true end
        end
       end
      end
     end
    end
   end
  end
  if incomplete then
   if not is_auto then
    if U['托管显示'] and U['托管显示']['屏幕提示'] then
     local c=G_ROOT['L常量'];U['托管显示']['屏幕提示']('背包空间不足或部分物品无法处理，剩余物品留在地面',c and c['颜色_红'])
    end
   else
    if picked>0 or saleCount>0 then auto_state.full_notified=false end
    if not auto_state.full_notified then
     if U['托管显示'] and U['托管显示']['屏幕提示'] then
      local c=G_ROOT['L常量'];U['托管显示']['屏幕提示']('背包空间不足或部分物品无法处理，剩余物品留在地面',c and c['颜色_红'])
     end
     auto_state.full_notified=true
    else
     pickup_stats.suppressed_full_msgs=pickup_stats.suppressed_full_msgs+1
    end
   end
  elseif is_auto then
   auto_state.full_notified=false
  end
  end)
  G_ROOT['__gm_range_pickup_guard']=nil
  auto_state.active=false
  if saleCount>0 then
   local display=ARG_U['托管显示']
   local show=display and display['屏幕提示']
   if type(show)=='function' then
    local colors=G_ROOT['L常量']
    local message='自动出售了白色装备，获得金币【'..tostring(saleGold)..'】'
    pcall(show,message,colors and colors['颜色_黄'] or -1,true)
   end
  end
  if not gm_ok and not is_auto then
   local u=ARG_U; local c=G_ROOT['L常量']
   if u and u['托管显示'] and u['托管显示']['屏幕提示'] then pcall(u['托管显示']['屏幕提示'],'范围拾取失败：'..tostring(gm_err),c and c['颜色_红']) end
  end
  return gm_ok
 end
 S.__gm_run_range_pickup_v299=run_range_pickup

 local function auto_precheck_has_item()
  local E=G_ROOT.Ae冻集
  if not (E and E.屏幕焦点) then return false end
  if (E.逻辑暂停 or 0)>0 or E.逻辑跳过 or E.游戏暂停 then return false end
  local mask=E.遮罩信息
  if mask and mask.启动 and mask.触发 then return false end
  if G_ROOT.Q_提示框 and G_ROOT.Q_提示框.可视 then return false end
  if S.Game_State~=nil and S.Game_State~=1 then return false end
  local windows=S.界面_窗口_数组
  if type(windows)=='table' then
   for i=1,#windows do
    local w=windows[i]
    if w and w.可视 and type(w.是否有输入框焦点)=='function' and w.是否有输入框焦点(w) then
     return false
    end
   end
  end
  local hero=S.Hero
  local bag=S.包裹物品组
  local control=S.控制对象 or hero
  if not (hero and bag and control) then return false end
  if hero.del__ or hero.已经死亡 or control.del__ or control.已经死亡 then return false end
  local qmap=G_ROOT.Q_地图
  local map=qmap and qmap.__gm_range_state
  local ground=map and map.地面物品组
  local to_idx=map and map.到逻辑格子
  local at=control.地图格子
  if not (ground and to_idx and at) then return false end
  local gx,gy=at.x,at.y
  local cols,rows=map.地图格子列数 or 0,map.地图格子行数 or 0
  if type(gx)~='number' or type(gy)~='number' or cols<=0 or rows<=0 then return false end
  if map~=auto_state.last_map then
   auto_state.last_map=map
   auto_state.full_notified=false
  end
  -- Lightweight 11x11 scan: zero temp tables, zero bag/attr/price reads, early exit on 1st valid item.
  pickup_stats.prechecks=pickup_stats.prechecks+1
  local y0=gy-5; if y0<0 then y0=0 end
  local y1=gy+5; if y1>=rows then y1=rows-1 end
  local x0=gx-5; if x0<0 then x0=0 end
  local x1=gx+5; if x1>=cols then x1=cols-1 end
  for y=y0,y1 do
   for x=x0,x1 do
    local bucket=ground[to_idx(x,y)]
    if bucket then
     for i=1,#bucket do
      pickup_stats.precheck_items_inspected=pickup_stats.precheck_items_inspected+1
      local o=bucket[i]
      if o and not o.del__ and not o.已经消失 and o.物品 then
       pickup_stats.precheck_hits=pickup_stats.precheck_hits+1
       return true
      end
     end
    end
   end
  end
  pickup_stats.precheck_empty=pickup_stats.precheck_empty+1
  auto_state.full_notified=false
  return false
 end
 S.__gm_auto_precheck_v299=auto_precheck_has_item

 local function pickup_frame(ARG_U,ARG_G)
  -- Lazy-install the bag UI button once when entering 「来世续缘」.
  if not auto_state.btn_installed and is_laishi() then
   pcall(install_autopickup_btn)
  end
  local eng=G_ROOT.引擎
  local L=G_ROOT.L常量
  local manual=eng and L and type(eng.取按键按下)=='function' and eng:取按键按下(L.键_ALT)
  if manual then
   local t=now_ms()
   if t~=nil then auto_state.last_ms=t end
   run_range_pickup(ARG_U,ARG_G,false)
   return
  end
  if G_ROOT.__gm_auto_pickup_on_v299~=true then return end
  if not is_laishi() then return end
  if auto_state.active or G_ROOT.__gm_range_pickup_guard then return end
  local t=now_ms()
  if t==nil then return end
  if auto_state.last_ms~=nil then
   if t<auto_state.last_ms then
    auto_state.last_ms=t
    return
   end
   if t-auto_state.last_ms<1000 then return end
  end
  auto_state.last_ms=t
  if auto_precheck_has_item() then
   run_range_pickup(ARG_U,ARG_G,true)
  end
 end

 G_ROOT.__gm_pickup_frame_v299=pickup_frame
 S.__gm_pickup_frame_v299=pickup_frame
