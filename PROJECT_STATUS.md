# 当前状态（2026-11-13，Asia/Shanghai）

## 已发布云环境本轮独立接手验证（2026-11-13，Asia/Shanghai）

本节是最新状态；下方“历史迁移记录”描述此前 Windows 机器，不代表当前云环境缺少工具。用户已发布云环境，本轮在发布后恢复的实例重新执行验证，未修改游戏规则、源码、输入字节码或依赖。

- 已读 AGENTS.md、README.txt、本状态文件及维护记录开头、第四十四节；全部跟踪输入已记录 SHA-256，见 verification_v177_20261113.json。
- GitHub main 可获取，测试源提交为 5aa783dd9f1668e361433677ec35d0f72c95bff6；已 fetch baseline-v1.177，指向 486159b9d6e53eed2a5d9313402936eafda9cae4，未移动标签。
- Python 3.12.14、GNU Make 4.4.1、GCC 14.2.0 可用；从附带 LuaJIT-2.0-b83bcba.tar.gz 全新解压并 make -j4 构建成功。运行时报告 LuaJIT 2.0.1794164847；未使用普通 Lua 或 LuaJIT 2.1。
- python3 patch_v177.py 重建 2689762 字节，SHA-256 为 18d317b5dc21073320d5d1998a68e210308da76a6cd746b696a32cea1095755f，符合目标。
- 删除旧 validation 后，使用刚构建运行时显式执行 test_v177.py --runtime；系统回归 normal/hot 各 118638 项，声望回归 normal/hot 各 145810 项断言，全通过；静态结构与模块加载检查通过。本轮 UTC 起止时间见 validation.current_run（北京时间为 2026-11-13）。
- package_v177.py 成功；玩家包和维护包 ZIP CRC 检查通过，玩家包 Lib/game.res 大小、哈希与重建资源一致。维护包在另一个干净目录独立解压、重建，得到同一大小和哈希，且使用本轮官方运行时重新执行四组回归全部通过。默认重建使用附带字节码，没有重新编译三份 Lua 源码。
- 更新记录后再次打包并检查最终维护包中的文档及 validation 与工作区一致，再从最终包独立重建核对资源。文件位于 deliverables/，仅提供本轮验证产物，没有创建 GitHub Release 或发布游戏补丁。

复现步骤（已有独立运行时）：python3 patch_v177.py；python3 test_v177.py --runtime /绝对路径/luajit；python3 package_v177.py。全新运行时从附带源码解压构建；本轮日志和独立副本保存在 /workspace/guimeng-verification-20261113/。脚本会生成 build/validation；后续运行应审查差异，不使用随包历史结果替代测试。

限制：没有完整 Windows 客户端实测，没有新版实机杀怪日志；引擎原语仍有替身，小怪声望问题不能宣称彻底解决。没有安装到实际游戏目录或覆盖存档。本轮 Git 提交仅记录验证与文档，不修改游戏规则。

## 历史迁移记录（以下为此前机器的检查）


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
