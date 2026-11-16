# 归梦 v2.26 魔改维护工程

当前 **v1.246：幸运词条排版、零幸运规则、祝福油反馈及默认关闭信息栏**。

幸运词条放在需要等级下方，上下各留约半行，保留原字体和颜色。装备幸运0不触发，从1开始按现有公式生效；技能幸运独立保留。祝福油强化结果记录到信息栏，并用原游戏屏幕提示显示；每次进入游戏默认关闭左下角信息栏，仍可手动打开。[实际机制及概率修改方法](docs/祝福油与幸运系统.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.246.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.246_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v246.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

官方LuaJIT2.0正常/hot当前相关回归通过：装备/消费/佣兵及快捷来源、247完整生物回调、零幸运和1～7边界、实际物品提示与原生丰富文本布局、原消息/屏幕提示，以及进角色窗口和信息开关片段。图形/基础实体及事件调度为有限桥接，没有完整Windows渲染或退出读档实测。详见PROJECT_STATUS.md与第一百二十二节。

```bash
python3 maintenance/patch_v246.py
python3 maintenance/test_v246.py
python3 maintenance/package_v246.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows显式--runtime，不能用2.1或普通Lua。缺少固定245时顺链重建，依赖见maintenance/manifest.json；不默认递归历史全套。

保留240仓库按钮/莲月剑光、239永久Buff与238元素提示及此前累计修改；不擅改字体、颜色、边框。玩家说明55项，旧测试/报告/JSON/ZIP不回写。开始前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。不公开原始上传日志或覆盖存档。
