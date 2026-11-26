# 归梦维护下载

当前版本 v1.345（2026-11-27，Asia/Shanghai）。

仅针对「来世续缘」（「前尘忆梦」完全未改动）：本版彻底修复 `v1.344` 实机读档完成时因调用 `rawset` 写入 `Gly独` 触发引擎底层 `C:\cccyyy\main:68 -> 公共方法_.lua:216 -> os.exit()` 而瞬间闪退的问题——完全移除 `runtime_v345.lua` 中全部 `rawset` 与 `Gly独` 表写入，改为在 `m14/253`（`Gly独.存档`）PC `0` / `核心.写到文件` 后与 `m14/99`（`Gly独.结束游戏`）PC `9` 直接通过纯字节码调用 `uv[0]=S` 回调，保留 `m14/256` `.wal` 恢复钩子、N 键【Save】按钮、`GMWAL1` 无卡顿 3 秒静默自动存档及 LuaJIT 2.0 `<= 200` 活跃局部变量防线，并同步更新游戏窗口标题栏与登录界面版本号为 `1.345`。

- [玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.345.zip)
- [完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.345_maintenance.zip)
- [校验值](checksums_v345.json)
- [源码与验证说明](https://github.com/wyex2002-ctrl/Guimeng/tree/c098ec5bc9ecd1f84a9bfa440cbc3e185c73e4ea)

退出游戏并备份存档及原 Lib/game.res 后，将玩家补丁中的 Lib 文件夹覆盖到游戏目录。受控与离线回归已通过；Windows 客户端实机体验以实测为准。