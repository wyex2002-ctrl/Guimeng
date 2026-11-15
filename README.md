# 归梦 v2.26 魔改维护工程

当前 **v1.230：修正悬停时长按不生效，移动保留自动模式**。单体远程技能按住2秒开启自动与旋转绿边，悬停查看说明不再阻断；点击地面移动保留模式，到达后继续。再次按技能键、点击交互对象/UI、输入、切图等退出，冷却/费用/伤害保持。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.230.zip)、[维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.230_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v230.json)。退出游戏并备份存档及原Lib/game.res后安装玩家补丁。维护包不是安装包。

在仓库根目录运行：

```bash
python3 maintenance/patch_v230.py
python3 maintenance/test_v230.py
python3 maintenance/package_v230.py
```

Python3.12+，仅标准库；测试使用同梱官方LuaJIT2.0，Windows需显式指定官方运行时，不能用2.1或普通Lua代替。缺少v229资源时沿保留的历史构建链重建。必要输入见maintenance/manifest.json；不要删除历史依赖。构建缓存、游戏目录和存档不提交Git。

本轮正常/hot通过：实际原生视口/快捷栏悬停片段、229无法启动的负对照、月魂灵波真实快捷/选敌/释放链及2秒计时、地面移动保留与交互取消、绿边/地图清理及原冷却回归。42模块非目标一致，只替换26/88及版本显示。输入、路径标记、图形和最终伤害为有限替身，没有完整Windows客户端或真实寻路/移动交接实测；实际观感仍需安装确认。详见PROJECT_STATUS.md及维护记录第一百零六节。

玩家说明基准见docs/玩家版说明_基础版.txt，当前51项。复现问题请提供游戏log目录的guimeng_detail_latest.txt、guimeng_critical_latest.txt及原错误日志，重启后提供previous文件；不产生log/log。main保存维护源码，downloads每版同步补丁及维护包，不创建Release。

各技能基础冷却核对见[清单](docs/reports/skill_cooldowns_v227.md)。未修改技能冷却规则。
