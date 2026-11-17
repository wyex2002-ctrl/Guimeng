# 归梦 v2.26 魔改维护工程

当前 **v1.264：祝福油调整与20秒自动存档**。

坐骑新随机批次为1～50项，已生成批次继续原进度。角色首次进入成功收到赠油后，弹出“系统赠送一瓶祝福油。”确定框；满包／失败下次再检测，已领过不重复。新祝福油不可叠加，原有堆叠数量保留，快捷栏仍按背包实物逐瓶使用。自动存档间隔为20秒，保留原存档条件。字体、颜色和边框未改。[实现与验证边界](docs/祝福油与自动存档_v264.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.264.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.264_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v264.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

```bash
python3 maintenance/patch_v264.py
python3 maintenance/test_v264.py
python3 maintenance/package_v264.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows显式--runtime，不能用2.1或普通Lua。缺少固定263时顺链重建，依赖见maintenance/manifest.json；不默认递归历史全套。

normal/hot专项与42模块检查通过，包含两剧情快捷栏／佣兵用油、赠送与原确认框API、原生入包／整理、旧堆叠保留，以及真实时钟→完整原生更新→公开run→自动存档段。文件IO、图形及模态框为有限测试边界，未做Windows完整客户端实测。详见PROJECT_STATUS.md及第一百四十节。保留此前全部累计修改。玩家说明56项，旧报告／JSON／ZIP不回写；修改前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。
