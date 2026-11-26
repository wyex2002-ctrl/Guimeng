# 归梦 v2.26 魔改维护工程

**v1.345 基于 v1.344 仅针对「来世续缘」彻底修复 `v1.344` 读档完成瞬间闪退的问题（实机崩溃栈确认 `wal_safe_rawset` 对 `Gly独` 执行 `rawset` 触发了引擎底层的 `C:\cccyyy\main:68 -> 公共方法_.lua:216 -> os.exit()` 自保护强退）：完全移除 `runtime_v345.lua` 中全部 `rawset` 调用及对 `Gly独` 表的写入，改用与 `m14/256` 同源的纯字节码无篡改挂钩方式，在 `m14/253`（`Gly独.存档`）PC `0` 与 `核心.写到文件` 后分别接入 `S.__gm_wal_try_save_v345` / `S.__gm_wal_after_vanilla_save_v345`，在 `m14/99`（`Gly独.结束游戏`）PC `9` 接入 `S.__gm_wal_on_exit_v345`；同步更新游戏窗口标题栏与登录界面版本号为 `1.345`，完整保留 v1.342【Save】按钮、v1.343 双层 `GMWAL1` 3 秒静默自动存档与 LuaJIT 2.0 局部变量限制防线。「前尘忆梦」与此前所有功能逻辑完全保留。**

```bash
python3 maintenance/patch_v345.py
python3 maintenance/test_v345.py
python3 maintenance/package_v345.py
```

[工程状态](PROJECT_STATUS.md)
