# 归梦 v2.26 魔改维护工程

当前 **v1.270：游戏内退出请求诊断**。

本次v269日志在3分钟存档前已退出，未记录Lua错误或具体故障调用。根因仍未确认，本版不宣称修复闪退。补充游戏自身的退出请求和调用栈记录，不要求或使用Windows事件记录／转储。玩法及3分钟自动存档保持。[诊断范围与使用方法](docs/游戏内退出诊断_v270.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.270.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.270_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v270.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

```bash
python3 maintenance/patch_v270.py
python3 maintenance/test_v270.py --resume
python3 maintenance/package_v270.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows构建显式--runtime，不能用2.1或普通Lua。缺少固定269时顺链重建，依赖见maintenance/manifest.json，不默认递归历史全套。

normal/hot退出请求、原保存退出、构造器／公开run、完整原生帧／自动存档及42模块检查通过；未完成完整客户端闪退复现。玩家说明54项不变，字体／颜色／边框不改。若继续退出，重新打开游戏前先复制整个log文件夹，包含新增guimeng_exit_latest.txt。其仅记录脚本退出请求，不能捕获底层原生故障。详见PROJECT_STATUS.md及第一百四十六节。修改前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。
