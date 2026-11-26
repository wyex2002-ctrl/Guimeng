# 归梦 v2.26 魔改维护工程

**v1.344 基于 v1.343 仅针对「来世续缘」修复 `v1.343` 因主加载块内 `do ... end` 叠加导致活跃局部变量达 `210` 个（突破 LuaJIT 2.0 单函数 `200` 个活跃局部变量硬限制）使 `loadstring` 静默失败的问题：将双层 WAL 分帧快存与 3 秒静默自动存档模块封入独立参数即时执行函数（`S.__gm_wal_boot_v344`，主块活跃局部变量降至 `183`），并用 `rawset` 加固 `S.script_setting.Gly独` 与 `_G.Gly独` 双宿主只读元表挂钩、兼容数字字符串角色槽位；同步更新游戏窗口标题栏与登录界面版本号为 `1.344`，完整恢复【Save】手动存档按钮、无卡顿 `GMWAL1` 3 秒静默自动存档、异常退出恢复及正常退出写回原版 `.dat`。「前尘忆梦」与此前所有功能逻辑完全保留。**

```bash
python3 maintenance/patch_v344.py
python3 maintenance/test_v344.py
python3 maintenance/package_v344.py
```

[工程状态](PROJECT_STATUS.md)
