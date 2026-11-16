# v1.251 幸运词条上下8像素间距

玩家：[归梦v2.26_魔改补丁_v1.251.zip](归梦v2.26_魔改补丁_v1.251.zip)

完整维护包：[Guimeng_v1.251_maintenance.zip](Guimeng_v1.251_maintenance.zip)

校验：[checksums_v251.json](checksums_v251.json)

退出游戏并备份存档和原Lib/game.res，再覆盖玩家包。

幸运词条上下各8像素，使用原生像素位移，不插空白行；保留250字体、金色及对应装备名称描边、亮色祝福油提示和无效文案。概率与其他累计修复不变。

官方LuaJIT2.0 normal/hot相关回归和双包校验通过，原生排版/绘制验证两处8像素位移；图形/字体度量等外围有限，没有完整Windows实际画面验证。详见源码PROJECT_STATUS.md及第一百二十七节。

源码：https://github.com/wyex2002-ctrl/Guimeng/commit/1b6068242c265aeff106ca2df6dd236ea343adf0
