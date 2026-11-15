# 归梦 v2.26 魔改维护工程

当前 **v1.231：修正隐藏子窗口阻断长按，增加自动技能检测日志**。真实背包子窗口在背包关闭时仍保留可视标记，旧版因此拒绝启动；现在沿父窗口/页面判断。单体远程快捷键按住2秒开启自动与旋转绿边，地面移动保留模式，到达后继续；再次按技能键、界面交互或切图等退出。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.231.zip)、[维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.231_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v231.json)。退出游戏并备份存档及原Lib/game.res后安装玩家补丁。维护包不是安装包。

在仓库根目录运行：

```bash
python3 maintenance/patch_v231.py
python3 maintenance/test_v231.py
python3 maintenance/package_v231.py
```

Python3.12+，仅标准库；使用同梱官方LuaJIT2.0，Windows显式指定官方运行时，不能用2.1或普通Lua替代。缺少v230基线时沿保留的历史构建链重建。必要输入见maintenance/manifest.json；不要删除历史依赖。缓存、游戏目录和存档不提交Git。

本轮正常/hot通过真实窗口构造/代理/父子绑定、230无法启用负对照、231长按/原施法/旋转绿边/移动及取消、原冷却专项和完整原生日志安装器验证。42模块非目标原型一致；物理输入及底层引擎原语有限，未做完整Windows客户端实测。详见PROJECT_STATUS.md和维护记录第一百零七节。

安装后重启，长按单体远程技能所在F1约3秒再松开。如仍无绿框，提供游戏log目录的guimeng_run_latest.txt、guimeng_detail_latest.txt、guimeng_critical_latest.txt及guimeng_error_latest.txt；重启过则附previous。新版repeat.*记录按键/长按/阻断原因/自动请求及绿框绘制，有数量上限，不逐帧写盘，不产生log/log。

玩家说明基准见docs/玩家版说明_基础版.txt，正文仍51项。main保存维护源码，downloads每版同步双包，无Release。各技能基础冷却见[清单](docs/reports/skill_cooldowns_v227.md)，本轮未改冷却规则。
