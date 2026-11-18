# 归梦 v2.26 魔改维护工程

当前 **v1.279：修复分步自动存档的引擎接口兼容问题**。

v1.278自动存档在角色信息加密时可能取得错误类型并触发脚本退出。279保留Lua采集、复制、排序及编码的分帧执行，把引擎加密、计时和写盘等调用交回原主循环上下文执行。[原因与验证边界](docs/分步存档引擎接口修正_v279.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.279.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.279_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v279.json)。退出游戏并备份存档及原Lib/game.res后安装。

沿用原自动存档条件，每10秒发起一轮，正常情况下以9秒内完成为目标。接近目标提高预算，不堆积任务。手动／退出同步保存会取消旧自动任务。原生加密、写盘等完整调用仍可能短暂停顿，不能硬性保证9秒或完全不卡。

`log/guimeng_autosave_latest.txt`／`previous.txt`记录各阶段、原生接口耗时／次数、最大切片和失败。自动save.return仅表示排队，新autosave returned表示原保存函数已返回。没有Windows事件记录或系统转储配置。

**仍保留此前祝福油高掉落测试设置，建议使用存档副本。** v1.277动画入口修正、其余玩法和字体颜色边框保持，54项玩家正文不变，不公开隐藏概率。

```bash
python3 maintenance/patch_v279.py
python3 maintenance/test_v279.py
python3 maintenance/package_v279.py
```

normal/hot在主Lua状态限制模型中复现278同一行错误，279通过完整原采集器／旧格式解码区段、真实变量／属性代理与table库、两剧情保存／退出、200轮及延期／取消／错误传递和原生完整帧衔接。42模块及277／278差异核对通过，模块22整个字节不变。

当前测试为Linux x64官方滚动LuaJIT2.0，文件、加密及部分引擎有限桥接，不是Windows x86 LuaJIT2.0.4实机效果或完整客户端读档验证。不换DLL、不关闭全局JIT、不重建C运行时。开始前不查询或拉取GitHub，完成后同步main/downloads双包，保留旧包，不创建Release。
