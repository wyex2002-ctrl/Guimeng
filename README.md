# 归梦维护下载

当前 v1.270（2026-11-17）：补充游戏自身的退出请求及调用栈记录，不要求或使用Windows事件记录／系统转储。本次v269日志未记录自动保存请求、Lua错误或具体故障调用，根因仍未确认；本版不宣称修复闪退。保留全部玩法及3分钟自动存档。字体、颜色及边框未改。

- [玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.270.zip)
- [完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.270_maintenance.zip)
- [校验值](checksums_v270.json)
- [源码与验证说明](https://github.com/wyex2002-ctrl/Guimeng/tree/adbf67ae468edd4e1d76907d03bb08112b052332)

退出游戏并备份存档及原Lib/game.res后安装玩家包。normal/hot实际退出包装、保存退出、构造器／公开接口、完整原生帧／自动存档及42模块检查通过；文件、保存、图形和实际终止为有限桥接，未在完整客户端复现本次退出。新增guimeng_exit_latest.txt仅记录脚本退出请求，不能捕获底层原生故障。若仍退出，重新打开游戏前先复制整个log文件夹，后续只需提供游戏自身日志。旧包继续保留，无Release。
