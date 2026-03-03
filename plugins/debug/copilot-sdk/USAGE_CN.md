# Copilot SDK 自动任务脚本使用说明

本目录提供了一个通用任务执行脚本，以及两个示例任务脚本：
- `auto_programming_task.py`（通用）
- `run_mindmap_action_to_tool.sh`（示例：mind map action → tool）
- `run_infographic_action_to_tool.sh`（示例：infographic action → tool）

## 1. 先决条件

- 在仓库根目录执行（非常重要）
- Python 3 可用
- 当前环境中可正常使用 Copilot SDK / CLI

建议先验证：

python3 plugins/debug/copilot-sdk/auto_programming_task.py --help | head -40

---

## 2. 核心行为（当前默认）

`auto_programming_task.py` 默认是 **两阶段自动执行**：

1) 先规划（Planning）：AI 根据你的需求自动补全上下文、扩展为可执行计划。
2) 再执行（Execution）：AI 按计划直接改代码并给出结果。

如果你要关闭“先规划”，可使用 `--no-plan-first`。

---

## 3. 可复制命令（通用）

### 3.1 最常用：直接写任务文本

python3 plugins/debug/copilot-sdk/auto_programming_task.py \
  --task "把 plugins/actions/xxx/xxx.py 转成 plugins/tools/xxx-tool/ 下的单文件 Tool 插件。保留 i18n 和语言回退逻辑。不要升级 SDK 版本。" \
  --cwd "$PWD" \
  --model "gpt-5.3-codex" \
  --reasoning-effort "xhigh" \
  --timeout 3600 \
  --stream \
  --trace-events \
  --heartbeat-seconds 8

### 3.2 使用任务文件（长任务推荐）

先写任务文件（例如 task.txt），再执行：

python3 plugins/debug/copilot-sdk/auto_programming_task.py \
  --task-file "./task.txt" \
  --cwd "$PWD" \
  --model "gpt-5.3-codex" \
  --reasoning-effort "xhigh" \
  --timeout 3600 \
  --stream \
  --trace-events \
  --heartbeat-seconds 8

### 3.3 关闭规划阶段（仅直接执行）

python3 plugins/debug/copilot-sdk/auto_programming_task.py \
  --task "你的任务" \
  --cwd "$PWD" \
  --model "gpt-5-mini" \
  --reasoning-effort "medium" \
  --timeout 1800 \
  --no-plan-first

---

## 4. 可复制命令（示例脚本）

### 4.1 Mind Map 示例任务

./plugins/debug/copilot-sdk/run_mindmap_action_to_tool.sh

### 4.2 Infographic 示例任务

./plugins/debug/copilot-sdk/run_infographic_action_to_tool.sh

说明：这两个脚本是“固定任务模板”，适合当前仓库；复制到其他仓库时通常需要改任务内容。

---

## 5. 结果如何判定“完成”

建议同时满足以下条件：

1) 进程退出码为 0
2) 输出中出现阶段结束信息（含最终摘要）
3) 看到 `session.idle`（若是 `session.error` 则未完成）
4) `git diff --name-only` 显示改动范围符合你的约束

可复制检查命令：

echo $?
git diff --name-only
git status --short

---

## 6. 参数速查

- `--task`：直接传任务文本
- `--task-file`：从文件读取任务文本（与 `--task` 二选一）
- `--cwd`：工作区目录（建议用 `$PWD`）
- `--model`：模型（例如 `gpt-5.3-codex`、`gpt-5-mini`）
- `--reasoning-effort`：`low|medium|high|xhigh`
- `--timeout`：超时秒数
- `--stream`：实时输出增量内容
- `--trace-events`：输出事件流，便于排错
- `--heartbeat-seconds`：心跳输出间隔
- `--no-plan-first`：关闭默认“先规划后执行”

---

## 7. 常见问题

### Q1：为什么提示找不到脚本？
你大概率不在仓库根目录。先执行：

pwd

确认后再运行命令。

### Q2：执行很久没有输出？
加上 `--trace-events --stream`，并适当增大 `--timeout`。

### Q3：改动超出预期范围？
把范围约束明确写进任务文本，例如：

“不要修改其他文件代码，可以读取整个项目作为代码库。”

并在完成后用：

git diff --name-only

进行核对。
