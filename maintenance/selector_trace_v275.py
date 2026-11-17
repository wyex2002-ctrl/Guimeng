"""Keep selector decisions intact; fix diagnostic scratch and JMP live ranges."""
from ljdis import OPS
from ljtool import Proto
from patch_v139 import rebuild_proto,ad
from bytecode_relocate import replace_instructions

TESTS=set('ISLT ISGE ISLE ISGT ISEQV ISNEV ISEQS ISNES ISEQN ISNEN ISEQP ISNEP ISTC ISFC IST ISF'.split())
BRANCH=set('JMP UCLO FORI FORL ITERL LOOP ISNEXT'.split())
def flow(p):
 n=len(p.bc);reads=[];writes=[];edges=[]
 for pc,x in enumerate(p.bc):
  op=OPS[x&255];a=x>>8&255;b=x>>24;c=x>>16&255;v=x>>16;r=set();w=set();out=[pc+1]if pc+1<n else[]
  if op in {'MOV','NOT','UNM','LEN'}:r={v};w={a}
  elif op in {'KSTR','KSHORT','KNUM','KPRI','UGET','GGET','TNEW','TDUP'}:w={a}
  elif op=='KNIL':w=set(range(a,v+1))
  elif op in {'TGETS','TGETB'}:r={b};w={a}
  elif op=='TGETV':r={b,c};w={a}
  elif op in {'TSETS','TSETB'}:r={a,b}
  elif op=='TSETV':r={a,b,c}
  elif op in {'GSET','TSETM'}:r={a}
  elif op=='USETV':r={v}
  elif op.startswith(('ADD','SUB','MUL','DIV','MOD','POW')):
   w={a};r={b,c}if op.endswith('VV')else{b}if op.endswith('VN')else{c}
  elif op=='CAT':r=set(range(b,c+1));w={a}
  elif op in {'ISLT','ISGE','ISLE','ISGT','ISEQV','ISNEV'}:r={a,v}
  elif op in {'ISEQS','ISNES','ISEQN','ISNEN','ISEQP','ISNEP'}:r={a}
  elif op in {'IST','ISF','ISTC','ISFC'}:r={v} # Conditional copies are conservative.
  elif op=='CALL':
   assert b>0 and c>0;r=set(range(a,a+c));w=set(range(a,p.frame))
  elif op=='RET0':out=[]
  elif op in {'RET1','RET'}:r=set(range(a,a+(1 if op=='RET1'else v-1)));out=[]
  elif op in {'FORI','FORL'}:r=set(range(a,a+3));w={a,a+3}
  elif op=='ITERC':r=set(range(a-3,a));w=set(range(a,a+b-1))
  elif op=='ITERL':r={a};w={a-1}
  elif op in {'JMP','UCLO','LOOP','ISNEXT'}:pass
  else:raise AssertionError((pc,op))
  if op in TESTS:out=[pc+1,pc+2]
  if op in BRANCH:
   target=pc+1+v-32768
   out=[target]if op in {'JMP','UCLO','ISNEXT'}else list(set(out+[target]))
  assert all(0<=i<n for i in out),(pc,op,out)
  reads.append(r);writes.append(w);edges.append(out)
 live=[set()for _ in range(n)]
 while True:
  changed=False
  for pc in range(n-1,-1,-1):
   val=reads[pc]|(set().union(*(live[t]for t in edges[pc]))-writes[pc])
   if val!=live[pc]:live[pc]=val;changed=True
  if not changed:break
 return live,edges

def repair(p):
 assert p.params==1 and p.frame==40 and p.nbc==1340
 original=list(p.bc);replacements={};probe_map={}
 # Each block has the same operations, constants and branch destinations. Only
 # diagnostic temporaries move down beside the live values of that boundary.
 blocks=[(1131,1162,1),(1162,1193,4),(1193,1225,3),(1225,1246,17),(1246,1267,17),(1267,1309,26),(1309,1340,7)]
 for start,end,base in blocks:
  probe_map[str(start)]=base
  def reg(v):return v-32+base if 32<=v<=35 else v
  for pc in range(start,end):
   x=original[pc];op=OPS[x&255];a=x>>8&255;b=x>>24;c=x>>16&255;v=x>>16
   if op in {'GGET','KSTR','CALL'}:a=reg(a)
   elif op in {'MOV'}:a=reg(a);v=reg(v);b=v>>8;c=v&255
   elif op=='TGETS':a=reg(a);b=reg(b)
   elif op in {'ISNES','ISLT','ISGT'}:
    a=reg(a)
    if op!='ISNES':v=reg(v);b=v>>8;c=v&255
   elif op=='ISF':v=reg(v);b=v>>8;c=v&255
   elif op in {'KSHORT','UGET','IST','TGETS','JMP'}:pass
   else:raise AssertionError((pc,op))
   # KSHORT is used for the event flag limits in the diagnostic block.
   if op=='KSHORT':a=reg(a)
   replacements[pc]=[(x&255)|(a<<8)|(c<<16)|(b<<24)]
 # Entry/dispatch blocks have no holes. The selector keeps R8=nil across its
 # optional target branch; R9..23 are dead before selection, and after release.
 replacements[1225]=[ad('KNIL',4,31)]+replacements[1225]
 replacements[1222]=[ad('KNIL',3,31)]+replacements[1222]
 replacements[1245]=[ad('KNIL',17,31)]+replacements[1245]
 replacements[1267]=[ad('KNIL',9,23)]+replacements[1267]
 # Native fallback does not define R6 on flag1. Its log value used to read a
 # stale slot. R3=function/R4=self are the only original call inputs here.
 replacements[1309]=[ad('KNIL',5,6)]+replacements[1309]
 raw,mp=replace_instructions(p,replacements);q=Proto(raw,p.idx)
 # Branches carried inside replacement fragments need explicit relocation;
 # replace_instructions relocates untouched original branches only.
 for pc,fragment in replacements.items():
  x=original[pc]
  if OPS[x&255]in BRANCH:
   at=mp[pc]+len(fragment)-1;target=pc+1+(x>>16)-32768
   q.bc[at]=(q.bc[at]&65535)|((mp[target]-at-1+32768)<<16)
 live,edges=flow(q);cuts=[]
 for pc,x in enumerate(q.bc):
  if OPS[x&255]!='JMP':continue
  target=edges[pc][0];needed=set(live[target])
  if pc and OPS[q.bc[pc-1]&255]in TESTS and pc+1<len(q.bc):needed|=live[pc+1]
  keep=max(needed,default=-1)+1
  assert 0<=keep<=q.frame,(pc,keep,q.frame)
  old=x>>8&255
  if keep!=old:q.bc[pc]=(x&~0xff00)|(keep<<8);cuts.append([pc,old,keep])
 # Core instructions and each original target are checked again by the test;
 # A is JIT liveness metadata, not a change to the selector's decisions.
 return Proto(rebuild_proto(q),q.idx),{'map':mp,'probes':probe_map,'cuts':cuts,'original_instructions':len(original),'instructions':q.nbc}
