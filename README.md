# v1.234 技能失效诊断版

本版用于定位自动模式退出后原技能快捷键无效的偶发问题。尚未确认最终根因，不声称已经修复。

玩家：[归梦v2.26_魔改补丁_v1.234.zip](归梦v2.26_魔改补丁_v1.234.zip)

完整维护包：[Guimeng_v1.234_maintenance.zip](Guimeng_v1.234_maintenance.zip)

校验：[checksums_v234.json](checksums_v234.json)

退出游戏，备份存档及原Lib/game.res，再覆盖玩家包；维护包用于开发。

保留233的1.5秒启用、3秒卡顿阈值、Alt/Q/W/E/V豁免和所有原释放限制。只新增按技能键时的repeat.skill_probe，记录冷却/可触发/动作/硬直及队列等，2秒限频、每30秒最多12条，不受旧240条会话诊断上限影响。不会清CD、强解角色状态或修改技能效果。

再次卡住时按住失效技能键约3秒，或间隔2秒按几次，然后尽快提供本次critical/detail/run/error；重启过附previous。普通/hot相关回归及两包校验通过，无完整Windows实测；硬直倒计时截取片段解释执行，完整助手和其他集成hot。详情见维护记录第一百一十节。

main/downloads同步，无Release，不公开原始日志、不覆盖存档。开始前不拉取GitHub。

源码：https://github.com/wyex2002-ctrl/Guimeng/commit/3d8822b1dd9640e6fa1fc09176175802e05c2aaa
