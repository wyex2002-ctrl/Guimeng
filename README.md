# 归梦 v2.26 魔改维护工程

当前 **v1.232：修复正常施法硬直清空长按的问题**。单体远程快捷键按住2秒启用自动与旋转绿边，松开后自动施法。正常硬直期间保留模式并暂停自动请求，恢复后继续；禁止攻击、界面交互、切图等取消条件保持。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.232.zip)、[维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.232_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v232.json)。退出游戏并备份存档及原Lib/game.res后安装玩家补丁。维护包不是安装包。

在仓库根目录运行：

```bash
python3 maintenance/patch_v232.py
python3 maintenance/test_v232.py
python3 maintenance/package_v232.py
```

Python3.12+，仅标准库；使用同梱官方LuaJIT2.0，Windows显式指定官方运行时，不能用2.1或普通Lua替代。缺少v231基线时沿保留的历史构建链重建。必要输入见maintenance/manifest.json；不要删除历史依赖。缓存、游戏目录和存档不提交Git。

本轮正常/hot通过原施法回调及公开主角硬直setter、231失败负对照、反复硬直期间长按启用/暂停请求/恢复、禁攻击取消及既有快捷释放、窗口、移动、绿边/冷却与日志专项。42模块非目标一致。同时修正26/3入口的高位寄存器调用。扩大回归曾hot间歇退出，修正入口后5次hot未复现；人工截取的硬直更新仍解释执行，完整自动助手及其余集成运行hot。物理输入和底层引擎原语有限，没有完整Windows客户端实测，详见PROJECT_STATUS.md及第一百零八节。

安装后重启，长按单体远程技能所在F1约3秒再松开。如仍无绿框，提供游戏log目录的guimeng_run_latest.txt、guimeng_detail_latest.txt、guimeng_critical_latest.txt及guimeng_error_latest.txt；重启过则附previous。新版repeat.*记录按键/长按/阻断原因/自动请求及绿框绘制，有数量上限，不逐帧写盘，不产生log/log。

玩家说明基准见docs/玩家版说明_基础版.txt，正文仍51项。main保存维护源码，downloads每版同步双包，无Release。各技能基础冷却见[清单](docs/reports/skill_cooldowns_v227.md)，本轮未改冷却规则。
