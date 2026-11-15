# 当前补丁 v1.232：施法硬直期间保留长按自动模式

玩家：[归梦v2.26_魔改补丁_v1.232.zip](归梦v2.26_魔改补丁_v1.232.zip)

完整维护包：[Guimeng_v1.232_maintenance.zip](Guimeng_v1.232_maintenance.zip)

校验：[checksums_v232.json](checksums_v232.json)

退出游戏，备份存档及原Lib/game.res，再覆盖玩家补丁。维护包用于开发。

修正正常施法硬直清空长按/自动模式：按住单体远程技能快捷键2秒启用，松开后自动施法；硬直期间保留计时与模式但暂停自动请求，恢复后继续。禁攻击、界面交互、切图等仍取消，原费用/CD/目标限制保持。修正原更新入口高位调用，其他配色/玩法保持。

官方LuaJIT2.0正常/hot相关回归及两包完整性/资源匹配通过。扩大测试曾遇hot间歇进程异常，修正入口连续调用寄存器后额外5次hot未复现；人工截取的硬直更新仅解释执行，完整助手和其余集成hot。不称完整Windows或完整原生帧JIT验证，详见维护记录第一百零八节。

重启进入角色，关闭操作窗口，长按月魂灵波快捷键约3秒后松开，确认绿边及自动施法。若仍异常，提供本次critical/detail/run/error日志；新增stiffness/forbidden字段帮助判断阻断。

main/downloads同步，无Release，不公开原始日志，不覆盖存档。开始前按约定未查询或拉取GitHub。

源码：https://github.com/wyex2002-ctrl/Guimeng/commit/d00ba5d42ea372108f0054e8234638dbf00d3bd8
