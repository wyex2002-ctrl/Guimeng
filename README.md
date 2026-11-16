# 归梦 v2.26 魔改维护工程

当前 **v1.251：幸运词条上下各8像素留白**。

幸运词条使用原生像素位移，上下各8像素，不插空白行。保留250字体、金色、对应装备名称描边，以及亮色祝福油提示和“无效”文案。幸运概率和其他功能保持。[完整幸运机制](docs/祝福油与幸运系统.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.251.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.251_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v251.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

官方LuaJIT2.0 normal/hot相关回归通过：原生格式化/解析/显示的实际坐标和高度、提示/描边/库存消息，保留B3/强化及佣兵闪退回归。图形/字体度量等外围有限，没有完整Windows画面实测。详见PROJECT_STATUS.md与第一百二十七节。

```bash
python3 maintenance/patch_v251.py
python3 maintenance/test_v251.py
python3 maintenance/package_v251.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows显式--runtime，不能用2.1或普通Lua。缺少固定250时顺链重建，依赖见maintenance/manifest.json；不默认递归历史全套。

保留240仓库按钮/莲月剑光、239永久Buff与238元素提示及此前累计修改；不擅改字体、颜色、边框。玩家说明55项，旧测试/报告/JSON/ZIP不回写。开始前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。不公开原始上传日志或覆盖存档。
