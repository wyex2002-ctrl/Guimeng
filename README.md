# 归梦 v2.26 魔改维护工程

当前 **v1.263：坐骑祝福油分批随机序列**。

每匹坐骑独立保存一批5～10个随机值和进度，按实际用油时的幸运套用原概率。读档保留已生成批次，最后一个值消耗后，等下一次有效用油才抽新批次；允许恢复换批前存档重抽下一批。旧坐骑首次有效用油时初始化，转移／整理保留进度。幸运、指针和扣油在原库存消费位置一并提交，原概率及+7上限保持。字体、颜色和边框未改。[实现与验证边界](docs/祝福油随机批次_v263.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.263.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.263_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v263.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

```bash
python3 maintenance/patch_v263.py
python3 maintenance/test_v263.py
python3 maintenance/package_v263.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows显式--runtime，不能用2.1或普通Lua。缺少固定262时顺链重建，依赖见maintenance/manifest.json；不默认递归历史全套。

normal/hot专项与42模块检查通过，包含真实物品消费／两剧情快捷栏／佣兵右键、原物品保存字段采集及序列化读回、转移和批次边界。未做Windows完整客户端存档退出重入、仓库画面或系统强杀实测。详见PROJECT_STATUS.md及第一百三十九节。保留此前佣兵远程／主动技能原时序／己方命中／Tab和等待动画等累计修改。玩家说明56项，旧报告／JSON／ZIP不回写；修改前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。
