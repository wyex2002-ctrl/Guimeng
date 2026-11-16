# v1.246 幸运排版、祝福油反馈与信息栏默认状态

玩家：[归梦v2.26_魔改补丁_v1.246.zip](归梦v2.26_魔改补丁_v1.246.zip)

完整维护包：[Guimeng_v1.246_maintenance.zip](Guimeng_v1.246_maintenance.zip)

校验：[checksums_v246.json](checksums_v246.json)

退出游戏并备份存档和原Lib/game.res，再覆盖玩家包。

幸运词条移至需要等级下方，上下各留约半行；原字体、颜色与描边保持。装备幸运0不触发，从1开始按现有规则生效。祝福油使用结果记录到信息栏，并用原屏幕提示即时显示；进游戏默认关闭左下角信息栏，可手动打开。佣兵与双方召唤物的独立幸运、祝福油强化概率及7点上限保持。

官方LuaJIT2.0正常/hot当前相关回归与双包校验通过；图形度量/实体基础/窗口和事件桥接有限，没有完整Windows渲染或退出读档实测。规则集中luck_rules_v246.lua，详见源码docs/祝福油与幸运系统.md及第一百二十二节。

源码：https://github.com/wyex2002-ctrl/Guimeng/commit/66e55adc179cd749abf1b50bd3eb01aa190eca05
