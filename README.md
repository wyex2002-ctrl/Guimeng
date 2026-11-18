# 归梦 v2.26 魔改维护工程

当前 **v1.278：10秒周期的分步自动存档与阶段计时**。

沿用原自动存档条件，每10秒发起一轮，将物品采集、任务遍历、保存格式的排序和序列化分散到多帧，正常情况下以9秒内完成为目标。接近目标时提高每帧预算；不堆积任务，超时记录日志并继续完成。手动／退出保存取消未完成自动任务，立即同步保存最新数据。[实现与验证边界](docs/分步自动存档_v278.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.278.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.278_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v278.json)。退出游戏并备份存档及原Lib/game.res后安装。

新增 `log/guimeng_autosave_latest.txt`／`previous.txt`，记录准备、采集、冻结副本、角色信息处理、排序、序列化、校验、加密、写盘耗时及最大执行片段耗时。原生加密和写盘、部分完整处理段仍同步，不能保证完全没有停顿，也不能在程序暂停或磁盘阻塞时硬性保证9秒。

**仍保留此前祝福油高掉落测试设置，建议使用存档副本。** v1.277动画入口修正、其余战斗逻辑和字体颜色边框保持。允许几秒内的数据时间差，每件物品的数量、幸运与油序列一次采集；切图、换角色或死亡时取消旧任务。

```bash
python3 maintenance/patch_v278.py
python3 maintenance/test_v278.py
python3 maintenance/package_v278.py
```

当前Linux x64官方滚动LuaJIT2.0 normal/hot通过完整原生采集器、新旧数据包对照、旧读档解码区段、真实变量／属性代理与table库、两剧情保存／退出、200轮保存、调度取消／失败和原生完整帧衔接。文件、加密及部分引擎为有限桥接；受控时钟结果不是Windows实机耗时或完整客户端读档验证。实际Windows x86 LuaJIT2.0.4仍需实测，不换DLL、不关闭全局JIT、不重建C运行时。

42模块原指令和分支核对通过，未改模块22的任何字节。玩家说明仍54项，只更新第53条存档说明，不公开隐藏概率。开始修改前不查询或拉取GitHub，完成后同步main/downloads双包，保留旧包、不创建Release。
