local work,mode=arg[1],arg[2]
if mode=='hot'then jit.opt.start('hotloop=1','hotexit=1')else jit.off()end
local n=0
local function eq(a,b,m)n=n+1;assert(a==b,(m or'check')..': '..tostring(a)..' ~= '..tostring(b))end
local make=assert(loadfile(work..'/modal_fixture.lua'))()
local text='【系统赠送您1瓶祝福油，请查看背包】'
local key='__gm_oil_notice_start_v280'
local function fixture()
 local env=setmetatable({},{__index=_G});return make(work,env),env
end
for _,input in ipairs({'click','enter'})do
 local u=fixture();u.now=10;local calls=0;u.show(text,nil,function()calls=calls+1 end)
 eq(u.box.提示内容,text);eq(u.box[key],10);eq(u.box.可视,true)
 for _,at in ipairs({10,10.01,11,12.999})do u.update(at,input);eq(u.box.可视,true);eq(calls,0)end
 u.box:显示();eq(#u.draws>0,true,'original rendering still runs while waiting')
 u.update(13,input);eq(u.box.可视,false);eq(calls,1);eq(u.box[key],nil)
 u.update(14,input);eq(calls,1,'one callback only')
end
-- The no-callback gift produced by the real Gly notice must also stay open.
local u=fixture();u.show(text);u.update(2.999,'click');eq(u.box.可视,true)
u.update(3,'enter');eq(u.box.可视,false)
-- Earlier clicks are consumed, not buffered until unlocking.
u=fixture();u.show(text);u.update(1,'click');u.update(3.01);eq(u.box.可视,true)
u.update(3.02,'click');eq(u.box.可视,false)
-- A gift queued behind another prompt starts counting only when displayed.
u=fixture();u.now=5;u.show('原有提示');u.show(text);eq(#u.box.缓存组,1);eq(u.box[key],nil)
u.update(100,'enter');eq(u.box.可视,true);eq(u.box.提示内容,text);eq(u.box[key],100)
u.update(102.999,'click');eq(u.box.可视,true);u.update(103,'click');eq(u.box.可视,false)
-- Reuse, cancel and normal prompt behavior retain their original timing.
u=fixture();u.show(text);u.show('后续普通提示');u.update(3,'enter')
eq(u.box.提示内容,'后续普通提示');eq(u.box[key],nil);u.update(3,'enter');eq(u.box.可视,false)
for i=1,200 do
 u=fixture();u.now=i*10;u.show(text);u.update(i*10+2.999,'enter');eq(u.box.可视,true)
 u.update(i*10+3,'click');eq(u.box.可视,false)
 u.show('普通确定');u.update(i*10+3,'click');eq(u.box.可视,false,'ordinary prompt remains immediate')
end
u=fixture();local yes,no=0,0
u.show('普通选择','确定取消',function()yes=yes+1 end,function()no=no+1 end)
u.update(0,'cancel');eq(no,1);eq(yes,0);eq(u.box.可视,false)
u.show(text,'确定取消',function()yes=yes+1 end);u.update(0,'enter');eq(yes,1,'only gift one-button prompt delayed')
if mode=='hot'then eq(jit.status(),true)end
print('MODAL_V280_PASS',mode,n,'actual modal class/init/show/update/close/render; finite engine/input/graphics')
