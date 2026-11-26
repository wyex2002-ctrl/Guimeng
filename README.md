# 归梦 v2.26 魔改维护工程

**v1.343 基于 v1.342 仅针对「来世续缘」彻底消除存档约 600–774 ms 主线程卡顿并实现类网游每 3 秒静默自动存档：采用双层 WAL（`GMWAL1` 分帧流式序列化，单帧预算 `<= 3 ms`，绕开全树排序与阻塞式 `核心.RC4`，配合 `base_md5` 绑定与原子替换写入 `*.dat.wal`），支持崩溃/断电重进无损恢复及 `Quit Game` 正常退出时同步写回 100% 原版兼容 `.dat`；同步更新游戏窗口标题栏与登录界面版本号为 `1.343`。「前尘忆梦」与此前所有功能逻辑完全保留。**

```bash
python3 maintenance/patch_v343.py
python3 maintenance/test_v343.py
python3 maintenance/package_v343.py
```

[工程状态](PROJECT_STATUS.md)
