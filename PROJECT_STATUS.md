# 当前状态（2026-11-27，Asia/Shanghai）

当前 v1.345 基于 v1.344，**仅针对「来世续缘」**彻底修复 `v1.344` 实机读档完成即闪退的故障（「前尘忆梦」保持原版存档/读档/退出逻辑不变，同步更新窗口标题栏 `1.345` 等全部版本号，完整保留 v1.344 及之前全部累计修改）：
- **根因定位（`d:\guimeng2.26\Log\guimeng_exit_latest.txt` 实机崩溃栈确证）**：
  - `v1.344` 为绕过 `Gly独` 只读 `__newindex` 在 `wal_safe_rawset` 中调用 `pcall(rawset, tbl, k, v)`；而引擎底层（`C:\cccyyy\main:66-68`）对 `rawset` / `Gly独` 写保护挂有原生退出回调 `公共方法_.lua:216: exit` -> `Sys.lua:38: Osexit`（直接执行 `os.exit()`，`pcall` 无法拦截），导致 `__gm_load_state_v299(false)` 刚完成读档触发 `install_wal_hooks_v343()` 时进程立即退出。
- **v1.345 零写入纯字节码修复**（`runtime_v345.lua` / `patch_v345.py` / `test_v345.py`）：
  1. **零 `rawset`、零 `Gly独` 表写入**：完全删除 `wal_safe_rawset`、`wal_hook_single_gly`、`install_wal_hooks_v343` 及所有 `Gly独` 表写入，只向已有 `uv[0]=S` 普通表注册回调；
  2. **原生字节码挂钩 `m14/253` 与 `m14/99`**：
     - `m14/253`（`Gly独.存档`）PC `0` 注入 `S.__gm_wal_try_save_v345(path, hero_data, key)`，命中 `GMWAL1` 分帧快存直接 `RET0`；走原版写盘分支时在 `核心.写到文件` 后调用 `S.__gm_wal_after_vanilla_save_v345(path)` 刷新 `base_md5` 并清理陈旧 `.wal`；
     - `m14/99`（`Gly独.结束游戏`）PC `9`（`__gm_diag_exit_v164` 与 `Ae冻集.逻辑结束` 之前）注入 `S.__gm_wal_on_exit_v345(flag)` 同步刷回原版 `.dat` 并删除 `.wal`；
     - 沿用 `m14/256`（`Gly独.读档`）PC `1045` / `1111` 双 WAL 恢复钩子及 `S.__gm_wal_boot_v345` 独立 IIFE 寄存器帧（`<main>` 峰值 `183` 活跃局部变量）。
  3. **版本号同步**：更新 `m12/76` 游戏窗口标题栏（`不烧心版 1.345` / `1.345`）与 `m12/22232` 登录界面等全部版本号。

外层模块差异限定 `[12, 14, 30]`、`Dump.rebuild()` 与原型树校验、`m12/76` 窗口标题与 `m12/22232` 版本号校验、`m12/37` 零 `JMP A < params`、`m14/253` + `m14/99` + `m14/256` 字节码钩子、`runtime_v345.lua` 严格 Lua 5.1 语法 / 零 GBK `0x5C` / 零 `rawset` / LuaJIT 2.0 活跃局部变量审计（`<main> max=183`）、高危 `rawset` 与 `Gly独.__newindex` 双陷阱全程零触发验证、`GMWAL1` 分帧快存与 3 秒静默自动存档（200 次复用循环）、v1.342【Save】按钮及 v1.341/v1.340/v1.339/v1.338/v1.335 回归均已通过；Windows x86 实机读档进图、【Save】按钮与任务管理器强退 `.wal` 恢复效果待玩家实测确认。[构建报告](docs/reports/build_v345.json) · [验证报告](docs/reports/validation_v345.json)

逐版本定位和专项回归按功能查 [专项维护参考](docs/专项维护参考.md)。
