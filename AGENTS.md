# 归梦维护约定

当前已发布 v1.344。开始维护时先读 [README.md](README.md) 和 [PROJECT_STATUS.md](PROJECT_STATUS.md)。版本尾数按整数比较。

## 按任务查阅

- 修改玩法、存档、原生接口、界面或诊断前，在[专项维护参考](docs/专项维护参考.md)中查到涉及功能的原入口、版本约束与回归范围，再核对[完整维护记录](docs/修改记录_维护版.txt)的相关章节。可用技能名、原型号或版本号检索。
- 历史定位以当前资源、源码及最近适用的记录为准。碰到历史规则相互冲突时，以最新的用户要求和后来生效的规则为准。旧原型号和旧报告用于定位与对照。

## Codex 协作与沟通

以下是本仓库采用的协作提示。执行时以用户授权和本文件的具体维护约定为准。英文按用户提供的版本保留。出处参见 [OpenAI GPT-6.2 提示词指南](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6.2-astra#prompting-best-practices)。

### 1. 像同事一样沟通

Use the following prompt if you want to use the model as a collaborator and thought partner for day to day work. Write using terminology the user and sources use. Keep technical details and use domain-specific language when they make the explanation more precise. Use the active voice and keep closely related details together. Cover the key points up front, and avoid references that the reader can only make sense of later in the response. Give the user enough context to follow your reasoning.

### 2. 让最终答复可以独立阅读

During longer tasks, the model can carry shorthand from its reasoning or from other agents into its final answer. Remind it to write a self-contained response that's clear to someone who hasn't followed the progress updates. Treat your final answer as the user's first look at your work, and not as a continuation of intermediate commentary. The final answer must always be fully self-contained: users should never need to read earlier commentary updates for context, since they are collapsed when the final answer is shown to the user. Write the final answer and all other human-facing material anew for the intended reader. Do not copy or closely paraphrase your reasoning or adopt its writing style. Do not carry over working shorthand, jargon, or abbreviations from your reasoning, tool calls, or instructions to subagents and automations.

### 3. 在授权范围内完成任务

Avoid stopping to end the turn while the task is incomplete or if there is an authorized next step you can take, and instead take the next steps within task scope to progress the user's request. If your final response before ending the turn is a suggested next step, a plan, a request to the user for a routine decision, instructions for a task to execute, or similar handoff to the user, take these steps yourself to make progress towards what the user asked for. Make sure that you have authorization to do so, and flag any assumptions or decisions you make to the user. Only stop to clarify with the user if there is significant change in task scope, you are concretely blocked, have a decision that the user needs to resolve, or before irreversible or destructive actions. Bias towards action, and persist until you've completed the task the user asked for. Avoid stopping to end the turn while the task is incomplete or if there is an authorized next step you can take, and instead take the next steps within task scope to progress the user's request. Make sure that you have accounted for every part of the user's request, and persist until you've delivered a result that fully satisfies the user's goal. If a task requires sustained work, do all the necessary work until the intended outcome is completely fulfilled. Progress autonomously towards the user's goal unless they are clearly destructive or irreversible. Before ending a turn or calling your work complete, check that your work fully satisfies what the user asked for. If any steps remain or any part of the result still needs verification, follow through on this work before finishing.

### 4. 对不明确的细节作可逆假设

When a detail is unclear, give the model room to state what it's assuming and continue with the task. Make reasonable, reversible assumptions to carry work forward and state them if it progresses the task within scope. Do not second guess yourself, stop after describing what you could do, offer to do the work, or provide a partial answer unless there is no way for you to proceed.

## 工程与输入

- 在仓库根目录运行 `python3 maintenance/patch_v294.py`、`python3 maintenance/test_v294.py`、`python3 maintenance/package_v294.py`。Python 3.12+，仅依赖标准库。
- 使用现有 checkout；云任务已隔离，除非用户要求，不创建 Git worktree。
- 必须保留 `maintenance/manifest.json` 列出的输入，尤其 `base_v176.zip`、三组 v177 Lua/字节码和 v179 Lua/字节码，以及官方 `LuaJIT-2.0-b83bcba.tar.gz`。
- v177、v179、v180、v181、v182、v183、v184、v185、v186、v187、v188、v189、v190、v191、v192、v193、v194、v195、v196、v197、v198、v199、v200、v201、v202、v203、v204、v205、v206、v207、v208、v209、v210、v211、v212、v213、v214、v215、v216、v217 构建是 v218 首次完整重建的依赖，历史测试按需运行；`patch_v139.py`、`ljtool.py`、`ljdis.py`、`bytecode_relocate.py`、`resource_tools.py`、`native_test_utils.py` 仍被导入，不能按旧版本号删除。
- Linux 测试会构建/复用官方 LuaJIT 2.0 缓存。Windows 必须显式传 `--runtime`。不得用 LuaJIT 2.1 或普通 Lua 替代。
- 历史和结果只保留一份：完整记录在 `docs/修改记录_维护版.txt`，归档报告在 `docs/reports/`；生成报告在 maintenance 的忽略路径，不将随包结果冒充本轮通过。
- 美术与贴图参考目录 `D:\guimeng_art`（解包 PNG 与索引）：界面 `.img` 视觉核对与切图尺寸查询使用 `guimeng_png_reference/index.csv` 与 `guimeng_png_reference/png/<id>.png`；角色/怪物/装备/特效帧图参考 `guimeng_character_reference`，地图/场景参考 `guimeng_environment_reference`。按 `agy-fast` 规则由只读子代理查看 PNG 图像后返回文本结果，不在主会话直接载入图片。

## 修改与验证

- 保留累计修改，尤其 v1.175 的 Ux 待应用难度、初始化顺序和原环境保护，以及 v1.176 的显式 API 导出修复。
- 数据库沙箱不提供 pcall/xpcall；不得通过 `_G` 回退或手动补齐 API 掩盖错误。原生事件的 Sys 是只读公开接口，使用 `get` 读取 hero、obj 和诊断函数；测试必须覆盖此边界，不能只提供内部 Sys 对象。
- 随机整数使用原 Gly 函数相同的引擎 API；不为绕过错误开放内部对象。
- 每次修改同步当前状态和完整维护记录。每次发版及部署到 `game.res` 的临时测试包均须同步更新界面版本号与游戏窗口标题栏版本号（`m12/76` 中的 `1.xxx` / `不烧心版 1.xxx`）。改源码后使用官方运行时重编译，审查编译字节码及资源哈希。
- 发布前按下述最新精简流程验证：完成本次重建、相关回归与一次最终交付检查；不默认反复重编译运行时、重跑所有历史版本或多次干净重建。
- 更新 `maintenance/manifest.json` 中的文件清单，确保维护包包括所有必要输入和当前文档。每次更新后在仓库根目录同步覆写 `使用说明_玩家版.txt`（不带版本号）。不要把构建缓存、游戏目录或存档提交 Git。

v181按用户明确要求移除了物品、角色及脚本反篡改检测，不得把旧惩罚或强退分支迁回。数据库的变量白名单和公开API隔离继续保留；正常保存退出、背包容量、穿戴与任务条件不能作为反作弊脚本删除。

### 专项回归

涉及数据代理、启动注册、诊断、存档或背包调用链时，按[专项维护参考中的跨版本约束](docs/专项维护参考.md#跨版本专项与回归)选择真实入口及必要对照。字节码修改须核对寄存器活跃范围、分支目的地及调试信息的重定位；涉及两剧情的入口要覆盖两条流程。

## 最新测试与交付流程（2026-11-14，用户要求优先）

- 重复调用测试默认约200次，保留必要边界和真实调用链；不要把200次再机械扩展为大量重复组合。涉及JIT时选取相关正常/hot场景，不能靠增加次数替代复现故障或核对真实环境。
- 普通局部修复只重建一次、运行本次修改及直接受影响的回归。旧脚本的全历史链和2万次压力循环是历史验证方式，不作为每轮默认要求；后续入口按本约定选择相关测试，不直接照搬耗时的递归全链。涉及共享基础代码且影响范围确实扩大，或出现新失败、同一问题反复修复仍未解决时，应主动扩大排查和相关验证，并说明实际原因，不拘泥于200次。
- 复用源码哈希已核对的官方LuaJIT2.0运行时；只有依赖源码、编译器或构建配置改变、缓存失效时才重新构建。继续禁止普通Lua或LuaJIT2.1替代。
- 最终玩家包和维护包各做一次ZIP完整性检查，玩家资源与本轮已测试资源做一次哈希比对。已检查且字节未变化的内容不反复检查；只更新文档不重跑玩法测试。
- 日常补丁不默认重复干净重建，也不在干净目录再次重跑全部历史测试。构建/打包流程、依赖或输入布局有变化，或独立重建出现疑点时，才增加一次必要的干净重建；输入和运行时均未变化时不再重复编译C运行时或为文档改动再建一轮。
- 测试失败后只重跑受修复影响的项目；通过后不因汇报、打包或上传而重复整套测试。最终文件发生变化时只重查对应文件。GitHub同步频率、必要输入保留及不覆盖玩家存档的约定不变。
- 汇报简述发现、修复和最终结果，不堆叠调用/断言次数或逐项重复校验进度。仍须如实区分静态、受控回归与Windows客户端实测；200次未复现就记录未复现，不声称彻底解决。
- 排查与工程提速约定（2026-11-25）：对比“A 正常、B 异常”时，先锁死唯一分叉链路，合并所需 proto 到单次脚本检查；静态反汇编 3 步内未定位根因即改用游戏 `log/` 打轻量帧号日志实测，禁止盲扫全模块或贴图资源。纯 Python `lua51_eval.py` 重复测试须把 `loadstring(runtime_v*.lua)` 提到循环外复用，只重置状态跑 200 次；不重复叠加跑已被新版覆盖的整套旧 200 次循环。Windows PowerShell 5.1 终端不使用 `&&`（改用 `; if ($LASTEXITCODE -eq 0)`），多行诊断脚本直接写文件执行而非 `-c` 硬拼转义。

本节是用户新的验证范围要求，优先于此前条目及历史记录中的强制全链、重复干净重建和高次数规定。历史报告/已发布版本不回写，不为落实此流程单独生成游戏补丁。

## 旧存档兼容范围（2026-11-15，用户最新要求）

今后修改默认只处理可能使旧存档发生致命故障的兼容问题，例如崩溃、无法读取或严重数据损坏。普通旧数据差异、旧规则留下的待发奖励、数值补偿、历史道具追溯更新等，不新增迁移或补偿逻辑，也不为此扩大测试。沿用当前存档和新规则即可；发现真实致命风险时再作必要处理。v1.207已发布的待发经验转换保留，不为本约定单独改资源或重发补丁。

## 玩家说明与发布

- [玩家说明基础版](docs/玩家版说明_基础版.txt)是唯一文案基准。新增内容放入对应主题并重排连续编号，保留安装、提交游戏 log 的说明及用户要求保留的数值。隐藏随机参数、具体概率和掉率仅记录在维护文档、源码和测试中。
- 发版时把基础版编号正文同步到本版 `maintenance/player_changes_v*.json`。已发版本的 JSON 和维护包作为历史快照保存。
- 纯文档维护同步 `main`；游戏发版将维护源码同步 `main`、双包与校验值同步 `downloads`，每版保留本地提交及完整维护包，继续采用分支发布，不创建 GitHub Release。发版回复同时提供玩家补丁和完整维护包链接。同步进度见 [sync_policy.json](maintenance/sync_policy.json)。
- 使用游戏自身的 `log/` 做诊断。日志直接写到该目录，避免产生 `log/log`。诊断使用游戏日志，用户已停用 Windows 事件查看器、系统事件日志和系统转储的收集流程。
- 配色和字体以 v1.193 为原基准，沿用后来获授权的调整。修改文字颜色、描边或字体前须有用户明确要求。

补丁命名采用 `归梦v2.26_魔改补丁_v1.xxx.zip`。下载文件集中在 `downloads` 分支；main 保存维护工程。按用户最新要求（2026-11-26）：每版通过验证后，如当前 `d:\guimeng2.26\Lib\game.res` 为旧版本且无同版备份则先备份，再直接用新版 `game_v*.res` 覆盖 `d:\guimeng2.26\Lib\game.res`（仍严禁修改玩家存档或把游戏目录/存档提交 Git）；`native_work`、`compile_work` 仅用于工程验证。

协作同步（用户最新指示）：开始修改前不查询或拉取GitHub，用户以后另行指示才拉取。基于当前工作区修改，完成后才推送main/downloads；保护未提交工作，禁止强推覆盖。发布时若远端有冲突，先保留本轮成果再按用户指示处理。
