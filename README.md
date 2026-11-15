# 当前补丁 v1.225（地图入口原生字形）

玩家下载 `归梦v2.26_魔改补丁_v1.225.zip`；维护包 `Guimeng_v1.225_maintenance.zip`；校验值 `checksums_v225.json`。

退出游戏，备份存档及原Lib/game.res，解压玩家包覆盖；异常时提供游戏log日志。

入口文字恢复原生1:1尺寸，取消导致笔画丢失的非整数缩小，白色及原可选描边、连接线保持。原字体模块恢复，仓库按钮开关、卫士召唤物保护和其他累计功能保留。

官方LuaJIT2.0正常/hot相关回归、42模块非目标一致性及两包完整性/资源匹配通过。底层字形/图形为有限测试边界，没有完整Windows客户端视觉实测，安装后请确认入口文字观感。

开始时不查询或拉取GitHub，完成后同步main/downloads，无Release，不覆盖存档、不公开日志。详情见第一百零一节。

源码提交：https://github.com/wyex2002-ctrl/Guimeng/commit/eb2e3ea1d146678ca8a4b1b0d2d5373c1b87db07
