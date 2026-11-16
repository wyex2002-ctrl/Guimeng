"""Reserve a real local slot for the legacy skill-name upvalue.

The original patch placed a persistent local in R54 above calls starting at R11,
then captured it from the skill-instance constructor. Calls may reuse those slots.
Move that local to R11, shift all scratch registers up one, and keep all parameter
registers and instruction/branch positions unchanged.
"""
from ljdis import OPS
from ljtool import Proto
from patch_v139 import rebuild_proto
from portal_routes_v213 import child_refs


def repair(d):
    p=d.protos[55]
    assert p.params==11 and p.frame==63
    old=list(p.bc)
    def reg(r):return 11 if r==54 else r+1 if r>=11 else r
    def boundary(r):return r+1 if r>=11 else r
    single={'KSTR','KCDATA','KSHORT','KNUM','KPRI','UGET','GGET','GSET','TNEW','TDUP','FNEW','TSETM','VARG','RET','RET1','RETM','CALL','CALLM','CALLT','CALLMT','ITERC','ITERN'}
    binary={'MOV','NOT','UNM','LEN','ISTC','ISFC'}
    branch={'JMP','UCLO','FORI','JFORI','FORL','IFORL','JFORL','ITERL','IITERL','JITERL','ISNEXT','LOOP','ILOOP','JLOOP'}
    fixed_cuts={36:13,80:13,1014:26,1018:27,1034:13}
    # Old jump36 loses selector result R12; jump80/1034 lose distance R12;
    # jumps1014/1018 lose conversion locals R25/R26.
    cuts={}
    for pc,x in enumerate(old):
        op=OPS[x&255];a=x>>8&255;b=x>>24;c=x>>16&255;v=x>>16
        if op in single:
            a=reg(a)
        elif op in binary:
            a=reg(a);v=reg(v);b=v>>8;c=v&255
        elif op in {'IST','ISF','USETV'}:
            v=reg(v);b=v>>8;c=v&255
        elif op in {'TGETS','TGETB','TSETS','TSETB'}:
            a=reg(a);b=reg(b)
        elif op in {'TGETV','TSETV'}:
            a=reg(a);b=reg(b);c=reg(c)
        elif op in {'ISLT','ISGE','ISLE','ISGT','ISEQV','ISNEV'}:
            a=reg(a);v=reg(v);b=v>>8;c=v&255
        elif op in {'ISEQS','ISNES','ISEQN','ISNEN','ISEQP','ISNEP'}:
            a=reg(a)
        elif op in branch:
            if pc in fixed_cuts:
                assert op=='JMP' and a==12
                cuts[pc]={'before':a,'after':boundary(fixed_cuts[pc])}
                a=boundary(fixed_cuts[pc])
            else:a=boundary(a)
        elif op.startswith(('ADD','SUB','MUL','DIV','MOD','POW')):
            a=reg(a)
            if op.endswith('VV'):b=reg(b);c=reg(c)
            elif op.endswith('VN'):b=reg(b)
            elif op.endswith('NV'):c=reg(c)
            else:raise AssertionError(op)
        elif op=='CAT':
            assert not b<=54<=c
            a=reg(a);b=reg(b);c=reg(c)
        elif op=='RET0':pass
        else:raise AssertionError((pc,op))
        p.bc[pc]=(x&255)|(a<<8)|(c<<16)|(b<<24)
    assert set(cuts)==set(fixed_cuts)
    p.frame=64
    d.protos[55]=Proto(rebuild_proto(p),55)
    # The sole direct child's captures point into this rebased frame.
    refs=child_refs(d);assert {k:v for k,v in refs.items()if k[0]==55}=={(55,82):54}
    child=d.protos[54];uv=bytearray(child.uv)
    for at in range(0,len(uv),2):
        value=int.from_bytes(uv[at:at+2],'little')
        if value&0x8000:
            value=(value&0xc000)|reg(value&0x3fff)
            uv[at:at+2]=value.to_bytes(2,'little')
    child.uv=bytes(uv);d.protos[54]=Proto(rebuild_proto(child),54)
    # The v139 damage trampoline discarded every live slot with JMP A=0.
    # Its result table R0 can then become a stale string on a hot trace exit.
    damage=d.protos[51]
    damaged_cuts=[]
    for pc,x in enumerate(damage.bc):
        if OPS[x&255]=='JMP' and ((x>>8)&255)==0:
            keep=9 if pc==34 else 17
            damage.bc[pc]=(x&~0xff00)|(keep<<8);damaged_cuts.append(pc)
    assert damaged_cuts==[34,90,91,99,101,105,107,116,117,122,123,128,129,134,135,142,143,150,151,153]
    # R9..R16 are scratch slots assigned by this trampoline/call setup.
    # Initialize them before boundary17; conditional trace exits also need the
    # fallthrough path's actor/coordinate slots, not just the jump target slots.
    from bytecode_relocate import replace_instructions
    from patch_v139 import ad
    damage=Proto(rebuild_proto(damage),51)
    raw,damage_map=replace_instructions(damage,{88:[ad('KNIL',9,16),damage.bc[88]]})
    d.protos[51]=Proto(raw,51)
    return {'selector_cuts':cuts,'damage_map':damage_map,'damage_cuts':damaged_cuts}
