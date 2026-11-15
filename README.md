# 归梦 v2.26 魔改维护工程

当前 **v1.229：单体远程技能长按自动连续使用**。长按对应快捷键2秒进入自动模式，活动格显示旋转绿边；再次按技能键、鼠标点击、切图或进入交互/暂停等会退出。复用原手动快捷事件、费用和冷却检查，保留228蓄气CD遮罩及累计修改。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.229.zip)、[维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.229_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v229.json)。退出游戏并备份存档及原Lib/game.res后安装玩家补丁。维护包不是安装包。

在仓库根目录运行：

```bash
python3 maintenance/patch_v229.py
python3 maintenance/test_v229.py
python3 maintenance/package_v229.py
```

Python3.12+，仅标准库；测试使用同梱官方LuaJIT2.0，Windows需显式指定官方运行时，不能用2.1或普通Lua代替。缺少v228资源时沿保留的历史构建链重建。必要输入见maintenance/manifest.json；不要删除历史依赖。构建缓存、游戏目录和存档不提交Git。

本轮正常/hot真实快捷闭包、原最近目标扫描/技能释放、长按/取消和地图清理、绿色精灵包装通过，保留228蓄气CD与召唤CD回归；42模块一致性和原指令/分支检查通过。修正技能构造器三条旧跳转的活跃槽边界。底层图形、物理输入、子弹飞行和最终伤害为有限测试边界，新增帧头按真实插入片段验证，未完成完整Windows启动/视觉/切图或实战测试。详见PROJECT_STATUS.md及维护记录第一百零五节。历史报告仅为历史证据。

玩家说明基准见docs/玩家版说明_基础版.txt，当前51项。复现问题请提供游戏log目录的guimeng_detail_latest.txt、guimeng_critical_latest.txt及原错误日志，重启后提供previous文件；不产生log/log。main保存维护源码，downloads每版同步补丁及维护包，不创建Release。

各技能基础冷却核对见[清单](docs/reports/skill_cooldowns_v227.md)。未修改技能冷却规则。
