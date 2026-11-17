# 归梦 v2.26 魔改维护工程

当前 **v1.271：密集即时日志与3秒自动存档**。

按用户要求取消日志采样，每帧、阶段、对象、回调及动作分派前后立即写入游戏日志并附当前调用栈，接受额外性能开销；自动存档改为每3秒一次，沿用原存档条件。此次上传的旧错误文件与当前运行不同，当前闪退根因仍未确认，本版不宣称修复。[证据与验证边界](docs/密集日志与3秒存档_v271.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.271.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.271_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v271.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包。

```bash
python3 maintenance/patch_v271.py
python3 maintenance/test_v271.py --resume
python3 maintenance/package_v271.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows构建显式--runtime，不用2.1或普通Lua。缺少固定270时顺链重建，依赖见maintenance/manifest.json，不默认递归历史全套。

normal/hot密集日志、退出链、原生完整帧／3秒存档及42模块检查通过，未完成完整客户端闪退复现。玩家说明54项，第53条同步3秒，字体／颜色／边框不改。日志覆盖固定文件及最近48条记录，不是全程流水。若仍退出，在重新打开游戏前复制整个log文件夹提供，不需要Windows事件记录或系统转储。详见PROJECT_STATUS.md及第一百四十七节。修改前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。
