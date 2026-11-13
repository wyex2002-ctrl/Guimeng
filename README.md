# 归梦 v2.26 魔改维护工程

当前补丁 **v1.189**。本仓库是补丁维护工程，不是完整游戏；不要将维护工程复制到游戏目录。

## 下载补丁

- [归梦v2.26_魔改补丁_v1.189.zip](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.189.zip)
- [维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.189_maintenance.zip)
- [文件校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v189.json)

退出游戏，备份存档及原 `Lib/game.res`，再解压玩家补丁覆盖。维护包用于开发，不用于安装。下载文件集中在 `downloads` 分支，`main` 只保存维护源码和必要输入。

## 目录

| 路径 | 用途 |
| --- | --- |
| `maintenance/` | 当前构建、测试、打包工具，Lua 源码及字节码，重建输入和官方 LuaJIT 源码 |
| `docs/玩家版说明_基础版.txt` | 今后玩家版说明的文案基准，按主题整理并连续编号 |
| `docs/修改记录_维护版.txt` | 唯一完整累计维护记录；当前修复见第六十一节 |
| `docs/reports/` | 已归档验证记录，仅作为历史证据 |
| `PROJECT_STATUS.md` | 当前状态和验证边界 |
| `AGENTS.md` | 维护约束 |

## 开发与验证

需要 Python 3.12+、make 和 C 编译器；Python 仅用标准库。命令均在仓库根目录运行：

```bash
python3 maintenance/patch_v189.py
python3 maintenance/test_v189.py
python3 maintenance/package_v189.py
```

Linux 首次测试会从同梱的官方 LuaJIT 2.0 源码构建运行时，后续复用与源码哈希匹配的本地缓存。不得用 LuaJIT 2.1 或普通 Lua 替代。Windows 请先构建同梱源码，再运行：

```powershell
python maintenance/patch_v189.py
python maintenance/test_v189.py --runtime C:/tools/luajit20/src/luajit.exe
python maintenance/package_v189.py
```

默认重建使用跟踪的字节码；如修改了构建链中的 Lua 源码，可给 `patch_v189.py` 加 `--runtime <官方运行时绝对路径>` 重新编译，并审查字节码及资源哈希变化。

生成的资源、报告、日志、运行时和 ZIP 均在 `maintenance/` 的忽略路径下，不提交 Git。玩家包和维护包输出到 `maintenance/deliverables/`。维护包保持与仓库相同的目录结构，解压后可独立运行以上命令。

当前 `game_v189.res`：2,650,197 字节，SHA-256：

```text
4bb6eb706e39cb4f900805f26cb8a0bb842c67c234158e39b94a2f606cad86c7
```

原 v1.177 构建和回归仍是当前流水线的依赖，故保留相关脚本及三组源文件/字节码。`patch_v139.py` 等旧编号工具仍被导入，不能按版本号删除。输入清单见 `maintenance/manifest.json`。

## 日志与验证边界

复现后提供游戏 `log/` 中的 `guimeng_detail_latest.txt`、`guimeng_critical_latest.txt`，以及原运行和错误日志；如已重启，提供对应 `previous` 文件。日志直接写入游戏 log，不产生 log/log。

v1.189 在调用前验证物品控件及使用方法，安全跳过失效控件并限量记录实际物品/格子/窗口/类型。修复物品使用字节码跳转的活跃寄存器边界，以及快捷格嵌套使用后错误回落到背包而重复用药的问题。新掉落的普通技能书按原书店规则生成秘籍或残篇，名称、标记和价格与书店结果一致；已有物品和商店原解读流程保留。保留v187自动存档间隔、原正常错误报告和全部其他累计玩法。

本次日志确认直接错误为Sys.lua:16274调用不存在的使用物品方法，Boss声望此前正常入账。缺少原始控件快照，不能认定实机控件失效的唯一成因；新诊断用于继续核对。572ms峰值主要落在场景对象更新，新增低频最慢对象耗时及名称，不据此虚称已解决全部性能问题。云端正常/hot及干净重建验证见PROJECT_STATUS；没有完整Windows客户端实测，不能替代实机战斗、切图和读档验证。小怪声望不宣称彻底解决。

按用户最新要求，从v1.187起每次更新都同步main维护源码和downloads补丁，不创建Release。

玩家版说明以 [基础版文案](docs/玩家版说明_基础版.txt) 为准，按八类连续编号，开头保留安装和提供log日志的方法。v1.189玩家包采用此文案；已发布旧版本JSON快照不回写。
