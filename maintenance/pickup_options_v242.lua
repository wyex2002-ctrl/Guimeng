return function()
 local win=Sys.run('取窗口对象',539);if not win then return end
 for _,c in ipairs(win.控件组)do if c.名称=='拾取出售选择_v242'then return end end
 -- Existing native nine-pixel UI font; no global font or color is changed.
 local font=__Res(2,Ae冻集.游戏素材组['宋_9_描边'].地址)
 local image=__Res(1,'-1657209002.img',0)
 local function option(name,caption,key,default,y)
  local width=9+math.ceil(font.取宽度(caption));local x=177-width
  local function selected()
   local hero=Sys.get('hero');if not hero or hero[key]==nil then return default end
   return hero[key]==true
  end
  local function factory()
   local self={id=name}
   return {getself=function()return self end,Main=function()
    local hero=Sys.get('hero');if hero then hero[key]=not selected();hero.__gm_pickup_elapsed_v242=0 end
   end,鼠标焦点=function()end}
  end
  win:增加控件(10,name,x,y,0,width,12,'',image,'[控件]\n按下效果=0\n按钮类型=1\n像素检测=假\n透明色=0\n',{factory})
  local c=win.控件组[#win.控件组];local object=c.对象;local display=object.显示;local destroy=object.销毁
  local edge=Q__.创建精灵(0,0,0,1,1);edge.置颜色(-5723992)
  local fill=Q__.创建精灵(0,0,0,1,1);fill.置颜色(-14671840)
  local tick=Q__.创建精灵(0,0,0,1,1);tick.置颜色(-1)
  object.显示=function(px,py,sx,sy,angle,color,alpha)
   display(px,py,sx,sy,angle,color,0)
   edge.显示_高级(px,py+2*sy,angle or 0,8*sx,8*sy)
   fill.显示_高级(px+sx,py+3*sy,angle or 0,6*sx,6*sy)
   if selected()then
    tick.显示_高级(px+2*sx,py+5*sy,angle or 0,sx,2*sy)
    tick.显示_高级(px+3*sx,py+6*sy,angle or 0,sx,2*sy)
    tick.显示_高级(px+4*sx,py+5*sy,angle or 0,sx,2*sy)
    tick.显示_高级(px+5*sx,py+4*sy,angle or 0,sx,2*sy)
    tick.显示_高级(px+6*sx,py+3*sy,angle or 0,sx,2*sy)
   end
   font.显示(px+9*sx,py+sy,caption,0,-1,-15724528)
  end
  object.销毁=function()edge.销毁();fill.销毁();tick.销毁();destroy()end
 end
 option('拾取出售选择_v242','拾取时自动出售','__gm_pickup_sell_v242',true,16)
 option('自动拾取选择_v242','自动拾取','__gm_auto_pickup_v242',false,29)
end
