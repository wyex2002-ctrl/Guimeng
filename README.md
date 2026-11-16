# 归梦 v2.26 魔改维护工程

当前 **v1.248：修复佣兵攻击触发幸运时的闪退**。

佣兵元素计算复用了技能伤害变量，未配置技能伤害时可能把“防火元素”等文字传给幸运计算。此次补回默认伤害上下限0，再由原技能配置覆盖；保留原幸运概率、伤害公式、翔空锁定判定与界面。[根因与验证边界](docs/佣兵幸运攻击闪退修复.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.248.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.248_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v248.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

官方LuaJIT2.0 normal/hot相关回归通过：完整原生佣兵攻击回调、真实公开属性/随机包装与幸运助手；旧247字符串/nil/装备表错误负对照，新248七元素/幸运0～7/触发与未触发、配置默认和200次混合调用。保留幸运/祝福油及界面相关回归；26与247逐字节一致。引擎整数、图形和基础实体等为有限桥接，没有Windows完整长时间战斗实测。详见PROJECT_STATUS.md与第一百二十四节。

```bash
python3 maintenance/patch_v248.py
python3 maintenance/test_v248.py
python3 maintenance/package_v248.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows显式--runtime，不能用2.1或普通Lua。缺少固定247时顺链重建，依赖见maintenance/manifest.json；不默认递归历史全套。

保留240仓库按钮/莲月剑光、239永久Buff与238元素提示及此前累计修改；不擅改字体、颜色、边框。玩家说明55项，旧测试/报告/JSON/ZIP不回写。开始前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。不公开原始上传日志或覆盖存档。
