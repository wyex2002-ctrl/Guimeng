# 归梦 v2.26 魔改维护工程

当前 **v1.245：佣兵独立幸运、佣兵祝福油与角色物品快捷栏**。

主角、佣兵分别使用自身装备累计幸运，双方召唤物各继承自己主人的幸运，互不混用。佣兵背包右键祝福油强化佣兵坐骑；主角背包或角色物品快捷栏强化主角坐骑。原0必成、40/30/30与上限7保持。旧油补快捷标记并重绑当前脚本，耗尽时不会免费使用快捷引用。[实际机制、主要函数和概率修改方法](docs/祝福油与幸运系统.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.245.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.245_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v245.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

官方LuaJIT2.0正常/hot当前专项通过：两套原装备累计/公开属性、原库存消费/数据代理、佣兵全档位、双方宝宝归属、两剧情真实快捷事件→按名称找实物→库存消费、佣兵背包真实右键，以及247完整生物回调。图形/基础实体及事件调度桥接有限，没有完整Windows拖拽/按键或退出读档实测；字段复制重载不等同完整存档验证。详见PROJECT_STATUS.md与第一百二十一节。

```bash
python3 maintenance/patch_v245.py
python3 maintenance/test_v245.py
python3 maintenance/package_v245.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows显式--runtime，不能用2.1或普通Lua。缺少固定244时顺链重建，依赖见maintenance/manifest.json；不默认递归历史全套。

保留240仓库按钮/莲月剑光、239永久Buff与238元素提示及此前累计修改；不擅改字体、颜色、边框。玩家说明55项，旧测试/报告/JSON/ZIP不回写。开始前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。不公开原始上传日志或覆盖存档。
