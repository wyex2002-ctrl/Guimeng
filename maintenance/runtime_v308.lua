-- Guimeng v1.308 runtime helper (compiled once via loadstring at module 14 init).
-- Scope: All v1.299/v1.300/v1.301/v1.302/v1.303/v1.304/v1.306/v1.307/v1.308 features apply ONLY to 「来世续缘」.
-- 「前尘忆梦」 keeps original manual Alt pickup, warehouse button, corpse digging, merc mode, and untouched mount/shop/UI logic.
local S=...
local G_ROOT=_G
if type(S)~='table' then return end
if S.__gm_runtime_v308_installed then return end
S.__gm_runtime_v308_installed=true
S.__gm_runtime_v307_installed=true
S.__gm_runtime_v306_installed=true
S.__gm_runtime_v304_installed=true
S.__gm_runtime_v303_installed=true
S.__gm_runtime_v302_installed=true
S.__gm_runtime_v301_installed=true
S.__gm_runtime_v300_installed=true
S.__gm_runtime_v299_installed=true

 local BATCH_KEY='__gm_oil_batch_v263'
 local BATCH_MAX=50
 local MAX_ROLL=1-2^-53

 local function get_env_val(k)
  local ss=S.script_setting
  if type(ss)=='table' and ss[k]~=nil then return ss[k] end
  return G_ROOT[k]
 end

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
  local bag=S.包裹物品组
  if type(bag)=='table' then
   for _,cell in pairs(bag) do
    if type(cell)=='table' and type(cell.道具)=='table' then
     visit_item(cell.道具,'load_bag')
    end
   end
  end
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
 -- Auto-pickup 3-mode toggle button (Window 539, left of 【仓库】)
 -- Mode 0: OFF (stone grey)
 -- Mode 1: Normal auto-pickup (emerald green, white equip auto-sell only)
 -- Mode 2: Auto-pickup + smart bulk sell (royal blue, sells equip & skill
 --         books like 一键出售, keeping 7-affix rare equip, Lv4/5 skill
 --         books, and protected/quest/non-sellable items)
 -- Check interval: 0.5s (500ms)
 -- ========================================================================
 local CHECK_INTERVAL_MS=500
 local COL_OFF_TEXT=-4210753       -- 0xFFBFBFBF light grey
 local COL_MODE1_TEXT=-11739014    -- 0xFF4CE07A vivid emerald green
 local COL_MODE2_TEXT=-8204545     -- 0xFF82CEFF bright luminous blue
 local COL_SKIN_OFF=-5723992       -- 0xFFA8A8A8 neutral stone OFF
 local COL_SKIN_OFF_HOVER=-4671304 -- 0xFFB8B8B8
 local COL_DOT_OFF=-8355712        -- 0xFF808080 dim grey dot
 local COL_SKIN_M1=-9910150        -- 0xFF68C97A emerald green Mode 1
 local COL_SKIN_M1_HOVER=-8658802  -- 0xFF7BE08E
 local COL_DOT_M1=-13369549        -- 0xFF33FF33 bright green dot
 local COL_SKIN_M2=-11365633       -- 0xFF5292FF royal blue Mode 2
 local COL_SKIN_M2_HOVER=-9721601  -- 0xFF6BA8FF
 local COL_DOT_M2=-13392385        -- 0xFF33A6FF bright sapphire dot

 local TIP_TEXT=
  '#c('..tostring(COL_MODE1_TEXT)..')【普通自动拾取】\n'..
  '#c('..tostring(COL_MODE2_TEXT)..')【自动拾取+自动出售】可售装备、技能书与普通怪材料，保留重要稀有物品'

 G_ROOT.__gm_auto_pickup_mode_v300=0
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

 local function get_auto_mode()
  local m=G_ROOT.__gm_auto_pickup_mode_v300
  if m==1 or m==2 then return m end
  return 0
 end
 S.__gm_get_auto_pickup_mode_v300=get_auto_mode

 local function now_ms()
  local eng=G_ROOT.引擎
  if not (eng and type(eng.取运行时间)=='function') then return nil end
  local s=tonumber(eng:取运行时间())
  if type(s)~='number' or s~=s then return nil end
  return s*1000
 end

 local function set_auto_mode(mode,silent)
  local m=tonumber(mode) or 0
  if m~=1 and m~=2 then m=0 end
  G_ROOT.__gm_auto_pickup_mode_v300=m
  G_ROOT.__gm_auto_pickup_on_v299=(m>0)
  auto_state.full_notified=false
  auto_state.last_ms=nil
  if not silent then
   local U=get_U()
   if U and U.托管显示 and U.托管显示.屏幕提示 then
    local msg,col
    if m==1 then
     msg='自动拾取已开启（普通模式）'
     col=COL_MODE1_TEXT
    elseif m==2 then
     msg='自动拾取已开启（自动出售模式）'
     col=COL_MODE2_TEXT
    else
     msg='自动拾取已关闭'
     col=COL_OFF_TEXT
    end
    U.托管显示.屏幕提示(msg,col)
   end
  end
  return m
 end
 S.__gm_set_auto_pickup_mode_v300=set_auto_mode

 local function set_auto_pickup(enabled,silent)
  if type(enabled)=='number' then
   return set_auto_mode(enabled,silent)
  end
  return set_auto_mode(enabled==true and 1 or 0,silent)
 end
 S.__gm_set_auto_pickup_v299=set_auto_pickup

 local function show_autopickup_tip()
  if not is_laishi() then return end
  local ox,oy=-1.05,0.08
  local E=G_ROOT.Ae冻集
  local mp=type(E)=='table' and E.鼠标_屏幕坐标
  if type(mp)=='table' then
   local mx,my=tonumber(mp.x),tonumber(mp.y)
   local sh=tonumber(E.屏幕高度) or 600
   if mx and mx<280 then ox=16 end
   if my and my>(sh-120) then oy=-10 end
  end
  local fn=S.气泡提示
  if type(fn)=='function' then
   fn(TIP_TEXT,0,235,ox,oy,false,0,0,0,nil,-1)
   return
  end
  local gly=G_ROOT.Gly独
  if type(gly)=='table' and type(gly.鼠标气泡)=='function' then
   gly.鼠标气泡(TIP_TEXT,0,235,ox,oy,0,nil,-1)
  end
 end
 S.__gm_autopickup_tip_v300=show_autopickup_tip

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
   local next_mode=(get_auto_mode()+1)%3
   set_auto_mode(next_mode,false)
  end
  local function on_hover_tip()
   show_autopickup_tip()
  end
  local function factory()
   local self={id=name}
   return {
    getself=function() return self end,
    Main=function() return on_toggle_click() end,
    鼠标焦点=function() return on_hover_tip() end,
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
   local mode=get_auto_mode()
   local hovered=type(object.是否有焦点)=='function' and object.是否有焦点()
   local eng=G_ROOT.引擎
   local L=G_ROOT.L常量
   local pressed=hovered and eng and L and eng:取按键事件(L.键_鼠标左)
   if pressed then y=y+sy end
   local shade,dot_col,text_col
   if mode==1 then
    shade=(hovered and not pressed) and COL_SKIN_M1_HOVER or COL_SKIN_M1
    dot_col=COL_DOT_M1
    text_col=color or -1
   elseif mode==2 then
    shade=(hovered and not pressed) and COL_SKIN_M2_HOVER or COL_SKIN_M2
    dot_col=COL_DOT_M2
    text_col=color or -1
   else
    shade=(hovered and not pressed) and COL_SKIN_OFF_HOVER or COL_SKIN_OFF
    dot_col=COL_DOT_OFF
    text_col=COL_OFF_TEXT
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
   dot_fg.置颜色(type(G_ROOT.SETA)=='function' and G_ROOT.SETA(dot_col,a_byte) or dot_col)
   dot_fg.显示_高级(dot_x+sx,dot_y+sy,angle or 0,4*sx,4*sy)
   local text_x=x+12*sx+(width-14-tw)*sx/2
   local text_y=y+(height-th)*sy/2-sy
   font.显示配置(layout,text_x,text_y,text_col,-15724528)
  end
  auto_state.btn_installed=true
  return true
 end
 S.__gm_install_autopickup_btn_v299=install_autopickup_btn

 -- ========================================================================
 -- v1.307 Remote 【仓库】 button upgrade (Window 539, 「来世续缘」 only)
 --   Click 1 (both closed): open 普通仓库 (仓库窗口) -> subtle warm amber tint
 --   Click 2 (普通仓库 open): close 普通仓库; if 行会仓库 activated (行会 ~= nil),
 --                            open 行会仓库 -> subtle cool teal-blue tint;
 --                            otherwise stay closed -> default neutral grey
 --   Click 3 (行会仓库 open): close 行会仓库 -> default neutral grey
 --   External close (X / ESC / NPC): immediately restores default neutral grey
 -- ========================================================================
 local COL_WH_OFF=-5723992          -- 0xFFA8A8A8 original default stone grey
 local COL_WH_OFF_HOVER=-4671304    -- 0xFFB8B8B8 original hover grey
 local COL_WH_NORM=-3886976         -- 0xFFC4B080 subtle warm amber (normal warehouse)
 local COL_WH_NORM_HOVER=-2834288   -- 0xFFD4C090 warm amber hover
 local COL_WH_GUILD=-8210232        -- 0xFF82B8C8 subtle cool teal-blue (guild warehouse)
 local COL_WH_GUILD_HOVER=-7026472  -- 0xFF94C8D8 cool teal-blue hover

 local wh_state={
  btn_installed=false,
  old_hidden=false,
  last_laishi=nil,
  opened_kind=nil, -- nil | 'normal' | 'guild'
  last_shade=COL_WH_OFF,
 }
 S.__gm_wh_state_v307=wh_state

 local function is_guild_warehouse_active(U)
  if type(U)~='table' or (type(U.啾啾啵啵)~='function' and type(U.啾啾啵啵)~='table') then return false end
  local ok,hero_data=pcall(U.啾啾啵啵)
  if not ok or type(hero_data)~='table' then return false end
  return type(hero_data.行会)=='table'
 end
 S.__gm_is_guild_wh_active_v307=is_guild_warehouse_active

 local function get_wh_win(name)
  local w=get_env_val(name)
  if type(w)=='table' then return w end
  local ctrls=S.tbl_controls
  local entry=type(ctrls)=='table' and ctrls[name] or nil
  if type(entry)=='table' then
   if type(entry.tbl)=='table' then return entry.tbl end
   return entry
  end
  return nil
 end

 local function call_proxy_method(obj,method)
  if type(obj)~='table' then return false end
  return pcall(function()
   local fn=obj[method]
   if type(fn)=='function' or type(fn)=='table' then
    return fn()
   end
  end)
 end

 local function get_wh_active_kind()
  local kind=wh_state.opened_kind
  if kind=='normal' then
   local nw=get_wh_win('仓库窗口')
   if type(nw)=='table' and nw.可视==true then return 'normal' end
   wh_state.opened_kind=nil
   return nil
  elseif kind=='guild' then
   local gw=get_wh_win('行会仓库')
   if type(gw)=='table' and gw.可视==true then return 'guild' end
   wh_state.opened_kind=nil
   return nil
  end
  return nil
 end
 S.__gm_get_wh_active_kind_v307=get_wh_active_kind

 local function on_wh_btn_click()
  if not is_laishi() then return end
  local U=get_U()
  if U and U.游戏音效 and U.游戏音效.按键音效1 then
   call_proxy_method(U.游戏音效.按键音效1,'播放')
  end
  local norm_win=get_wh_win('仓库窗口')
  local guild_win=get_wh_win('行会仓库')
  local norm_open=(type(norm_win)=='table' and norm_win.可视==true)
  local guild_open=(type(guild_win)=='table' and guild_win.可视==true)
  if guild_open then
   call_proxy_method(guild_win,'关闭')
   if norm_open then call_proxy_method(norm_win,'关闭') end
   wh_state.opened_kind=nil
  elseif norm_open then
   call_proxy_method(norm_win,'关闭')
   if is_guild_warehouse_active(U) and type(guild_win)=='table' then
    call_proxy_method(guild_win,'打开')
    if guild_win.可视==true then
     wh_state.opened_kind='guild'
    else
     wh_state.opened_kind=nil
    end
   else
    wh_state.opened_kind=nil
   end
  else
   if type(norm_win)=='table' then
    call_proxy_method(norm_win,'打开')
    if norm_win.可视==true then
     wh_state.opened_kind='normal'
    else
     wh_state.opened_kind=nil
    end
   end
  end
 end
 S.__gm_wh_btn_click_v307=on_wh_btn_click

 local function sync_warehouse_btn_v307()
  if type(S.取窗口对象)~='function' then return false end
  local win=S.取窗口对象(539)
  if type(win)~='table' or type(win.控件组)~='table' then return false end
  local cur_laishi=is_laishi()
  local old_ctrl,new_ctrl=nil,nil
  local new_name='远程仓库按钮_v307'
  for i=1,#win.控件组 do
   local c=win.控件组[i]
   if type(c)=='table' then
    if c.名称=='远程仓库按钮' then old_ctrl=c
    elseif c.名称==new_name then new_ctrl=c end
   end
  end
  if not cur_laishi then
   if old_ctrl then
    old_ctrl.可视=true
    if type(old_ctrl.对象)=='table' and type(old_ctrl.对象.禁用按钮)=='function' then
     pcall(old_ctrl.对象.禁用按钮,false)
    end
    wh_state.old_hidden=false
   end
   if new_ctrl then
    new_ctrl.可视=false
    if type(new_ctrl.对象)=='table' and type(new_ctrl.对象.禁用按钮)=='function' then
     pcall(new_ctrl.对象.禁用按钮,true)
    end
   end
   wh_state.opened_kind=nil
   wh_state.last_laishi=false
   return true
  end
  if not new_ctrl then
   if type(G_ROOT.__Res)~='function' or type(G_ROOT.Q__)~='table' then return false end
   local font=G_ROOT.__Res(2,'400132927.img')
   local image=G_ROOT.__Res(1,'-1657209002.img',0)
   if not (font and image) then return false end
   local text='仓库'
   local width=(old_ctrl and old_ctrl.w) or math.floor(math.floor(math.max(42,math.ceil(font.取宽度(text))+16)*1.3+0.5)*0.8+0.5)
   local height=(old_ctrl and old_ctrl.h) or math.floor(17*1.3+0.5)
   local bx=(old_ctrl and old_ctrl.x) or (235-5-width-6)
   local by=(old_ctrl and old_ctrl.y) or (15+(26-height)/2+3)
   local function factory()
    local self={id=new_name}
    return {
     getself=function() return self end,
     Main=function() return on_wh_btn_click() end,
     鼠标焦点=function() end,
    }
   end
   win:增加控件(10,new_name,bx,by,0,width,height,'',image,
    '[控件]\n按下效果=0\n按钮类型=1\n像素检测=假\n透明色=0\n',{factory})
   new_ctrl=win.控件组[#win.控件组]
   local object=new_ctrl and new_ctrl.对象
   if type(object)~='table' then return false end
   local original=object.显示
   local destroy=object.销毁
   local left=G_ROOT.Q__.创建精灵(image,0,0,6,17)
   local middle=G_ROOT.Q__.创建精灵(image,6,0,1,17)
   local right=G_ROOT.Q__.创建精灵(image,28,0,6,17)
   local tw,th=font.取宽度(text,0),font.取高度(text,0)
   local layout=font.解析(text,0,0)
   object.销毁=function()
    left.销毁(); middle.销毁(); right.销毁()
    if type(destroy)=='function' then destroy() end
   end
   object.显示=function(x,y,sx,sy,angle,color,alpha)
    if not is_laishi() then return end
    if type(original)=='function' then original(x,y,sx,sy,angle,0,0) end
    sx=sx or 1; sy=sy or 1
    local hovered=type(object.是否有焦点)=='function' and object.是否有焦点()
    local eng=G_ROOT.引擎
    local L=G_ROOT.L常量
    local pressed=hovered and eng and L and eng:取按键事件(L.键_鼠标左)
    if pressed then y=y+sy end
    local kind=get_wh_active_kind()
    local shade
    if kind=='normal' then
     shade=(hovered and not pressed) and COL_WH_NORM_HOVER or COL_WH_NORM
    elseif kind=='guild' then
     shade=(hovered and not pressed) and COL_WH_GUILD_HOVER or COL_WH_GUILD
    else
     shade=(hovered and not pressed) and COL_WH_OFF_HOVER or COL_WH_OFF
    end
    wh_state.last_shade=shade
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
    font.显示配置(layout,x+(width-tw)*sx/2,y+(height-th)*sy/2-sy,color or -1,-15724528)
   end
  end
  if old_ctrl then
   old_ctrl.可视=false
   if type(old_ctrl.对象)=='table' and type(old_ctrl.对象.禁用按钮)=='function' then
    pcall(old_ctrl.对象.禁用按钮,true)
   end
   wh_state.old_hidden=true
  end
  if new_ctrl then
   new_ctrl.可视=true
   if type(new_ctrl.对象)=='table' and type(new_ctrl.对象.禁用按钮)=='function' then
    pcall(new_ctrl.对象.禁用按钮,false)
   end
   wh_state.btn_installed=true
  end
  wh_state.last_laishi=true
  return true
 end
 S.__gm_sync_wh_btn_v307=sync_warehouse_btn_v307

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
 -- Exact non-4/5-level skill book set from 「一键出售」 (14/428 gc 230).
 local SELLABLE_BOOKS={
  ['Q火球术']=true,['专心']=true,['主灵融合1']=true,['主灵融合2']=true,['主灵融合3']=true,
  ['乾坤大挪移']=true,['养生术']=true,['冰咆哮']=true,['冰月神掌']=true,['冰月震天']=true,
  ['冰沙掌']=true,['冲虚闪']=true,['凝血离魂']=true,['击风']=true,['分身术']=true,
  ['刺杀剑术']=true,['十方斩']=true,['半月弯刀']=true,['召唤神兽']=true,['召唤骷髅']=true,
  ['吸星大法']=true,['地狱火']=true,['地狱雷光']=true,['垂柳舞']=true,['基本剑术']=true,
  ['大火球']=true,['天打雷劈']=true,['妙影无踪']=true,['幽灵盾']=true,['异形换位']=true,
  ['强魔震法']=true,['快刀斩麻']=true,['怒神霹雳']=true,['攻杀剑术']=true,['斗转星移']=true,
  ['施毒大法']=true,['施毒术']=true,['旋风墙']=true,['最后抵抗']=true,['月桂']=true,
  ['月魂断玉']=true,['月魂灵波']=true,['横扫千军']=true,['残月之乱']=true,['治愈术']=true,
  ['泰山压顶']=true,['深渊']=true,['满月饿狼']=true,['火墙']=true,['火球术']=true,
  ['灭日龙轰']=true,['灭魂火符']=true,['灵魂火符']=true,['炎天火雨']=true,['烈火剑法']=true,
  ['爆裂火焰']=true,['猛虎强势']=true,['疾光电影']=true,['疾风']=true,['白莲']=true,
  ['盛开']=true,['瞬回术']=true,['破血狂杀']=true,['磨炼']=true,['神圣战甲术']=true,
  ['移花接木']=true,['移花接玉']=true,['空拳刀法']=true,['精神力战法']=true,['红莲']=true,
  ['罗刹降临']=true,['群体治愈术']=true,['翔空剑法']=true,['莲月剑法']=true,['蔓藤舞']=true,
  ['蝉舞']=true,['诱惑之光']=true,['赤焰星爆']=true,['超强召唤神兽']=true,['超强召唤骷髅']=true,
  ['运气术']=true,['迷魂大法']=true,['金刚之躯']=true,['铁布衫']=true,['闪电雷鸣']=true,
  ['阴阳法环']=true,['隐身术']=true,['雷电术']=true,['霹雳掌']=true,['风掌']=true,
  ['风震天']=true,['魄冰刺']=true,['魔法盾']=true,['龙卷风']=true,
 }
 -- All 36 ordinary-monster corpse-dig materials (identical to 「一键出售」 v1.305).
 -- Strictly excludes Boss / rare / quest / seal items (沃玛号角, 精灵骸骨, 飞龙剑碎片, 火影晶体, 震天魔印, 商会物资, *_印记).
 local ORDINARY_MOB_MATERIALS={
  ['僵尸骨头']=true,['兔肉']=true,['号角']=true,['夜明珠']=true,['宝玉']=true,['思念珍珠']=true,['指甲']=true,
  ['毒蛇胆汁']=true,['毒蜘蛛牙齿']=true,['潘夜之泪']=true,['牙齿']=true,['牛肉']=true,['狼肉']=true,
  ['猪肉']=true,['皮']=true,['神灵雕像']=true,['羊毛']=true,['羊肉']=true,['羊角']=true,['蚂蚁卵']=true,['蛆卵']=true,
  ['蜘蛛线']=true,['蝎子的尾巴']=true,['褐色栗子']=true,['跳蚤皮']=true,['遗物']=true,['金色栗子']=true,
  ['铜色栗子']=true,['银色栗子']=true,['食人花果实']=true,['食人花树叶']=true,['骷髅骨']=true,
  ['鸡肉']=true,['鸡血']=true,['鹿肉']=true,['鹿茸']=true,
 }

 local function is_rank45_book(name,extra)
  local rank=type(extra)=='table' and tonumber(extra['强化书'])
  if rank==4 or rank==5 then return true end
  if type(name)=='string' then
   local check=string.sub(name,1,1)=='Q' and string.sub(name,2) or name
   if string.find(check,'四级',1,true)==1 or string.find(check,'五级',1,true)==1 then return true end
  end
  return false
 end

 local function can_bulk_sell_ground(it,qty)
  if type(it)~='table' then return false,'非道具表' end
  local name=it['名称']
  if PROTECT_ITEMS[name] then return false,'保护名单' end
  if it['禁止出售'] then return false,'禁止出售' end
  if it['任务关联'] then return false,'任务关联' end
  if it['剧情关联'] then return false,'剧情关联' end
  local price=finite(it['价格'])
  local n=finite(qty or it['数量'] or 1)
  if not price or price<0 or not n or n<1 or n~=math.floor(n) then return false,'价格或数量异常' end
  local value=math.ceil(price/2)*n
  if not finite(value) then return false,'售价溢出' end
  local cat=it['分类']
  local extra=it['附加']
  if cat=='装备' then
   local affixes=type(extra)=='table' and tonumber(extra['条数']) or 0
   if affixes and affixes>=7 then return false,'7条极品保留' end
   return true,'装备'
  elseif cat=='道具' then
   local is_book=(type(name)=='string' and SELLABLE_BOOKS[name]) or (type(extra)=='table' and extra['商店']=='书店')
   if is_book then
    if is_rank45_book(name,extra) then return false,'4/5级技能书保留' end
    return true,'技能书'
   end
  end
  if type(name)=='string' and ORDINARY_MOB_MATERIALS[name] then
   return true,'材料'
  end
  return false,'非可售分类'
 end
 S.__gm_can_bulk_sell_v300=can_bulk_sell_ground

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

 local function run_range_pickup(ARG_U,ARG_G,is_auto,auto_mode)
  if auto_state.active or G_ROOT['__gm_range_pickup_guard'] then return false end
  auto_state.active=true
  local bulk_mode=(is_auto==true and auto_mode==2)
  local saleCount,saleEquipCount,saleBookCount,saleMatCount,saleGold=0,0,0,0,0
  local picked=0
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
  if not is_auto and not E['屏幕焦点'] then reason='游戏窗口没有焦点'
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
  local function sell(o,it,kind)
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
   saleCount,saleGold=saleCount+1,saleGold+pay
   if kind=='技能书' then saleBookCount=saleBookCount+1
   elseif kind=='材料' then saleMatCount=saleMatCount+1
   else saleEquipCount=saleEquipCount+1 end
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
        local sale_ok,sale_kind
        if bulk_mode then
         sale_ok,sale_kind=can_bulk_sell_ground(it,n)
        else
         sale_ok,sale_kind=safe_sell(it)
        end
        if sale_ok then
         local sold=sell(o,it,sale_kind)
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
    local message
    if not bulk_mode then
     message='自动出售了白色装备，获得金币【'..tostring(saleGold)..'】'
    elseif saleMatCount>0 then
     local parts={}
     if saleEquipCount>0 then parts[#parts+1]='装备' end
     if saleBookCount>0 then parts[#parts+1]='技能书' end
     parts[#parts+1]='普通怪材料'
     local joined=parts[1]
     for i=2,#parts do joined=joined..'、'..parts[i] end
     message='自动出售了'..joined..'，获得金币【'..tostring(saleGold)..'】'
    elseif saleEquipCount>0 and saleBookCount>0 then
     message='自动出售了装备与技能书，获得金币【'..tostring(saleGold)..'】'
    elseif saleBookCount>0 then
     message='自动出售了技能书，获得金币【'..tostring(saleGold)..'】'
    else
     message='自动出售了装备，获得金币【'..tostring(saleGold)..'】'
    end
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
  if not E then return false end
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

 -- ============================================================================
 -- v1.301/v1.304/v1.306 Feature 1: Corpse-digging -> Direct monster death drop
 --   - Rolls U.岗位上的()[monster_name] fresh on death with 5x amplified 采集
 --     level scaling:
 --       denom <= 1: 100%
 --       gather_lv == 0: 1 / (3 * denom)
 --       gather_lv >= 1: min(1, (2.5 * gather_lv) / denom)
 --         (e.g. denom=100: Lv0=1/300, Lv1=2.5/100, Lv2=5/100, Lv3=7.5/100)
 --   - Killing 鸡/猪/牛/羊/狼 near hero grants 采集 skill XP via U.窗口相关.元素窗口('采集')
 --   - Clears ev_obj.附加.挖取 = {} to prevent double-loot by digging
 --   - Restores live engine sprite handles from S.游戏道具组[名称]
 -- ============================================================================
 local GATHER_XP_MONSTERS={鸡=true,猪=true,牛=true,羊=true,狼=true}

 local function get_pub_event_obj(actor)
  if type(actor)~='table' then return nil end
  local gly=get_env_val('Gly独')
  local aid=tonumber(actor.id)
  if type(gly)=='table' and type(gly.事件对象)=='function' and aid~=nil then
   local ok,ev_obj=pcall(gly.事件对象,aid)
   if ok and type(ev_obj)=='table' then return ev_obj end
  end
  return nil
 end

 local function get_monster_name(actor,ev_obj)
  local prop=type(actor)=='table' and actor.属性 or nil
  local nm=type(prop)=='table' and prop.名称 or nil
  if type(nm)=='string' and #nm>0 then return nm end
  local ep=type(ev_obj)=='table' and ev_obj.属性 or nil
  nm=type(ep)=='table' and ep.名称 or nil
  if type(nm)=='string' and #nm>0 then return nm end
  return nil
 end

 local function get_dig_table_entry(U,monster_name)
  if not monster_name or monster_name=='镖车' then return nil end
  if type(U)~='table' or type(U.岗位上的)~='function' then return nil end
  local ok,tbl=pcall(U.岗位上的)
  if not ok or type(tbl)~='table' then return nil end
  local list=tbl[monster_name]
  if type(list)=='table' and #list>0 then return list end
  return nil
 end

 local function get_gather_level(U)
  if type(U)~='table' or type(U.啾啾啵啵)~='function' then return 0 end
  local ok,hero_data=pcall(U.啾啾啵啵)
  local sk=ok and type(hero_data)=='table' and hero_data.技能 or nil
  local g=type(sk)=='table' and sk.采集 or nil
  if type(g)=='table' and type(g[1])=='number' and g[1]>0 then
   return math.floor(g[1])
  end
  return 0
 end

 local function calc_gather_drop_prob(denom,gather_lv)
  if type(denom)~='number' or denom<=1 then return 1 end
  if type(gather_lv)~='number' or gather_lv<=0 then
   return 1/(3*denom)
  end
  local p=(2.5*gather_lv)/denom
  if p>1 then p=1 end
  return p
 end
 S.__gm_calc_gather_prob_v306=calc_gather_drop_prob

 local function build_live_drop_item(item_name,custom_item)
  if type(item_name)~='string' or #item_name==0 then return nil end
  local entry=type(S.游戏道具组)=='table' and S.游戏道具组[item_name] or nil
  local tpl=type(entry)=='table' and (type(entry.数据)=='table' and entry.数据 or entry) or nil
  local raw_tpl=type(tpl)=='table' and (type(tpl.__数据)=='table' and tpl.__数据 or tpl) or nil
  local out={}
  if type(raw_tpl)=='table' then
   for k,v in pairs(raw_tpl) do
    out[k]=v
   end
  end
  if type(custom_item)=='table' then
   for k,v in pairs(custom_item) do
    if k~='精灵' and k~='地面精灵' and k~='发现音效' and k~='动画效果' and k~='格子底图' and k~='格子动画' then
     out[k]=v
    end
   end
  end
  if type(custom_item)~='table' or type(custom_item.附加)~='table' then
   local extra_out={}
   if type(out.附加)=='table' then
    local src_ex=type(out.附加.__数据)=='table' and out.附加.__数据 or out.附加
    for k,v in pairs(src_ex) do extra_out[k]=v end
   end
   out.附加=extra_out
  end
  if type(custom_item)~='table' or type(custom_item.属性)~='table' then
   local prop_out={}
   if type(out.属性)=='table' then
    local src_pr=type(out.属性.__数据)=='table' and out.属性.__数据 or out.属性
    for k,v in pairs(src_pr) do prop_out[k]=v end
   end
   out.属性=prop_out
  end
  if out.地面精灵==nil and out.精灵==nil then return nil end
  return out
 end

 local function award_gather_xp_if_eligible(U,actor,monster_name)
  if not GATHER_XP_MONSTERS[monster_name] then return false end
  if type(actor)=='table' and actor.所属阵营~=nil and actor.所属阵营~='敌方' then return false end
  -- Require monster to be within screen range (16 tiles) of hero so off-screen guard kills do not grant XP.
  local hero=S.控制对象 or S.Hero
  local hp=type(hero)=='table' and hero.地图格子 or nil
  local mp=type(actor)=='table' and actor.地图格子 or nil
  if hp and mp and type(hp.x)=='number' and type(hp.y)=='number' and type(mp.x)=='number' and type(mp.y)=='number' then
   if math.max(math.abs(hp.x-mp.x),math.abs(hp.y-mp.y))>16 then return false end
  end
  local wr=type(U)=='table' and U.窗口相关 or nil
  if type(wr)=='table' and type(wr.元素窗口)=='function' then
   pcall(wr.元素窗口,'采集')
   return true
  end
  return false
 end

 local function corpse_has_v301(actor)
  if not is_laishi() then return false end
  if type(actor)~='table' then return false end
  local U=get_U()
  local ev_obj=get_pub_event_obj(actor)
  local mname=get_monster_name(actor,ev_obj)
  if mname=='镖车' then return false end
  if GATHER_XP_MONSTERS[mname] then return true end
  if get_dig_table_entry(U,mname)~=nil then return true end
  local ex=type(ev_obj)=='table' and ev_obj.附加 or actor.附加
  return type(ex)=='table' and type(ex.挖取)=='table' and #ex.挖取>0
 end

 local function corpse_drop_v301(actor,drops)
  if not is_laishi() then return 0 end
  if type(actor)~='table' or type(drops)~='table' then return 0 end
  local U=get_U()
  local ev_obj=get_pub_event_obj(actor)
  local mname=get_monster_name(actor,ev_obj)
  if mname=='镖车' then return 0 end

  -- Clear pre-spawned 附加.挖取 immediately so dead bodies cannot be double-looted by digging.
  local saved_dig=nil
  local dig_holder=nil
  if type(ev_obj)=='table' and type(ev_obj.附加)=='table' and type(ev_obj.附加.挖取)=='table' and #ev_obj.附加.挖取>0 then
   saved_dig=ev_obj.附加.挖取
   dig_holder=ev_obj.附加
  elseif type(actor.附加)=='table' and type(actor.附加.挖取)=='table' and #actor.附加.挖取>0 then
   saved_dig=actor.附加.挖取
   dig_holder=actor.附加
  end
  if dig_holder then dig_holder.挖取={} end

  local added=0
  local list=get_dig_table_entry(U,mname)
  if list then
   local gather_lv=get_gather_level(U)
   local gly=get_env_val('Gly独')
   local wr=type(U)=='table' and U.窗口相关 or nil
   local mlv=(type(ev_obj)=='table' and type(ev_obj.属性)=='table' and type(ev_obj.属性.附加)=='table' and ev_obj.属性.附加.等级)
    or (type(actor.属性)=='table' and ((type(actor.属性.附加)=='table' and actor.属性.附加.等级) or actor.属性.等级))
    or 1
   for i=1,#list do
    local row=list[i]
    local item_name=type(row)=='table' and row[1] or nil
    local denom=type(row)=='table' and tonumber(row[2]) or nil
    if type(item_name)=='string' and #item_name>0 and denom~=nil then
     local prob=calc_gather_drop_prob(denom,gather_lv)
     if prob>=1 or random_unit()<prob then
      local custom=nil
      if type(gly)=='table' and type(gly.取道具信息_名称)=='function' then
       local ok_i,got=pcall(gly.取道具信息_名称,item_name)
       if ok_i and type(got)=='table' then custom=got end
      end
      if type(custom)=='table' and custom.分类=='装备' and type(wr)=='table' and type(wr.全图窗口)=='function' then
       local ok_e,eq=pcall(wr.全图窗口,item_name,mlv,nil,1)
       if ok_e and type(eq)=='table' then custom=eq end
      end
      local out=build_live_drop_item(item_name,custom)
      if out then
       if type(out.附加)=='table' and out.附加.品质~=nil then
        local q=math.floor(random_unit()*10)+1
        if q<1 then q=1 elseif q>10 then q=10 end
        out.附加.品质=q
        if type(out.价格)=='number' then
         out.价格=out.价格+q*10
        end
       end
       drops[#drops+1]={物品道具=out,掉落数量=1}
       added=added+1
      end
     end
    end
   end
  elseif saved_dig then
   -- Fallback if 岗位上的() table is unavailable
   local decrypt=get_env_val('文本加解密')
   local ss=S.script_setting
   local ss_tbl=type(ss)=='table' and ss.table or nil
   local g_tbl=G_ROOT.table
   local load_tbl=(type(ss_tbl)=='table' and ss_tbl.loadstring) or (type(g_tbl)=='table' and g_tbl.loadstring) or nil
   for i=1,#saved_dig do
    local raw=saved_dig[i]
    local item=nil
    if type(raw)=='table' then
     item=raw
    elseif type(raw)=='string' and #raw>0 and type(decrypt)=='function' and type(load_tbl)=='function' then
     local ok1,plain=pcall(decrypt,raw,'mir3zuobigou')
     if ok1 and type(plain)=='string' and #plain>0 then
      local ok2,parsed=pcall(load_tbl,plain)
      if ok2 and type(parsed)=='table' then item=parsed end
     end
    end
    if type(item)=='table' and item.名称~=nil then
     local out=build_live_drop_item(item.名称,item)
     if out then
      drops[#drops+1]={物品道具=out,掉落数量=1}
      added=added+1
     end
    end
   end
  end

  -- Award 采集 skill修炼经验 when killing 鸡/猪/牛/羊/狼
  award_gather_xp_if_eligible(U,actor,mname)
  return added
 end
 G_ROOT.__gm_corpse_has_v301=corpse_has_v301
 S.__gm_corpse_has_v301=corpse_has_v301
 G_ROOT.__gm_corpse_drop_v301=corpse_drop_v301
 S.__gm_corpse_drop_v301=corpse_drop_v301

 -- ============================================================================
 -- v1.301/v1.303 Feature 2 & 3: Ranged assassin mercenary skill blink & projectile sync
 --   - Trigger: ANY adjacent alive enemy monster (Chebyshev dist <= 1)
 --   - Destination: behind the currently locked attack target (target.地图格子)
 --     at ring distance 2~4 (preferring walkable tile not adjacent to any enemy)
 --   - Ranged skills still launch spinning weapon projectile, deferring both
 --     damage and skill hit effect animation (目标动画) to projectile arrival
 --   - Re-wraps automatically if game_start (14/421 -> 14/420) resets prepare
 -- ============================================================================
 local MERC_BASIC='刺客普通攻击'
 local MERC_RETREAT_DIST={蝉舞=4,盛开=2,白莲=2,红莲=3,月桂=3}
 local MERC_RING_SIDES={{-1,-1,1,0},{1,-1,0,1},{1,1,-1,0},{-1,1,0,-1}}
 local wrapped_prepare_v303=nil

 local function merc_alive(a)
  return type(a)=='table' and not a.已经消失 and a.是否有效~=false and not a.del__
   and type(a.属性)=='table' and type(a.属性.hp)=='number' and a.属性.hp>0
 end

 local function merc_binding(item)
  if type(item)~='table' or item.分类~='装备' or item.子类~='武器' then return nil end
  local a=item.附加
  local b=type(a)=='table' and a.绑定技能 or nil
  if b==nil then return MERC_BASIC end
  return b
 end

 local function merc_weapon()
  local b=S.包裹物品组 and S.包裹物品组[397]
  return type(b)=='table' and b.拿起~=true and b.道具 or nil
 end

 local function merc_is_ranged(actor)
  local U=get_U()
  local m=U and U.佣兵对象
  local id=type(m)=='table' and m.id or nil
  if type(actor)~='table' or type(id)~='number' or id<=0 or actor.id~=id then return false end
  return merc_binding(merc_weapon())==MERC_BASIC and actor.绑定技能==MERC_BASIC
 end

 local function has_adjacent_enemy(actor,target)
  local p=actor.地图格子
  if not p then return false end
  if merc_alive(target) and target~=actor and target.所属阵营=='敌方' and not target.不可选中 and target.地图格子 then
   local q=target.地图格子
   if math.max(math.abs(p.x-q.x),math.abs(p.y-q.y))<=1 then
    return true
   end
  end
  local actors=S.屏幕事件组
  if type(actors)~='table' then return false end
  for _,e in pairs(actors) do
   if e~=actor and merc_alive(e) and e.所属阵营=='敌方' and not e.不可选中 and e.地图格子 then
    local q=e.地图格子
    if math.max(math.abs(p.x-q.x),math.abs(p.y-q.y))<=1 then
     return true
    end
   end
  end
  return false
 end

 local function is_retreat_tile_safe(x,y,actor)
  local actors=S.屏幕事件组
  if type(actors)~='table' then return true end
  for _,e in pairs(actors) do
   if e~=actor and merc_alive(e) and e.所属阵营=='敌方' and not e.不可选中 and e.地图格子 then
    local q=e.地图格子
    if math.max(math.abs(x-q.x),math.abs(y-q.y))<=1 then
     return false
    end
   end
  end
  return true
 end

 local function install_merc_ranged_v301()
  local cur=G_ROOT.__gm_merc_visual_prepare_v255
  if type(cur)~='function' then return false end
  if cur==wrapped_prepare_v303 then return true end
  local orig=cur
  local function prepare_v303(state,public)
   if not is_laishi() then
    return orig(state,public)
   end
   if type(state)~='table' or type(public)~='table' then return end
   local actor,target,cfg=state.施法者,state.目标,state.对象
   if type(cfg)~='table' or not merc_is_ranged(actor) or not merc_alive(target) or target==actor then
    return
   end
   local distance=MERC_RETREAT_DIST[cfg.名称]
   if distance and has_adjacent_enemy(actor,target) then
    local q=target.地图格子
    local p=actor.地图格子
    local dir_fn=get_env_val('取两点间方向')
    local qmap=get_env_val('Q_地图')
    if q and p and target.所属阵营=='敌方' and not target.不可选中
     and type(dir_fn)=='function' and type(qmap)=='table' and type(qmap.取格子信息)=='function' then
     local facing
     if target.方向~=nil then
      facing=(target.方向+3)%8+1
     else
      facing=dir_fn(p.x,p.y,q.x,q.y)
     end
     local first
     for i=0,7 do
      local side=MERC_RING_SIDES[math.floor(i/2)+1]
      local rx,ry=q.x+side[1]+side[3]*(i%2),q.y+side[2]+side[4]*(i%2)
      if dir_fn(q.x,q.y,rx,ry)==facing then first=i*distance; break end
     end
     if first~=nil then
      local pick_x,pick_y,fb_x,fb_y
      for i=0,8*distance-1 do
       local n=(first+i)%(8*distance)
       local side=MERC_RING_SIDES[math.floor(n/(2*distance))+1]
       local offset=n%(2*distance)
       local rx,ry=q.x+side[1]*distance+side[3]*offset,q.y+side[2]*distance+side[4]*offset
       if qmap.取格子信息(rx,ry,'障碍')==0 then
        if fb_x==nil then fb_x=rx; fb_y=ry end
        if is_retreat_tile_safe(rx,ry,actor) then
         pick_x=rx; pick_y=ry
         break
        end
       end
      end
      local bx,by=pick_x or fb_x,pick_y or fb_y
      local U=get_U()
      local merc=U and U.佣兵对象
      if bx~=nil and by~=nil and type(merc)=='table' and type(merc.瞬移)=='function' then
       merc.瞬移(bx,by)
       merc.方向=dir_fn(bx,by,q.x,q.y)
      end
     end
    end
   end
   -- Launch spinning weapon projectile & defer both damage and skill hit animation
   -- for basic ranged attack AND all 5 ranged assassin skills.
   if cfg.名称~=MERC_BASIC and not distance then return end
   local item=merc_weapon()
   if type(item)~='table' then return end
   local template=S.游戏道具组 and S.游戏道具组[item.名称]
   local image=item.地面图标 or (type(template)=='table' and template.地面图标)
   image=image or item.图标 or (type(template)=='table' and template.图标)
   if not image then return end
   local sys=get_env_val('Sys')
   local fireball=type(sys)=='table' and type(sys.get)=='function' and sys.get('skill','火球术') or nil
   local speed=type(fireball)=='table' and fireball.子弹速度
   if type(speed)~='number' or speed~=speed or speed<=0 or speed==math.huge then return end
   local original=state.伤害进度
   local offsets={}
   local first_dmg=type(original)=='table' and original[1] or nil
   if type(first_dmg)~='number' then return end
   local retire=math.max(first_dmg,state.命中动画延迟 or 0)
   for i,v in ipairs(original) do
    offsets[i]=v-first_dmg
    retire=math.max(retire,v)
    original[i]=math.huge
   end
   local shot={
    image=image,
    target=target,
    launch=math.max(0,state.起手动画延迟 or 0),
    speed=speed*1.2,
    retire=retire,
    offsets=offsets,
    raw=public.刷新,
    elapsed=0,
   }
   state.命中动画延迟=math.huge
   state.__gm_merc_visual_v255=shot
   public.刷新=function()
    shot.elapsed=shot.elapsed+(get_env_val('dt') or 0)
    local done=shot.raw()
    if shot.cancelled or (done and not state.伤害产生_已结束) then
     shot.cancelled=true
     return true
    end
    if shot.elapsed>=shot.retire and state.起手动画_已播放 then
     if not done then shot.retired=true; shot.skip=true end
     return true
    end
    return false
   end
  end
  wrapped_prepare_v303=prepare_v303
  G_ROOT.__gm_merc_visual_prepare_v255=prepare_v303
  S.__gm_merc_visual_prepare_v301=prepare_v303
  return true
 end
 install_merc_ranged_v301()
 S.__gm_install_merc_ranged_v301=install_merc_ranged_v301

 local function pickup_frame(ARG_U,ARG_G)
  -- Re-ensure merc ranged hook (immune to game_start / 14/421 re-running 14/420)
  if G_ROOT.__gm_merc_visual_prepare_v255~=wrapped_prepare_v303 then
   pcall(install_merc_ranged_v301)
  end
  local cur_laishi=is_laishi()
  if not auto_state.btn_installed and cur_laishi then
   pcall(install_autopickup_btn)
  end
  if wh_state.last_laishi~=cur_laishi or (cur_laishi and (not wh_state.btn_installed or not wh_state.old_hidden)) then
   pcall(sync_warehouse_btn_v307)
  end
  local eng=G_ROOT.引擎
  local L=G_ROOT.L常量
  local E=G_ROOT.Ae冻集
  local manual=E and E.屏幕焦点 and eng and L and type(eng.取按键按下)=='function' and eng:取按键按下(L.键_ALT)
  if manual then
   local t=now_ms()
   if t~=nil then auto_state.last_ms=t end
   run_range_pickup(ARG_U,ARG_G,false,0)
   return
  end
  local mode=get_auto_mode()
  if mode==0 then return end
  if not is_laishi() then return end
  if auto_state.active or G_ROOT.__gm_range_pickup_guard then return end
  local t=now_ms()
  if t==nil then return end
  if auto_state.last_ms~=nil then
   if t<auto_state.last_ms then
    auto_state.last_ms=t
    return
   end
   if t-auto_state.last_ms<CHECK_INTERVAL_MS then return end
  end
  auto_state.last_ms=t
  if auto_precheck_has_item() then
   run_range_pickup(ARG_U,ARG_G,true,mode)
  end
 end

 G_ROOT.__gm_pickup_frame_v299=pickup_frame
 S.__gm_pickup_frame_v299=pickup_frame
