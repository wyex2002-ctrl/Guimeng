# 归梦 v2.26 魔改维护工程

**v1.346 基于 v1.345 仅针对「来世续缘」屏蔽原版游戏内各处自带的自动存档触发（定期定时、任务/押镖/商店/锻造及自动 C 盘备份存档等），统一改由已稳定生效的 3 秒无卡顿 `GMWAL1` 静默自动存档与【Save】手动存档按钮接管：在 `runtime_v346.lua` 的 `S.__gm_wal_boot_v346` IIFE 中包装 `Ux雌.窗口相关.存档读档`，进入游戏且主存档已存在时拦截游戏内自动触发的 `存档读档('存档', ...)` 调用，完整保留手动【Save】、正常退出同步写回原版 `.dat`、新建角色首次建档、读档及「前尘忆梦」原版逻辑；同步更新游戏窗口标题栏与登录界面版本号为 `1.346`。「前尘忆梦」与此前所有功能逻辑完全保留。**

```bash
python3 maintenance/patch_v346.py
python3 maintenance/test_v346.py
python3 maintenance/package_v346.py
```

[工程状态](PROJECT_STATUS.md)
