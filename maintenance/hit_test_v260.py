from native_test_utils import standalone,trees
from patch_v139 import ad,jump
from test_v192 import lua
from pathlib import Path

def prepare_hit_tests(work,old,new,report):
 meta=[];ids=[];treecache={id(d):trees(d)for d in list(old.values())+list(new.values())}
 for mid,idx,pc in report['hit_sites']:
  p,q=old[mid].protos[idx],new[mid].protos[idx];mp={int(k):v for k,v in report['hit_maps'][f'{mid}/{idx}'].items()}
  kind='hero'if(mid,idx)==(12,280)else'merc'if(mid,idx)==(12,18010)else'monster'if mid==12 else'basic'if mid==22 and pc==346 else'native_monster'if mid==22 else'native_hero'
  den=p.bc[pc]>>8&255;D=p.bc[pc]>>24;A=p.bc[pc+6]>>24;result=p.bc[pc+6]>>8&255
  name=f'{mid}_{idx}_{pc}';start=pc-5 if kind in['hero','merc']else pc-7 if kind=='monster'else pc-3 if kind in['native_monster','native_hero']else pc
  end=140 if kind=='merc'else pc+12 if mid==12 else pc+26 if kind=='basic'else pc+29
  roll=7 if kind in['hero','merc']else 21 if kind=='monster'else 28 if kind=='basic'else 26 if kind=='native_monster'else 17
  for label,d,proto,mapping in [('new',new[mid],q,mp),('old',old[mid],p,{i:i for i in range(p.nbc+1)})]:
   for typ,first,last,reg in [('ratio',pc,pc+8,result),('decision',start,end,roll)]:
    raw=standalone(d,treecache[id(d)],idx,{0:jump(0,mapping[first],p.frame),mapping[last]:ad('RET1',reg,2)},proto.frame)
    (work/(name+'_'+label+'_'+typ+'.ljbc')).write_bytes(raw)
  meta.append([name,kind,q.frame,A,D,den,result,idx,pc])
  if kind=='monster':ids.append(name)
 (work/'hit_meta.lua').write_bytes(('return '+lua({i+1:{j+1:(v.encode()if isinstance(v,str)else v)for j,v in enumerate(row)}for i,row in enumerate(meta)})).encode('gbk'))
 for mid,idx,name in [(14,220,'hit_public_actor'),(22,44,'hit_full_monster'),(26,29,'hit_full_hero')]:
  d=new[mid];(work/(name+'.ljbc')).write_bytes(standalone(d,treecache[id(d)],idx))
 (work/'hit_mode.ljbc').write_bytes((Path(__file__).parent/'merc_mode_v260.ljbc').read_bytes())
 src=work/'hit.lua';src.write_bytes((Path(__file__).parent/'hit_regression_v260.lua').read_text().encode('gbk'));return src
