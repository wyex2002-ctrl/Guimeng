from pathlib import Path
import hashlib,json,zipfile
from patch_v177 import W
OUT=W.parent/'deliverables'
def txt(s):return ('\ufeff'+s.lstrip('\ufeff').replace('\r\n','\n').replace('\n','\r\n')).encode('utf8')
def package():
 b=json.loads((W/'build_v177.json').read_text());v=json.loads((W/'validation_v177.json').read_text())
 data=(W/'game_v177.res').read_bytes();sha=hashlib.sha256(data).hexdigest()
 assert v['all_passed'] and v['version']=='v1.177' and sha==b['sha256']==v['sha256']
 c=json.loads((W/'player_changes_v177.json').read_text());assert len(c)==48
 player='《归梦v2.26【激活版】魔改补丁v1.177》玩家使用说明\n\n'
 player+='使用：完全退出游戏，备份存档及原Lib/game.res，再将补丁内Lib文件夹复制到游戏目录并覆盖同名文件。已有角色可继续使用；新角色赠品仅在创建角色时发放，新装备生成规则用于后续掉落。\n\n'
 player+='相比原版的累计修改：\n\n'+'\n\n'.join(str(i)+'. '+s for i,s in enumerate(c,1))+'\n'
 assert not any(s in player for s in ['%','％','11倍','12倍','堆栈','受控','测试','验证','LuaJIT','Windows'])
 intro=f'当前版本：v1.177（2026-11-13）\n当前game.res：{len(data):,}字节；SHA-256：{sha}\n\nv1.177调整玛法名俊每日双倍为4小时并补齐当天差额，改善已开启时的余额提示；恢复指定五类装备的暴击及破防词条，衣服不出攻击元素；修正声望数值兼容和实际Sys日志接收对象。尚无本轮实机杀怪日志，普通怪声望的剩余实机原因未确认，须依据新版日志继续诊断。保留v1.175/v1.176启动和沙箱修复。以文末第四十四节为准。\n\n'
 maint=intro+(W/'history_through_v176.txt').read_text(encoding='utf-8-sig')+'\n\n'+(W/'maintenance_notes_v177.txt').read_text()
 OUT.mkdir(exist_ok=True)
 playerzip=OUT/'归梦v2.26_魔改补丁_v1.177.zip';kit=OUT/'Guimeng_v1.177_maintenance.zip'
 with zipfile.ZipFile(playerzip,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  z.writestr('Lib/game.res',data);z.writestr('log/',b'');z.writestr('使用说明_玩家版.txt',txt(player))
 names=['base_v176.zip','ljtool.py','ljdis.py','patch_v139.py','bytecode_relocate.py','resource_tools.py','native_test_utils.py',
  'daily_double_v177.lua','daily_double_v177.ljbc','activate_double_v177.lua','activate_double_v177.ljbc','kill_reputation_v177.lua','kill_reputation_v177.ljbc',
  'patch_v177.py','test_v177.py','package_v177.py','systems_regression_v177.lua','reputation_regression_v177.lua','LuaJIT-2.0-b83bcba.tar.gz',
  'build_v177.json','validation_v177.json','player_changes_v177.json','history_through_v176.txt','maintenance_notes_v177.txt']
 with zipfile.ZipFile(kit,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name in names:z.write(W/name,name)
  z.writestr('修改记录_维护版.txt',txt(maint))
  z.writestr('README.txt',txt('维护工程，不放入游戏目录。先读修改记录_维护版.txt开头及文末第四十四节。以base_v176.zip为基线，依次运行python3 patch_v177.py、python3 test_v177.py、python3 package_v177.py。patch/test可用--runtime指定官方LuaJIT2.0。无runtime时patch读取附带的编译字节码，test从附带源码构建。数据库沙箱没有pcall或xpcall，不得通过_G回退给数据库测试补齐缺失API。原Sys.script_setting显式导出与保护已纳入回归。普通怪声望实机原因尚未确认，需要新版杀怪日志；完整Windows客户端未运行。native_work及compile_work只用于测试，不可安装。'))
 for path in [playerzip,kit]:
  with zipfile.ZipFile(path) as z:assert z.testzip() is None
  print(json.dumps({'file':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()},ensure_ascii=False))
 with zipfile.ZipFile(playerzip) as z:
  assert z.namelist()==['Lib/game.res','log/','使用说明_玩家版.txt'] and z.read('Lib/game.res')==data
if __name__=='__main__':package()
