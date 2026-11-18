# 归梦维护下载

当前 v1.278（2026-11-18，Asia/Shanghai）：10秒周期的分步自动存档与阶段计时。

沿用原自动存档条件，每10秒发起一轮，将采集、整理、排序和序列化分散到多帧，正常情况下以9秒内完成为目标。接近目标时提高执行预算；超时继续分帧，不堆积任务。手动及退出保存取消旧自动任务后同步执行。

- [玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.278.zip)
- [完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.278_maintenance.zip)
- [校验值](checksums_v278.json)
- [源码与验证说明](https://github.com/wyex2002-ctrl/Guimeng/tree/3025043817f41e7bcfed7e88701e3123243d038d)

退出游戏并备份存档及原Lib/game.res后安装。**仍保留此前祝福油高掉落测试设置，建议使用存档副本。** 保留v1.277动画入口修正、其余玩法与字体颜色边框。

新增log/guimeng_autosave_latest.txt及previous，记录各阶段耗时、总耗时、最大执行片段和取消／失败等情况。原生加密、写盘和部分完整处理段仍同步，可能残留短暂停顿；9秒不是磁盘阻塞等异常情况下的硬保证。

normal/hot针对性回归、旧格式解码区段、两剧情保存／退出、200轮保存、调度取消及原生完整帧衔接和42模块核对通过。使用Linux x64官方滚动LuaJIT2.0，文件／加密及部分引擎为有限桥接，不是Windows x86 LuaJIT2.0.4实机耗时或完整客户端读档验证。不换DLL、不关闭全局JIT。

旧版本双包全部保留，无Release。若仍卡顿，请提供新的autosave日志；若再次退出，重新打开游戏前复制整个log文件夹。无需Windows事件记录或系统转储设置。
