# 归梦 v2.26 魔改维护工程

当前 **v1.276：祝福油高掉落测试版**。

保留祝福油等级分档、击杀归属及原生掉落流程，临时提高掉落强度，用于排查战斗闪退。此版用于测试，不代表常规掉落规则，也不宣称修复闪退。[实现与验证范围](docs/祝福油高掉落测试_v276.md)。

下载：[玩家测试补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.276.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.276_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v276.json)。退出游戏并备份存档及原Lib/game.res后安装，建议使用存档副本。

```bash
python3 maintenance/patch_v276.py
python3 maintenance/test_v276.py
python3 maintenance/package_v276.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows构建显式--runtime，不用2.1或普通Lua。缺少固定275时顺链重建，依赖见maintenance/manifest.json，不默认递归历史全套。

本次normal/hot原生死亡／等级分档／归属／掉落／地面构造专项及42模块静态对照通过，图形、地图、引擎和文件为有限桥接，未做Windows客户端挂机实测。等级判断次数不随掉率倍率增加，此测试主要频繁触发生成落地分支；大量地面物品也会增加场景负担，不能仅凭一次结果确定原闪退原因。

自动存档仍5秒，日志及字体、颜色、边框沿用275。玩家54项正文保持，包内开头明确标注测试用途，不公开精确掉率。常规掉落对照包v1.275及旧包继续保留。修改前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。
