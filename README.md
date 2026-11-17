# v1.254 远程武器包裹标题与佣兵战斗换装

玩家：[归梦v2.26_魔改补丁_v1.254.zip](归梦v2.26_魔改补丁_v1.254.zip)

完整维护包：[Guimeng_v1.254_maintenance.zip](Guimeng_v1.254_maintenance.zip)

校验：[checksums_v254.json](checksums_v254.json)

退出游戏并备份存档和原Lib/game.res，再覆盖玩家包。

刺客单手远程武器在包裹完整信息的普通／幻化标题显示“（远程）”，包含实战杀伤刀。取消佣兵战斗中装备、卸下及更换武器的限制和相关检测，原职业／等级／类型等条件保留。佣兵近战／8格远程、远程蝉舞与累计玩法保持；字体、颜色、描边和边框未改。

官方LuaJIT2.0最终normal/hot专项与42模块检查通过，完整提示及原换装入口／请求均执行。首次hot探测曾一次进程SIGSEGV，有限复查未再现，根因未确认；不称已彻底排除。引擎、地图及UI／图形外围有限，未完成Windows实机、完整战斗换装或退出读档验证。详见源码PROJECT_STATUS.md与第一百三十节。保留历史下载，无Release。

源码：https://github.com/wyex2002-ctrl/Guimeng/commit/bd05cfb8183f46b78e59fd4e46981b4bb251a0a4
