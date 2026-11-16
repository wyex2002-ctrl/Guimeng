# 归梦 v2.26 魔改维护工程

当前 **v1.238：核对两种防御Buff重复覆盖，补充元素加成提示**。

已按用户要求先同步GitHub的v1.237。幽灵盾、神圣战甲术重复成功施放时以新效果覆盖旧效果，即使新加成更低也会替换，同名不累加；两种技能各自独立。Buff悬停说明末尾新增“攻击元素总和越高，加成越高”。原永久效果、七元素公式、实际增量显示和死亡清除保持。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.238.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.238_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v238.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。安装后重新施放两招即可应用本次效果。

237原不可叠加配置与主角/事件角色的清除重建逻辑已支持最新覆盖，本轮保留并补测更强/更弱/相同覆盖，不添加重复清理。只修改两招专属说明的末尾拼接及版本文字；颜色、字体、边框、原技能费用/冷却和其他累计功能保持。

官方LuaJIT2.0正常/hot当前专项通过：两剧情、六档、19份分派，主角自身及独立友方目标真实公开接口/BUFF生命周期、加成降低覆盖/无残留、不互相覆盖、提示末句仅一次、永久状态及字段往返；42模块非目标一致。图形、角色基础与最终属性重算等有有限替身，没有完整Windows客户端实测，详见PROJECT_STATUS.md及维护记录第一百一十四节。

```bash
python3 maintenance/patch_v238.py
python3 maintenance/test_v238.py
python3 maintenance/package_v238.py
```

Python3.12+，标准库，官方LuaJIT2.0缓存；Windows显式指定--runtime，不使用2.1或普通Lua。缺少固定237基线时沿保留链重建，依赖见maintenance/manifest.json。不默认递归历史测试或重复干净重建。

玩家说明仍52项，历史快照不回写。日常仅用户要求时先拉取，完成后同步main/downloads双包，无Release。不提交缓存、游戏目录、存档或用户原始日志。
