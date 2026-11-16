# 归梦 v2.26 魔改维护工程

当前 **v1.240：神水闪退修复、莲月剑光减速、仓库按钮变窄**。

修复六种神水默认效果倍率未初始化的错误，保留原效果、时长和行会加成。莲月剑光播放速率变为原来的80%，伤害时点与攻击节奏保持；仓库按钮宽度变为原来的80%（默认44×22），右边缘不动，原反馈/开关/配色保持。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.240.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.240_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v240.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

官方LuaJIT2.0正常/hot相关回归通过：24个神水规格、二份脚本/两剧情、原代理/元数据/库存使用/消耗及Buff属性；旧239精确复现上传两处错误。实际莲月技能/特效播放链及其他剑光/伤害时点、仓库原生控件/按钮/精灵和反馈均检查；42模块非目标保持。底层图形、基础数据/最终属性重算及物品使用前UI事件有限，没有完整Windows实机验证，详见PROJECT_STATUS.md及第一百一十六节。

```bash
python3 maintenance/patch_v240.py
python3 maintenance/test_v240.py
python3 maintenance/package_v240.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows显式--runtime，不能用2.1或普通Lua。缺少固定239时顺链重建，依赖见maintenance/manifest.json；不默认递归历史全套。

保留239永久Buff和238元素提示及此前累计修改；不擅改字体、颜色或边框。玩家说明54项，历史JSON/ZIP不回写。开始前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。不提交缓存、游戏目录、存档或上传日志。
