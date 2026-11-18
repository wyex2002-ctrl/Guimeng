# 归梦维护下载

当前 v1.279（2026-11-18，Asia/Shanghai）：修复分步自动存档的引擎接口兼容问题。

v1.278在自动存档的角色信息加密阶段可能取得布尔值并触发脚本退出。本版保留Lua采集、复制、排序和编码的分帧执行，把引擎加密、计时及写盘等调用交回原主循环上下文，避免引擎固定Lua状态与协程不兼容。

- [玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.279.zip)
- [完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.279_maintenance.zip)
- [校验值](checksums_v279.json)
- [源码与验证说明](https://github.com/wyex2002-ctrl/Guimeng/tree/f15b24dc7ed7819cdbbd3d1ae905ccf3869e2baa)

每10秒发起一轮，正常情况下以9秒内完成为目标；保留原自动存档条件。手动／退出保存取消旧自动任务后同步执行。原生加密、写盘等完整调用仍可能短暂停顿，9秒不是异常磁盘阻塞等情况下的硬保证。原存档格式和算法保持。

退出游戏，备份存档与原Lib/game.res后安装。**仍保留此前祝福油高掉落测试设置，建议使用存档副本。** v1.277动画修正、其他玩法与字体颜色边框保持。

log/guimeng_autosave_latest.txt／previous增加原生接口耗时、调用次数和失败接口。自动save.return只表示排队，autosave returned表示原保存函数已返回；不证明磁盘物理刷盘。没有Windows事件记录或系统转储设置。

normal/hot在主Lua状态限制模型下复现278同一行错误，279通过完整原采集器、旧格式解码区段、两剧情保存／退出、200轮、延期／取消／手动优先及原帧衔接和42模块核对。Linux x64官方滚动LuaJIT2.0，文件／加密及部分引擎有限桥接，非Windows x86 LuaJIT2.0.4实机或完整客户端读档验证。不换DLL、不关闭全局JIT。

旧版本双包全部保留，无Release。若再退出，重新打开游戏前复制整个log文件夹；重点保留新的autosave日志。
