import struct
from ljtool import Reader,uleb
from ljdis import OPS
from patch_v139 import rebuild_proto

BRANCHES={'JMP','UCLO','FORI','JFORI','FORL','IFORL','ITERL','IITERL','LOOP','ILOOP','ISNEXT'}

def numeric_and_debug(p):
    r=Reader(p.raw[p.kend:])
    for _ in range(p.nkn):
        x=r.u()
        if x&1:r.u()
    return p.raw[p.kend:p.kend+r.p],p.raw[p.kend+r.p:]

def relocated_debug(p,mapping,owners):
    numeric,debug=numeric_and_debug(p)
    if not p.ndbg:return numeric,b''
    width=1 if p.lines<256 else 2 if p.lines<65536 else 4
    lineinfo=debug[:p.nbc*width]
    newlines=b''.join(lineinfo[pc*width:(pc+1)*width] for pc in owners)
    tail=Reader(debug[p.nbc*width:]);names=bytearray()
    for _ in range(p.nuv):
        while True:
            b=tail.take(1);names.extend(b)
            if b==b'\0':break
    newvars=bytearray();last=last_new=0
    # Debug PC numbering includes LuaJIT's implicit function header at PC0;
    # the dump's first explicit instruction is PC1.
    def relocate(pc):
        if pc==0:return 0
        assert 1<=pc<=p.nbc+1,(p.idx,pc,p.nbc)
        return mapping[pc-1]+1
    while True:
        c=tail.take(1)
        if c==b'\0':newvars.extend(c);break
        name=bytearray(c)
        if c[0]>=7:
            while name[-1]:name.extend(tail.take(1))
        start=last+tail.u();end=start+tail.u();last=start
        ns,ne=relocate(start),relocate(end)
        newvars.extend(name);newvars.extend(uleb(ns-last_new));newvars.extend(uleb(ne-ns));last_new=ns
    assert tail.p==len(tail.b),(p.idx,tail.p,len(tail.b))
    return numeric,newlines+names+newvars

def replace_instructions(p,replacements):
    """Insert straight-line fragments and relocate branches AND debug ranges."""
    old=list(p.bc);mapping={};owners=[];out=[]
    for pc,ins in enumerate(old):
        mapping[pc]=len(out);block=replacements.get(pc,[ins])
        # An empty block deletes an instruction in an explicitly replaced span.
        # Callers must reject incoming branches to the span interior first.
        out.extend(block);owners.extend([pc]*len(block))
    mapping[len(old)]=len(out)
    for pc,ins in enumerate(old):
        if pc in replacements:continue
        if OPS[ins&255] in BRANCHES:
            target=pc+1+(ins>>16)-32768;assert target in mapping
            delta=mapping[target]-mapping[pc]-1;assert -32768<=delta<=32767
            out[mapping[pc]]=(ins&65535)|((delta+32768)<<16)
    numeric,debug=relocated_debug(p,mapping,owners)
    header=bytes([p.flags,p.params,p.frame,p.nuv])+uleb(p.nkgc)+uleb(p.nkn)+uleb(len(out))+uleb(len(debug))
    if debug:header+=uleb(p.first)+uleb(p.lines)
    raw=header+struct.pack('<'+'I'*len(out),*out)+p.uv+b''.join(p.kraw)+numeric+debug
    return raw,mapping
