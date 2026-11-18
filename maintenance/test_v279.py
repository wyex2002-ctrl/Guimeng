"""Native save-format equivalence and incremental scheduler regressions."""
from test_v225 import *
from patch_v278 import BASE_SHA
from patch_v139 import encstr,rebuild_proto
from ljtool import Proto
from bytecode_relocate import numeric_and_debug


def main(runtime):
    work=W/'native_work/v279';work.mkdir(parents=True,exist_ok=True)
    a=(W/'game_v277.res').read_bytes();b=(W/'game_v279.res').read_bytes()
    assert hashlib.sha256(a).hexdigest()==BASE_SHA
    _,old=decode(a,range(2,86,2));_,new=decode(b,range(2,86,2))
    build=json.loads((W/'build_v279.json').read_text());count=build['helper_count'];ctor=build['constructor']
    changed={(12,20),(14,8),(14,10),(14,253),(14,301),(14,779)}
    for mid,d in new.items():
        trees(d);assert d.rebuild()==d.raw
        after=[p for p in d.protos if mid!=14 or not 779<=p.idx<ctor]
        assert len(after)==len(old[mid].protos)
        for p,q in zip(old[mid].protos,after):
            if(mid,p.idx)in changed:continue
            restored=Proto(q.raw,q.idx)
            for j,v in enumerate(restored.kgc):
                if not isinstance(v,bytes):continue
                back=v.replace(b'v1.279',b'v1.277')
                if mid==12 and p.idx in [76,22196]:back=back.replace(b'1.279',b'1.277')
                if back!=v:restored.kgc[j]=back;restored.kraw[j]=encstr(back)
            assert rebuild_proto(restored)==p.raw,(mid,p.idx,q.idx)
        for p in d.protos:
            for pc,x in enumerate(p.bc):
                if OPS[x&255]in BRANCHES:assert 0<=pc+1+(x>>16)-32768<p.nbc,(mid,p.idx,pc)
    for name,positions in build['original_at'].items():
        idx=int(name);p=old[14].protos[idx];q=new[14].protos[ctor if idx==779 else idx]
        mp={int(k):v for k,v in build['maps'][name].items()}
        assert(p.params,p.frame,p.uv)==(q.params,q.frame,q.uv)
        for pc,x in enumerate(p.bc):
            at=positions[str(pc)];y=q.bc[at]
            if idx==253 and at in build['native_alias_pcs']:
                assert OPS[x&255]==OPS[y&255]=='GGET' and (x>>8&255)==(y>>8&255)
                assert q.gc(y>>16)=={'核心':'__gm_save_core_v279','引擎':'__gm_save_engine_v279','调试输出':'__gm_save_debug_v279'}[p.gc(x>>16).decode('gbk')].encode('gbk')
                continue
            if idx==253 and at in build['native_callback_pcs']:
                assert OPS[x&255]==OPS[y&255]=='CALL'and x>>8&255==y>>8&255 and x>>24==y>>24
                assert x>>16&255==1 and y>>16&255==2
                assert OPS[q.bc[at-2]&255]=='MOV'and OPS[q.bc[at-1]&255]=='GGET'
                assert q.gc(q.bc[at-1]>>16)==b'__gm_save_call0_v279'
                continue
            if idx==253 and pc in [161,400,445]:
                assert OPS[y&255]=='GGET'and q.gc(y>>16)==b'__gm_save_pairs_v278';continue
            if OPS[x&255]in BRANCHES:
                assert x&65535==y&65535
                assert at+1+(y>>16)-32768==mp[pc+1+(x>>16)-32768]
            else:assert x==y,(idx,pc,at,OPS[x&255],OPS[y&255])
    # The two crash-related entry repairs and all combat/oil code stay exact.
    assert old[22].raw==new[22].raw
    # This release changes only the save collector's private routing and the
    # scheduler. Compare directly to 278 as well as the original 277 collector.
    _,previous=decode((W/'game_v278.res').read_bytes(),range(2,86,2))
    for mid,d in previous.items():
        before=[p for p in d.protos if mid!=14 or not 779<=p.idx<799]
        after=[p for p in new[mid].protos if mid!=14 or not 779<=p.idx<ctor]
        assert len(before)==len(after)
        for p,q in zip(before,after):
            if mid==14 and p.idx==253:continue
            restored=Proto(q.raw,q.idx)
            for j,v in enumerate(restored.kgc):
                if not isinstance(v,bytes):continue
                back=v.replace(b'v1.279',b'v1.278')
                if mid==12 and p.idx in [76,22196]:back=back.replace(b'1.279',b'1.278')
                if back!=v:restored.kgc[j]=back;restored.kraw[j]=encstr(back)
            assert rebuild_proto(restored)==p.raw,(mid,p.idx,'278 direct comparison')

    def export(mid,idx,name,patches=None,params=None,baseline=False):
        d=(old if baseline else new)[mid]
        (work/(name+'.ljbc')).write_bytes(standalone(d,trees(d),idx,patches,params))
    broken=decode((W/'game_v278.res').read_bytes(),[14])[1][14]
    for idx,name in [(798,'install_broken'),(301,'gly_factory_broken'),(8,'sort_broken'),(11,'encode_broken')]:
        (work/(name+'.ljbc')).write_bytes(standalone(broken,trees(broken),idx))
    export(14,ctor-1,'install')
    export(14,13,'readonly')
    export(14,ctor,'public_exports',{0:ad('KNIL',1,1),1:jump(1,build['maps']['779']['286'],2)},1)
    export(12,4,'variable_proxy')
    for version in ['old','new']:
        base=version=='old'
        for idx,name in [(301,'gly_factory'),(8,'sort'),(11,'encode'),(9,'decode'),(253,'save')]:
            export(14,idx,name+'_'+version,baseline=base)
        export(12,20,'timer_'+version,{140:ad('RET0',0,1)},baseline=base)
        export(14,779 if base else ctor,'native_exports_'+version,{0:ad('KNIL',1,1),1:jump(1,280,2)},1,baseline=base)
    export(30,193,'table_register',{0:jump(0,33),42:jump(42,48),69:ad('RET0',0,1)})
    export(14,500,'protect')
    # The complete native decoder/checksum prefix, ending before world rebuild.
    export(14,256,'read_native',{0:jump(0,1,3),136:ad('GGET',9,0),187:ad('RET1',4,2)},baseline=True)
    for mid,idx,name in [(12,150,'ui_a'),(12,181,'ui_b'),(12,126,'role_a'),(12,132,'role_b'),
                         (12,129,'config_a'),(12,134,'config_b'),(12,73,'mode_get'),
                         (12,154,'quit_a'),(12,190,'quit_b')]:export(mid,idx,name)
    for mid,idx,name in [(14,167,'timer_factory'),(14,427,'native_frame'),
                         (14,725,'profile_only'),(14,13,'public_sys')]:export(mid,idx,name)
    runs=[]
    src=work/'test.lua';source=W/'autosave_regression_v279.lua';src.write_bytes(source.read_text().encode('gbk'))
    for mode in ['normal','hot']:
        r=subprocess.run([runtime,str(src),str(work),mode],capture_output=True,timeout=120)
        out=(r.stdout+r.stderr).decode('gbk','replace');print(out,flush=True)
        (work/(mode+'.log')).write_text(out);assert r.returncode==0,(mode,r.returncode,out[-6000:])
        runs.append({'mode':mode,'output':out})
    # Real complete native frame/clock/public.run + unchanged watch wrappers.
    # The collector is covered above; this probe yields at native frame edges
    # without requiring a full map or character construction in the harness.
    reference=(W/'autosave_regression_v273.lua').read_text()
    frame=reference[:reference.index('-- Real two-story getters')]+reference[reference.index('local costs={}'):reference.index('-- Manual/exit saving')]
    frame=frame.replace("load('native_exports',env)","load('native_exports_'..version,env)")
    frame=frame.replace("eq(n,version=='old'and 2 or 8)","eq(n,version=='old'and 8 or 4)")
    frame=frame.replace('401','421')
    needle=" local create=load('timer_factory',env);"
    frame=frame.replace(needle,''' local completed=0
 S.script_setting.Ux雌=t.U
 if version=='new'then
  local callback=t.U.窗口相关.存档读档
  t.U.窗口相关.存档读档=function(...)
   callback(...)
   assert(env.__gm_save_dispatch_v278('frame-probe',{},'test'))
  end
  S.__gm_autosave_raw_v278=function()
   for i=1,200 do env.__gm_save_step_v278('frame_probe')end
   completed=completed+1;return true
  end
 end
'''+needle)
    frame=frame.replace(" eq(t.t['时间'],421);", " if version=='new'then eq(completed,4);eq(S.__gm_autosave_v278.active,false)end\n eq(t.t['时间'],421);")
    frame += "\nprint('AUTOSAVE_FRAME_V279_PASS',mode,count)\n"
    frame_script=work/'frame.lua';frame_script.write_bytes(frame.encode('gbk'))
    for mode in ['normal','hot']:
        r=subprocess.run([runtime,str(frame_script),str(work),mode],capture_output=True,timeout=120)
        out=(r.stdout+r.stderr).decode('gbk','replace');print(out,flush=True)
        (work/('frame.'+mode+'.log')).write_text(out);assert r.returncode==0,(mode,r.returncode,out[-6000:])
        runs.append({'suite':'full_native_frame','mode':mode,'output':out})
    names=['patch_v279.py','test_v279.py','package_v279.py','player_changes_v279.json',
           'autosave_v279.lua','autosave_v279.ljbc','autosave_regression_v279.lua','autosave_regression_v273.lua']
    result={'version':'v1.279','all_passed':True,'sha256':hashlib.sha256(b).hexdigest(),
            'runs':runs,'all_42_modules_checked':True,'autosave_seconds':10,'completion_target_seconds':9,
            'runtime_version':subprocess.check_output([runtime,'-v'],stderr=subprocess.STDOUT).decode().strip(),
            'full_windows_game_run':False,'reproduced_v278_error_in_affinity_model':True,'native_main_context_required_in_tests':True,
            'scope':'main-state affinity model reproduces 278 CAT error; complete original collector, real Gly factory, native sort/codec/decoder prefix, proxies and UI; finite engine/file/crypto clocks, not Windows full client load/IO or timing',
            'tested_files':{n:hashlib.sha256((W/n).read_bytes()).hexdigest()for n in names}}
    (W/'validation_v279.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--runtime');args=p.parse_args();main(args.runtime or str(ensure_runtime()))
