# 归梦 v2.26 魔改维护工程

当前 **v1.273：自动存档5秒**。

自动存档间隔由20秒改为5秒，沿用原条件。日志频率、扩展覆盖、玩法、字体、颜色及边框保持v1.272。[实现与验证范围](docs/自动存档5秒_v273.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.273.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.273_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v273.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包。

```bash
python3 maintenance/patch_v273.py
python3 maintenance/test_v273.py
python3 maintenance/package_v273.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows构建显式--runtime，不用2.1或普通Lua。缺少固定272时顺链重建，依赖见maintenance/manifest.json，不默认递归历史全套。

normal/hot两剧情存档边界、原生时钟／完整帧／当前构造器与公开run及42模块非目标检查通过；未做完整客户端存档IO实测。玩家54项第53条同步5秒，不宣称修复未确定根因的闪退，不使用Windows事件记录或系统转储。详见PROJECT_STATUS.md及第一百四十九节。修改前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。
