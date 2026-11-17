# 归梦 v2.26 魔改维护工程

当前 **v1.268：打怪闪退诊断版**。

补充主更新、佣兵／召唤物更新阶段及存档前后的有界日志。上传日志未记录Lua错误，根因尚未确认，本版不宣称修复闪退。退出后先复制整个log文件夹，再启动游戏；请一并提供新增native_watch与原critical、run、detail日志。[诊断范围与使用方法](docs/打怪闪退定位_v268.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.268.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.268_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v268.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

```bash
python3 maintenance/patch_v268.py
python3 maintenance/test_v268.py
python3 maintenance/package_v268.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows显式--runtime，不能用2.1或普通Lua。缺少固定267时顺链重建，依赖见maintenance/manifest.json；不默认递归历史全套。

normal/hot诊断与原生帧／受控自动存档回归、42模块非目标检查通过。未进行Windows完整客户端实测。玩法及54项玩家说明保持。详见PROJECT_STATUS.md及第一百四十四节。修改前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。
