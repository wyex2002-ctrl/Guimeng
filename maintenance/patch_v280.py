"""Use v277's synchronous game, v267 oil drops, five-minute save and gift delay."""
from patch_v277 import *
from resource_tools import change_numbers
from bytecode_relocate import replace_instructions

BASE_SHA='a0014ce27435f9784b3e605e9c86f3075c1cd9d685a92f4a4a1b2ddcb8c3ad75'
GIFT_TEXT='【系统赠送您1瓶祝福油，请查看背包】'
NOTICE_START='__gm_oil_notice_start_v280'


def modal_delay(d):
    maps={};original_at={}
    p=d.protos[3];key=gcid(p,NOTICE_START)
    assert key<256 and OPS[p.bc[24]&255]=='TSETS'
    mode=gcid(p,'确定');message=gcid(p,GIFT_TEXT)
    assert mode<256
    fragment=[ad('KPRI',8,0),abc('TSETS',8,0,key),ad('ISNES',1,mode),0,
              ad('ISNES',2,message),0,ad('GGET',8,gcid(p,'引擎')),ad('MOV',9,8),
              abc('TGETS',8,8,gcid(p,'取运行时间')),abc('CALL',8,2,2),abc('TSETS',8,0,key),p.bc[24]]
    raw,mp=replace_instructions(p,{24:fragment});q=Proto(raw,3);at=mp[24]
    q.bc[at+3]=jump(at+3,at+len(fragment)-1,8);q.bc[at+5]=jump(at+5,at+len(fragment)-1,8)
    d.protos[3]=Proto(rebuild_proto(q),3);maps['3']=mp
    original_at['3']={i:mp[i]+(len(fragment)-1 if i==24 else 0)for i in range(p.nbc)}
    p=d.protos[1];key=gcid(p,NOTICE_START);assert key<256
    assert p.bc[21]==ad('IST',0,1)and OPS[p.bc[123]&255]=='TGETS'
    fragment=[abc('TGETS',2,0,key),ad('ISEQP',2,0),0,ad('GGET',3,gcid(p,'引擎')),
              ad('MOV',4,3),abc('TGETS',3,3,gcid(p,'取运行时间')),abc('CALL',3,2,2),
              abc('SUBVV',3,3,2),ad('KSHORT',4,3),ad('ISLT',3,4),0,
              ad('KPRI',2,0),abc('TSETS',2,0,key),p.bc[21]]
    raw,mp=replace_instructions(p,{21:fragment});q=Proto(raw,1);at=mp[21]
    q.bc[at+2]=jump(at+2,at+len(fragment)-1,2);q.bc[at+10]=jump(at+10,mp[123],2)
    d.protos[1]=Proto(rebuild_proto(q),1);maps['1']=mp
    original_at['1']={i:mp[i]+(len(fragment)-1 if i==21 else 0)for i in range(p.nbc)}
    return maps,original_at


def build(runtime=None,rebuild_history=False):
    path=W/'game_v277.res'
    if rebuild_history or not path.exists():
        subprocess.run(['python3',str(W/'patch_v277.py')]
                       +(['--rebuild-history']if rebuild_history else[])
                       +(['--runtime',runtime]if runtime else[]),check=True)
    base=path.read_bytes();assert hashlib.sha256(base).hexdigest()==BASE_SHA
    outer,mods=decode(base,[12,14,22,30,44])
    p=mods[12].protos[20];assert p.bc[120]==abc('MODVN',1,1,25)
    mods[12].protos[20]=change_numbers(p,{25:3000})
    runtime=runtime or str(ensure_runtime());work=W/'compile_work';work.mkdir(exist_ok=True)
    compiler=work/'compile280.lua';compiler.write_text('local f=assert(loadfile(arg[1]))();local o=assert(io.open(arg[2],"wb"));o:write(string.dump(f));o:close()')
    def compile(name,source):
        src=work/(name+'_gbk.lua');src.write_bytes((W/source).read_text().encode('gbk'))
        out=W/(name+'.ljbc');subprocess.run([runtime,str(compiler),str(src),str(out)],check=True)
        helper=Dump(out.read_bytes());assert len(helper.protos)==1 and helper.protos[0].nuv==0
        return helper.protos[0]
    oil=compile('oil_drop_v280','oil_drop_v267.lua')
    assert oil.raw==Dump((W/'oil_drop_v267.ljbc').read_bytes()).protos[0].raw
    mods[22].protos[112]=Proto(oil.raw,112)
    gift=compile('oil_gift_v280','oil_gift_v280.lua')
    for idx in [149,180]:mods[12].protos[idx]=Proto(gift.raw,idx)
    maps,original_at=modal_delay(mods[44])
    for mid,d in mods.items():
        for i,p in enumerate(d.protos):
            changed=False
            for j,v in enumerate(p.kgc):
                if not isinstance(v,bytes):continue
                new=v.replace(b'v1.277',b'v1.280')
                if mid==12 and i in [76,22196]:new=new.replace(b'1.277',b'1.280')
                if new!=v:p.kgc[j]=new;p.kraw[j]=encstr(new);changed=True
            if changed:d.protos[i]=Proto(rebuild_proto(p),i)
        raw=rebuild_dump(d,set());assert Dump(raw).rebuild()==raw;(W/f'module_{mid}_v280.ljbc').write_bytes(raw)
        packet=bytes.fromhex('0d0f3e03')+struct.pack('<I',len(raw))+zlib.compress(raw,9)
        enc=rc4(packet,bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'));set_string(outer.protos[0],mid,enc if mid==12 else enc.hex().upper().encode())
    data=rc4(rebuild_dump(outer,{0}),b'_Npi_dest__cc_&%_23')+base[-10:];(W/'game_v280.res').write_bytes(data)
    report={'version':'v1.280','gameplay_base':'v1.277','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
            'autosave_seconds':300,'autosave_ticks':3000,'timer_period_seconds':.1,'incremental_save_present':False,
            'drop_rules':'v1.267','high_drop_test':False,'gift_text':GIFT_TEXT,'gift_minimum_visible_seconds':3,
            'maps':maps,'original_at':original_at,'player_note_count':54,'font_color_border_unchanged':True}
    (W/'build_v280.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print({k:v for k,v in report.items()if k not in ['maps','original_at']})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--runtime');p.add_argument('--rebuild-history',action='store_true');a=p.parse_args();build(a.runtime,a.rebuild_history)
