# v1.243 删除拾取选项并修复祝福油掉落

玩家：[归梦v2.26_魔改补丁_v1.243.zip](归梦v2.26_魔改补丁_v1.243.zip)

完整维护包：[Guimeng_v1.243_maintenance.zip](Guimeng_v1.243_maintenance.zip)

校验：[checksums_v243.json](checksums_v243.json)

退出游戏，备份存档和原Lib/game.res，再覆盖玩家包。

删除仓库左侧两行勾选框及每秒自动拾取，保留Alt的11×11范围和原安全自动出售规则。修复祝福油把物品/数量参数传反造成的杀怪报错，保留每怪一瓶测试规则、红名说明及神水加成提示。幸运功能仍未开放。

正常/hot当前相关专项通过，旧242助手经实际掉落函数/地面构造器精确复现用户错误，新版完整原生落地构造通过。底层图形/地图/引擎分配桥接有限，没有完整Windows客户端实测。详见源码PROJECT_STATUS与第一百一十九节。main/downloads双包，无Release。

源码：https://github.com/wyex2002-ctrl/Guimeng/commit/1d234dbfbc169e6e2ae0be2ae7764d0f6a90ef9c
