from ljdis import *
import hashlib,json,zipfile
W=Path(__file__).resolve().parent
KEY=b'__gm_cisha_target_v139'
def encstr(x):return uleb(len(x)+5)+x
def gcid(p,s):
 if isinstance(s,str):s=s.encode('gbk')
 for i,v in enumerate(p.kgc):
  if v==s:return p.nkgc-1-i
 p.kgc.insert(0,s);p.kraw.insert(0,encstr(s));p.nkgc+=1
 return p.nkgc-1

def abc(op,a,b,c):return OPS.index(op)|(a<<8)|(c<<16)|(b<<24)
def ad(op,a,d):return OPS.index(op)|(a<<8)|((d&65535)<<16)
def jump(pc,to,a=0):
 assert -32768<=to-pc-1<=32767
 return ad('JMP',a,to-pc-1+32768)
class Asm:
 def __init__(self,p):self.p=p;self.base=len(p.bc);self.ins=[];self.labels={};self.fix=[]
 def emit(self,op,a=0,d=0,b=None,c=None):
  self.ins.append(ad(op,a,d) if b is None else abc(op,a,b,c))
 def get(self,a,b,key):self.emit('TGETS',a,b=b,c=gcid(self.p,key))
 def set(self,a,b,key):self.emit('TSETS',a,b=b,c=gcid(self.p,key))
 def const(self,a,s):self.emit('KSTR',a,gcid(self.p,s))
 def glob(self,a,s):self.emit('GGET',a,gcid(self.p,s))
 def mark(self,label):self.labels[label]=self.base+len(self.ins)
 def jmp(self,label,a=0,op='JMP'):
  self.fix.append((len(self.ins),op,a,label));self.ins.append(0)
 def finish(self):
  for i,op,a,label in self.fix:
   to=self.labels[label] if isinstance(label,str) else label
   self.ins[i]=ad(op,a,to-(self.base+i)-1+32768)
  self.p.bc.extend(self.ins)

def rebuild_proto(p):
 # Keep numeric constants and existing source/variable records exactly. Extend
 # lineinfo for appended trampoline instructions without relocating original PCs.
 r=Reader(p.raw[p.kend:])
 for i in range(p.nkn):
  x=r.u()
  if x&1:r.u()
 numeric=p.raw[p.kend:p.kend+r.p];debug=p.raw[p.kend+r.p:]
 old_nbc=p.nbc
 extra=len(p.bc)-old_nbc
 if p.ndbg:
  width=1 if p.lines<256 else 2 if p.lines<65536 else 4
  line_len=width*old_nbc
  assert len(debug)==p.ndbg
  debug=debug[:line_len]+bytes(width*extra)+debug[line_len:]
 header=bytes([p.flags,p.params,p.frame,p.nuv])+uleb(p.nkgc)+uleb(p.nkn)+uleb(len(p.bc))+uleb(len(debug))
 if debug:header+=uleb(p.first)+uleb(p.lines)
 return header+struct.pack('<'+'I'*len(p.bc),*p.bc)+p.uv+b''.join(p.kraw)+numeric+debug

def rebuild_dump(d,changed):
 chunks=[d.header]
 for p in d.protos:
  raw=rebuild_proto(p) if p.idx in changed else p.raw
  chunks.extend((uleb(len(raw)),raw))
 chunks.append(b'\0')
 return b''.join(chunks)

