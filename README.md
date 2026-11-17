# 归梦维护下载

当前 v1.269（2026-11-17）：自动存档间隔改为3分钟，沿用原存档条件，手动／退出存档保持。本次闪退日志中，最后采样帧及最近一次保存均已返回，但未记录具体故障调用；根因仍未确认，本版不宣称修复闪退。保留v268诊断和全部累计玩法。字体、颜色及边框未改。

- [玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.269.zip)
- [完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.269_maintenance.zip)
- [校验值](checksums_v269.json)
- [源码与验证说明](https://github.com/wyex2002-ctrl/Guimeng/tree/1ee9b88b045eb373041f00fe983c9c1cdbea2c64)

退出游戏并备份存档及原Lib/game.res后安装玩家包。normal/hot两剧情自动存档边界、原生时钟／完整帧／公开run及42模块非目标检查通过。文件、保存和图形存在有限桥接，未进行Windows客户端存档或闪退复现实测。若继续退出，除整个log文件夹外，需进一步结合Windows应用程序错误中的故障模块、异常代码或崩溃转储判断；重启前先复制日志。旧包继续保留，无Release。
