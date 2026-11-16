# 当前补丁 v1.233：自动模式时长与按键豁免

玩家：[归梦v2.26_魔改补丁_v1.233.zip](归梦v2.26_魔改补丁_v1.233.zip)

完整维护包：[Guimeng_v1.233_maintenance.zip](Guimeng_v1.233_maintenance.zip)

校验：[checksums_v233.json](checksums_v233.json)

退出游戏，备份存档及原Lib/game.res，再覆盖玩家补丁。维护包用于开发。

长按单体远程技能快捷键1.5秒启用；单帧不超过3秒的卡顿保留模式，严格超过3秒才取消；Alt拾取及Q/W/E/V按键不因按键本身取消。实际打开背包/仓库、输入、死亡、禁攻击、切图等其他取消条件保持。原费用/CD/目标、硬直和地面移动规则保持。

官方LuaJIT2.0正常/hot专项和42模块非目标一致性、两包完整性与玩家资源匹配通过，包含时间边界及按键豁免和旧232负对照。人工截取的硬直更新仅解释执行，完整助手及其余集成hot；没有完整Windows客户端或完整Alt地面拾取/出售实测。详情见维护记录第一百零九节。

main/downloads同步，无Release，不公开原始日志、不覆盖存档。按约定开始前不查询或拉取GitHub。

源码：https://github.com/wyex2002-ctrl/Guimeng/commit/a5b9d2c606ce4528ce06d0f3177b9906bcaedef6
