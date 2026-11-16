# 归梦 v2.26 魔改维护工程

当前 **v1.233：长按1.5秒启用，单帧超过3秒才取消**。Alt拾取及Q、W、E、V按键不因按键本身取消自动模式；正常硬直和地面移动保留模式，恢复后继续。实际打开背包/仓库、输入、切图等其他取消条件保持。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.233.zip)、[维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.233_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v233.json)。退出游戏并备份存档及原Lib/game.res后安装玩家补丁。维护包不是安装包。

在仓库根目录运行：

```bash
python3 maintenance/patch_v233.py
python3 maintenance/test_v233.py
python3 maintenance/package_v233.py
```

Python3.12+，仅标准库；使用同梱官方LuaJIT2.0，Windows显式指定官方运行时，不能用2.1或普通Lua替代。缺少v232基线时沿保留的历史构建链重建。必要输入见maintenance/manifest.json；不要删除历史依赖。缓存、游戏目录和存档不提交Git。

本轮正常/hot通过1.5秒临界值（15/60FPS）、3秒以内保留/严格超过3秒取消、Alt/Q/W/E/V及快捷列表Q豁免、旧232负对照，以及真实快捷释放、硬直、窗口、移动、绿框/CD和完整日志专项。42模块非目标一致。人工截取的硬直更新仅解释执行，完整助手和其余集成仍hot；没有完整Windows客户端或完整Alt拾取流程实测，详情见PROJECT_STATUS.md及第一百零九节。

安装后重启，长按单体远程技能快捷键 1.5 秒再松开。如仍无绿框，提供游戏log目录的guimeng_run_latest.txt、guimeng_detail_latest.txt、guimeng_critical_latest.txt及guimeng_error_latest.txt；重启过则附previous。新版repeat.*记录按键/长按/阻断原因/自动请求及绿框绘制，有数量上限，不逐帧写盘，不产生log/log。

玩家说明基准见docs/玩家版说明_基础版.txt，正文仍51项。main保存维护源码，downloads每版同步双包，无Release。各技能基础冷却见[清单](docs/reports/skill_cooldowns_v227.md)，本轮未改冷却规则。
