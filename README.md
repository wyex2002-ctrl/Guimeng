# v1.245 佣兵独立幸运与祝福油使用来源

玩家：[归梦v2.26_魔改补丁_v1.245.zip](归梦v2.26_魔改补丁_v1.245.zip)

完整维护包：[Guimeng_v1.245_maintenance.zip](Guimeng_v1.245_maintenance.zip)

校验：[checksums_v245.json](checksums_v245.json)

退出游戏并备份存档和原Lib/game.res，再覆盖玩家包。

佣兵与其召唤物使用佣兵自己的装备幸运，不借主角幸运。佣兵背包右键祝福油强化佣兵坐骑；主角背包/角色物品快捷栏强化主角坐骑。强化概率及7点上限保持；旧油自动补快捷标记/更新Main，引用无油时不免费强化或扣掉引用。其余物品右键转移行为保持。

官方LuaJIT2.0正常/hot当前相关回归和双包校验通过；图形/实体基础/事件桥接有限，没有完整Windows快捷输入/视觉或退出读档实测。规则集中luck_rules_v245.lua，详见源码docs/祝福油与幸运系统.md及第一百二十一节。

源码：https://github.com/wyex2002-ctrl/Guimeng/commit/1ab451ab8bb99dc7c40ab806c43b65ed5ccf35ce
