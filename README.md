# 归梦维护下载

当前版本 v1.343（2026-11-26，Asia/Shanghai）。

仅针对「来世续缘」（「前尘忆梦」完全未改动）：本版彻底消除原版存档约 600–774 ms 主线程卡顿并实现类网游每 3 秒静默自动存档——采用双层 WAL 架构（`GMWAL1` 帧预算 `<= 3 ms/帧` 分帧快存，绕开全树排序与阻塞式 `核心.RC4`，原子写盘并绑定底层 `.dat` 24 位校验值，挂机发呆自动跳过冗余写盘；正常退出时同步写回 100% 原版兼容 `.dat` 并清理 `.wal`；异常退出后重进可自动恢复至几秒前进度）；同时更新游戏窗口标题栏与登录界面版本号为 `1.343`，完整保留 v1.342 N 键设置界面【Save】手动存档按钮及此前全部功能更新。

- [玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.343.zip)
- [完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.343_maintenance.zip)
- [校验值](checksums_v343.json)
- [源码与验证说明](https://github.com/wyex2002-ctrl/Guimeng/tree/d4425916244cecda2c9cede5c35bde877589ac7d)

退出游戏并备份存档及原 Lib/game.res 后，将玩家补丁中的 Lib 文件夹覆盖到游戏目录。受控与离线回归已通过；Windows 客户端实机体验以实测为准。
