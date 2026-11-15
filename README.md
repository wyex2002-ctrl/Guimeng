# 归梦 v2.26 魔改维护工程

当前补丁 **v1.210（近战起手响应测试版）**。本仓库是补丁维护工程，不是完整游戏；不要将维护工程复制到游戏目录。

## 下载补丁

- [归梦v2.26_魔改补丁_v1.210.zip](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.210.zip)
- [维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.210_maintenance.zip)
- [文件校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v210.json)

退出游戏，备份存档及原 `Lib/game.res`，再解压玩家补丁覆盖。维护包用于开发，不用于安装。下载文件集中在 `downloads` 分支，`main` 只保存维护源码和必要输入。

## 目录

| 路径 | 用途 |
| --- | --- |
| `maintenance/` | 当前构建、测试、打包工具，Lua 源码及字节码，重建输入和官方 LuaJIT 源码 |
| `docs/玩家版说明_基础版.txt` | 今后玩家版说明的文案基准，按主题整理并连续编号 |
| `docs/修改记录_维护版.txt` | 唯一完整累计维护记录；当前修复见第八十六节 |
| `docs/reports/` | 已归档验证记录，仅作为历史证据 |
| `PROJECT_STATUS.md` | 当前状态和验证边界 |
| `AGENTS.md` | 维护约束 |

## 开发与验证

需要 Python 3.12+、make 和 C 编译器；Python 仅用标准库。命令均在仓库根目录运行：

```bash
python3 maintenance/patch_v210.py
python3 maintenance/test_v210.py
python3 maintenance/package_v210.py
```

Linux 首次测试会从同梱的官方 LuaJIT 2.0 源码构建运行时，后续复用与源码哈希匹配的本地缓存。不得用 LuaJIT 2.1 或普通 Lua 替代。Windows 请先构建同梱源码，再运行：

```powershell
python maintenance/patch_v210.py
python maintenance/test_v210.py --runtime C:/tools/luajit20/src/luajit.exe
python maintenance/package_v210.py
```

日常入口默认复用哈希匹配的上一版固定资源，只重建本版，并只跑当前相关测试；首次缺少基线时仍需完整构建。当前专项保留正常/hot、实际主角类/技能释放/刷新/状态/动作和原动画更新、原计时片段及出手时间表对照，重复调用集中在一个代表场景约200次，其他必要边界各测一次。

同一个问题反复修复仍未解决时，应扩大相关排查及必要回归；v192用药回归仍保留`test_v192.py --iterations 2000 --full-history`入口，v210仅运行当前近战起手响应专项，不默认递归旧版测试。

修改历史构建源码、上游Lua或依赖时，必须显式重建历史；需要重新编译Lua时同时指定官方运行时：

```bash
python3 maintenance/patch_v210.py --rebuild-history --runtime /absolute/path/to/luajit
```

`--runtime`本身只选择编译器，不取消固定基线复用。复用不代表历史源码已重新编译或重测，报告会记录实际范围。本版继续使用精简流程，历史包保留原交付快照。

生成的资源、报告、日志、运行时和 ZIP 均在 `maintenance/` 的忽略路径下，不提交 Git。玩家包和维护包输出到 `maintenance/deliverables/`。维护包保持与仓库相同的目录结构，解压后可独立运行以上命令。

当前 `game_v210.res`：2,659,172 字节，SHA-256：

```text
d9552d34be5cdc3b20af2a4282b4d425779dcd17f4be775a8d21a111c061d817
```

原 v1.177 构建和回归仍是当前流水线的依赖，故保留相关脚本及三组源文件/字节码。`patch_v139.py` 等旧编号工具仍被导入，不能按版本号删除。输入清单见 `maintenance/manifest.json`。

## 日志与验证边界

复现后提供游戏 `log/` 中的 `guimeng_detail_latest.txt`、`guimeng_critical_latest.txt`，以及原运行和错误日志；如已重启，提供对应 `previous` 文件。日志直接写入游戏 log，不产生 log/log。

v1.210针对主角普通攻击及战士近战攻击的启动响应：受理当次推进动作首帧，身体和武器同步；Shift强制刺杀首次按下不再等待下一轮100ms周期时钟。持续Shift检测仍100ms，原周期任务不提速。保留209动作/相关延迟系数、伤害时间、每击计算、攻速/CD和原恢复限制，其他技能/佣兵怪物及颜色保持。游戏显示魔改版 1.210。

普通/hot相关专项通过：实际主角类/输入/技能/脚本/状态/动作和原动画更新、实际Shift注册/公开主角接口、原时钟工厂及原时钟循环片段。受控标准输入首个Shift请求由等待0.11秒改为当次受理，稳定连续间隔仍0.90秒；首次相位变化使首个间隔有一更新步量化，不声称绝对出手时刻全部相同。原自动/直接频率表、首帧多层/反向/短帧和200次代表Shift链通过。图像、地图查询、最终移动/伤害及禁足效果为有限边界；没有完整Windows客户端、完整资源视觉、完整原生帧或真实走砍实测，手感仍需客户端反馈，不能宣称完整实机DPS已验证。没有本版实机杀怪日志，小怪声望不能宣称彻底解决，神兽等既有边界保留。

当前入口复用哈希固定的v209，缺失时按仓库保留的依赖链重建，不将随包历史报告冒充本轮测试。

按用户最新要求，从v1.187起每次更新都同步main维护源码和downloads补丁，不创建Release。

玩家版说明以 [基础版文案](docs/玩家版说明_基础版.txt) 为准，按八类连续编号（当前49项），开头保留安装和提供log日志的方法。v1.210玩家包采用此文案；已发布旧版本JSON快照不回写。
