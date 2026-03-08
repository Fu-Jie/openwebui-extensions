# OpenWebUI Skills Manager 安全修复测试指南

## 快速开始

### 无需 OpenWebUI 依赖的独立测试

已创建完全独立的测试脚本，**不需要任何 OpenWebUI 依赖**，可以直接运行：

```bash
python3 plugins/debug/openwebui-skills-manager/test_security_fixes.py
```

### 测试输出示例

```
🔒 OpenWebUI Skills Manager 安全修复测试
版本: 0.2.2
============================================================

✓ 所有测试通过！

修复验证：
  ✓ SSRF 防护：阻止指向内部 IP 的请求
  ✓ TAR/ZIP 安全提取：防止路径遍历攻击
  ✓ 名称冲突检查：防止技能名称重复
  ✓ URL 验证：仅接受安全的 HTTP(S) URL
```

---

## 五个测试用例详解

### 1. SSRF 防护测试

**文件**: `test_security_fixes.py` - `test_ssrf_protection()`

测试 `_is_safe_url()` 方法能否正确识别并拒绝危险的 URL：

<details>
<summary>被拒绝的 URL (10 种)</summary>

```
✗ http://localhost/skill
✗ http://127.0.0.1:8000/skill              # 127.0.0.1 环回地址
✗ http://[::1]/skill                       # IPv6 环回
✗ http://0.0.0.0/skill                     # 全零 IP
✗ http://192.168.1.1/skill                 # RFC 1918 私有范围
✗ http://10.0.0.1/skill                    # RFC 1918 私有范围
✗ http://172.16.0.1/skill                  # RFC 1918 私有范围
✗ http://169.254.1.1/skill                 # Link-local
✗ file:///etc/passwd                       # file:// 协议
✗ gopher://example.com/skill                # 非 http(s)
```

</details>

<details>
<summary>被接受的 URL (3 种)</summary>

```
✓ https://github.com/Fu-Jie/openwebui-extensions/raw/main/SKILL.md
✓ https://raw.githubusercontent.com/user/repo/main/skill.md
✓ https://example.com/public/skill.zip
```

</details>

**防护机制**:

- 检查 hostname 是否在 localhost 变体列表中
- 使用 `ipaddress` 库检测私有、回环、链接本地和保留 IP
- 仅允许 `http` 和 `https` 协议

---

### 2. TAR 提取安全性测试

**文件**: `test_security_fixes.py` - `test_tar_extraction_safety()`

测试 `_safe_extract_tar()` 方法能否防止**路径遍历攻击**：

**被测试的攻击**:

```
TAR 文件包含: ../../etc/passwd
↓
提取时被拦截，日志输出:
  WARNING - Skipping unsafe TAR member: ../../etc/passwd
↓
结果: /etc/passwd 文件 NOT 创建 ✓
```

**防护机制**:

```python
# 验证解析后的路径是否在提取目录内
member_path.resolve().relative_to(extract_dir.resolve())
# 如果抛出 ValueError，说明有遍历尝试，跳过该成员
```

---

### 3. ZIP 提取安全性测试

**文件**: `test_security_fixes.py` - `test_zip_extraction_safety()`

与 TAR 测试相同，但针对 ZIP 文件的路径遍历防护：

```
ZIP 文件包含: ../../etc/passwd
↓
提取时被拦截
↓
结果: /etc/passwd 文件 NOT 创建 ✓
```

---

### 4. 技能名称冲突检查测试

**文件**: `test_security_fixes.py` - `test_skill_name_collision()`

测试 `update_skill()` 方法中的名称碰撞检查：

```
场景 1: 尝试将技能2改名为 "MySkill" (已被技能1占用)
↓
检查逻辑触发，检测到冲突
返回错误: Another skill already has the name "MySkill" ✓

场景 2: 尝试将技能2改名为 "UniqueSkill" (不存在)
↓
检查通过，允许改名 ✓
```

---

### 5. URL 标准化测试

**文件**: `test_security_fixes.py` - `test_url_normalization()`

测试 URL 验证对各种无效格式的处理：

