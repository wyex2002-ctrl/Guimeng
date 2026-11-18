# 归梦 v2.26 魔改维护工程

当前 **v1.280：回到v1.277游戏基础，恢复常规祝福油掉落与5分钟自动存档**。

按用户要求暂缓短周期分步自动存档，直接基于277资源构建，保留277动画稳定性修正和累计玩法。祝福油掉落恢复v1.267常规设置；自动存档每5分钟一次，沿用原条件和同步保存方式，手动／退出保存保持。[实现与验证说明](docs/回归277基础与赠油提示_v280.md)。

成功领取首次赠油后显示“【系统赠送您1瓶祝福油，请查看背包】”，从提示实际显示起满3秒后可通过确认按钮或回车关闭。排队中的提示不提前计时。满包下次进入再检测，成功入包才标记，每角色仅一次，其他提示框按原时序工作。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.280.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.280_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v280.json)。退出游戏并备份存档及原Lib/game.res后安装。

本版取消祝福油高掉落测试，已有物品和领取记录保留。字体、颜色、边框保持。278／279的分步保存调度器不在本版资源中，旧autosave日志文件不再更新；当前日志沿用277策略。

```bash
python3 maintenance/patch_v280.py
python3 maintenance/test_v280.py
python3 maintenance/package_v280.py
```

normal/hot通过267掉落规则与实际原死亡／保护／地面链、两剧情领取／保存标记、原生完整提示框类及3秒边界／排队／输入检查、5分钟边界与完整原帧／时钟／只读public.run。42模块及原分支、相对277非目标字节核对通过，原保存格式和277动画入口保留。

运行时为Linux x64官方滚动LuaJIT2.0，文件、图形、输入和部分引擎为有限桥接，不是Windows x86 LuaJIT2.0.4完整客户端实测。不换DLL、不关闭全局JIT、不配置Windows事件记录。修改前不查询／拉取GitHub，完成后同步main/downloads双包，保留旧包，不创建Release。
