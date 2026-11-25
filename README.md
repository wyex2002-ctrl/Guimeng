# 归梦 v2.26 魔改维护工程

**v1.341 基于 v1.340 仅针对「来世续缘」进一步消除刺客佣兵远程技能（盛开/白莲/红莲/月桂/蝉舞）剩余延迟体感（清理 `Magic_04.empak` `<技能>_命中` 前置透明占位空帧并首帧预热、`跳斩`/`跳刺` 动作按攻速缩放对齐 `横切`、以及切换目标释放 `蝉舞` 时即时解除旧 `播放动作` 阻塞）；「前尘忆梦」与近战双手刺客完全不改动。**

```bash
python3 maintenance/patch_v341.py
python3 maintenance/test_v341.py
python3 maintenance/package_v341.py
```

[工程状态](PROJECT_STATUS.md)
