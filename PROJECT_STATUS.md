# 当前状态（2026-11-13，Asia/Shanghai）

## GitHub 与云端迁移进度

公开仓库：https://github.com/wyex2002-ctrl/Guimeng 。本地 origin 已连接该仓库，main 跟踪 origin/main；初始导入与迁移文档提交已推送，baseline-v1.177 标签保持原提交。Git 推送在使用系统既有代理 127.0.0.1:7890 后成功，仅在命令中指定代理，未修改系统网络设置。

GitHub 账号授权与仓库读写权限已确认。Codex 云端目前仅检测到 Default environment，保存的仓库列表仍为空；网页操作超时，因此尚未完成可复用云环境的关联/发布，不能宣称云端回归已通过。本地 main 与基线标签已在 GitHub，可由云任务克隆。

用户在 Codex 的“Work in / 工作位置”选择 Cloud，创建环境时选择 wyex2002-ctrl/Guimeng。环境准备要求：Python 3.12+、make 和 C 编译器；使用随仓库官方 LuaJIT 2.0 b83bcba 源码，不安装替代的 2.1 运行时。先读 AGENTS.md，再执行 python3 patch_v177.py、python3 test_v177.py，核对资源大小及 SHA-256。静态和正常/hot 原生测试全部通过后更新本文件与维护记录，再保存并发布环境。没有必要上传实际游戏目录和存档。

云端首次接手提示：克隆上述公开仓库，确认 baseline-v1.177 标签，接手 v1.177 维护工程；本轮只检查环境、重建和回归，不改游戏规则。保留 v1.175/v1.176 启动修复及数据库显式 API/保护约束。不要把历史 validation 当作本轮通过，不宣称小怪声望实机问题彻底解决。未跑完整 Windows 客户端。

维护基线 v1.177；初始 Git 工作区干净。`baseline-v1.177` 指向导入提交 `486159b9d6e53eed2a5d9313402936eafda9cae4`，本次不移动标签，不修改游戏规则。

已阅读 README、维护记录开头及第四十四节，并检查构建/测试/打包及底层工具。所有必要源码、三份输入编译字节码、基线包、官方依赖源码、历史记录保持跟踪。

## 本次检查结果

- Python 3.13.15 可用：`C:\Users\wyex2\AppData\Local\Programs\Python\Python313\python.exe`；标准库导入和实际重建可运行。系统默认文本编码 cp936，故脚本中文输入/JSON 输出改为显式 UTF-8。
- `python3` 指向不可执行的 WindowsApps 别名；`py --list` 未识别安装。请使用 `python`。
- PATH 未发现 `luajit`、`make`、`gcc`、`clang`、`cl`；常见 Visual Studio/MSYS2 目录未发现工具。WSL 报告未安装。尚未完成官方 LuaJIT 2.0 构建或源码再编译。
- `python patch_v177.py` 使用附带字节码成功重建 `game_v177.res`：2689762 字节，SHA-256 `18d317b5dc21073320d5d1998a68e210308da76a6cd746b696a32cea1095755f`，完全符合目标。
- `python test_v177.py` 的资源结构、差异原型、跳转/常量、显式导出及保留启动原型静态断言已执行通过；随后缺少 make，原生测试未执行。兼容调整后 Windows 会清晰报告须指定 runtime，而非尝试 Linux make。
- `validation_v177.json` 保留云端历史结果，本次没有覆盖为通过；没有运行完整 Windows 客户端，没有新版实机杀怪日志。
- 打包默认输出移到工程内 deliverables，并增加 --output；维护包包含交接文档及当前完整维护记录。暂未运行正式打包/发布，须先取得本轮原生回归结果。

## 补齐工具及下一步

方案 A：安装 Visual Studio Build Tools 的“使用 C++ 的桌面开发”（MSVC 和 Windows SDK）。在 Developer Command Prompt 内解压随包 `LuaJIT-2.0-b83bcba.tar.gz` 至 `native_work`，进入 `native_work\luajit20\src` 执行 `msvcbuild.bat`；随后用 `python test_v177.py --runtime <luajit.exe绝对路径>`。运行时及 lua51.dll 保持同目录。不要用 LuaJIT 2.1 的构建结果替代。

方案 B：管理员安装 WSL（`wsl --install -d Ubuntu`，按提示重启）；Ubuntu 中安装 `sudo apt update`、`sudo apt install python3 build-essential`。在独立维护工程内运行 `python3 patch_v177.py`、`python3 test_v177.py`，脚本用随包源码 make 构建官方版本。本次未执行安装或声称上述工具已可用。

运行正常/hot 全部回归并审查本轮 validation 后再打包；若从源码编译，额外核对编译字节码差异及最终资源哈希。下一次游戏规则维护仍需实机击杀日志 `log/guimeng_run_latest.txt`，以及独立的客户端验证。本次只操作维护工程。
