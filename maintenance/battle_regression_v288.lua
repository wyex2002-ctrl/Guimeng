local elemental = {'火', '冰', '雷', '风', '神', '暗', '幻'}

local function checkPoison(manual, preferred, values)
    local s = setup('new', {skill = '普通攻击'})
    local h = s.hero
    local total = 0
    h.属性.属性集 = {}
    for i, element in ipairs(elemental) do
        local key = '攻' .. element .. '元素'
        h.自定义属性表[key] = true
        h.属性.属性集[key], h.属性['附加_' .. key] = values[i], 0
        total = total + values[i]
    end
    s.stock(31, green, 4)
    s.stock(126, red, 4)
    s.rank.位置 = preferred
    if manual then
        h.当前状态, h.硬直 = 0, 0
        h.远程目标 = s.target
        eq(s:cast(poison), true)
    else
        h.攻击目标, h.远程目标 = s.target, s.target
        attack(s)
    end
    s:step(170)
    if preferred == 1 then
        eq(assert(s.status(green)).生命值, -(s.rank.减少生命 + math.ceil(total * 2 / 5)))
    else
        local extra = assert(s.status(red))
        eq(extra.最大防御, -(s.rank.削弱防御 + total))
        eq(extra.最大魔防, extra.最大防御)
    end
end

for _, manual in ipairs({false, true}) do
    for preferred = 1, 2 do
        checkPoison(manual, preferred, {1, 2, 3, 4, 5, 6, 7})
        checkPoison(manual, preferred, {0, 0, 0, 0, 0, 0, 0})
        checkPoison(manual, preferred, {1, 2, 3, 4, 5, 0, 0})
    end
end

local steps = {{0,-1},{1,-1},{1,0},{1,1},{0,1},{-1,1},{-1,0},{-1,-1}}
local function direction(x,y,tx,ty)
    local dx,dy=tx-x,ty-y
    dx=dx==0 and 0 or dx/math.abs(dx)
    dy=dy==0 and 0 or dy/math.abs(dy)
    for i,p in ipairs(steps) do if p[1]==dx and p[2]==dy then return i end end
end

local native, db = setmetatable({}, {__index=_G}), {math=math}
local function actor(x,y,id)
    return {id=id,属性={hp=100,攻击速度倍数=1},地图格子={x=x,y=y},
        地图坐标={x=x,y=y},施法速度=1,方向=1,目标格子={x=x,y=y}}
end
local merc,target=actor(11,10,42),actor(10,10,9)
merc.绑定技能,merc.所属阵营='刺客普通攻击','友方'
target.所属阵营='敌方'
local rangedWeapon={分类='装备',子类='武器'}
local bag={[397]={道具=rangedWeapon}}
local state={屏幕事件组={merc,target},包裹物品组=bag}
native.引擎={取运行时间=function()return 0 end}
native.Sys={run=function()return true end}
local free, checked, moved
local cells = setmetatable({}, {__index=function(_, key)
    local x,y=key%32,math.floor(key/32)
    return {障碍=free(x,y) and 0 or 1}
end})
native.Q_地图={地图格子列数=20,地图格子行数=20,信息组_jit=cells,
    到逻辑格子=function(x,y)return y*32+x end,置格子信息=noop}
