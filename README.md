# 归梦 v2.26 魔改维护工程

当前 **v1.272：日志降频与20秒自动存档**。

普通诊断改为约每半秒一组进入／返回快照，不再每条事件写盘；错误、退出及存档前后仍即时记录。近期记录扩大至256条，补充原诊断事件流、对象／特效／窗口／定时器数组长度和Lua内存等上下文。自动存档恢复20秒，沿用原条件。[实现与验证范围](docs/日志降频与20秒存档_v272.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.272.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.272_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v272.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包。

```bash
python3 maintenance/patch_v272.py
python3 maintenance/test_v272.py --resume
python3 maintenance/package_v272.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows构建显式--runtime，不用2.1或普通Lua。缺少固定271时顺链重建，依赖见maintenance/manifest.json，不默认递归历史全套。

normal/hot日志／退出链／原生完整帧与20秒存档、42模块检查通过；未做完整客户端流畅度或闪退复现实测，闪退根因仍未确认。玩家54项第53条同步20秒。字体／颜色／边框不改，不使用Windows事件记录或系统转储。详见PROJECT_STATUS.md及第一百四十八节。修改前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。
