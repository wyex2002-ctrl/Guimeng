return function(C)
  pcall(function()
    local out=Sys.get('__gm_diag_checkpoint_v159')
    if type(out)=='function' then out('diagnostics.attach.v179',C) end
  end)
end
