return function()
    -- The native clock returns fractional seconds. The shared potion
    -- scheduler records milliseconds and needs subsecond precision.
    return 引擎:取运行时间() * 1000
end
