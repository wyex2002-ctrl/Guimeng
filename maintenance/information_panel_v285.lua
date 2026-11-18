-- Use the same control and text history limit as the first story's system messages.
return function(text)
    local box = 聊天文本框
    if not box or type(box.加入文本) ~= 'function' then return end
    if box.内容高度 >= 500 then box.内容 = '' end
    box.加入文本(text)
end
