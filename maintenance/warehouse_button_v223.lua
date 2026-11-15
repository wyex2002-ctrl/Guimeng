-- Installed once in the trusted native UI constructor, after all windows exist.
return function()
 local win = Sys.run('取窗口对象', 539)
 if not win then return end
 local name='远程仓库按钮'
 for _,c in ipairs(win.控件组) do if c.名称==name then return end end
 local font=__Res(2,'400132927.img')
 local text='仓库'
 local width=math.floor(math.max(42,math.ceil(font.取宽度(text))+16)*1.3+0.5)
 local height=math.floor(17*1.3+0.5)
 -- Header close artwork occupies the native 235/15/26/26 region.
 -- Apply the requested six-pixel left and three-pixel down adjustment.
 local bx,by=235-5-width-6,15+(26-height)/2+3
 local image=__Res(1,'-1657209002.img',0)
 local function factory()
  local self={id=name}
  return {getself=function()return self end,Main=function()
    Ux雌.游戏音效.按键音效1.播放()
    仓库窗口.打开()
  end,鼠标焦点=function()end}
 end
 win:增加控件(10,name,bx,by,0,width,height,'',image,
  '[控件]\n按下效果=0\n按钮类型=1\n像素检测=假\n透明色=0\n',{factory})
 local control=win.控件组[#win.控件组]
 local object=control.对象
 local original=object.显示
 -- Copy only the text-free left/right edges; stretch a blank inside column.
 -- The original NEXT glyphs are covered, never squeezed under the new caption.
 local left=Q__.创建精灵(image,0,0,6,17)
 local middle=Q__.创建精灵(image,6,0,1,17)
 local right=Q__.创建精灵(image,28,0,6,17)
 local destroy=object.销毁
 object.销毁=function()left.销毁();middle.销毁();right.销毁();destroy()end
 local tw,th=font.取宽度(text,0),font.取高度(text,0)
 local layout=font.解析(text,0,0)
 object.显示=function(x,y,sx,sy,angle,color,alpha)
  original(x,y,sx,sy,angle,0,0) -- state/focus only; avoid a bright underlay during movement
  sx=sx or 1;sy=sy or 1
  local offset=0
  local hovered=object.是否有焦点()
  local pressed=hovered and 引擎:取按键事件(L常量.键_鼠标左)
  if pressed then offset=1 end
  y=y+offset*sy
  local shade=-5723992
  if hovered and not pressed then shade=-4671304 end -- FFB8B8B8, subtle hover only
  local skin=SETA(shade,math.floor(255*(alpha or 1))) -- FFA8A8A8, button skin only
  left.置颜色(skin);middle.置颜色(skin);right.置颜色(skin)
  -- Preserve the original top/bottom bevel instead of stretching it brighter/thicker.
  for row=1,3 do
   local sourceY,sourceH,dy,targetH=0,3,0,3
   if row==2 then sourceY=3;sourceH=11;dy=3;targetH=height-6 end
   if row==3 then sourceY=14;sourceH=3;dy=height-3;targetH=3 end
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
