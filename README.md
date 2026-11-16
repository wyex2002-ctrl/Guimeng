# 归梦 v2.26 魔改维护工程

当前 **v1.237：幽灵盾、神圣战甲术永久生效，并显示实际加成**。

两招加成改为技能基础值加七种攻击元素合计的50%（向上取整一次）。Buff图标隐藏倒计时，悬停显示防御与抵抗的实际增量；只增加防御上限，原有死亡清除规则保持。旧Buff读入后取消计时，重施后按新公式计算。护身符、MP和冷却规则不变。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.237.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.237_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v237.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。安装后重新施放两招即可使用新加成。

官方LuaJIT2.0正常/hot当前专项通过：两剧情、六档技能、全部19份分派，实际公开属性/状态注册/BUFF属性加减、重复施放、长时间、旧状态字段恢复、死亡处理片段、无倒计时及实际悬停说明；42模块非目标一致。没有完整Windows客户端实测，图形、角色基础与最终属性重算等有限边界见PROJECT_STATUS.md和第一百一十三节。

```bash
python3 maintenance/patch_v237.py
python3 maintenance/test_v237.py
python3 maintenance/package_v237.py
```

Python3.12+，标准库，官方LuaJIT2.0缓存；Windows显式指定--runtime，不使用2.1或普通Lua。缺少固定236基线时按保留链重建，依赖见maintenance/manifest.json。不默认递归历史测试或重复干净重建。

保留此前自动施法、地图入口、仓库和其他累计修改；未经要求不更改颜色、字体或边框。玩家说明52项，历史JSON/ZIP不回写。开始前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。不提交缓存、游戏目录、存档或用户原始日志。