local lookupCell=bound('map_cell',native,native.Q_地图)
native.Q_地图.取格子信息=function(x,y,kind)
    eq(kind,'障碍')
    checked[#checked+1]={x,y}
    return lookupCell(x,y,kind)
end
merc.置位置=function(_,x,y) moved={x,y};merc.地图格子={x=x,y=y} end
local public={id=merc.id,瞬移=bound('teleport',native,{对象=merc})}
db.Ux雌={佣兵对象=public}
db.取两点间方向=direction
db.Gly独={事件对象=function()return {HP=100,地图格子=target.地图格子} end}
load('merc_install',native)(state,db)

local construct=load('merc_skill',native)
local function cast(name, dx, dy, facing, space)
    merc.地图格子={x=10+dx,y=10+dy}
    target.方向=facing
    free,checked,moved=space,{},nil
    local configuration={名称=name,施放位置='目标',位移距离=0,起手延迟=100,命中延迟=200,伤害延迟=200,脚本={}}
    local result=construct(merc,configuration,merc,target,0,{},0,1)
    assert(type(result.刷新)=='function')
    return moved
end
local any=function() return true end
local none=function() return false end
for name,r in pairs({蝉舞=4,盛开=2,白莲=2,红莲=3,月桂=3}) do
    for facing=1,8 do
        local reverse=steps[(facing+3)%8+1]
        local position=assert(cast(name,1,1,facing,any))
        eq(position[1],10+reverse[1]*r);eq(position[2],10+reverse[2]*r)
        eq(public.方向,direction(position[1],position[2],10,10))
        eq(#checked,1)
    end
    local position=assert(cast(name,0,-1,5,function(x,y) return x==11 and y==10-r end))
    eq(position[1],11);eq(position[2],10-r);eq(#checked,2)
    eq(cast(name,1,0,5,none),nil);eq(#checked,8*r)
    eq(cast(name,2,0,5,any),nil);eq(#checked,0)
end
bag[397].道具={分类='装备',子类='武器',附加={绑定技能='刺客双手攻击'}}
eq(cast('蝉舞',1,0,5,any),nil);eq(#checked,0)
bag[397].道具=rangedWeapon
target.属性.hp=0
eq(cast('蝉舞',1,0,5,any),nil);eq(#checked,0)
target.属性.hp=100
target.地图格子={x=10,y=1}
target.方向=5
merc.地图格子={x=10,y=2}
free,checked,moved=any,{},nil
construct(merc,{名称='蝉舞',施放位置='目标',位移距离=0,起手延迟=1,命中延迟=1,伤害延迟=1,脚本={}},
    merc,target,0,{},0,1)
assert(moved and moved[2]>=0 and #checked>1, 'blocked map edge falls through to an in-bounds cell')
target.地图格子={x=10,y=10}
for i=1,200 do
    local facing=(i-1)%8+1
    local position=assert(cast('红莲',1,0,facing,any))
    eq(math.max(math.abs(position[1]-10),math.abs(position[2]-10)),3)
end
-- Original Chant event pays and applies the buff before the original cast
-- reaches the same native instance constructor as the other four skills.
local chant=load('chant',db)
local chantBuffs,chantCasts=0,0
db.FXru胃啪={目标=0}
db.Ux雌.胚子考虑=function()return{佣兵操作=0}end
db.Ux雌.啾啾啵啵=function()return{佣兵={技能={蝉舞=1}}}end
db.Gly独.取出技能信息=function()return{消耗魔法=5}end
db.Gly独.取随机数=function(low)return low end
public.取状态列表=function()return{}end
public.增加状态=function(name)eq(name,'蝉舞');chantBuffs=chantBuffs+1 end
public.释放技能=function(name,id)
    eq(name,'蝉舞');eq(id,target.id)
    local dx,dy=merc.地图格子.x-10,merc.地图格子.y-10
    cast(name,dx,dy,target.方向,any)
    chantCasts=chantCasts+1
end
for _,dist in ipairs({1,2,7}) do
    public.MP=100
    merc.地图格子={x=10+dist,y=10}
    public.地图格子=merc.地图格子
    target.方向=5
    moved=nil
    chant(target.id)
    eq(public.MP,dist<=6 and 95 or 100)
    if dist==1 then eq(assert(moved)[2],6) else eq(moved,nil) end
end
eq(chantBuffs,2);eq(chantCasts,2)

local rank=load('mana_rank',db)()
eq(rank.法力转换,.17)
public.属性={最大法力值=100}
eq(load('mana_damage',db)(nil,nil,nil,nil,nil,nil,rank),17)
public.属性.最大法力值=125
eq(load('mana_damage',db)(nil,nil,nil,nil,nil,nil,rank),22)
print('BATTLE_V288_PASS',mode)
