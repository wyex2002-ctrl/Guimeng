# 归梦维护下载

当前 v1.276（2026-11-17）：祝福油高掉落测试版。保留等级分档、击杀归属及原生掉落流程，临时强化掉落，用于排查战斗闪退，不代表常规掉落规则，也不宣称修复闪退。

- [玩家测试补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.276.zip)
- [完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.276_maintenance.zip)
- [校验值](checksums_v276.json)
- [源码与验证说明](https://github.com/wyex2002-ctrl/Guimeng/tree/70940ead8342fb65732899142410bea7d81e116f)

退出游戏并备份存档及原Lib/game.res后安装，建议用存档副本。等级判断次数不会随掉落强度增加，本版主要频繁触发物品生成落地分支，大量地面物品会增加场景负担，不能凭一次结果确定原闪退原因。官方LuaJIT2.0 normal/hot原死亡／分档／归属／掉落／地面构造专项及42模块对照通过；引擎地图图形为有限桥接，未做Windows挂机实测。

自动存档仍5秒、275日志及字体颜色边框保持。常规掉落对照v1.275及旧包保留，无Release。若再退出，重新打开游戏前复制整个log文件夹；不使用Windows记录或系统转储。
