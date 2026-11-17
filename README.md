# 归梦 v2.26 魔改维护工程

当前 **v1.258：佣兵投射自转三倍速**。

佣兵远程普攻投出旋转武器，优先使用其地面掉落图像；蝉舞、月桂、红莲、白莲、盛开保留原特效并补充飞行表现。远程距离统一6格，双手近战保持原版。投射初速为当前剧情火球术的1.2倍，伤害到达后仍走原佣兵结算；出手节奏／费用／冷却／单次伤害／次数保持，首次命中推迟，稳定持续DPS不变；继续允许战斗换装。字体、颜色和边框未改。[实现与验证边界](docs/佣兵投射自转三倍速_v258.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.258.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.258_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v258.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

```bash
python3 maintenance/patch_v258.py
python3 maintenance/test_v258.py
python3 maintenance/package_v258.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows显式--runtime，不能用2.1或普通Lua。缺少固定254时顺链重建，依赖见maintenance/manifest.json；不默认递归历史全套。

最终normal/hot受控专项及42模块检查通过。佣兵武器飞行自转速度调整为上一版3倍（每秒9圈），逐帧对照确认飞行坐标、到达及伤害时刻保持。未做Windows实际像素或完整客户端战斗／读档验证。详见PROJECT_STATUS.md及第一百三十四节。玩家说明56项，旧报告／JSON／ZIP不回写；开始前不查询或拉取GitHub，完成后同步main/downloads双包，无Release，不覆盖存档或公开原始日志。
