# 归梦维护下载

当前 v1.271（2026-11-17）：按用户要求启用密集即时游戏内日志，取消帧／阶段／对象／回调／动作记录采样，每次附当前调用栈，接受额外性能开销。自动存档改为每3秒一次，沿用原条件。当前闪退根因尚未确认，本版不宣称修复。不要求或使用Windows事件记录／系统转储；字体、颜色和边框保持。

- [玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.271.zip)
- [完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.271_maintenance.zip)
- [校验值](checksums_v271.json)
- [源码与验证说明](https://github.com/wyex2002-ctrl/Guimeng/tree/4e64e04b7003dae13e3a286087651a0f3b6dd711)

退出游戏并备份存档及原Lib/game.res后安装玩家包。normal/hot密集日志、原退出链、实际构造器／公开run、完整原生帧／3秒存档及42模块核对通过；文件、保存、图形和终止为有限桥接，尚未完整客户端复现闪退。日志覆盖固定文件并保留最近48条记录，可能明显影响流畅度，但不是无限增长的全程流水。若再退出，重新打开游戏前复制整个log文件夹提供即可。旧包继续保留，无Release。
