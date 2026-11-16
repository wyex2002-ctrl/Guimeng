# 归梦 v2.26 魔改维护工程

当前 **v1.253：佣兵近战／远程双模式与更浅的金币地面名称**。

佣兵按武器实际绑定自动选择原版近战或8格远程；远程普攻和五主动技能均支持8格，蝉舞不再瞬移。战斗中禁止武器装备、卸下与替换，动态显示远程标识。金币地面名调淡为#FFF5CC。[完整规则及142件武器审计](docs/佣兵近远程模式_v253.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.253.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.253_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v253.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

官方LuaJIT2.0正常/hot专项与42模块检查通过：原生AI、蝉舞、换装入口、技能目标／延迟伤害及显示路径；完整地面构造器覆盖22药品和5金币。引擎、地图、动作和图形外围有限，未完成Windows实机及读档验证。详见PROJECT_STATUS.md与第一百二十九节。

```bash
python3 maintenance/patch_v253.py
python3 maintenance/test_v253.py
python3 maintenance/package_v253.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows显式--runtime，不能用2.1或普通Lua。缺少固定252时顺链重建，依赖见maintenance/manifest.json；不默认递归历史全套。

保留240仓库按钮/莲月剑光、239永久Buff与238元素提示及此前累计修改；不擅改字体、颜色、边框。玩家说明56项，旧测试/报告/JSON/ZIP不回写。开始前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。不公开原始上传日志或覆盖存档。
