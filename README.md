# 归梦 v2.26 魔改维护工程

当前 **v1.274：分层战斗日志**。

补充目标变化、对象生命周期、技能状态和飞行道具记录；分层保护保存首次Lua错误的内层栈与上下文。普通日志继续缓冲、低频写盘，自动存档仍5秒。[实现与验证范围](docs/分层战斗日志_v274.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.274.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.274_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v274.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包。

```bash
python3 maintenance/patch_v274.py
python3 maintenance/test_v274.py --resume
python3 maintenance/package_v274.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows构建显式--runtime，不用2.1或普通Lua。缺少固定273时顺链重建，依赖见maintenance/manifest.json，不默认递归历史全套。

normal/hot真实构造器／只读接口、原技能／选择器／飞行道具、完整帧及存档／退出回归通过；42模块非目标检查通过。引擎、图形和IO为有限桥接，未做Windows客户端闪退复现，不宣称修复尚未确定根因的闪退，不使用Windows记录。再次退出时，重新打开游戏前复制整个log文件夹提供，无需重启电脑。玩家54项、玩法、字体、颜色及边框保持。详见PROJECT_STATUS.md及第一百五十节。修改前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。
