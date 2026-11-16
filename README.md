# 归梦 v2.26 魔改维护工程

当前 **v1.235：施法寄存器与自动模式误取消修正**。修正旧施法跳板丢失活跃寄存器及高位局部跨调用的问题；点击敌人、使用物品快捷项不再误取消自动模式。实际UI/NPC交互仍可取消，按住鼠标或移动时自动请求等待。保留1.5秒启用、超过3秒卡顿取消及Alt/Q/W/E/V豁免。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.235.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.235_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v235.json)。退出游戏，备份存档与原Lib/game.res后安装玩家包；维护包用于开发。

普通/hot相关回归及额外3次hot复查通过，包含真实月魂灵波/雷电术快捷施放、伤害回调结果表、选择转换与训练名捕获、鼠标/物品按键和原冷却/日志链。未做完整Windows客户端实测；本次底层修正是否解决用户存档中月魂灵波失效，仍需安装确认，不能声称全部根因已排除。具体证据与边界见PROJECT_STATUS.md及第一百一十一节。

安装后重启，先试月魂灵波手动与长按，再试雷电术自动状态下点击敌人与地面。若月魂灵波仍不能用，按住其快捷键约3秒，尽快提供log的critical/detail/run/error最新文件。新增skill_snapshot缓存最近8种技能状态，每5秒轮流重发一条，避免先试F1、后用F6时早期记录被滚动覆盖；仍限频写盘，不新增日志文件、不产生log/log。

在仓库根目录运行：

```bash
python3 maintenance/patch_v235.py
python3 maintenance/test_v235.py
python3 maintenance/package_v235.py
```

Python3.12+，标准库，官方LuaJIT2.0缓存；Windows显式指定--runtime，不使用2.1或普通Lua。缺少固定234基线时按保留链重建，依赖见maintenance/manifest.json，保留历史输入。硬直倒计时为解释执行的明示截取片段，完整自动助手/其余集成仍hot，物理输入/底层图形/地图等有限。

玩家说明仍51项，历史JSON/ZIP不回写。开始前不向GitHub查询或拉取，完成后同步main/downloads双包，无Release。缓存/游戏目录/存档及用户原始日志不提交Git，未经要求不改配色。
