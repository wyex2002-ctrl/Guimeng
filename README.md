# 归梦维护下载

当前 v1.272（2026-11-17）：自动存档改为20秒。普通日志每半秒一组进入／返回快照，不再每条事件写盘；错误、退出及存档前后仍即时记录。近期记录扩为256条，增加原诊断事件流、各类对象／窗口／定时器数组长度、Lua堆内存和累计计数。字体、颜色及边框保持。

- [玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.272.zip)
- [完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.272_maintenance.zip)
- [校验值](checksums_v272.json)
- [源码与验证说明](https://github.com/wyex2002-ctrl/Guimeng/tree/81677419f24f1183e2d713a60d70f764ad42f844)

退出游戏并备份存档及原Lib/game.res后安装玩家包。normal/hot降频日志、诊断原返回／错误身份、原退出链、实际构造器／公开run、完整原生帧／20秒存档及42模块检查通过。文件、保存、图形和终止为有限桥接，未进行完整客户端流畅度或闪退复现实测；根因仍未确认。日志固定文件覆盖，并非完整流水或冻结对象快照。不使用Windows事件记录或系统转储。若继续退出，重新打开游戏前复制整个log文件夹提供即可。旧包继续保留，无Release。
