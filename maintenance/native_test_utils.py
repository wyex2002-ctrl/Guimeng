from ljtool import Proto,uleb
from patch_v139 import rebuild_proto

def trees(d):
    stack=[];out={}
    for p in d.protos:
        children=[]
        for k in p.kgc:
            if k==('child',):children.append(stack.pop())
        out[p.idx]=[i for child in reversed(children) for i in child]+[p.idx]
        stack.append(out[p.idx])
    assert len(stack)==1
    return out

def standalone(d,subtrees,index,patches=None,params=None):
    pieces=[d.header]
    for i in subtrees[index]:
        p=Proto(d.protos[i].raw,i)
        if i==index:
            if params is not None:p.params=params
            if patches:
                for pc,ins in patches.items():p.bc[pc]=ins
            raw=rebuild_proto(p)
        else:raw=p.raw
        pieces.extend([uleb(len(raw)),raw])
    pieces.append(b'\0')
    return b''.join(pieces)

