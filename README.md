# 归梦 v2.26 魔改维护工程

当前 **v1.243：删除拾取勾选框并修复祝福油掉落报错**。

移除仓库左侧两行勾选框及每秒自动拾取，Alt仍拾取11×11范围并按原安全规则自动出售。祝福油掉落调用原本把物品与数量顺序传反，现已修正；每怪额外一瓶、红名说明及未开放的幸运效果保持。神水Buff具体加成提示保持。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.243.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.243_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v243.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

官方LuaJIT2.0正常/hot相关专项通过：原UI/仓库、Alt规则、完整零输入帧、真实死亡/数据保护/原生掉落函数/完整地面物品构造器。旧242油助手在同一实际链精确复现用户第94行number value错误。242仅用最终掉落请求替身，未发现参数顺序错误；本版补测这条实际链，旧报告不回写。底层图形/地图/引擎分配和公开操作桥接有限，没有完整Windows客户端实测。详见PROJECT_STATUS.md与第一百一十九节。

```bash
python3 maintenance/patch_v243.py
python3 maintenance/test_v243.py
python3 maintenance/package_v243.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows显式--runtime，不能用2.1或普通Lua。缺少固定242时顺链重建，依赖见maintenance/manifest.json；不默认递归历史全套。

保留240仓库按钮/莲月剑光、239永久Buff与238元素提示及此前累计修改；不擅改字体、颜色、边框。玩家说明54项，旧测试/报告/JSON/ZIP不回写。开始前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。不公开原始上传日志或覆盖存档。
