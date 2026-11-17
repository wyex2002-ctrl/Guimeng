# 归梦维护下载

当前 v1.274（2026-11-17）：优化分层战斗日志，补充目标变化、对象生命周期、技能状态和飞行道具记录，保存首次Lua错误的内层栈与上下文。普通记录继续缓冲、低频写盘。自动存档仍5秒，玩法、字体、颜色及边框保持。

- [玩家补丁](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/归梦v2.26_魔改补丁_v1.274.zip)
- [完整维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.274_maintenance.zip)
- [校验值](checksums_v274.json)
- [源码与验证说明](https://github.com/wyex2002-ctrl/Guimeng/tree/a112accfc42dc8263af804bf8982b6e397fdb7b6)

退出游戏并备份存档及原Lib/game.res后安装玩家包。官方LuaJIT2.0 normal/hot通过真实构造器／只读接口、原技能／目标选择／飞行道具、完整更新及保存／退出回归，并核对42模块非目标逻辑。文件、保存、图形和引擎为有限桥接，未做Windows客户端闪退复现或帧率实测，尚未确定玩家闪退根因。仅使用游戏自身日志，不使用Windows事件记录或系统转储。

再次退出时，在重新打开游戏前复制整个log文件夹提供即可，不需要重启电脑。旧包继续保留，无Release。
