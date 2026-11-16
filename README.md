# 归梦 v2.26 魔改维护工程

当前 **v1.247：缩小幸运间距，翔空剑法保留出手目标判定**。

幸运词条上下额外留白各2像素，比246减少约67%，接近70%，字体和颜色保持。翔空剑法自动出手后，原锁定敌人即使移出范围仍判定一次；已在范围内不重复，其他格子的范围与伤害比例保持。[具体规则与实现边界](docs/翔空剑法锁定判定.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.247.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.247_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v247.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

官方LuaJIT2.0 normal/hot相关回归通过：原主角自动攻击/技能/范围收集和伤害分派、8朝向范围/比例与旧版对照、目标移动/死亡/换锁/去重及200次混合释放；原丰富文本布局和显示的绘制坐标、幸运/祝福油/佣兵与快捷消费回归。地图/最终命中伤害/字体图形等有限桥接，没有完整Windows鼠标或画面实测。详见PROJECT_STATUS.md与第一百二十三节。

```bash
python3 maintenance/patch_v247.py
python3 maintenance/test_v247.py
python3 maintenance/package_v247.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows显式--runtime，不能用2.1或普通Lua。缺少固定246时顺链重建，依赖见maintenance/manifest.json；不默认递归历史全套。

保留240仓库按钮/莲月剑光、239永久Buff与238元素提示及此前累计修改；不擅改字体、颜色、边框。玩家说明55项，旧测试/报告/JSON/ZIP不回写。开始前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。不公开原始上传日志或覆盖存档。
