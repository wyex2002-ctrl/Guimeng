# 归梦 v2.26 魔改维护工程

当前 **v1.254：补齐远程武器包裹标题，取消佣兵战斗换装限制**。

刺客单手远程武器的包裹完整信息标题显示“（远程）”，普通及幻化标题均覆盖。佣兵战斗中可正常装备、卸下及更换武器；原装备条件继续保留。v253近战／8格远程双模式、远程蝉舞及累计玩法保持。字体、颜色、描边和边框未改。[本轮规则与验证边界](docs/佣兵武器显示与换装_v254.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.254.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.254_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v254.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

```bash
python3 maintenance/patch_v254.py
python3 maintenance/test_v254.py
python3 maintenance/package_v254.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows显式--runtime，不能用2.1或普通Lua。缺少固定253时顺链重建，依赖见maintenance/manifest.json；不默认递归历史全套。

验证范围与已观察到的JIT异常复查情况详见PROJECT_STATUS.md与第一百三十节。没有完整Windows实机／像素或读档验证。玩家说明56项，历史报告／JSON／ZIP不回写。开始前不查询或拉取GitHub，完成后同步main/downloads双包，无Release；不覆盖存档，不公开原始日志。
