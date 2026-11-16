# 归梦 v2.26 魔改维护工程

当前 **v1.236：切换到其他程序时保留自动施法模式**。失焦期间屏蔽本助手对其他程序键鼠输入的响应，切回首帧不会因残留按键误取消；游戏持续更新时仍走原自动施法流程。其他独立的死亡、暂停、界面和切图等取消条件保持。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.236.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.236_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v236.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

正常/hot当前回归通过：失焦保留/旧235负对照、后台键鼠隔离、原技能回调/释放、Alt+Tab、返焦残留输入与长间隔、再次真实按技能键取消；42模块非目标一致。没有完整Windows焦点切换或后台施法实测。引擎本身若暂停后台更新，不会因此强制它运行，详情见PROJECT_STATUS.md及第一百一十二节。

```bash
python3 maintenance/patch_v236.py
python3 maintenance/test_v236.py
python3 maintenance/package_v236.py
```

Python3.12+，标准库，官方LuaJIT2.0缓存；Windows显式指定--runtime，不使用2.1或普通Lua。缺少固定235基线时按保留链重建，依赖见maintenance/manifest.json。硬直更新是解释执行的明示截取片段，完整助手/其余相关集成仍hot，物理输入和底层图形/地图等有限。

保留1.5秒启用、前台帧超过3秒取消、Alt/Q/W/E/V豁免及235修正。月魂灵波仍须可用护身符：用户已确认补充后恢复释放，材料规则未改。诊断仍在原log，不产生log/log；异常提供critical/detail/run/error，重启过附previous。

玩家说明仍51项，历史JSON/ZIP不回写。开始前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。不提交缓存、游戏目录、存档或用户原始日志，不擅自改配色。
