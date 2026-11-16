# 归梦 v2.26 魔改维护工程

当前 **v1.252：幸运空白行、提示对比和药品/金币地面名称配色**。

幸运词条删除8像素位移，改为上下各一空白行。祝福油提示提高红绿饱和度，保留与纯色的区别；各类金创药、魔法药及药包地面名称为白色，金币为淡黄色。只调整地面标签，不改背包或物品模板颜色。[地面配色规则](docs/地面药品与金币名称配色.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.252.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.252_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v252.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

官方LuaJIT2.0正常/hot相关回归通过：原生排版空白行/提示/字体、完整新旧地面构造器与22药/5金币模板、叠加和描边、其他物品/装备品质对照及200次构造。保留B3、阶梯和佣兵闪退回归。图形/地图/引擎等外围有限，没有完整Windows画面实测。详见PROJECT_STATUS.md与第一百二十八节。

```bash
python3 maintenance/patch_v252.py
python3 maintenance/test_v252.py
python3 maintenance/package_v252.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows显式--runtime，不能用2.1或普通Lua。缺少固定251时顺链重建，依赖见maintenance/manifest.json；不默认递归历史全套。

保留240仓库按钮/莲月剑光、239永久Buff与238元素提示及此前累计修改；不擅改字体、颜色、边框。玩家说明55项，旧测试/报告/JSON/ZIP不回写。开始前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。不公开原始上传日志或覆盖存档。
