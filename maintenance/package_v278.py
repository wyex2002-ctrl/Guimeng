from pathlib import Path
import hashlib,json,zipfile,re
W=Path(__file__).resolve().parent
ROOT=W.parent

def package():
 data=(W/'game_v278.res').read_bytes();sha=hashlib.sha256(data).hexdigest()
 b=json.loads((W/'build_v278.json').read_text(encoding='utf-8'));v=json.loads((W/'validation_v278.json').read_text(encoding='utf-8'))
 for name,digest in v['tested_files'].items():assert hashlib.sha256((W/name).read_bytes()).hexdigest()==digest,(name,'changed since test')
 assert v['all_passed'] and v['version']=='v1.278' and b['sha256']==v['sha256']==sha
 c=json.loads((W/'player_changes_v278.json').read_text(encoding='utf-8'));basis=(ROOT/'docs/玩家版说明_基础版.txt').read_text(encoding='utf-8')
 numbered=re.findall(r'^(\d+)\. (.+)$',basis,re.M)
 assert [int(n)for n,_ in numbered]==list(range(1,len(c)+1)) and [s for _,s in numbered]==c
 assert len(c)==54 and basis.count('使用：')==basis.count('排查问题：')==1
 info=basis.replace('《归梦 v2.26 魔改补丁》玩家版说明','《归梦 v2.26 魔改补丁 v1.278》',1)
 info=info.replace('》','》\n\n【分步自动存档】每10秒发起一轮，正常情况下每轮9秒内完成；手动及退出保存保持同步。仍保留此前祝福油高掉落测试设置，建议使用存档副本。',1)
 out=W/'deliverables';out.mkdir(exist_ok=True)
 player=out/'归梦v2.26_魔改补丁_v1.278.zip'
 with zipfile.ZipFile(player,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  z.writestr('Lib/game.res',data);z.writestr('log/',b'');z.writestr('使用说明_玩家版.txt',('\ufeff'+info).encode('utf-8'))
 manifest=json.loads((W/'manifest.json').read_text(encoding='utf-8'))
 names=manifest['package_files']+manifest['generated_reports']
 assert len(names)==len(set(names))
 kit=out/'Guimeng_v1.278_maintenance.zip'
 with zipfile.ZipFile(kit,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name in names:z.write(ROOT/name,name)
 result=[]
 for p in [player,kit]:
  with zipfile.ZipFile(p) as z:assert z.testzip() is None
  result.append({'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 with zipfile.ZipFile(player) as z:assert z.read('Lib/game.res')==data
 (out/'checksums_v278.json').write_text(json.dumps({'resource_sha256':sha,'packages':result},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':package()
