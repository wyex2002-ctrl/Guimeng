from pathlib import Path
import argparse,hashlib,json,zipfile
from patch_v177 import W
OUT=W/'deliverables'
def txt(s):return ('\ufeff'+s.lstrip('\ufeff').replace('\r\n','\n').replace('\n','\r\n')).encode('utf8')
def package():
 b=json.loads((W/'build_v177.json').read_text(encoding='utf-8'));v=json.loads((W/'validation_v177.json').read_text(encoding='utf-8'))
 data=(W/'game_v177.res').read_bytes();sha=hashlib.sha256(data).hexdigest()
 assert v['all_passed'] and v['version']=='v1.177' and sha==b['sha256']==v['sha256']
 c=json.loads((W/'player_changes_v177.json').read_text(encoding='utf-8'));assert len(c)==48
 player='《归梦v2.26【激活版】魔改补丁v1.177》玩家使用说明\n\n'
 player+='使用：完全退出游戏，备份存档及原Lib/game.res，再将补丁内Lib文件夹复制到游戏目录并覆盖同名文件。已有角色可继续使用；新角色赠品仅在创建角色时发放，新装备生成规则用于后续掉落。\n\n'
 player+='相比原版的累计修改：\n\n'+'\n\n'.join(str(i)+'. '+s for i,s in enumerate(c,1))+'\n'
 assert not any(s in player for s in ['%','％','11倍','12倍','堆栈','受控','测试','验证','LuaJIT','Windows'])
 maint=(W/'修改记录_维护版.txt').read_text(encoding='utf-8-sig')
 OUT.mkdir(exist_ok=True)
 playerzip=OUT/'归梦v2.26_魔改补丁_v1.177.zip';kit=OUT/'Guimeng_v1.177_maintenance.zip'
 with zipfile.ZipFile(playerzip,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  z.writestr('Lib/game.res',data);z.writestr('log/',b'');z.writestr('使用说明_玩家版.txt',txt(player))
 names=['base_v176.zip','ljtool.py','ljdis.py','patch_v139.py','bytecode_relocate.py','resource_tools.py','native_test_utils.py',
  'daily_double_v177.lua','daily_double_v177.ljbc','activate_double_v177.lua','activate_double_v177.ljbc','kill_reputation_v177.lua','kill_reputation_v177.ljbc',
  'patch_v177.py','test_v177.py','package_v177.py','systems_regression_v177.lua','reputation_regression_v177.lua','LuaJIT-2.0-b83bcba.tar.gz',
  'build_v177.json','validation_v177.json','player_changes_v177.json','history_through_v176.txt','maintenance_notes_v177.txt',
  'AGENTS.md','PROJECT_STATUS.md','.gitignore']
 with zipfile.ZipFile(kit,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name in names:z.write(W/name,name)
  z.writestr('修改记录_维护版.txt',txt(maint))
  z.writestr('README.txt',txt((W/'README.txt').read_text(encoding='utf-8-sig')))
 for path in [playerzip,kit]:
  with zipfile.ZipFile(path) as z:assert z.testzip() is None
  print(json.dumps({'file':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()},ensure_ascii=False))
 with zipfile.ZipFile(playerzip) as z:
  assert z.namelist()==['Lib/game.res','log/','使用说明_玩家版.txt'] and z.read('Lib/game.res')==data
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=OUT);a=ap.parse_args()
 OUT=a.output.resolve();package()
