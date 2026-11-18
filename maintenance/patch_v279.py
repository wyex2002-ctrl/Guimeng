"""Repair DM native Lua-state affinity without changing save format or timing."""
from patch_v278 import *

BASE_SHA='f5b95e3918bc708a9b4ed103e985cbc05eb89d4bf30b8ce2024ea5f6dc68479b'


def build(runtime=None,rebuild_history=False):
    path=W/'game_v278.res'
    if rebuild_history or not path.exists():
        subprocess.run(['python3',str(W/'patch_v278.py')]
                       +(['--rebuild-history']if rebuild_history else[])
                       +(['--runtime',runtime]if runtime else[]),check=True)
    base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
    outer,mods=decode(base,[12,14,30]);d=mods[14]
    previous=json.loads((W/'build_v278.json').read_text())
    p=d.protos[253];changed=[]
    aliases={'核心':'__gm_save_core_v279','引擎':'__gm_save_engine_v279','调试输出':'__gm_save_debug_v279'}
    for pc,x in enumerate(p.bc):
        if OPS[x&255]!='GGET':continue
        name=p.gc(x>>16).decode('gbk')
        if name in aliases:
            p.bc[pc]=ad('GGET',x>>8&255,gcid(p,aliases[name]));changed.append(pc)
    assert len(changed)==11,changed
    callbacks=[previous['original_at']['253'][str(pc)]for pc in [31,236,242]]
    repl={}
    for pc in callbacks:
        x=p.bc[pc];assert OPS[x&255]=='CALL'and (x>>16&255)==1
        a=x>>8&255
        repl[pc]=[ad('MOV',a+1,a),ad('GGET',a,gcid(p,'__gm_save_call0_v279')),abc('CALL',a,x>>24,2)]
    raw,mapping=replace_instructions(p,repl)
    d.protos[253]=Proto(raw,253)
    changed=[mapping[pc]for pc in changed]
    previous['maps']['253']={key:mapping[pc]for key,pc in previous['maps']['253'].items()}
    previous['original_at']['253']={key:mapping[pc]+(2 if pc in callbacks else 0)for key,pc in previous['original_at']['253'].items()}
    runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
    compiler=work/'compile279.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
    src=work/'autosave_v279_gbk.lua';src.write_bytes((W/'autosave_v279.lua').read_text().encode('gbk'))
    out=W/'autosave_v279.ljbc';subprocess.run([runtime,str(compiler),str(src),str(out)],check=True)
    helper=Dump(out.read_bytes());assert helper.protos[-1].nuv==0
    start=previous['helper_at'];oldcount=previous['helper_count'];oldctor=previous['constructor']
    d.protos[start:oldctor]=[Proto(p.raw,start+i)for i,p in enumerate(helper.protos)]
    ctor=start+len(helper.protos)
    for mid,d in mods.items():
        for i,p in enumerate(d.protos):
            p.idx=i;updated=False
            for j,v in enumerate(p.kgc):
                if not isinstance(v,bytes):continue
                new=v.replace(b'v1.278',b'v1.279')
                if mid==12 and i in [76,22196]:new=new.replace(b'1.278',b'1.279')
                if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);updated=True
            if updated:d.protos[i]=Proto(rebuild_proto(p),i)
        raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v279.ljbc').write_bytes(raw)
        packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
        enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
    data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v279.res').write_bytes(data)
    report={**previous,'version':'v1.279','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
            'helper_count':len(helper.protos),'constructor':ctor,'previous_helper_count':oldcount,
            'native_alias_pcs':changed,'native_callback_pcs':[mapping[pc]+2 for pc in callbacks],'native_calls_on_main':True}
    (W/'build_v279.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print({k:v for k,v in report.items()if k not in ['maps','original_at']})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--runtime');p.add_argument('--rebuild-history',action='store_true');a=p.parse_args();build(a.runtime,a.rebuild_history)
