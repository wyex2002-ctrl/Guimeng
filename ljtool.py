import struct,zlib,json
from pathlib import Path

def uleb(n):
 o=bytearray()
 while n>=128:o.append((n&127)|128);n>>=7
 o.append(n);return bytes(o)
class Reader:
 def __init__(self,b):self.b=b;self.p=0
 def take(self,n):r=self.b[self.p:self.p+n];self.p+=n;return r
 def u(self):
  n=s=0
  while True:
   x=self.take(1)[0];n|=(x&127)<<s
   if x<128:return n
   s+=7
 def tablevalue(self):
  t=self.u()
  if t>=5:return self.take(t-5)
  if t==3:return ('int',self.u())
  if t==4:return ('num',self.u(),self.u())
  return (None,False,True)[t]
class Proto:
 def __init__(self,b,idx):
  self.raw=b;self.idx=idx;r=Reader(b)
  self.flags,self.params,self.frame,self.nuv=r.take(4)
  self.nkgc,self.nkn,self.nbc=r.u(),r.u(),r.u();self.ndbg=r.u();self.first=r.u() if self.ndbg else 0;self.lines=r.u() if self.ndbg else 0
  self.hend=r.p;self.bc=list(struct.unpack('<'+'I'*self.nbc,r.take(4*self.nbc)));self.uv=r.take(2*self.nuv);self.kgc=[];self.kraw=[]
  for i in range(self.nkgc):
   start=r.p;t=r.u()
   if t>=5:v=r.take(t-5)
   elif t==0:v=('child',)
   elif t==1:
    na,nh=r.u(),r.u();v=('table',[r.tablevalue() for _ in range(na)],[(r.tablevalue(),r.tablevalue()) for _ in range(nh)])
   elif t in (2,3):v=(t,r.u(),r.u())
   elif t==4:v=(t,r.u(),r.u(),r.u(),r.u())
   else:raise ValueError(t)
   self.kgc.append(v);self.kraw.append(b[start:r.p])
  self.kend=r.p
 def strings(self):return [x for x in self.kgc if isinstance(x,bytes)]
 def gc(self,d):return self.kgc[-1-d]
 def rebuild(self):
  return self.raw[:self.hend]+struct.pack('<'+'I'*len(self.bc),*self.bc)+self.uv+b''.join(self.kraw)+self.raw[self.kend:]
class Dump:
 def __init__(self,b):
  self.raw=b;r=Reader(b);assert r.take(3)==b'\x1bLJ';self.version=r.take(1)[0];self.flags=r.u()
  if not self.flags&2:r.take(r.u())
  self.header=b[:r.p];self.protos=[]
  while True:
   n=r.u()
   if not n:break
   self.protos.append(Proto(r.take(n),len(self.protos)))
  assert r.p==len(b),(r.p,len(b))
 def rebuild(self):return self.header+b''.join(uleb(len(b))+b for b in [p.rebuild() for p in self.protos])+b'\0'
def rc4(data,key):
 s=list(range(256));j=0
 for i in range(256):
  j=(j+s[i]+key[i%len(key)])%256;s[i],s[j]=s[j],s[i]
 i=j=0;o=bytearray()
 for b in data:
  i=(i+1)%256;j=(j+s[i])%256;s[i],s[j]=s[j],s[i];o.append(b^s[(s[i]+s[j])%256])
 return bytes(o)
def decode_module(h):
 b=rc4(bytes.fromhex(h.decode('ascii')),bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));assert b[:4]==bytes.fromhex('0d0f3e03');d=zlib.decompress(b[8:]);assert len(d)==struct.unpack('<I',b[4:8])[0];return d
