"""Extract map-label destinations from the existing portal scripts, without running them."""
import re
from collections import defaultdict
from ljdis import OPS
from patch_v196 import number_pool

def child_refs(d):
 stack=[];refs={}
 for p in d.protos:
  for j,k in enumerate(p.kgc):
   if k==('child',):refs[p.idx,p.nkgc-1-j]=stack.pop()
  stack.append(p.idx)
 return refs

def extract(d):
 refs=child_refs(d);events={};portals={}
 for p in d.protos:
  text=next((k.decode('gbk')for k in p.kgc if isinstance(k,bytes)and k.startswith('【事件/'.encode('gbk'))and len(k)<200),None)
  if not text:continue
  found=re.fullmatch(r'【事件/(.+)/(\d+)/(默认脚本|回调脚本)】',text)
  if not found:continue
  source,ident,kind=found.groups();ident=int(ident);events.setdefault(ident,{})[kind]=p.idx
  if kind=='回调脚本':
   for ins in p.bc:
    if OPS[ins&255]=='FNEW'and '地图标识_传送'.encode('gbk')in d.protos[refs[p.idx,ins>>16]].kgc:portals[ident]=source
 # Fixed-ID dispatcher: use the existing numeric constants, not their indices.
 p=d.protos[6488];nums=number_pool(p);routes=defaultdict(set);ident=None;proof=[]
 for pc,ins in enumerate(p.bc):
  op=OPS[ins&255];a=(ins>>8)&255;c=(ins>>16)&255
  if op in ['ISEQN','ISNEN']and pc:
   prev=p.bc[pc-1]
   if OPS[prev&255]=='TGETS'and p.gc((prev>>16)&255)==b'id':ident=int(nums[ins>>16])
  if op=='TGETS'and p.gc(c)=='地图坐标'.encode('gbk'):
   for j in range(pc+1,min(pc+7,p.nbc)):
    x=p.bc[j]
    if OPS[x&255]=='KSTR'and ((x>>8)&255)==a+3:
     name=p.gc(x>>16).decode('gbk');routes[ident].add(name);proof.append((ident,name,pc))
 # These IDs share an OR branch (the final ID alone isn't its full condition).
 group=[int(nums[i])for i in range(21,27)]
 assert set(group)=={1368,1369,1370,1371,1372,1441},group
 assert p.gc(p.bc[466]>>16)=='魔灵迷阵'.encode('gbk')
 for ident in group:routes[ident]={'魔灵迷阵'}
 # Dynamic maze routing increments the selected counter before deciding. The
 # display resolver mirrors that decision read-only, including staying in-map.
 dynamic={1373,1374,1375,1376}
 # Ship entrance dialogs have their destination in a child action callback.
 for ident in [1301,1329,1330,1331]:
  root=d.protos[events[ident]['默认脚本']];children=[root.idx];seen=set()
  while children:
   idx=children.pop();seen.add(idx)
   children += [v for (parent,_),v in refs.items()if parent==idx and v not in seen]
  assert any('神舰'.encode('gbk')in d.protos[i].kgc and '地图坐标'.encode('gbk')in d.protos[i].kgc for i in seen)
  routes[ident]={'神舰'}
 result={}
 for ident in portals:
  if ident in dynamic:result[ident]='@maze'
  else:
   assert len(routes[ident])==1,(ident,portals[ident],routes[ident])
   result[ident]=next(iter(routes[ident]))
 assert len(result)==len(portals)==99
 return result,{'portal_count':len(portals),'dynamic_ids':sorted(dynamic),'sources':portals,'fixed_dispatch_prototype':6488,'fixed_call_evidence':proof,'maze_return_group':group}
