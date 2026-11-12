import struct
from ljtool import Dump,Proto,Reader,uleb,rc4,decode_module
from bytecode_relocate import numeric_and_debug

def argb(rgb):return (0xff000000|rgb)-(1<<32)

def numbers(p):
    r=Reader(p.raw[p.kend:]);values=[];raw=[]
    for _ in range(p.nkn):
        start=r.p;x=r.u()
        if x&1:v=struct.unpack('<d',struct.pack('<II',x>>1,r.u()))[0]
        else:v=(x>>1) if (x>>1)<2**31 else (x>>1)-2**32
        values.append(v);raw.append(r.b[start:r.p])
    return values,raw

def change_numbers(p,changes,append=()):
    _,parts=numbers(p);_,debug=numeric_and_debug(p)
    for i,v in changes.items():parts[i]=uleb((v&0xffffffff)<<1)
    parts.extend(uleb((v&0xffffffff)<<1) for v in append);p.nkn=len(parts)
    header=bytes([p.flags,p.params,p.frame,p.nuv])+uleb(p.nkgc)+uleb(p.nkn)+uleb(len(p.bc))+uleb(len(debug))
    if debug:header+=uleb(p.first)+uleb(p.lines)
    return Proto(header+struct.pack('<'+'I'*len(p.bc),*p.bc)+p.uv+b''.join(p.kraw)+b''.join(parts)+debug,p.idx)

def decode(data,indices):
    outer=Dump(rc4(data[:-10],b'_Npi_dest__cc_&%_23'));root=outer.protos[0]
    return outer,{m:Dump(decode_module(root.gc(m).hex().upper().encode() if m==12 else root.gc(m))) for m in indices}
