# 归梦维护下载

当前 v1.277（2026-11-18，Asia/Shanghai）：佣兵与召唤物动画入口稳定性修正。

根据原始dump中的调用帧恢复异常，将动作切换和动画更新入口的新增调用移到参数后的连续临时槽，保留原有等待动画及后续动作逻辑。

- [玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.277.zip)
- [完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.277_maintenance.zip)
- [校验值](checksums_v277.json)
- [源码与验证说明](https://github.com/wyex2002-ctrl/Guimeng/tree/eb6e8fd67d4064cbc576089c782d6040092c0dd4)

**本版仍保留此前祝福油高掉落测试设置，建议使用存档副本。** 退出游戏并备份存档及原Lib/game.res后安装。自动存档仍5秒，现有日志、其他玩法与字体颜色边框保持。

普通／JIT hot针对性回归及42模块静态核对通过，测试为Linux x64官方滚动LuaJIT2.0，有限图形／引擎／动作事件边界，未做Windows x86 LuaJIT2.0.4客户端挂机验证，不保证涵盖全部历史闪退。不关闭全局JIT、不替换DLL、不增加日志频率。

旧版本双包全部保留，无Release。若再次退出，重新打开游戏前复制整个log文件夹；用户现有独立ProcDump流程可继续使用，无需Windows事件记录或系统转储设置。
