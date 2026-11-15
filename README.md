# 归梦 v2.26 魔改维护工程

当前 **v1.227：快捷栏半透明冷却遮罩**。基于v1.226，用已有纯色精灵绘制半透明扇形，读取原生技能CD状态，保留冷却规则及全部累计修改。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.227.zip)、[维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.227_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v227.json)。退出游戏并备份存档及原Lib/game.res后安装玩家补丁。维护包不是安装包。

在仓库根目录运行：

```bash
python3 maintenance/patch_v227.py
python3 maintenance/test_v227.py
python3 maintenance/package_v227.py
```

Python3.12+，仅标准库；测试使用同梱官方LuaJIT2.0，Windows需显式指定官方运行时，不能用2.1或普通Lua代替。缺少v226资源时沿保留的历史构建链重建。必要输入见maintenance/manifest.json；不要删除历史依赖。构建缓存、游戏目录和存档不提交Git。

本轮正常/hot实际召唤神兽释放→原CD计时→真实技能格→精灵包装链通过，42模块非目标原型一致；底层图形/资源为有限替身，未执行Windows客户端视觉实测，遮罩几何及顺时针方向已核对，实际Windows像素仍待确认。详细范围见PROJECT_STATUS.md及维护记录第一百零三节。历史报告仅为历史证据。

玩家说明基准见docs/玩家版说明_基础版.txt，当前50项。复现问题请提供游戏log目录的guimeng_detail_latest.txt、guimeng_critical_latest.txt及原错误日志，重启后提供previous文件；不产生log/log。main保存维护源码，downloads每版同步补丁及维护包，不创建Release。

各技能基础冷却核对见[清单](docs/reports/skill_cooldowns_v227.md)。未修改技能冷却规则。
