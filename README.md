# 归梦 v2.26 魔改维护工程

当前 **v1.249：祝福油阶梯概率与主角B3幸运**。

装备幸运0仍不生效，从1开始主角及主角宝宝使用B3，幸运7约51.33%；原技能幸运/幸运加持合并一次，攻防独立。祝福油双方坐骑使用新阶梯概率，0→7理论平均约998.27瓶，无保底，上限7。佣兵及其宝宝保留原独立战斗公式。[完整概率表、公式与边界](docs/祝福油与幸运系统.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.249.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.249_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v249.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

官方LuaJIT2.0 normal/hot当前相关回归通过：阶梯阈值/单次消费、精确状态模型、B3 0～9安全范围、真实技能幸运档位与多源合并、角色/宝宝实时装备和佣兵旧规则、实际库存/快捷/佣兵完整攻击、247完整生物回调及原字体/消息。保留248闪退修复，26与248字节一致；引擎/图形等外围有限，没有完整Windows长期实战或退出读档验证。详见PROJECT_STATUS.md与第一百二十五节。

```bash
python3 maintenance/patch_v249.py
python3 maintenance/test_v249.py
python3 maintenance/package_v249.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows显式--runtime，不能用2.1或普通Lua。缺少固定248时顺链重建，依赖见maintenance/manifest.json；不默认递归历史全套。

保留240仓库按钮/莲月剑光、239永久Buff与238元素提示及此前累计修改；不擅改字体、颜色、边框。玩家说明55项，旧测试/报告/JSON/ZIP不回写。开始前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。不公开原始上传日志或覆盖存档。
