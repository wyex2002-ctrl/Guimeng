local single, group = '治愈术', '群体治愈术'
local elements = {'火', '冰', '雷', '风', '神', '暗', '幻'}
for _, mid in ipairs({12,14,22,26,30}) do
    assert(loadfile(work..'/module_'..mid..'.ljbc'))
end

local function fixture(story, useLow, instant, wellness)
    local s = setup('new', {skill = single})
    local E, N, h = s.db, s.env, s.hero
    N.Ae冻, E.Ux雌.版本选择 = E.Ux雌, story
    N.Ae冻.地图id = 100
    h.属性.hp, h.属性.maxhp, h.属性.属性集 = 1000, 1000, {}
    h.属性.附加 = {}
    h.增加状态 = load('hero_add_status', N)
    for i, element in ipairs(elements) do
        local key = '攻' .. element .. '元素'
        h.自定义属性表[key] = true
        h.属性.属性集[key], h.属性['附加_' .. key] = i, 0
    end
    local role = {技能 = {[single]={0}, [group]={0}, [poison]={0}}}
    if instant ~= nil then role.技能.瞬回术 = {instant} end
    if wellness ~= nil then role.技能.养生术 = {wellness} end
    E.Ux雌.啾啾啵啵 = function()return role end
    E.Ux雌.主角攻神元素 = 999
    E.Ux雌.主角最小自然, E.Ux雌.主角最大自然 = 10, 20
    E.Ux雌.主角最小灵魂, E.Ux雌.主角最大灵魂 = 10, 20
    local rolls={}
    E.Gly独.取随机数=function(lo,hi) rolls[#rolls+1]={lo,hi};return useLow and lo or hi end
    N.max=math.max
    N.lookupHelixNumber=load('helix',N)
    N.判断是否在攻击范围=load('native_range',N)
    local merc,p1,p2=s.add(5,2,0),s.add(6,3,0),s.add(7,4,0)
    for _, unit in ipairs({merc,p1,p2}) do
        unit.所属阵营='友方'
        unit.属性.hp, unit.属性.maxhp = 500, 500
    end
    p1.宠物配置={主人=h}
    p2.主人id=0
    N.Ae冻.佣兵对象={id=5}
    s.owner.游戏状态组[single]={name=single,不可叠加=true,脚本=load('heal_status',E)()}
    for name, proto in pairs({[single]='heal_single',[group]='heal_group'}) do
        local skill=s.skills[name]
        skill.脚本=load(proto,E)()
        load('rank_update',E)(name)
        h:技能配置(name)
        h.技能信息[name].可用=true
    end
    local slot=load('skill_slot',N)
    s.press=function()
        return slot({Hero=h,绑定技能=single})
    end
    s.hover=function(unit) N.Ae冻集.鼠标焦点事件对象=unit end
    s.merc,s.p1,s.p2,s.rolls,s.role=merc,p1,p2,rolls,role
    return s
end

local function treatment(s, target)
    local hp=s.hero.属性.mp
    s.hero.攻击目标,s.hero.远程目标=s.target,s.target
    eq(s.press(),true,'native shortcut accepted')
    eq(upstate(s).目标,target,'native release retained target reference')
    eq(s.hero.攻击目标,s.target);eq(s.hero.远程目标,s.target)
    assert(s.hero.属性.mp<hp, 'native mana cost')
    return upstate(s)
end

for _, story in ipairs({'前尘忆梦','来世续缘'}) do
    for _, which in ipairs({'merc','p1'}) do
        local s=fixture(story,true)
        s.hero.属性.hp=800
        s.hover(s[which])
        treatment(s,s[which])
        s.hover(s.p2)
        s.move(s[which],5,1)
        s:step(140)
        eq(#s.effects,1)
        eq(s.effects[1].who,s[which].id)
    end
    for _, leave in ipairs({false,true}) do
        local s=fixture(story,true)
        local h=s.hero
        h.__gm_melee_state_v208={ready=false}
        s.hover(s.p1)
        eq(s.press(),false)
        eq(h.下次技能,single)
        eq(#h.释放技能组,0)
        h.__gm_melee_state_v208=nil
        s.hover(s.p2)
        if leave then s.p1.已经消失=true end
        eq(h:技能释放(single,true,s.target,true),not leave)
        eq(h.__gm_heal_pending_v289,nil)
        if leave then
            eq(#h.释放技能组,0)
        else
            eq(upstate(s).目标,s.p1)
            s:step(140)
            eq(s.effects[1].who,s.p1.id)
        end
    end
    local choices={
        {800,100,50,50,'hero'}, {1000,200,300,310,'merc'},
        {1000,400,100,150,'p1'}, {1000,500,500,500,'hero'},
        {1000,0,300,100,'p2'}, {1000,200,200,200,'merc'},
        {1000,500,100,100,'p1'},
    }
    for _, choice in ipairs(choices) do
        local s=fixture(story,true)
        s.hero.属性.hp,s.merc.属性.hp,s.p1.属性.hp,s.p2.属性.hp=unpack(choice,1,4)
        s.hover(s.target)
        treatment(s,s[choice[5]])
        s:step(140)
        eq(s.effects[1].who,s[choice[5]].id)
    end
    for _, invalid in ipairs({'dead','removed','reused','map','mapid','distant','npc'}) do
        local s=fixture(story,true)
        local target=s.p1
        s.hover(target)
        if invalid=='distant' then
            s.move(target,20,0)
            eq(s.press(),false)
            eq(#s.hero.释放技能组,0)
        elseif invalid=='npc' then
            target.宠物配置={}
            treatment(s,s.hero)
        else
            treatment(s,target)
            if invalid=='dead' then target.属性.hp=0
            elseif invalid=='removed' then target.已经消失=true
            elseif invalid=='reused' then
                for i,a in ipairs(s.owner.屏幕事件组) do
                    if a==target then table.remove(s.owner.屏幕事件组,i);break end
                end
                s.add(target.id,3,0).所属阵营='友方'
            elseif invalid=='map' then s.env.Q_地图={}
            else s.env.Ae冻.地图id=101 end
            s:step(140)
            eq(#s.effects,0,invalid)
            eq(#s.hero.释放技能组,0)
        end
    end
end

local function effect(s, name, original)
    local args={0,{s.p1.id},0,0}
    local script=original or s.skills[name].脚本
    local callback=script.技能命中
    s.env.Sys.run('fun',callback,args)
    return s.effects[#s.effects].extra
end

for _, story in ipairs({'前尘忆梦','来世续缘'}) do
    for _, low in ipairs({false,true}) do
        local s=fixture(story,low)
        local f=effect(s,single)
        eq(f.持续时间,5)
        local found=false
        for _, roll in ipairs(s.rolls) do if roll[1]==23 and roll[2]==28 then found=true end end
        eq(found,true,'seven elements produce original 80 to 100 percent bounds')
        local base=f.生命值
        local U=s.db.Ux雌
        local oldSingle=load('heal_single_old',s.db)()
        local oldGroup=load('heal_group_old',s.db)()
        U.主角攻神元素=28
        eq(effect(s,single,oldSingle).生命值,base,'original formula with equivalent element input')
        U.主角攻神元素=999
        for level=0,5 do
            s.role.技能.瞬回术={level}
            local nextEffect=effect(s,single)
            eq(nextEffect.持续时间,1)
            eq(nextEffect.生命值,base*(level+2))
            s.role.技能.养生术={2}
            eq(effect(s,single).生命值,base*(level+5))
            s.role.技能.养生术=nil
        end
        s.role.技能.瞬回术=nil
        s.role.技能.养生术={2}
        eq(effect(s,single).生命值,base*4)
        local a=effect(s,group)
        U.主角攻神元素=28
        eq(effect(s,group,oldGroup).生命值,a.生命值,'original group formula with equivalent element input')
        U.主角攻神元素=999
        s.hero.属性['附加_攻火元素']=10
        local b=effect(s,group)
        U.主角攻神元素=38
        eq(effect(s,group,oldGroup).生命值,b.生命值,'group uses live bonus')
        assert(b.生命值>a.生命值)
        eq(a.持续时间,b.持续时间)
        local prior=#s.effects
        s.env.Sys.run('fun',s.skills[group].脚本.技能命中,{0,{s.p1.id,s.p2.id},0,0})
        eq(#s.effects,prior+2)
        eq(s.effects[prior+1].who,s.p1.id)
        eq(s.effects[prior+2].who,s.p2.id)
    end
end

local results, rolls={},0
local templates={}
local names={'金创药_小','Q金创药_小','金创药_特大_包','魔法药_大','Q魔法药_小',
    '魔法药_特_包','回城卷','回城卷_包','太阳水','随机卷','金币_小','木剑'}
local rows={}
for i,name in ipairs(names) do
    templates[i]={名称=name,叠加=i%2,附加={},属性={}}
    rows[i]={道具标识=i,最小几率=1,掉落数量=1}
end
local D=setmetatable({table=setmetatable({copy=function(v)
    local copy={} for k,x in pairs(v) do copy[k]=x end return copy
end},{__index=table})},{__index=_G})
D.引擎={置随机数种子=noop,取随机整数=function()rolls=rolls+1;return 1 end}
D.Q_地图={取格子信息=function()return 0 end}
D.lookupHelixNumber=function(x,y)return math.abs(x)*13+math.abs(y) end
D.Sys={get=function(op,id)eq(op,'item');return templates[id] end,run=function(op,...)
    local args={...}
    if op=='数据保护' then return args[1] end
    if op=='掉落物前置处理' then return false,args[4],args[3] end
    eq(op,'掉落物品')
    results[#results+1]=args[2].名称
end}
load('monster_drop',D)({id=77,宠物配置={},地图格子={x=10,y=10},属性={掉宝数据表=rows,掉宝倍数=1}})
eq(rolls,#names)
eq(table.concat(results,','),'太阳水,随机卷,金币_小,木剑')

local function sale(story)
    local bank,role={金币=100},{鸡皮={100,101,1},胶布香港={100,101,0,1}}
    local messages={}
    local U={啾啾啵啵=function()return role end,人物选择=1,窗口相关={},
        游戏音效={金币音效={播放=noop}},托管显示={屏幕提示=function(m)messages[#messages+1]=m end}}
    local E=setmetatable({Ux雌=U,FXru胃啪=bank,格式化数值=tostring,
        Q金币标签1={},Q金币标签2={},金币标签={},包裹声望标签={},声望标签={},
        Gly独={取随机数=function()return 1 end},L常量={颜色_黄=-256}},{__index=_G})
    E._G=E
    E.Ae冻集={屏幕焦点=true}
    E.Q_提示框={可视=false}
    local window={可视=true}
    local hero={背包格子={{31,0,true},{32,0,true},{33,0,true}}}
    local models={[31]={道具={名称='木剑',分类='装备',价格=11}},
                  [32]={道具={名称='治愈术',分类='道具',价格=19,数量=2}},
                  [33]={道具={名称='木剑',分类='装备',价格=11,禁止出售=true}}}
    local boxes={}
    for id,model in pairs(models) do boxes[id]={重置道具=function()model.道具=nil end} end
    E.Sys={get=function(key)
        if key=='hero' then return hero end
        if key=='item_arr' then return models end
        return {}
    end}
    E.Gly独.取控件对象=function(name)if name=='背包窗口' then return window end end
    E.Gly独.从ID取格子=function(id)return boxes[id]end
    local prompt
    E.Gly独.询问=function(text,confirm)
        prompt=text;E.Q_提示框.可视=true;E.Q_提示框.确定_回调方法=confirm
    end
    local currency=load(story=='前尘忆梦' and 'currency_early' or 'currency_late',E)
    if story=='来世续缘' then debug.setupvalue(currency,1,{}) end
    U.窗口相关.界面切换=currency
    local dispatch=setfenv(assert(loadfile(work..'/bag_sale.lua')),E)()
    local function upvalue(fn,key)
        for i=1,32 do
            local name,value=debug.getupvalue(fn,i)
            if name==key then return value,i end
        end
    end
    local tick=assert(upvalue(dispatch,'tick'))
    local _, index=upvalue(tick,'buttonRequest')
    assert(debug.setupvalue(tick,index,{hero=hero,window=window}))
    eq(dispatch(U,E.Gly独,false),true)
    assert(prompt:find('合计获得：26金币',1,true))
    E.Q_提示框.确定_回调方法()
    eq(#messages,1);eq(messages[1],'已出售3件物品，获得26金币')
    eq(story=='前尘忆梦' and role.鸡皮[1] or bank.金币,126)
    eq(models[31].道具,nil);eq(models[32].道具,nil);assert(models[33].道具)
end
sale('前尘忆梦')
sale('来世续缘')
print('TREATMENT_LOOT_V289_PASS',mode,checks)
