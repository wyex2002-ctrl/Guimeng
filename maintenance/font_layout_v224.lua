-- Existing type-2 glyph-layout renderer; optional scale is used only by portals.
return function(layout,x,y,color,outline,scale)
 if outline==nil then outline=-1234567 end
 if not scale or scale==1 then
  for i=1,#layout do
   local glyph=layout[i]
   __Sprite.显示2(glyph[1],outline,color,glyph[2]+x,glyph[3]+y)
  end
  return
 end
 for i=1,#layout do
  local glyph=layout[i];local gx=x+glyph[2]*scale;local gy=y+glyph[3]*scale
  if outline and outline~=-1234567 then
   __Sprite.置渲染色(glyph[1],outline)
   __Sprite.显示_高级(glyph[1],gx-1,gy,0,scale,scale)
   __Sprite.显示_高级(glyph[1],gx+1,gy,0,scale,scale)
   __Sprite.显示_高级(glyph[1],gx,gy-1,0,scale,scale)
   __Sprite.显示_高级(glyph[1],gx,gy+1,0,scale,scale)
  end
  __Sprite.置渲染色(glyph[1],color)
  __Sprite.显示_高级(glyph[1],gx,gy,0,scale,scale)
 end
end
