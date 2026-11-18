"""Ten-second incremental autosave, retaining native collectors and file format."""
from patch_v277 import *
from resource_tools import change_numbers
from bytecode_relocate import replace_instructions

BASE_SHA='a0014ce27435f9784b3e605e9c86f3075c1cd9d685a92f4a4a1b2ddcb8c3ad75'


def checkpoint(p, reg, phase=None):
    out=[ad('GGET',reg,gcid(p,'__gm_save_step_v278'))]
    if phase is None:
        out.append(abc('CALL',reg,1,1))
    else:
        out += [ad('KSTR',reg+1,gcid(p,phase)),abc('CALL',reg,1,2)]
    return out


def build(runtime=None,rebuild_history=False):
    path=W/'game_v277.res'
    if rebuild_history or not path.exists():
        subprocess.run(['python3',str(W/'patch_v277.py')]
                       +(['--rebuild-history']if rebuild_history else[])
                       +(['--runtime',runtime]if runtime else[]),check=True)
    base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
    outer,mods=decode(base,[12,14,30]);d=mods[14];maps={};original_at={}
    # Auto-only request uses the existing Ux table; it exposes no native state.
    p=change_numbers(mods[12].protos[20],{25:100})
    assert OPS[p.bc[132]&255]=='TGETS' and p.gc(p.bc[133]>>16&255)=='存档读档'.encode('gbk')
    key=gcid(p,'__gm_auto_save_v278')
    p.bc[132]=ad('KSTR',2,key)
    p.bc[133]=abc('TGETV',1,1,2)
    mods[12].protos[20]=Proto(rebuild_proto(p),20)

    # Capture the original closure when the real Gly factory creates it. This
    # avoids suspending the shared diagnostic wrappers across game frames.
    p=d.protos[301]
    assert OPS[p.bc[111]&255]=='TSETS'and p.gc(p.bc[111]>>16&255)=='存档'.encode('gbk')
    key=gcid(p,'__gm_autosave_raw_v278');assert key<256
    raw,mp=replace_instructions(p,{111:[p.bc[111],ad('UGET',91,1),abc('TSETS',81,91,key)]})
    d.protos[301]=Proto(raw,301);maps['301']=mp;original_at['301']={i:mp[i]for i in range(p.nbc)}

    p=d.protos[253];old=list(p.bc);repl={}
    prefix=[ad('GGET',3,gcid(p,'__gm_save_dispatch_v278')),ad('MOV',4,0),
            ad('MOV',5,1),ad('MOV',6,2),abc('CALL',3,2,4),ad('IST',0,3),ad('JMP',4,32768)]
    repl[0]=prefix+checkpoint(p,3,'collect_items')+[old[0]]
    repl[26]=[ad('GGET',9,gcid(p,'__gm_save_windows_v278')),ad('MOV',10,8),
              abc('CALL',9,2,2),ad('MOV',8,9),old[26]]
    repl[158]=checkpoint(p,23)+[old[158]]
    for pc,reg,phase in [(160,15,'collect_skills'),(223,16,'collect_buffs'),
                          (245,17,'collect_role'),(382,21,'role_encode'),
                          (398,22,'collect_tasks'),(443,23,'collect_cooldowns'),
                          (497,34,'serialize'),(500,35,'checksum'),
                          (524,38,'encrypt'),(533,38,'encrypt'),(551,38,'write')]:
        repl[pc]=checkpoint(p,reg,phase)+[old[pc]]
    for pc in [161,400,445]:
        assert OPS[old[pc]&255]=='GGET'and p.gc(old[pc]>>16)==b'pairs'
        repl[pc]=[ad('GGET',old[pc]>>8&255,gcid(p,'__gm_save_pairs_v278'))]
    repl[494]=[ad('GGET',33,gcid(p,'__gm_save_freeze_v278')),ad('MOV',34,32),
               abc('CALL',33,2,2),ad('MOV',32,33)]+checkpoint(p,33,'sort')+[old[494]]
    raw,mp=replace_instructions(p,repl);q=Proto(raw,253)
    # Original branch 158 is carried inside a replacement fragment.
    for pc,fragment in repl.items():
        if OPS[old[pc]&255]in BRANCHES:
            at=mp[pc]+len(fragment)-1;target=pc+1+(old[pc]>>16)-32768
            q.bc[at]=(old[pc]&65535)|((mp[target]-at-1+32768)<<16)
    end=len(q.bc);q.bc.append(ad('RET0',0,1));q.bc[6]=jump(6,end,4)
    d.protos[253]=Proto(rebuild_proto(q),253);maps['253']=mp
    original_at['253']={i:mp[i]+(len(repl[i])-1 if i in repl else 0)for i in range(p.nbc)}

    # These are the original save-format recursion helpers, not game-wide
    # table.copy or unrelated render/actor functions.
    for idx,points in [(8,{28:(10,None),35:(10,None),38:(5,None),53:(9,None)}),
                       (10,{111:(7,None),114:(2,None)})]:
        p=d.protos[idx];old=list(p.bc)
        repl={pc:([old[pc]]+checkpoint(p,reg,phase) if pc in [35,111]
                  else checkpoint(p,reg,phase)+[old[pc]])for pc,(reg,phase)in points.items()}
        raw,mp=replace_instructions(p,repl);q=Proto(raw,idx)
        for pc,fragment in repl.items():
            if OPS[old[pc]&255]in BRANCHES:
                at=mp[pc]+len(fragment)-1;target=pc+1+(old[pc]>>16)-32768
                q.bc[at]=(old[pc]&65535)|((mp[target]-at-1+32768)<<16)
        d.protos[idx]=Proto(rebuild_proto(q),idx);maps[str(idx)]=mp
        original_at[str(idx)]={i:mp[i]+(0 if i in [35,111]else len(repl[i])-1)if i in repl else mp[i]for i in range(p.nbc)}

    runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
    compiler=work/'compile278.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
    src=work/'autosave_v278_gbk.lua';src.write_bytes((W/'autosave_v278.lua').read_text().encode('gbk'))
    out=W/'autosave_v278.ljbc';subprocess.run([runtime,str(compiler),str(src),str(out)],check=True)
    helper=Dump(out.read_bytes());assert helper.protos[-1].nuv==0
    p=d.protos[779];logical=p.nkgc;p.kgc.insert(0,('child',));p.kraw.insert(0,uleb(0));p.nkgc+=1;p.flags|=1
    raw,mp=replace_instructions(p,{286:[ad('FNEW',2,logical),ad('MOV',3,0),abc('CALL',2,1,2),p.bc[286]]})
    d.protos[779]=Proto(raw,779);maps['779']=mp;original_at['779']={i:mp[i]+(3 if i==286 else 0)for i in range(p.nbc)}
    d.protos[779:779]=[Proto(p.raw,779+i)for i,p in enumerate(helper.protos)]
    for mid,d in mods.items():
        for i,p in enumerate(d.protos):
            p.idx=i;changed=False
            for j,v in enumerate(p.kgc):
                if not isinstance(v,bytes):continue
                new=v.replace(b'v1.277',b'v1.278')
                if mid==12 and i in [76,22196]:new=new.replace(b'1.277',b'1.278')
                if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
            if changed:d.protos[i]=Proto(rebuild_proto(p),i)
        raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v278.ljbc').write_bytes(raw)
        packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
        enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
    data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v278.res').write_bytes(data)
    report={'version':'v1.278','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
            'autosave_seconds':10,'normal_completion_target_seconds':9,'helper_at':779,'helper_count':len(helper.protos),
            'constructor':779+len(helper.protos),'maps':maps,'original_at':original_at,'high_drop_test_retained':True,'native_crypto_and_write_synchronous':True}
    (W/'build_v278.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print({k:v for k,v in report.items()if k not in ['maps','original_at']})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--runtime');parser.add_argument('--rebuild-history',action='store_true');args=parser.parse_args();build(args.runtime,args.rebuild_history)
