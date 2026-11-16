# 归梦 v2.26 魔改维护工程

当前 **v1.242：神水加成提示、拾取开关及祝福油测试掉落**。

神水Buff悬停追加实际增加的属性与数值。仓库左侧新增两行勾选框：“拾取时自动出售”每次进入角色默认开启，“自动拾取”默认关闭、开启后每秒执行同一Alt拾取逻辑。范围改为11×11。祝福油每击败一只敌方怪物额外掉落一瓶，名称红色并更新说明；幸运效果仍为预览，使用不消耗。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.242.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.242_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v242.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

官方LuaJIT2.0正常/hot相关回归通过：49份真实道具工厂/原生神水Buff加成及消费、实际控件/仓库开关、原生角色默认值与帧拾取入口、范围边界/出售保护、原生死亡及复活/公开Sys/数据代理。图形、字体、地面物品拾取与最终掉落请求等为明确有限接口，没有完整Windows客户端实测，详见PROJECT_STATUS.md与第一百一十八节。

```bash
python3 maintenance/patch_v242.py
python3 maintenance/test_v242.py
python3 maintenance/package_v242.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows显式--runtime，不能用2.1或普通Lua。缺少固定241时顺链重建，依赖见maintenance/manifest.json；不默认递归历史全套。

保留240仓库按钮/莲月剑光、239永久Buff与238元素提示及此前累计修改；不擅改字体、颜色、边框。玩家说明54项，旧测试/报告/JSON/ZIP不回写。开始前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。不公开原始上传日志或覆盖存档。
