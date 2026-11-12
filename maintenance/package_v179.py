from pathlib import Path
import hashlib,json,zipfile
W=Path(__file__).resolve().parent
ROOT=W.parent

def package():
 data=(W/'game_v179.res').read_bytes();sha=hashlib.sha256(data).hexdigest()
 b=json.loads((W/'build_v179.json').read_text());v=json.loads((W/'validation_v179.json').read_text())
 assert v['all_passed'] and v['version']=='v1.179' and b['sha256']==v['sha256']==sha
 c=json.loads((W/'player_changes_v177.json').read_text());assert len(c)==48
 info='《归梦 v2.26 魔改补丁 v1.179》\n\n使用：退出游戏，备份存档及原 Lib/game.res，将本包 Lib 文件夹覆盖到游戏目录。\n排查问题：重现后退出游戏，将 log 中本次详细日志、关键日志及错误日志一起提供。重开游戏会将上一轮日志保留为 previous。\n\n累计功能：\n\n'+'\n\n'.join(str(i)+'. '+s for i,s in enumerate(c,1))+'\n'
 out=W/'deliverables';out.mkdir(exist_ok=True)
 player=out/'归梦v2.26_魔改补丁_v1.179.zip'
 with zipfile.ZipFile(player,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  z.writestr('Lib/game.res',data);z.writestr('log/',b'');z.writestr('使用说明_玩家版.txt',('\ufeff'+info).encode('utf-8'))
 manifest=json.loads((W/'manifest.json').read_text(encoding='utf-8'))
 names=manifest['package_files']+manifest['generated_reports']
 assert len(names)==len(set(names))
 kit=out/'Guimeng_v1.179_maintenance.zip'
 with zipfile.ZipFile(kit,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name in names:z.write(ROOT/name,name)
 result=[]
 for p in [player,kit]:
  with zipfile.ZipFile(p) as z:assert z.testzip() is None
  result.append({'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 with zipfile.ZipFile(player) as z:assert z.read('Lib/game.res')==data
 (out/'checksums_v179.json').write_text(json.dumps({'resource_sha256':sha,'packages':result},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':package()