def build():
 d=Dump((W/'module_29.ljbc').read_bytes())
 # At skill-instance construction, param 2 is the actual launch target passed
 # from hero attack -> skill release. The native code later replaces its anchor
 # with the caster for self-centred area attacks; keep the target separately.
 p=d.protos[54]
 assert p.gc((p.bc[4]>>16)&255)=='子弹角度'.encode('gbk')
 original=p.bc[4];a=Asm(p);start=a.base
 a.get(8,0,'对象');a.get(8,8,'名称')
 a.emit('ISNES',8,gcid(p,'刺杀剑术'));a.jmp('done')
 a.set(2,7,KEY)
 a.mark('done');a.ins.append(original);a.jmp(5);a.finish();p.bc[4]=jump(4,start)
 # After native grid collection and before effects/damage consume the list:
 # deduplicate all area results, then add the original living, valid enemy.
 p=d.protos[53];assert p.bc[1336]==ad('UGET',3,0)
 a=Asm(p);start=a.base
 a.emit('UGET',3,0);a.get(4,3,'技能信息');a.get(4,4,'对象');a.get(4,4,'名称')
 a.emit('ISNES',4,gcid(p,'刺杀剑术'));a.jmp('done')
 a.get(4,3,'命中目标组');a.emit('TNEW',5,0);a.emit('TNEW',6,0)
 a.emit('KSHORT',7,1);a.emit('LEN',8,4);a.emit('KSHORT',9,1);a.jmp('afterloop',7,'FORI')
 a.mark('loop');a.emit('TGETV',11,b=4,c=10);a.emit('TGETB',12,b=11,c=1)
 a.emit('ISEQP',12,0);a.jmp('next')
 a.emit('TGETV',13,b=6,c=12);a.emit('IST',d=13);a.jmp('next')
 a.emit('KPRI',13,2);a.emit('TSETV',13,b=6,c=12)
 a.glob(12,'table');a.get(12,12,'insert');a.emit('MOV',13,5);a.emit('MOV',14,11);a.emit('CALL',12,b=1,c=3)
 a.mark('next');a.jmp('loop',7,'FORL');a.mark('afterloop')
 a.set(5,3,'命中目标组')
 a.get(4,3,KEY)
 a.glob(12,'type');a.emit('MOV',13,4);a.emit('CALL',12,b=2,c=2)
 a.emit('ISNES',12,gcid(p,'table'));a.jmp('done')
 a.get(12,4,'id');a.emit('ISEQP',12,0);a.jmp('done')
 a.get(12,4,'已经消失');a.emit('IST',d=12);a.jmp('done')
 a.get(12,4,'是否有效');a.emit('ISEQP',12,1);a.jmp('done')
 a.get(12,4,'不可选中');a.emit('IST',d=12);a.jmp('done')
 a.get(12,4,'所属阵营');a.emit('ISNEV',12,1);a.jmp('done')
 a.get(7,4,'属性');a.glob(12,'type');a.emit('MOV',13,7);a.emit('CALL',12,b=2,c=2)
 a.emit('ISNES',12,gcid(p,'table'));a.jmp('done')
 a.get(7,7,'hp');a.glob(12,'type');a.emit('MOV',13,7);a.emit('CALL',12,b=2,c=2)
 a.emit('ISNES',12,gcid(p,'number'));a.jmp('done')
 a.emit('KSHORT',8,0);a.emit('ISGE',8,7);a.jmp('done')
 a.emit('TGETV',12,b=6,c=4);a.emit('IST',d=12);a.jmp('done')
 a.emit('TNEW',7,3);a.emit('TSETB',4,b=7,c=1);a.emit('KSHORT',8,100);a.emit('TSETB',8,b=7,c=2)
 a.glob(12,'table');a.get(12,12,'insert');a.emit('MOV',13,5);a.emit('MOV',14,7);a.emit('CALL',12,b=1,c=3)
 a.mark('done');a.emit('UGET',3,0);a.jmp(1337);a.finish();p.bc[1336]=jump(1336,start)
 b29=rebuild_dump(d,{53,54});(W/'module_29_v139.ljbc').write_bytes(b29)
 # Decode the existing skill configuration, retaining every other setting,
 # line ending and the original eight facing-direction order.
 db=Dump((W/'module_36.ljbc').read_bytes());p=db.protos[6464];k=p.nkgc-1-722;s=p.kgc[k]
 assert s[-1:]==b'*';body=bytes(x^16 for x in bytes.fromhex(s[:-33].decode('ascii')))
 assert hashlib.md5(body).hexdigest().upper().encode()==s[-33:-1]
 rows=body.split(b'\r\n');key='作用范围='.encode('gbk');hits=[i for i,row in enumerate(rows) if row.startswith(key)];assert len(hits)==1
 idx=hits[0];old=rows[idx][len(key):].split(b'&');assert len(old)==8
 new=[]
 for cells in old:
  grid=cells.split(b'|');assert len([x for x in grid if x])==4
  new.append(b'|'.join(grid[:2])+b'|')
 rows[idx]=key+b'&'.join(new);fresh=b'\r\n'.join(rows)
 news=bytes(x^16 for x in fresh).hex().upper().encode()+hashlib.md5(fresh).hexdigest().upper().encode()+b'*'
 p.kgc[k]=news;p.kraw[k]=encstr(news)
 b36=rebuild_dump(db,{6464});(W/'module_36_v139.ljbc').write_bytes(b36)
 (W/'cisha_config_v139.txt').write_bytes(fresh)
 # Replace only those two module constants, encrypt and preserve the tail.
 outer=Dump((W/'patch.ljbc').read_bytes());meta=json.loads((W/'modules.json').read_text(encoding='utf8'))
 for m,b in [(29,b29),(36,b36)]:
  info=meta[m];op=outer.protos[info['outer_proto']];ki=info['kgc']
  packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(b))+zlib.compress(b,9)
  coded=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30')).hex().upper().encode('ascii')
  op.kgc[ki]=coded;op.kraw[ki]=encstr(coded)
 out=rebuild_dump(outer,{0});res=rc4(out,b'_Npi_dest__cc_&%_23')+(W/'patch.res').read_bytes()[-10:]
 (W/'game_v139.res').write_bytes(res)
 print(json.dumps({'version':'v1.139','bytes':len(res),'sha256':hashlib.sha256(res).hexdigest(),'changed_modules':[29,36],'capture_added':len(d.protos[54].bc)-d.protos[54].nbc,'merge_added':len(d.protos[53].bc)-d.protos[53].nbc},indent=2))
if __name__=='__main__':build()
