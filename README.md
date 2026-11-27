# 归梦维护下载

当前版本 v1.346（2026-11-27，Asia/Shanghai）。

仅针对「来世续缘」（「前尘忆梦」完全未改动）：本版在已稳定运行的 `v1.345` 3 秒静默 GMWAL1 自动存档与【Save】按钮基础上，关闭并屏蔽原版游戏内全部零散自动存档触发（定期定时、任务/押镖/商店/锻造及自动 C 盘备份等 Ux雌.窗口相关.存档读档('存档', ...) 调用），统一由每 3 秒静默自动存档与【Save】手动按钮接管；完整保留手动【Save】、正常退出同步写回原版 .dat、新建角色首次建档、读档及「前尘忆梦」原版逻辑，并同步更新游戏窗口标题栏与登录界面版本号为 `1.346`。

- [玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.346.zip)
- [完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.346_maintenance.zip)
- [校验值](checksums_v346.json)
- [源码与验证说明](https://github.com/wyex2002-ctrl/Guimeng/tree/b8d9eacd0f42bf6737ae0662702227138a8b0524)

退出游戏并备份存档及原 Lib/game.res 后，将玩家补丁中的 Lib 文件夹覆盖到游戏目录。受控与离线回归已通过；Windows 客户端实机体验以实测为准。