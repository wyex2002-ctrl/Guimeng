# 归梦 v2.26 魔改维护工程

**v1.281 将刺杀剑术和翔空剑法已有的锁定判定扩展到半月弯刀和十方斩。** 出手时锁定的敌人如果在结算前移出范围，只要仍有效，也会走一次原命中判定。还在格内时沿用该格伤害比例，周围怪物仍按各自所在格子判定。

本版沿用 v1.280 的5分钟自动存档、v1.267 常规祝福油掉落与赠油提示规则。

[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.281.zip) · [完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.281_maintenance.zip) · [校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v281.json)

```bash
python3 maintenance/patch_v281.py
python3 maintenance/test_v281.py
python3 maintenance/package_v281.py
```

普通与JIT热路径的对照覆盖原自动攻击、八个方向、移出格子、重复条目、换锁和失效目标。41个非业务改动模块及原分支核对通过。受控回归使用Linux x64 LuaJIT2.0和有限引擎替身，Windows完整实战待验证。 [工程状态](PROJECT_STATUS.md)
