# 归梦 v2.26 魔改维护工程

**v1.342 基于 v1.341 仅针对「来世续缘」在按 N 键打开的系统设置界面（`系统窗口` / 561）底部红框位置新增对齐的【Save】手动存档按钮（复用 `-1480207602.img` 石质金边按钮 1:1 三段拼接并具备正常/悬停/按下/存档成功闪烁状态与防连点/拖拽/阵亡校验，调用原生 `Ux雌.窗口相关.存档读档` 随时存档）；「前尘忆梦」与此前所有功能逻辑完全保留。**

```bash
python3 maintenance/patch_v342.py
python3 maintenance/test_v342.py
python3 maintenance/package_v342.py
```

[工程状态](PROJECT_STATUS.md)
