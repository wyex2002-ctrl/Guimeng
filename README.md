# 归梦维护下载

当前 v1.275（2026-11-17）：修正旧技能入口诊断的寄存器／热编译存活范围风险，保留原目标选择与技能释放；新增小体积技能进度日志。此前玩家闪退根因仍未确认，未进行Windows客户端复现。

- [玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.275.zip)
- [完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.275_maintenance.zip)
- [校验值](checksums_v275.json)
- [源码与验证说明](https://github.com/wyex2002-ctrl/Guimeng/tree/4e19011fc3b458bbdc0285432eddda452fdf8208)

退出游戏并备份存档及原Lib/game.res后安装玩家包。普通大日志仍低频写盘，自动存档仍5秒，54项玩家正文、玩法、字体、颜色及边框保持。官方LuaJIT2.0相关normal/hot回归与42模块静态对照通过；引擎、图形、文件及存档为有限桥接，不冒充完整客户端实测。

若再退出，在重新打开游戏前复制整个log文件夹，包含新增guimeng_skill_steps_latest.txt；无需重启电脑或Windows事件记录、系统转储。旧包保留，无Release。
