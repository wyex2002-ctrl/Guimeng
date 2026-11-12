# 归梦维护工程接手约定

维护基线为《归梦 v2.26》魔改 v1.177；Git 标签 `baseline-v1.177` 是云端维护工程导入快照。先读 README.txt、PROJECT_STATUS.md、修改记录_维护版.txt 开头及第四十四节，再改动。历史冲突以最新节为准，版本尾数按整数比较。

## 结构与必须保留的文件

- `base_v176.zip`：重建输入，内含上一版玩家资源，不能删除或替换。
- 三组 `*_v177.lua` / 同名 `.ljbc`：UTF-8 源码与官方 LuaJIT 2.0 编译字节码均须保留；默认重建直接依赖字节码。
- `patch_v177.py`、`test_v177.py`、`package_v177.py`：构建、回归、打包入口。
- `ljtool.py`、`ljdis.py`、`patch_v139.py`、`bytecode_relocate.py`、`resource_tools.py`、`native_test_utils.py`：必要底层工具；旧版本号不表示可删。
- `systems_regression_v177.lua`、`reputation_regression_v177.lua`：实际字节码回归。
- `LuaJIT-2.0-b83bcba.tar.gz`：官方依赖源码；不可换成 LuaJIT 2.1 或普通 Lua。
- `build_v177.json`、`validation_v177.json`：构建与历史验证记录；后者随包原件不代表本机测试通过。
- `修改记录_维护版.txt`、`history_through_v176.txt`、`maintenance_notes_v177.txt`、`player_changes_v177.json`：完整历史、当前节与玩家累计功能来源。

## 构建、测试、发布

在工程目录使用 Python 3.12+（依赖标准库；本机可用 `python`，勿依赖 Windows 的 python3 商店别名）。

```powershell
python patch_v177.py
python test_v177.py --runtime C:/tools/luajit20/src/luajit.exe
python package_v177.py
```

有官方运行时时可用 `python patch_v177.py --runtime <绝对路径>` 从源码重新编译，会重写三份受跟踪字节码，须审查差异与最终哈希。Linux/WSL 可用 `python3`；`test_v177.py` 不带 runtime 会解压依赖并调用 `make -j4`。Windows 自动 make 路径不适用，须显式指定已构建运行时。

发布前先重建、核对目标哈希、完成正常及 hot 两模式回归，检查 validation 是本轮生成的，不能用随包云端结果冒充本机测试。默认包输出在工程 `deliverables/`，可用 `--output <目录>` 指定；不会安装游戏。玩家包 `归梦v2.26_魔改补丁_v1.177.zip` 仅含 `Lib/game.res`、`log/` 和玩家说明；维护包 `Guimeng_v1.177_maintenance.zip` 保留重建输入和迁移文档。验证 ZIP 完整性和玩家包资源哈希后才可对外发布。本次无原生运行时，不发布。

## 长期边界

保留全部累计修改，尤其 v1.175 的 Ux 待应用难度、初始化顺序与原环境保护，以及 v1.176 显式 API 导出修复。数据库沙箱没有 pcall/xpcall，不得用 `_G` 回退或普通 Lua 环境补齐这些 API 来掩盖问题。现有测试中其他引擎替身须按作用域审查。

玩家说明仅保留累计编号功能，不写详细版本历史和概率；详细修改、测试和限制写入维护记录。日志直接写游戏 log，不能形成 log/log。小怪声望仍须新版实机杀怪日志，不能宣称彻底解决；受控原生回归也不等于完整客户端实测。

每次修改同步 PROJECT_STATUS.md 和维护记录；维护包使用当前完整维护记录，避免打包丢失迁移追加内容。不要覆盖实际游戏目录或存档。native_work、compile_work、生成模块与资源仅用于工程验证，不可安装。
