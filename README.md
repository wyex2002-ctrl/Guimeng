# 归梦维护下载

当前 v1.257（2026-11-17）：佣兵武器飞行自转修复。武器图片一边飞行一边绕自身中心持续旋转，每秒三圈。修复私有视觉回调被脚本登记分派跳过的问题。飞行速度沿用256的当前剧情火球术×1.2，6格射程、出手节奏与伤害时序保持；双手近战保持。

- [玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.257.zip)
- [完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.257_maintenance.zip)
- [校验值](checksums_v257.json)
- [源码与验证说明](https://github.com/wyex2002-ctrl/Guimeng/tree/9331e1145c8cbd25ea906c6430a521242851f3a4)

退出游戏并备份存档及原Lib/game.res后安装玩家包。normal/hot专项通过，连续攻击出手及伤害时刻对照一致；底层图形为有限记录边界，未做Windows客户端画面验证。旧包继续保留。
