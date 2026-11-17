# 归梦 v2.26 魔改维护工程

当前 **v1.265：玩家说明精简与1秒长按连发**。

按用户原编号润色指定玩家说明，删除原22、42条后连续编号为54项；原第52条现为第50条。单体远程技能长按开启自动连续使用的实际门槛由1.5秒改为1秒，沿用原快捷回调、持续施放与退出条件。字体、颜色及边框未改。[实现与验证边界](docs/玩家说明与1秒连发_v265.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.265.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.265_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v265.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

```bash
python3 maintenance/patch_v265.py
python3 maintenance/test_v265.py
python3 maintenance/package_v265.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows显式--runtime，不能用2.1或普通Lua。缺少固定264时顺链重建，依赖见maintenance/manifest.json；不默认递归历史全套。

normal/hot当前专项与42模块检查通过：实际类注册／更新入口／技能槽回调，1秒临界点、多帧率与原退出边界；输入、图形和技能请求为有限桥接，未做Windows完整客户端实测。说明删除仅影响玩家文案，累计玩法及本版未涉及的祝福油／20秒存档等保持。详见PROJECT_STATUS.md及第一百四十一节。玩家说明54项，旧报告／JSON／ZIP不回写；修改前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。
