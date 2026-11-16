# v1.244 祝福油坐骑强化与幸运系统

玩家：[归梦v2.26_魔改补丁_v1.244.zip](归梦v2.26_魔改补丁_v1.244.zip)

完整维护包：[Guimeng_v1.244_maintenance.zip](Guimeng_v1.244_maintenance.zip)

校验：[checksums_v244.json](checksums_v244.json)

退出游戏并备份存档及原Lib/game.res，再覆盖玩家包。

祝福油右键强化已装备坐骑：0必成，1～6为40%升、30%降、30%不变，最高7；每次有效消耗1瓶。装备幸运影响主角与其召唤物攻防最大取值，技能幸运和原行会幸运直接相加，攻防各自独立一次。宝宝实时读取主角幸运。规则集中，说明见源码docs/祝福油与幸运系统.md。

正常/hot当前相关回归与双包校验通过；图形/实体基础等有限，只有保存字段重载，没有完整Windows存档重入/视觉实测。不增加拾取开关，保留原Alt11×11及每怪一瓶祝福油测试掉落。

源码：https://github.com/wyex2002-ctrl/Guimeng/commit/25dc5bbb0b038781679679b3b905858dea9dc18f
