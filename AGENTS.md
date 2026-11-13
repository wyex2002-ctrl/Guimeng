# 归梦维护约定

当前版本 v1.183。先读 README.md、PROJECT_STATUS.md，以及 docs/修改记录_维护版.txt 开头、第四十四节、第四十九节、第五十二节、第五十三节和第五十四节；历史冲突以最新节为准，版本尾数按整数比较。

## 工程与输入

- 在仓库根目录运行 `python3 maintenance/patch_v183.py`、`python3 maintenance/test_v183.py`、`python3 maintenance/package_v183.py`。Python 3.12+，仅依赖标准库。
- 使用现有 checkout；云任务已隔离，除非用户要求，不创建 Git worktree。
- 必须保留 `maintenance/manifest.json` 列出的输入，尤其 `base_v176.zip`、三组 v177 Lua/字节码和 v179 Lua/字节码，以及官方 `LuaJIT-2.0-b83bcba.tar.gz`。
- v177、v179、v180、v181、v182 构建/测试是 v183 的依赖；`patch_v139.py`、`ljtool.py`、`ljdis.py`、`bytecode_relocate.py`、`resource_tools.py`、`native_test_utils.py` 仍被导入，不能按旧版本号删除。
- Linux 测试会构建/复用官方 LuaJIT 2.0 缓存。Windows 必须显式传 `--runtime`。不得用 LuaJIT 2.1 或普通 Lua 替代。
- 历史和结果只保留一份：完整记录在 `docs/修改记录_维护版.txt`，归档报告在 `docs/reports/`；生成报告在 maintenance 的忽略路径，不将随包结果冒充本轮通过。

## 修改与验证

- 保留累计修改，尤其 v1.175 的 Ux 待应用难度、初始化顺序和原环境保护，以及 v1.176 的显式 API 导出修复。
- 数据库沙箱不提供 pcall/xpcall；不得通过 `_G` 回退或手动补齐 API 掩盖错误。原生事件的 Sys 是只读公开接口，使用 `get` 读取 hero、obj 和诊断函数；测试必须覆盖此边界，不能只提供内部 Sys 对象。
- 随机整数使用原 Gly 函数相同的引擎 API；不为绕过错误开放内部对象。
- 每次修改同步当前状态和完整维护记录。改源码后使用官方运行时重编译，审查编译字节码及资源哈希。
- 发布前执行重建、正常/hot 回归、资源结构和非目标原型一致性检查、ZIP 完整性和玩家资源哈希检查，并从维护包干净解压独立重建。
- 更新 `maintenance/manifest.json` 中的文件清单，确保维护包包括所有必要输入和当前文档。不要把构建缓存、游戏目录或存档提交 Git。

v181按用户明确要求移除了物品、角色及脚本反篡改检测，不得把旧惩罚或强退分支迁回。数据库的变量白名单和公开API隔离继续保留；正常保存退出、背包容量、穿戴与任务条件不能作为反作弊脚本删除。

修改数据代理后，必须覆盖公共方法的真实 table.copy(value, true)、table.check、table.convert、insert_/remove_/getn 及角色原始初始化调用链；不能用 Lua clone mock 代替这条集成测试。保留空 __p 标识只用于代理识别，不恢复数值镜像检查。

删除检测代码时必须逐项核对被删除的函数注册和被置空函数的返回约定。版本/频道初始化测试执行真实注册语句、原始页面工厂和Main，不手工注入金轮法王等游戏函数；停用检测仍保留原接口表或回调返回类型，不能将返回表/true的函数一律改为RET0。

## 交付边界

玩家说明保留累计编号，用简单易懂的效果描述；不写详细版本历史和概率，尽量不写公式或数值，具体数值留在维护记录。日志直接写游戏 log，不产生 log/log。没有完整 Windows 客户端实测，不得把受控回归称为客户端验证；小怪声望效果仍须新版实机日志确认。

补丁命名采用 `归梦v2.26_魔改补丁_v1.xxx.zip`。下载文件集中在 `downloads` 分支；main 保存维护工程。不要覆盖真实游戏目录或存档；native_work、compile_work 仅用于工程验证。

## 同步频率

用户要求：维护源码每三个版本同步一次GitHub（上批已同步至v1.182；下次v1.185），补丁下载分支每版更新。本地每版保留提交和完整维护包，不能每次生成补丁就推送main。进度记录在maintenance/sync_policy.json。
