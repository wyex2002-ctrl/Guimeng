# 归梦 v2.26 魔改维护工程

当前 **v1.250：祝福油亮色提示、无效文案与幸运词条样式**。

成功/无效提示改为亮柔绿，失败改为亮柔红；不变结果显示“祝福油使用无效。”，成功/失败去掉“坐骑”。幸运词条去掉额外上下留白，保留金色，描边与对应装备名称一致。概率、幸运0无效和此前修复保持。[完整幸运机制](docs/祝福油与幸运系统.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.250.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.250_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v250.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

官方LuaJIT2.0正常/hot相关回归通过：实际消息/库存消费、新文案和颜色、两种物品提示、原生字体/名称描边和丰富文本绘制坐标；保留B3/阶梯和佣兵闪退回归。图形/引擎等外围有限，没有完整Windows画面实测。详见PROJECT_STATUS.md与第一百二十六节。

```bash
python3 maintenance/patch_v250.py
python3 maintenance/test_v250.py
python3 maintenance/package_v250.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows显式--runtime，不能用2.1或普通Lua。缺少固定249时顺链重建，依赖见maintenance/manifest.json；不默认递归历史全套。

保留240仓库按钮/莲月剑光、239永久Buff与238元素提示及此前累计修改；不擅改字体、颜色、边框。玩家说明55项，旧测试/报告/JSON/ZIP不回写。开始前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。不公开原始上传日志或覆盖存档。
