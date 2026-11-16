# v1.252 幸运空白行、提示对比及地面名称配色

玩家：[归梦v2.26_魔改补丁_v1.252.zip](归梦v2.26_魔改补丁_v1.252.zip)

完整维护包：[Guimeng_v1.252_maintenance.zip](Guimeng_v1.252_maintenance.zip)

校验：[checksums_v252.json](checksums_v252.json)

退出游戏并备份存档和原Lib/game.res，再覆盖玩家包。

删除幸运词条上下8像素位移，改为上下各一空白行。祝福油提示采用更饱和的亮绿/珊瑚红，保留与纯色的区别；地面各类金创药、魔法药及药包名称白色，金币名称淡黄。只改地面标签，不写物品或背包颜色；其他品质名称/描边、概率和既有修复保持。

官方LuaJIT2.0正常/hot相关回归和双包校验通过：原生富文本空白行、提示颜色；完整地面构造器覆盖22药品/药包和5金币、叠加/描边、其他物品及装备品质，200次代表调用，保留B3与佣兵闪退回归。图形/地图/引擎等外围有限，未完成Windows实际画面验证。详见源码PROJECT_STATUS.md及第一百二十八节。

源码：https://github.com/wyex2002-ctrl/Guimeng/commit/2d87edce957476fc95e20caf7a24e33510afcd6e
