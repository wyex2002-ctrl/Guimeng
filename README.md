# 归梦 v2.26 魔改维护工程

当前 **v1.239：魔法盾无限持续，重施覆盖旧效果，悬停显示实际加成**。

魔法盾图标隐藏倒计时，鼠标悬停显示实际增加的伤害减免与破防抵抗。每次施放按当前技能等级替换旧盾，同级或学会更高等级后均可立即重施，不重复叠加。原加成、MP、冷却和死亡/骑乘等独立清除规则保持；幽灵盾与神圣战甲术沿用238，保留新增的元素加成提示。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.239.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.239_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v239.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。安装后重新施放魔法盾即可按当前等级应用效果。

官方LuaJIT2.0正常/hot相关回归通过：两剧情、六档、全部34份分派，原公开状态接口和BUFF属性加减、升级/同级/降级重施、旧状态恢复、动画可视回调、原死亡Buff片段、无倒计时及悬停提示。上一版两防御技能专项及42模块非目标一致。没有完整Windows客户端实测；图形/动画绑定、基础属性和最终属性重算等有限边界见PROJECT_STATUS.md和第一百一十五节。

```bash
python3 maintenance/patch_v239.py
python3 maintenance/test_v239.py
python3 maintenance/package_v239.py
```

Python3.12+，标准库，官方LuaJIT2.0缓存；Windows显式指定--runtime，不使用2.1或普通Lua。缺少固定238时按保留链重建，依赖见maintenance/manifest.json，不默认递归历史全套。

保留此前累计修改，不擅改颜色、字体或边框。玩家说明53项，历史JSON/ZIP不回写。开始前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。不提交缓存、游戏目录、存档或用户原始日志。
