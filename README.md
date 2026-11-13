# 归梦 v2.26 魔改维护工程

当前补丁 **v1.184**。本仓库是补丁维护工程，不是完整游戏；不要将维护工程复制到游戏目录。

## 下载补丁

- [归梦v2.26_魔改补丁_v1.184.zip](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.184.zip)
- [维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.184_maintenance.zip)
- [文件校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v184.json)

退出游戏，备份存档及原 `Lib/game.res`，再解压玩家补丁覆盖。维护包用于开发，不用于安装。下载文件集中在 `downloads` 分支，`main` 只保存维护源码和必要输入。

## 目录

| 路径 | 用途 |
| --- | --- |
| `maintenance/` | 当前构建、测试、打包工具，Lua 源码及字节码，重建输入和官方 LuaJIT 源码 |
| `docs/修改记录_维护版.txt` | 唯一完整累计维护记录；当前修复见第五十五节 |
| `docs/reports/` | 已归档验证记录，仅作为历史证据 |
| `PROJECT_STATUS.md` | 当前状态和验证边界 |
| `AGENTS.md` | 维护约束 |

## 开发与验证

需要 Python 3.12+、make 和 C 编译器；Python 仅用标准库。命令均在仓库根目录运行：

```bash
python3 maintenance/patch_v184.py
python3 maintenance/test_v184.py
python3 maintenance/package_v184.py
```

Linux 首次测试会从同梱的官方 LuaJIT 2.0 源码构建运行时，后续复用与源码哈希匹配的本地缓存。不得用 LuaJIT 2.1 或普通 Lua 替代。Windows 请先构建同梱源码，再运行：

```powershell
python maintenance/patch_v184.py
python maintenance/test_v184.py --runtime C:/tools/luajit20/src/luajit.exe
python maintenance/package_v184.py
```

默认重建使用跟踪的字节码；如修改了构建链中的 Lua 源码，可给 `patch_v184.py` 加 `--runtime <官方运行时绝对路径>` 重新编译，并审查字节码及资源哈希变化。

生成的资源、报告、日志、运行时和 ZIP 均在 `maintenance/` 的忽略路径下，不提交 Git。玩家包和维护包输出到 `maintenance/deliverables/`。维护包保持与仓库相同的目录结构，解压后可独立运行以上命令。

当前 `game_v184.res`：2,639,980 字节，SHA-256：

```text
559c611484d9eb85b7c6fadcdd6bd9f052d956be74197e2436002707d7bb351b
```

原 v1.177 构建和回归仍是当前流水线的依赖，故保留相关脚本及三组源文件/字节码。`patch_v139.py` 等旧编号工具仍被导入，不能按版本号删除。输入清单见 `maintenance/manifest.json`。

## 日志与验证边界

复现后提供游戏 `log/` 中的 `guimeng_detail_latest.txt`、`guimeng_critical_latest.txt`，以及原运行和错误日志；如已重启，提供对应 `previous` 文件。日志直接写入游戏 log，不产生 log/log。

v1.184 优化诊断日志的临时分配和高频写盘，保留错误栈及关键记录；尚未完成完整 Windows 客户端实测，实机小怪声望修复效果仍需新版日志确认。历史验证报告不能代替本轮实际测试。

维护源码每三个版本同步GitHub，下载分支每版更新；上次源码已同步至v1.182，v1.183/v1.184源码保留本地提交和完整维护包，下次源码同步为v1.185。
