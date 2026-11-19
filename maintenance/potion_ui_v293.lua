return function(mode, data)
    if not Ae冻 or Ae冻.版本选择 ~= '来世续缘' then return end
    if mode == 1 then
        if data.标识 == '道具CD' then return true end
    elseif data.名称 == '太阳水' or data.名称 == '强效太阳水' or data.名称 == '万年雪霜' then
        return data.道具说明 .. '\n#md与红蓝药冷却独立。'
    end
end
