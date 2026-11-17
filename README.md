# 归梦 v2.26 魔改维护工程

当前 **v1.267：低等级Boss祝福油掉落调整**。

调整低等级Boss的祝福油掉落机会。保留原己方击杀归属、每生命一次判定及其余祝福油规则。玩家说明不公开具体概率或隐藏随机参数，精确配置见维护源码与记录。字体、颜色及边框未改。[实现与验证边界](docs/祝福油低等级Boss掉落_v267.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.267.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.267_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v267.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

```bash
python3 maintenance/patch_v267.py
python3 maintenance/test_v267.py
python3 maintenance/package_v267.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows显式--runtime，不能用2.1或普通Lua。缺少固定266时顺链重建，依赖见maintenance/manifest.json；不默认递归历史全套。

normal/hot当前掉落专项与42模块非目标检查通过，覆盖实际原生死亡／重生／归属／物品保护／掉落及完整地面构造器，等级和整数判定边界、失败不重抽等。引擎随机、地图和图形为有限桥接，未做Windows完整客户端实测。保留此前全部累计玩法。详见PROJECT_STATUS.md及第一百四十三节。玩家说明54项，旧报告／JSON／ZIP不回写；修改前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。
