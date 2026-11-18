"""277 baseline, 267 drop rules, synchronous timer and native modal boundary tests."""
from test_v225 import *
from patch_v280 import BASE_SHA, GIFT_TEXT
from patch_v139 import encstr,rebuild_proto
from resource_tools import change_numbers
from ljtool import Proto,Dump


def main(runtime,resume=False):
    work=W/'native_work/v280';work.mkdir(parents=True,exist_ok=True)
    a=(W/'game_v277.res').read_bytes();b=(W/'game_v280.res').read_bytes()
    assert hashlib.sha256(a).hexdigest()==BASE_SHA
    _,old=decode(a,range(2,86,2));_,new=decode(b,range(2,86,2))
    report=json.loads((W/'build_v280.json').read_text());changes={}
    drop=Dump((W/'oil_drop_v267.ljbc').read_bytes()).protos[0]
    for mid,d in new.items():
        trees(d);assert d.rebuild()==d.raw and len(d.protos)==len(old[mid].protos)
        for p,q in zip(old[mid].protos,d.protos):
            if p.raw!=q.raw:changes.setdefault(mid,[]).append(p.idx)
            for pc,x in enumerate(q.bc):
                if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<q.nbc,(mid,q.idx,pc)
            if mid==44 and p.idx in [1,3]:
                mp={int(k):v for k,v in report['maps'][str(p.idx)].items()}
                positions=report['original_at'][str(p.idx)]
                assert(p.params,p.frame,p.uv)==(q.params,q.frame,q.uv)
                for pc,x in enumerate(p.bc):
                    at=positions[str(pc)];y=q.bc[at]
                    if OPS[x&255]in BRANCHES:
                        assert x&65535==y&65535 and at+1+(y>>16)-32768==mp[pc+1+(x>>16)-32768]
                    else:assert x==y,(p.idx,pc)
                continue
            if mid==22 and p.idx==112:
                assert q.raw==drop.raw;continue
            restored=Proto(q.raw,q.idx)
            if mid==12 and p.idx==20:restored=change_numbers(restored,{25:50})
            for j,v in enumerate(restored.kgc):
                if not isinstance(v,bytes):continue
                back=v.replace(b'v1.280',b'v1.277')
                if mid==12 and p.idx in [76,22196]:back=back.replace(b'1.280',b'1.277')
                if mid==12 and p.idx in [149,180]:back=back.replace(GIFT_TEXT.encode('gbk'),'系统赠送一瓶祝福油。'.encode('gbk'))
                if back!=v:restored.kgc[j]=back;restored.kraw[j]=encstr(back)
            assert rebuild_proto(restored)==p.raw,(mid,p.idx)
    for idx in [8,10,253,301,779]:assert new[14].protos[idx].bc==old[14].protos[idx].bc
    for idx in [89,97]:assert new[22].protos[idx].raw==old[22].protos[idx].raw
    for d in new.values():
        for p in d.protos:
            assert not any(b'__gm_autosave_'in v or b'__gm_save_dispatch_v278'in v for v in p.strings()),(d,p.idx)

    def export(mid,idx,name,patches=None,params=None,baseline=False):
        d=(old if baseline else new)[mid]
        (work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx,patches,params))
    # Actual modal root registers all five original methods; no handmade update.
    export(44,5,'modal_class')
    for mid,idx,name in [(14,13,'public_sys'),(14,458,'public_get'),(14,339,'fx_getter'),(14,500,'data_protection'),
                         (14,419,'merc_helper'),(12,4091,'oil_template'),(22,112,'oil_helper'),(22,64,'death_new'),
                         (22,3,'spawn'),(12,193,'currency_new'),(14,444,'native_drop'),(76,1,'ground_init'),
                         (14,223,'template_info'),(14,727,'oil_reset'),(14,94,'notice'),(14,614,'stack_install'),
                         (14,454,'add_item'),(14,451,'free_slots'),(14,87,'gly_add'),(12,126,'role_q'),(12,132,'role_main'),
                         (12,126,'role_a'),(12,132,'role_b'),(12,129,'config_a'),(12,134,'config_b'),(12,73,'mode_get'),
                         (12,154,'quit153'),(12,190,'quit188'),(14,167,'timer_factory'),(14,427,'native_frame'),(14,725,'profile_only')]:
        export(mid,idx,name)
    export(30,193,'table_register',{0:jump(0,33),42:jump(42,48),69:ad('RET0',0,1)})
    export(14,779,'native_exports',{0:ad('KNIL',1,1),1:jump(1,280,2)},1)
    export(12,20,'timer_new',{140:ad('RET0',0,1)})
    export(12,20,'timer_old',{140:ad('RET0',0,1)},baseline=True)
    login_maps=json.loads((W/'build_v259.json').read_text())['login_maps']
    for prev,idx,pc,start,end in [(149,150,319,142,151),(179,181,613,214,228)]:
        target=int(login_maps[str(prev)][str(pc)])+1
        export(12,idx,'login_'+str(prev),{0:jump(0,start,4),end:jump(end,target,5)})
        export(12,idx,'save_'+str(prev))
    p=new[12].protos[4092]
    def cv(v):return v[1]if isinstance(v,tuple)and v[0]=='int'else v
    for x in p.bc:
        if OPS[x&255]!='TDUP':continue
        t=p.gc(x>>16)
        if isinstance(t,tuple)and t[0]=='table':
            fields={k:cv(v)for k,v in t[2]}
            if fields.get('名称'.encode('gbk'))=='自然神水_小'.encode('gbk'):
                (work/'water_base.lua').write_bytes(('return '+lua(fields)).encode('gbk'));break
    else:raise AssertionError('water template absent')
    (work/'modal_fixture.lua').write_bytes((W/'modal_fixture_v280.lua').read_text().encode('gbk'))
    runs=[]
    suites={'oil_drop':'oil_drop_regression_v267.lua','gift_stack':'gift_stack_regression_v280.lua',
            'modal':'modal_regression_v280.lua','autosave':'autosave_regression_v280.lua'}
    for suite,source in suites.items():
        src=work/(suite+'.lua');src.write_bytes((W/source).read_text().encode('gbk'))
        for mode in ['normal','hot']:
            receipt=work/(suite+'.'+mode+'.passed.json')
            identity={'resource_sha256':hashlib.sha256(b).hexdigest(),'suite_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
                      'modal_fixture_sha256':hashlib.sha256((work/'modal_fixture.lua').read_bytes()).hexdigest()}
            if resume and receipt.exists():
                saved=json.loads(receipt.read_text())
                if saved['identity']==identity:
                    runs.append(saved['run']);print('Reusing passed '+suite+' '+mode,flush=True);continue
            r=subprocess.run([runtime,str(src),str(work),mode],capture_output=True,timeout=90)
            out=(r.stdout+r.stderr).decode('gbk','replace');print(out,flush=True)
            (work/(suite+'.'+mode+'.log')).write_text(out)
            assert r.returncode==0,(suite,mode,out[-4000:])
            runs.append({'suite':suite,'mode':mode,'output':out})
            receipt.write_text(json.dumps({'identity':identity,'run':runs[-1]},ensure_ascii=False))
    names=['patch_v280.py','test_v280.py','package_v280.py','player_changes_v280.json','oil_gift_v280.lua','oil_gift_v280.ljbc',
           'oil_drop_v267.lua','oil_drop_v267.ljbc','oil_drop_v280.ljbc','modal_fixture_v280.lua',*suites.values()]
    names=list(dict.fromkeys(names))
    result={'version':'v1.280','all_passed':True,'sha256':hashlib.sha256(b).hexdigest(),'runs':runs,'changed_prototypes':changes,
            'all_42_modules_checked':True,'base':'v1.277','drop_rules':'v1.267','autosave_seconds':300,
            'incremental_save_present':False,'native_modal_minimum_seconds':3,'full_windows_game_run':False,
            'runtime_version':subprocess.check_output([runtime,'-v'],stderr=subprocess.STDOUT).decode().strip(),
            'scope':'actual death/proxy/drop/ground and 267 integer thresholds; two-story login/gift/add/save-marker and real modal class/init/show/update/close; original timer, full frame and read-only public.run; finite engine/graphics/file/input bridges, not Windows full client validation',
            'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
    (W/'validation_v280.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--runtime');p.add_argument('--resume',action='store_true');a=p.parse_args();main(a.runtime or str(ensure_runtime()),a.resume)
