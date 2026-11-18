# 归梦维护下载

当前 v1.281（2026-11-18，Asia/Shanghai）：半月弯刀与十方斩的锁定目标判定。

- [玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.281.zip)
- [完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.281_maintenance.zip)
- [校验值](checksums_v281.json)
- [源码与验证说明](https://github.com/wyex2002-ctrl/Guimeng/tree/bd5f988aedad35c9e125f17be905d7583c5693b3)

半月弯刀和十方斩自动出手时记录原锁定敌人。结算时目标仍有效，即使移出原格子，也会进行一次命中判定。目标还在格内时沿用该格的原伤害比例。周围怪物继续按原格子判定。

本版沿用v1.280的5分钟自动存档、常规祝福油掉落与赠油提示。替换前退出游戏并备份Lib/game.res与存档。

普通与JIT热路径回归覆盖原自动攻击、八方向和原格比例、原目标离开范围、换锁、重复条目及失效目标。回归使用Linux x64 LuaJIT2.0和有限引擎替身，Windows完整实战待验证。
