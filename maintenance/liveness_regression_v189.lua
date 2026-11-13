local work,mode=arg[1],arg[2]or'normal'
if mode=='hot'then require('jit.opt').start('hotloop=1','hotexit=1')end
local function run(which)
 jit.flush()
 local n=0
 local controls={}
 local slots={[31]={['道具']={['名称']='药水'}},[32]={['道具']={['名称']='药水'}}}
 local item=slots[31]
 for _,id in ipairs({31,32})do controls[#controls+1]={['类型']=6,['格子ID']=id,['对象']={['使用物品']=function()n=n+1;return true end}}end
 local S={['Hero']={['背包格子']={{31,0,true},{32,0,true}}},['包裹物品组']=slots,['界面_窗口_数组']={{['控件组']=controls}}}
 local f=assert(loadfile(work..'/'..which..'.ljbc'));debug.setupvalue(f,1,S)
 local i
 local ok,err=pcall(function()
 for j=1,20000 do
  i=j
  if j%50==0 then slots[31]=nil else slots[31]=item end
  assert(f('药水')==true,'bad return')
 end
 end)
 print(which,ok,i,tostring(err),n)
 if which=='use_old'then assert(not ok,'v188 liveness fault not reproduced')else assert(ok,err);assert(n==20000)end
end
run('use_old');run('use')
print('LIVENESS_V189_PASS',mode)
