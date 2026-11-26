# 归梦维护下载

当前版本 v1.344（2026-11-26，Asia/Shanghai）。

仅针对「来世续缘」（「前尘忆梦」完全未改动）：本版修复 `v1.343` 因主加载块内 `do ... end` 叠加触发 LuaJIT 2.0 单函数 200 个活跃局部变量编译上限而导致运行库未加载的问题（改由独立注册表帧 IIFE `S.__gm_wal_boot_v344` 承载，主块降至 183 局部变量，并用 `rawset` 加固双宿主 `Gly独` 挂钩、兼容数字字符串角色槽位），正式恢复并启用 N 键【Save】手动存档按钮、无卡顿 `GMWAL1` 分帧快存（`<= 3 ms/帧`）、类网游每 3 秒静默自动存档、异常退出恢复及正常退出同步写回 100% 原版兼容 `.dat`；同步更新游戏窗口标题栏与登录界面版本号为 `1.344`，完整保留此前全部功能更新。

- [玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.344.zip)
- [完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.344_maintenance.zip)
- [校验值](checksums_v344.json)
- [源码与验证说明](https://github.com/wyex2002-ctrl/Guimeng/tree/977afce5e6d5a7caff079c8cf54eccf4e9c794de)

退出游戏并备份存档及原 Lib/game.res 后，将玩家补丁中的 Lib 文件夹覆盖到游戏目录。受控与离线回归已通过；Windows 客户端实机体验以实测为准。
