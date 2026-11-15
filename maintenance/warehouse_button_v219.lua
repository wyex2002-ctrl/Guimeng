-- Installed once in the trusted native UI constructor, after all windows exist.
return function()
 local win = Sys.run('取窗口对象', 539)
 if not win then return end
 local name='远程仓库按钮'
 for _,c in ipairs(win.控件组) do if c.名称==name then return end end
 local font=__Res(2,'400132927.img')
 local text='仓库'
 local width=math.max(42,math.ceil(font.取宽度(text))+16)
 local height=17
 local image=__Res(1,'-1657209002.img',0)
 local function factory()
  local self={id=name}
  return {getself=function()return self end,Main=function()
    Ux雌.游戏音效.按键音效1.播放()
    仓库窗口.打开()
  end,鼠标焦点=function()end}
 end
 win:增加控件(10,name,230-width,20,0,width,height,'',image,
  '[控件]\n按下效果=0\n按钮类型=1\n像素检测=假\n透明色=0\n',{factory})
 local control=win.控件组[#win.控件组]
 local object=control.对象
 local original=object.显示
 -- Copy only the text-free left/right edges; stretch a blank inside column.
 -- The original NEXT glyphs are covered, never squeezed under the new caption.
 local left=D2D_精灵.创建(image,0,0,6,height)
 local middle=D2D_精灵.创建(image,6,0,1,height)
 local right=D2D_精灵.创建(image,28,0,6,height)
 local destroy=object.销毁
 object.销毁=function()left.销毁();middle.销毁();right.销毁();destroy()end
 local tw,th=font.取宽度(text),font.取高度(text)
 object.显示=function(x,y,sx,sy,angle,color,alpha)
  original(x,y,sx,sy,angle,color,alpha)
  sx=sx or 1;sy=sy or 1
  left.置颜色(color or -1);middle.置颜色(color or -1);right.置颜色(color or -1)
  left.显示_高级(x,y,angle or 0,sx,sy)
  middle.显示_高级(x+6*sx,y,angle or 0,(width-12)*sx,sy)
  right.显示_高级(x+(width-6)*sx,y,angle or 0,sx,sy)
  font.显示(x+(width-tw)*sx/2,y+(height-th)*sy/2,text,0,color or -1,-15724528)
 end
end
