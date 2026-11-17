# 归梦 v2.26 魔改维护工程

当前 **v1.269：3分钟自动存档与闪退日志复核**。

自动存档间隔改为3分钟，沿用原存档条件。此次日志显示最近一次保存及最后采样帧均已返回，但没有记录具体故障调用，闪退根因尚未确认；本版保留v268诊断，不宣称修复闪退。[复核结论与验证范围](docs/闪退复核与3分钟存档_v269.md)。

下载：[玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.269.zip)、[完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.269_maintenance.zip)、[校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v269.json)。退出游戏并备份存档及原Lib/game.res后安装玩家包，维护包用于开发。

```bash
python3 maintenance/patch_v269.py
python3 maintenance/test_v269.py
python3 maintenance/package_v269.py
```

Python3.12+、标准库、官方LuaJIT2.0缓存；Windows显式--runtime，不能用2.1或普通Lua。缺少固定268时顺链重建，依赖见maintenance/manifest.json；不默认递归历史全套。

normal/hot两剧情存档边界、原生时钟／完整帧／公开run及42模块非目标检查通过。未进行Windows完整客户端实测或闪退复现。玩家说明仍54项，第53条同步3分钟。详见PROJECT_STATUS.md及第一百四十五节。修改前不查询或拉取GitHub，完成后同步main/downloads双包，无Release。
