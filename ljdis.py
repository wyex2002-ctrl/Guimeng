from ljtool import *
OPS="ISLT ISGE ISLE ISGT ISEQV ISNEV ISEQS ISNES ISEQN ISNEN ISEQP ISNEP ISTC ISFC IST ISF MOV NOT UNM LEN ADDVN SUBVN MULVN DIVVN MODVN ADDNV SUBNV MULNV DIVNV MODNV ADDVV SUBVV MULVV DIVVV MODVV POW CAT KSTR KCDATA KSHORT KNUM KPRI KNIL UGET USETV USETS USETN USETP UCLO FNEW TNEW TDUP GGET GSET TGETV TGETS TGETB TSETV TSETS TSETB TSETM CALLM CALL CALLMT CALLT ITERC ITERN VARG ISNEXT RETM RET RET0 RET1 FORI JFORI FORL IFORL JFORL ITERL IITERL JITERL LOOP ILOOP JLOOP JMP FUNCF IFUNCF JFUNCF FUNCV IFUNCV JFUNCV FUNCC FUNCCW".split()
def val(v):
 if isinstance(v,bytes):return repr(v.decode('gbk','replace'))
 return str(v)
def dis(p,start=0,end=None):
 out=[f'proto {p.idx} line {p.first} params {p.params} frame {p.frame} uv {p.uv.hex()}']
 for pc in range(start,len(p.bc) if end is None else end):
  ins=p.bc[pc];op=ins&255;a=(ins>>8)&255;c=(ins>>16)&255;b=ins>>24;d=ins>>16
  name=OPS[op] if op<len(OPS) else str(op);comment=''
  if name in ('KSTR','GGET','GSET','ISEQS','ISNES','FNEW','TDUP','USETS'):comment=val(p.gc(d))
  elif name in ('TGETS','TSETS'):comment=val(p.gc(c))
  elif name in ('JMP','UCLO','FORI','FORL','ITERL','LOOP','ISNEXT'):comment=f'=> {pc+1+d-0x8000}'
  elif name=='KSHORT':comment=str(d if d<32768 else d-65536)
  out.append(f'{pc:5} {name:8} {a:3} {b:3} {c:3} D={d:5}  {comment}')
 return '\n'.join(out)
if __name__=='__main__':
 import sys
 sys.stdout.reconfigure(encoding='utf-8');d=Dump(Path(sys.argv[1]).read_bytes())
 for idx in map(int,sys.argv[2:]):print(dis(d.protos[idx]))
