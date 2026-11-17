# 归梦 v2.26 魔改维护工程

当前 **v1.277：佣兵与召唤物动画入口稳定性修正**。

根据原始 dump 重建出的调用帧恢复异常，将动作切换和动画更新入口的新增调用移到参数后的连续临时槽，保留原有等待动画与后续动作逻辑。普通／JIT hot 针对性验证及42模块静态核对通过；尚未完成 Windows 32位客户端挂机验证，不保证涵盖全部历史闪退。[实现、证据与验证边界](docs/动画入口调用帧修正_v277.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.277.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.277_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v277.json)。退出游戏并备份存档及原Lib/game.res后安装。

**本版仍保留此前祝福油高掉落测试设置，建议使用存档副本。** 自动存档仍5秒，现有日志、其他玩法与字体颜色边框保持。

```bash
python3 maintenance/patch_v277.py
python3 maintenance/test_v277.py
python3 maintenance/package_v277.py
```

Python3.12+、标准库、现有官方LuaJIT2.0缓存。实际客户端为Windows x86 LuaJIT2.0.4，缓存是Linux x64滚动2.0分支，受控回归不等同于客户端验证。Windows测试须显式--runtime，不用2.1或普通Lua；本轮没有重建运行时，也没有替换客户端DLL。

只有22/89及22/97入口共7条指令的A字段与版本文字变化；参数、frame元数据、常量、调试记录、指令数量和分支目标保持。等待动画助手、伤害／技能时序、攻速、选敌／追击规则均保持。维护包仅包含脱敏后的dump证据摘要，不包含上传的原始内存、存档或DLL。

玩家54项正文保持，不公开概率。保留旧版本双包，不创建Release。修改前不查询或拉取GitHub，完成后同步main/downloads。若再次退出，重新打开游戏前复制整个log文件夹；已有独立ProcDump流程可继续使用，无需配置Windows事件记录或系统转储。
