# 归梦 v2.26 魔改维护工程

当前 **v1.241：补齐神水独立脚本的闪退修复**。

240只修了两个实际道具回调，其他规格仍可能报同样的效果乘法错误。241盘点49份同类消费脚本，补齐其余47份神水分支的默认倍率；按24种神水各自真正绑定的工厂和Main验证，保留原加成、持续时间、行会与佣兵效果、消费数量。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.241.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.241_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v241.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

官方LuaJIT2.0正常/hot当前回归通过：实际注册到工厂/自身Main的49份绑定、24种原神水模板及行会/佣兵边界、真实代理/元数据/库存使用/消费/BUFF增减、普通药品对照；旧240真实道具工厂可精确复现本次61411错误。修正240测试人为复用两个兄弟Main的覆盖缺口。42模块非目标保持；最终回血请求、图形与最终属性重算等有限，没有完整Windows客户端实测，详见PROJECT_STATUS.md与第一百一十七节。

```bash
python3 maintenance/patch_v241.py
python3 maintenance/test_v241.py
python3 maintenance/package_v241.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows显式--runtime，不能用2.1或普通Lua。缺少固定240时顺链重建，依赖见maintenance/manifest.json；不默认递归历史全套。

保留240仓库按钮/莲月剑光、239永久Buff与238元素提示及此前累计修改；不擅改字体、颜色、边框。玩家说明54项，旧测试/报告/JSON/ZIP不回写。开始前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。不公开原始上传日志或覆盖存档。
