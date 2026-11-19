return function(operation, cell, item)
    if not Ae冻 or Ae冻.版本选择 ~= '来世续缘' then return end
    local _, handled = Sys.run('qs_item_box', {-293, cell.标识, item.名称, operation, item.显示名})
    return handled
end
