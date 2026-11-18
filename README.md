# 归梦 v2.26 魔改维护工程

**v1.282 加入攻击命中自动施毒。** 主角习得施毒术后，普通攻击、指定近战招式和单体远程伤害技能实际命中当前锁定的怪物时，可以自动施毒。自动施毒沿用原版药粉、法力消耗和毒效果，并与手动施毒术共用冷却。

[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.282.zip) · [完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.282_maintenance.zip) · [校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v282.json)

```bash
python3 maintenance/patch_v282.py
python3 maintenance/test_v282.py
python3 maintenance/package_v282.py
```

Linux x64 LuaJIT 2.0 的普通与 JIT 热路径回归覆盖近战、投射命中、换锁、重复命中、药粉消耗和手动冷却互锁。Windows 客户端实战仍待验证。 [工程状态](PROJECT_STATUS.md)
