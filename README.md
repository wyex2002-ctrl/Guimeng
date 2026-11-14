# 归梦 v2.26 魔改维护工程

当前补丁 **v1.192**。本仓库是补丁维护工程，不是完整游戏；不要将维护工程复制到游戏目录。

## 下载补丁

- [归梦v2.26_魔改补丁_v1.192.zip](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.192.zip)
- [维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.192_maintenance.zip)
- [文件校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v192.json)

退出游戏，备份存档及原 `Lib/game.res`，再解压玩家补丁覆盖。维护包用于开发，不用于安装。下载文件集中在 `downloads` 分支，`main` 只保存维护源码和必要输入。

## 目录

| 路径 | 用途 |
| --- | --- |
| `maintenance/` | 当前构建、测试、打包工具，Lua 源码及字节码，重建输入和官方 LuaJIT 源码 |
| `docs/玩家版说明_基础版.txt` | 今后玩家版说明的文案基准，按主题整理并连续编号 |
| `docs/修改记录_维护版.txt` | 唯一完整累计维护记录；当前修复见第六十四节 |
| `docs/reports/` | 已归档验证记录，仅作为历史证据 |
| `PROJECT_STATUS.md` | 当前状态和验证边界 |
| `AGENTS.md` | 维护约束 |

## 开发与验证

需要 Python 3.12+、make 和 C 编译器；Python 仅用标准库。命令均在仓库根目录运行：

```bash
python3 maintenance/patch_v192.py
python3 maintenance/test_v192.py
python3 maintenance/package_v192.py
```

Linux 首次测试会从同梱的官方 LuaJIT 2.0 源码构建运行时，后续复用与源码哈希匹配的本地缓存。不得用 LuaJIT 2.1 或普通 Lua 替代。Windows 请先构建同梱源码，再运行：

```powershell
python maintenance/patch_v192.py
python maintenance/test_v192.py --runtime C:/tools/luajit20/src/luajit.exe
python maintenance/package_v192.py
```

默认重建使用跟踪的字节码；如修改了构建链中的 Lua 源码，可给 `patch_v192.py` 加 `--runtime <官方运行时绝对路径>` 重新编译，并审查字节码及资源哈希变化。

生成的资源、报告、日志、运行时和 ZIP 均在 `maintenance/` 的忽略路径下，不提交 Git。玩家包和维护包输出到 `maintenance/deliverables/`。维护包保持与仓库相同的目录结构，解压后可独立运行以上命令。

当前 `game_v192.res`：2,650,342 字节，SHA-256：

```text
56032988b1fa172a4400b2e21d0671015f6a4381d010c81d463ddb2334ab0082
```

原 v1.177 构建和回归仍是当前流水线的依赖，故保留相关脚本及三组源文件/字节码。`patch_v139.py` 等旧编号工具仍被导入，不能按版本号删除。输入清单见 `maintenance/manifest.json`。

## 日志与验证边界

复现后提供游戏 `log/` 中的 `guimeng_detail_latest.txt`、`guimeng_critical_latest.txt`，以及原运行和错误日志；如已重启，提供对应 `previous` 文件。日志直接写入游戏 log，不产生 log/log。

v1.192修复v191自动喝药误用事件环境不存在的Sys而退出的问题。用户11:05:05日志的实际错误是数据库.lua:20617全局Sys为nil，直接栈在周期更新/辅助窗口，没有证据表明治疗技能本体出错。三处查找改用原Gly独.取控件对象按格子名读取实时公开控件，缺失控件安全跳过，不向事件环境开放Sys。

保留快捷栏优先、普通背包后备、原药效/阈值/冷却、一次消耗及全部其他魔改；只改12/283和诊断版本标签。真实事件沙箱、实际周期用药片段、原控件查询和五种药品脚本回归详见PROJECT_STATUS与第六十四节。没有完整Windows客户端实测；云端请求/扣量回归不能代替实机治疗和药效tick测试，小怪声望验证边界保留。

按用户最新要求，从v1.187起每次更新都同步main维护源码和downloads补丁，不创建Release。

玩家版说明以 [基础版文案](docs/玩家版说明_基础版.txt) 为准，按八类连续编号（当前45项），开头保留安装和提供log日志的方法。v1.192玩家包采用此文案；已发布旧版本JSON快照不回写。
