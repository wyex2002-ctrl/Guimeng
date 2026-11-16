# 归梦 v2.26 魔改维护工程

当前 **v1.234：技能失效诊断版**。用于定位偶发的“自动模式退出后，原技能按快捷键也无法施放”。**尚未确认根因，不声称已经修复。** 保留v1.233的长按1.5秒、卡顿超过3秒取消、Alt/Q/W/E/V按键豁免等规则。

下载：[玩家诊断补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.234.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.234_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v234.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包；维护包用于开发。

安装后重启，卡住时按住失效技能键约3秒，或间隔2秒按几次，随后尽快提供游戏log的critical/detail/run/error最新文件；重启过附previous。新增repeat.skill_probe记录冷却、可触发、动作、硬直及队列/目标等状态，2秒限频、每30秒最多12条，旧240条预算用尽仍可诊断；没有新增日志文件，不产生log/log。

构建/测试/打包：

```bash
python3 maintenance/patch_v234.py
python3 maintenance/test_v234.py
python3 maintenance/package_v234.py
```

Python3.12+，仅标准库；官方LuaJIT2.0缓存，Windows显式传--runtime，不用2.1或普通Lua。缺少固定233基线时按保留链重建，必要输入见maintenance/manifest.json，勿删除历史依赖。

正常/hot当前回归通过，42模块非目标一致；实际施法/冷却和共享日志模块保持233原字节。人工截取硬直倒计时仅解释执行，物理键鼠/图形/地图等有有限替身，无完整Windows客户端实测，也未据现有日志复现并确认最终故障原因。详情见PROJECT_STATUS.md和维护记录第一百一十节。

玩家正文基准仍51项，历史JSON和ZIP不回写。开始修改前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。缓存/游戏目录/存档和用户原始日志不提交Git，不擅自改配色。
