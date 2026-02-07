# 开发指南勘误与更新

## 权限控制章节修正（第 2.2 节）

### ⚠️ 关键勘误

在实际测试中发现，Shell 权限请求使用的是 **`fullCommandText`** 字段，而非文档中提到的 `command` 字段。

### 需要修改的代码行

**第 89 行（错误）：**

```python
command = request.get("command", "")
```

**应改为（正确）：**

```python
command = request.get("fullCommandText", "") or request.get("command", "")
```

### 完整的正确实现

```python
async def on_user_permission_request(request, context):
    """
    统一权限审批网关
    """
    kind = request.get("kind")  # shell, write, mcp, read, url
    # ✅ 正确：使用 fullCommandText（shell）或 command（其他）
    command = request.get("fullCommandText", "") or request.get("command", "")

    # 1. 超级模式：全部允许
    if self.valves.PERMISSIONS_ALLOW_ALL:
        return {"kind": "approved"}

    # 2. 默认安全：始终允许 "读" 和 "Web浏览"
    if kind in ["read", "url"]:
        return {"kind": "approved"}

    # 3. 细粒度控制
    if kind == "shell":
        if self.valves.PERMISSIONS_ALLOW_SHELL:
            return {"kind": "approved"}
        
        pattern = self.valves.PERMISSIONS_SHELL_ALLOW_PATTERN
        if pattern and command:
            try:
                if re.match(pattern, command):
                    return {"kind": "approved"}
            except re.error:
                print(f"[Config Error] Invalid Regex: {pattern}")

    if kind == "write" and self.valves.PERMISSIONS_ALLOW_WRITE:
        return {"kind": "approved"}
        
    if kind == "mcp" and self.valves.PERMISSIONS_ALLOW_MCP:
        return {"kind": "approved"}

    # 4. 默认拒绝
    print(f"[Permission Denied] Blocked: {kind} {command}")
    return {
        "kind": "denied-by-rules", 
        "rules": [{"kind": "check-openwebui-valves"}]
    }
```

### Shell 权限请求的完整结构

```json
{
  "kind": "shell",
  "toolCallId": "call_xxx",
  "fullCommandText": "ls -la",                    // ← 关键字段
  "intention": "List all files and directories",
  "commands": [
    {
      "identifier": "ls -la",
      "readOnly": false
    }
  ],
  "possiblePaths": [],
  "possibleUrls": [],
  "hasWriteFileRedirection": false,
  "canOfferSessionApproval": false
}
```

## 测试验证

已通过完整测试套件验证（8/8 通过），详见 [PERMISSION_TEST_REPORT.md](./PERMISSION_TEST_REPORT.md)。

---

**更新日期**: 2026-01-30  
**验证状态**: ✅ 已测试  
**影响范围**: 2.2 权限与确认章节
