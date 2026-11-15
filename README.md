# 归梦 v2.26 魔改维护工程

当前补丁 **v1.222（仓库按钮交互版）**。本仓库是补丁维护工程，不是完整游戏；不要将维护工程复制到游戏目录。

## 下载补丁

- [归梦v2.26_魔改补丁_v1.222.zip](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/%E5%BD%92%E6%A2%A6v2.26_%E9%AD%94%E6%94%B9%E8%A1%A5%E4%B8%81_v1.222.zip)
- [维护包](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/Guimeng_v1.222_maintenance.zip)
- [文件校验值](https://raw.githubusercontent.com/wyex2002-ctrl/Guimeng/downloads/checksums_v222.json)

退出游戏，备份存档及原 `Lib/game.res`，再解压玩家补丁覆盖。维护包用于开发，不用于安装。下载文件集中在 `downloads` 分支，`main` 只保存维护源码和必要输入。

## 目录

| 路径 | 用途 |
| --- | --- |
| `maintenance/` | 当前构建、测试、打包工具，Lua 源码及字节码，重建输入和官方 LuaJIT 源码 |
| `docs/玩家版说明_基础版.txt` | 今后玩家版说明的文案基准，按主题整理并连续编号 |
| `docs/修改记录_维护版.txt` | 唯一完整累计维护记录；当前修复见第九十八节 |
| `docs/reports/` | 已归档验证记录，仅作为历史证据 |
| `PROJECT_STATUS.md` | 当前状态和验证边界 |
| `AGENTS.md` | 维护约束 |

## 开发与验证

需要 Python 3.12+、make 和 C 编译器；Python 仅用标准库。命令均在仓库根目录运行：

```bash
python3 maintenance/patch_v222.py
python3 maintenance/test_v222.py
python3 maintenance/package_v222.py
```

Linux 首次测试会从同梱的官方 LuaJIT 2.0 源码构建运行时，后续复用与源码哈希匹配的本地缓存。不得用 LuaJIT 2.1 或普通 Lua 替代。Windows 请先构建同梱源码，再运行：

```powershell
python maintenance/patch_v222.py
python maintenance/test_v222.py --runtime C:/tools/luajit20/src/luajit.exe
python maintenance/package_v222.py
```

日常入口默认复用哈希匹配的上一版固定资源，只重建本版，并只跑当前相关测试；首次缺少基线时仍需完整构建。当前专项保留正常/hot、原生主角/技能/特效链、实际技能选择与公开角色API、原等级费用刷新和BUFF冷却过期对照，重复调用集中在一个代表场景约200次，其他必要边界各测一次。

同一个问题反复修复仍未解决时，应扩大相关排查及必要回归；v192用药回归仍保留`test_v192.py --iterations 2000 --full-history`入口，v222仅运行当前近战剑光及自动蓄力专项，不默认递归旧版测试。

修改历史构建源码、上游Lua或依赖时，必须显式重建历史；需要重新编译Lua时同时指定官方运行时：

```bash
python3 maintenance/patch_v222.py --rebuild-history --runtime /absolute/path/to/luajit
```

`--runtime`本身只选择编译器，不取消固定基线复用。复用不代表历史源码已重新编译或重测，报告会记录实际范围。本版继续使用精简流程，历史包保留原交付快照。

生成的资源、报告、日志、运行时和 ZIP 均在 `maintenance/` 的忽略路径下，不提交 Git。玩家包和维护包输出到 `maintenance/deliverables/`。维护包保持与仓库相同的目录结构，解压后可独立运行以上命令。

当前 `game_v222.res`：2,674,052 字节，SHA-256：

```text
22b7ab8268a6e84d9704485962f990cbfa873ce483d18740093ba65c00ca7c61
```

原 v1.177 构建和回归仍是当前流水线的依赖，故保留相关脚本及三组源文件/字节码。`patch_v139.py` 等旧编号工具仍被导入，不能按版本号删除。输入清单见 `maintenance/manifest.json`。

## 日志与验证边界

复现后提供游戏 `log/` 中的 `guimeng_detail_latest.txt`、`guimeng_critical_latest.txt`，以及原运行和错误日志；如已重启，提供对应 `previous` 文件。日志直接写入游戏 log，不产生 log/log。

v1.222修复两剧情整叠药品出售结算，回城卷支持每格999叠加，背包顶部新增“仓库”按钮，复用现有按钮图像边框和原仓库打开流程。保留218近战及所有累计修改。

官方LuaJIT2.0正常/hot专项通过：两剧情原物品事件/确认闭包、原数据代理/公共copy/道具信息、原整理合并和单张消耗、原UI安装段/窗口查找/控件工厂/绑定/单图按钮按下弹起/显示/销毁；42模块非目标原型一致。只执行当前相关专项，未重跑全部历史。

图形/字体/鼠标和引擎原语为有限测试边界，没有完整Windows客户端或真实资源视觉实测，也没有完整仓库存取、传送或退出重入实测。按钮最终观感需安装确认，小怪声望等原有实机边界保持。详见PROJECT_STATUS.md和维护记录第九十八节。

当前入口复用哈希固定的v218，缺失时按保留依赖链重建，不将随包历史结果冒充本轮通过。

按用户最新要求，从v1.187起每次更新都同步main维护源码和downloads补丁，不创建Release。

玩家版说明以 [基础版文案](docs/玩家版说明_基础版.txt) 为准，按八类连续编号（当前49项），开头保留安装和提供log日志的方法。v1.222玩家包采用此文案；已发布旧版本JSON快照不回写。

本版修复仓库按钮D2D精灵self调用错误及类型2字体参数错位；按上传214核对物品提示、字体、富文本样式保持一致。正常/hot专项含真实16/73精灵包装及219负对照通过，无完整Windows视觉实测。未经明确要求不改颜色。

221：仓库按钮放大30%为55×22，距左侧按钮5像素并上下居中。悬停上浮/按下下沉各1像素，配色不变。专项正常/hot通过，Windows视觉仍需安装确认。

222：更正为右侧关闭区域约5像素、上下居中；仓库按钮暗色调制及保留立体斜边，消除位移反馈露出的亮底边。其他颜色保持，最终Windows观感需确认。
