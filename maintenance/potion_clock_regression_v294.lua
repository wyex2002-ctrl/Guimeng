local baseline = arg[3] == 'v293'
local start = 100.25

do
    local f = fixture(start)
    eq(f.E.Gly独.取运行时间(), 1, 'legacy public clock rounds native seconds')
    if not baseline then
        eq(f.E.Gly独.__gm_potion_ms_v294(), start, 'potions retain fractional milliseconds')
    end

    f.put(31, '金创药_特', 3)
    f.put(32, '魔法药_特', 3)
    f.put(33, ice, 3)
    f.put(21, '魔法药_特', 1, true)
    eq(f.manual(31), true)
    eq(f.key(21), true)
    eq(f.manual(33), true)

    f.advance(2999)
    eq(f.manual(31), false)
    eq(f.key(21), false)
    eq(f.manual(33), false)
    f.advance(1)
    for _, id in ipairs({31, 32, 33}) do
        eq(f.manual(id), not baseline, 'same three groups retried after three seconds')
        eq(f.count(id), baseline and 2 or 1)
    end
end

do
    local f = fixture(start)
    local merc = f.mercenary()
    f.U.主角HP, f.U.主角MP, merc.HP, merc.MP = 150, 150, 150, 150
    f.put(31, red, 3); f.put(32, blue, 3); f.put(33, sun, 3)
    f.mercPut(1, red, 3); f.mercPut(2, blue, 3); f.mercPut(3, sun, 3)
    f.tick()
    eq(f.count(31), 2); eq(f.count(32), 2)
    eq(f.mercCount(1), 2); eq(f.mercCount(2), 2)
    f.advance(999); f.tick()
    eq(f.count(33), 3); eq(f.mercCount(3), 3)
    f.advance(1); f.tick()
    eq(f.count(33), baseline and 3 or 2, 'hero rescue after one second')
    eq(f.mercCount(3), baseline and 3 or 2, 'mercenary rescue after one second')
    f.advance(1999); f.tick()
    eq(f.count(31), 2); eq(f.count(32), 2)
    eq(f.mercCount(1), 2); eq(f.mercCount(2), 2)
    f.advance(1); f.tick()
    eq(f.count(31), baseline and 2 or 1, 'hero red retries after three seconds')
    eq(f.count(32), baseline and 2 or 1, 'hero blue retries after three seconds')
    eq(f.mercCount(1), baseline and 2 or 1, 'mercenary red retries after three seconds')
    eq(f.mercCount(2), baseline and 2 or 1, 'mercenary blue retries after three seconds')
    eq(#f.notices, 0, 'automatic attempts stay quiet')
end

if baseline then
    print('V293_CLOCK_BUG_REPRODUCED ' .. mode)
    return
end

do
    local f = fixture(start)
    f.put(31, red, 4)
    eq(f.manual(31), true)
    eq(f.manual(31), false); eq(#f.notices, 1)
    f.advance(499)
    eq(f.manual(31), false); eq(#f.notices, 1)
    f.advance(1)
    eq(f.manual(31), false); eq(#f.notices, 2, 'half-second throttle uses the same clock')
    eq(f.count(31), 3)
end
