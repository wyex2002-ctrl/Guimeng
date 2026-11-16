# 归梦 v2.26 魔改维护工程

当前 **v1.244：祝福油坐骑强化与统一幸运系统**。

右键祝福油强化已装备坐骑，幸运0必升1；1～6按40%升1、30%降1、30%不变，有效使用1瓶、上限7。装备幸运影响主角与其召唤物原随机攻防取值，技能幸运和原幸运加持直接相加，攻防分别判定；宝宝实时读取主角装备幸运。金色幸运词条和信息栏反馈。[实际机制、主要函数、概率修改方法及验证边界](docs/祝福油与幸运系统.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.244.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.244_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v244.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

官方LuaJIT2.0正常/hot当前专项通过：原库存使用/消费、代理/深复制、原装备累计循环/真实公开属性、全部247个完整生物伤害回调、一次合并概率/独立防御、强化边界及提示/描边包装。底层引擎图形/基础属性等有限；保存只测字段导出重载，没有完整Windows实机存档重入或视觉验证。详见PROJECT_STATUS.md与第一百二十节。

```bash
python3 maintenance/patch_v244.py
python3 maintenance/test_v244.py
python3 maintenance/package_v244.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows显式--runtime，不能用2.1或普通Lua。缺少固定243时顺链重建，依赖见maintenance/manifest.json；不默认递归历史全套。

保留240仓库按钮/莲月剑光、239永久Buff与238元素提示及此前累计修改；不擅改字体、颜色、边框。玩家说明55项，旧测试/报告/JSON/ZIP不回写。开始前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。不公开原始上传日志或覆盖存档。
