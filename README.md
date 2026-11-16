# v1.250 祝福油提示与幸运词条样式

玩家：[归梦v2.26_魔改补丁_v1.250.zip](归梦v2.26_魔改补丁_v1.250.zip)

完整维护包：[Guimeng_v1.250_maintenance.zip](Guimeng_v1.250_maintenance.zip)

校验：[checksums_v250.json](checksums_v250.json)

退出游戏并备份存档和原Lib/game.res，再覆盖玩家包。

祝福油成功/无效提示使用更亮的柔绿，失败使用更亮的柔红。不变结果显示“祝福油使用无效。”，仍按原不变结果扣1瓶；成功/失败删除“坐骑”字样，佣兵保留归属。幸运词条去掉上下额外留白，保持金色与原字号，描边匹配对应装备名称（含七条属性名称样式）。不改变概率或其他已完成修复。

官方LuaJIT2.0 normal/hot相关回归和双包校验通过：原消息/消费、两种物品提示、原生字体及丰富文本绘制坐标，保留B3/阶梯与佣兵闪退回归。图形/字体度量和引擎等外围有限，没有完整Windows实际画面验证。详见源码PROJECT_STATUS.md及第一百二十六节。

源码：https://github.com/wyex2002-ctrl/Guimeng/commit/703b1d4df9b1783b9415360e8b54c6122f0750f5
