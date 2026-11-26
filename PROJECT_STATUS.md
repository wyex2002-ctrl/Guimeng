# 当前状态（2026-11-26，Asia/Shanghai）

当前 v1.344 基于 v1.343，**仅针对「来世续缘」**修复了 `v1.343` 在 LuaJIT 2.0 实机环境下运行库未加载的缺陷，使 `v1.342` 的【Save】手动存档按钮与 `v1.343` 的双层 WAL 分帧快存 + 类网游 3 秒静默自动存档均正常生效（「前尘忆梦」保持原版存档/读档/退出逻辑不变，同步更新窗口标题栏 `1.344` 等全部版本号，完整保留 v1.343 及之前全部累计修改）：
- **根因定位（实机现象与 AST 审计确认）**：
  - `v1.342` `runtime_v342.lua` 主块已有 `184` 个活跃局部变量；`v1.343` 在 `runtime_v343.lua` 顶层使用 `do ... end` 隔离 WAL 模块，而在 Lua 5.1 / LuaJIT 2.0 中 `do ... end` 仍共用所在函数的局部变量槽位，导致主块峰值达到 **`210` 个活跃局部变量**，超过 LuaJIT 2.0 单函数 **`200` 个活跃局部变量**硬上限，`m14/781` 中的 `loadstring(runtime_v343.lua)` 编译阶段静默返回 `nil`，致使整份运行库（含 `Save` 按钮与 WAL 自动存档）未执行，也因此任务管理器强杀后只有原版 `归梦_1.dat` 更新、未生成 `.wal`。
- **v1.344 修复与加固**（`runtime_v344.lua` / `patch_v344.py` / `test_v344.py`）：
  1. **IIFE 独立寄存器帧**：将 `v1.343` WAL 模块从 `do ... end` 改为显式传参即时执行函数 `S.__gm_wal_boot_v344=(function(S,G_ROOT,get_env_val,get_U,is_laishi,unproxy,now_ms) ... end)(...)`，并将 `load_state` 通知改为 `S.__gm_wal_on_load_state_v343`，主块活跃局部变量上限降至 **`183`（低于 `200`）**；
  2. **双宿主 + `rawset` 元表穿透加固**：`wal_hook_single_gly` 通过 `rawset` 绕过 `m14/302` 给 `Gly独` 设置的只读 `__newindex` 元表限制，同时以 `known_save_wraps` / `known_exit_wraps` 防重复嵌套，兼容 `S.script_setting.Gly独` 与 `_G.Gly独`；角色槽位经 `tonumber(U.人物选择)` 兼容数字字符串；
  3. **自动化局部变量防线**：在 `test_v344.py` 中固化 `assert_luajit20_local_limits(rt_src, max_limit=195)` 全 AST 递归检查，杜绝后续补丁再次触发 LuaJIT 2.0 `200` 局部变量编译上限；
  4. **版本号同步**：更新 `m12/76` 游戏窗口标题栏（`不烧心版 1.344` / `1.344`）与 `m12/22232` 登录界面等全部版本号。

外层模块差异限定 `[12, 14, 30]`、`Dump.rebuild()` 与原型树校验、`m12/76` 窗口标题与 `m12/22232` 版本号校验、`m12/37` 零 `JMP A < params`、`m14/256` 双 WAL 字节码钩子、`runtime_v344.lua` 严格 Lua 5.1 语法与零 GBK `0x5C`、全函数 LuaJIT 2.0 活跃局部变量上限审计（`<main> max=183`）、`rawset` 穿透只读元表与数字字符串槽位、`GMWAL1` 分帧快存与 3 秒静默自动存档（200 次复用循环）、v1.342【Save】按钮及 v1.341/v1.340/v1.339/v1.338/v1.335 回归均已通过；Windows x86 实机【Save】按钮、`.wal` 3 秒自动生成与任务管理器强退恢复效果待玩家实测确认。[构建报告](docs/reports/build_v344.json) · [验证报告](docs/reports/validation_v344.json)

逐版本定位和专项回归按功能查 [专项维护参考](docs/专项维护参考.md)。
