# 归梦维护下载

当前版本 v1.347（2026-11-27，Asia/Shanghai）。

在 `v1.346` 基础上调整两处原本 `刷新间隔=0` 的一次性事件 Boss 为每 45 秒循环/重刷，完整保留 N 键【Save】手动存档、`GMWAL1` 每 3 秒静默自动存档及原生高频自动存档屏蔽，并同步更新窗口标题栏与登录界面版本号为 `1.347`：
- **火影地牢密室——冥影魔王（ID `1377`）**：`m12/18558 #1497` 改为 `刷新间隔=45`，进图 2 秒首刷后，每次击杀 45 秒原地重刷。
- **赤龙城——赤龙女王（ID `1477`）↔ 赤龙魔王（ID `1478`）45 秒循环**：「来世续缘」击杀赤龙女王后全难度统一 45 秒出现赤龙魔王，击杀赤龙魔王后 45 秒再次出现赤龙女王循环；「前尘忆梦」赤龙女王→赤龙魔王亦统一 45 秒。

- [玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.347.zip)
- [完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.347_maintenance.zip)
- [校验值](checksums_v347.json)
- [源码与验证说明](https://github.com/wyex2002-ctrl/Guimeng/tree/b4610020e2cb4218d4f99378599a62056e10d858)

退出游戏并备份存档及原 Lib/game.res 后，将玩家补丁中的 Lib 文件夹覆盖到游戏目录。受控与离线回归已通过；Windows 客户端实机体验以实测为准。