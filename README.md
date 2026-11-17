# 归梦 v2.26 魔改维护工程

当前 **v1.275：技能入口诊断稳定性与轻量进度日志**。

修正旧技能入口诊断的高位临时寄存器及JMP存活范围风险，保留原目标选择与释放逻辑；新增小体积技能进度日志。玩家闪退根因仍未确认，未进行Windows客户端复现。[实现与验证范围](docs/技能入口诊断稳定性_v275.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.275.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.275_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v275.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包。

```bash
python3 maintenance/patch_v275.py
python3 maintenance/test_v275.py --resume
python3 maintenance/package_v275.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows构建显式--runtime，不用2.1或普通Lua。缺少固定274时顺链重建，依赖见maintenance/manifest.json，不默认递归历史全套。

普通大日志仍低频写盘，自动存档仍5秒，54项玩家正文、玩法、字体、颜色及边框保持。normal/hot相关回归与42模块静态对照通过，引擎、图形、存档及文件均为有限桥接。再次退出时，在重新打开游戏前复制整个log文件夹提供，包含新增的guimeng_skill_steps_latest.txt；无需重启电脑或Windows记录。修改前不查询或拉取GitHub，完成后同步main/downloads双包，旧包保留，无Release。