```
被拒绝的无效 URL:
✗ not-a-url             # 不是有效 URL
✗ ftp://example.com     # 非 http/https 协议
✗ ""                    # 空字符串
✗ "   "                 # 纯空白
```

---

## 如何修改和扩展测试

### 添加自己的测试用例

编辑 `plugins/debug/openwebui-skills-manager/test_security_fixes.py`：

```python
def test_my_custom_case():
    """我的自定义测试"""
    print("\n" + "="*60)
    print("测试 X: 我的自定义测试")
    print("="*60)
    
    tester = SecurityTester()
    
    # 你的测试代码
    assert condition, "错误消息"
    
    print("\n✓ 自定义测试通过!")

# 在 main() 中添加
def main():
    # ...
    test_my_custom_case()  # 新增
    # ...
```

### 测试特定的 URL

直接在 `unsafe_urls` 或 `safe_urls` 列表中添加：

```python
unsafe_urls = [
    # 现有项
    "http://internal-server.local/api",  # 新增: 本地局域网
]

safe_urls = [
    # 现有项
    "https://api.github.com/repos/Fu-Jie/openwebui-extensions",  # 新增
]
```

---

## 与 OpenWebUI 集成测试

如果需要在完整的 OpenWebUI 环境中测试，可以：

### 1. 单元测试方式

创建 `tests/test_skills_manager.py`（需要 OpenWebUI 环境）：

```python
import pytest
from plugins.tools.openwebui_skills_manager.openwebui_skills_manager import Tool

@pytest.fixture
def skills_tool():
    return Tool()

def test_safe_url_in_tool(skills_tool):
    """在实际工具对象中测试"""
    assert not skills_tool._is_safe_url("http://localhost/skill")
    assert skills_tool._is_safe_url("https://github.com/user/repo")
```

运行方式:

```bash
pytest tests/test_skills_manager.py -v
```

### 2. 集成测试方式

在 OpenWebUI 中手动测试：

1. **安装插件**:

   ```
   OpenWebUI → Admin → Tools → 添加 openwebui-skills-manager 工具
   ```

2. **测试 SSRF 防护**:

   ```
   调用: install_skill(url="http://localhost:8000/skill.md")
   预期: 返回错误 "Unsafe URL: points to internal or reserved destination"
   ```

3. **测试名称冲突**:

   ```
   1. create_skill(name="MySkill", ...)
   2. create_skill(name="AnotherSkill", ...)
   3. update_skill(name="AnotherSkill", new_name="MySkill")
   预期: 返回错误 "Another skill already has the name..."
   ```

4. **测试文件提取**:

   ```
   上传包含 ../../etc/passwd 的恶意 TAR/ZIP
   预期: 提取成功但恶意文件被跳过
   ```

---

## 故障排除

### 问题: `ModuleNotFoundError: No module named 'ipaddress'`

**解决**: `ipaddress` 是内置模块，无需安装。检查 Python 版本 >= 3.3

```bash
python3 --version  # 应该 >= 3.3
```

### 问题: 测试卡住

**解决**: TAR/ZIP 提取涉及文件 I/O，可能在某些系统上较慢。检查磁盘空间：

```bash
df -h  # 检查是否有足够空间
```

### 问题: 权限错误

**解决**: 确认脚本可执行：

```bash
chmod +x plugins/debug/openwebui-skills-manager/test_security_fixes.py
```

---

## 修复验证清单

- [x] SSRF 防护 - 阻止内部 IP 请求
- [x] TAR 提取安全 - 防止路径遍历
- [x] ZIP 提取安全 - 防止路径遍历
- [x] 名称冲突检查 - 防止重名技能
- [x] 注释更正 - 移除误导性文档
- [x] 版本更新 - 0.2.2

---

## 相关链接

- GitHub Issue: <https://github.com/Fu-Jie/openwebui-extensions/issues/58>
- 修改文件: `plugins/tools/openwebui-skills-manager/openwebui_skills_manager.py`
- 测试文件: `plugins/debug/openwebui-skills-manager/test_security_fixes.py`
