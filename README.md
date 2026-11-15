# 当前补丁 v1.231（长按自动技能修正与诊断）

玩家下载 `归梦v2.26_魔改补丁_v1.231.zip`；完整维护包 `Guimeng_v1.231_maintenance.zip`；校验值 `checksums_v231.json`。

退出游戏，备份存档及原Lib/game.res，解压玩家包覆盖并重启。

修正隐藏背包窗口的子窗口误阻断长按。单体远程技能快捷键按住2秒开启自动连续使用和旋转绿边；点击地面移动保留模式，到达后继续。新增有上限的repeat.*按键、长按、阻断原因及绿框绘制日志，复用原log文件，不逐帧写盘。

真实窗口父子链旧版负对照/新版正对照、原技能与冷却、完整原生日志安装器正常/hot回归通过。物理输入与底层引擎原语有限，未进行完整Windows客户端实测。安装后长按月魂灵波所在F1约3秒并松开；若仍无绿框，请提供log里的run/detail/critical/error四份latest日志，重启过则附previous。

开始时不查询或拉取GitHub，完成后同步main/downloads，无Release，不覆盖存档、不公开上传日志。详情见维护记录第一百零七节。

源码提交：https://github.com/wyex2002-ctrl/Guimeng/commit/ef090b4
