# 🔐 Domain Whitelist Quick Reference

## TL;DR (主要点)

| 需求 | 配置示例 | 允许的 URL |
| --- | --- | --- |
| 仅 GitHub | `github.com` | ✓ github.com、api.github.com、gist.github.com |
| GitHub + Raw | `github.com,githubusercontent.com` | ✓ 上述所有 + raw.githubusercontent.com |
| 多个源 | `github.com,huggingface.co,anthropic.com` | ✓ 对应域名及所有子域名 |

## Valve 配置

**Trusted Domains (Required):**

```
TRUSTED_DOMAINS = "github.com,huggingface.co"
```

⚠️ **注意：** 域名白名单是**必须启用的**，无法禁用。必须配置至少一个信任域名。

## 匹配逻辑

### ✅ 通过白名单

```python
URL Domain: api.github.com
Whitelist: github.com

检查:
  1. api.github.com == github.com? NO
  2. api.github.com.endswith('.github.com')? YES ✅
  
结果: 允许安装
```

### ❌ 被白名单拒绝

```python
URL Domain: raw.githubusercontent.com
Whitelist: github.com

检查:
  1. raw.githubusercontent.com == github.com? NO
  2. raw.githubusercontent.com.endswith('.github.com')? NO ❌
  
结果: 拒绝
提示: 需要在白名单中添加 'githubusercontent.com'
```

## 常见域名组合

### Option A: 精简 (GitHub + HuggingFace)

```
github.com,huggingface.co
```

**用途:** 绝大多数开源技能项目  
**缺点:** 不支持 GitHub 原始文件链接

### Option B: 完整 (GitHub 全家桶 + HuggingFace)

```
github.com,githubusercontent.com,huggingface.co
```

**用途:** 完全支持 GitHub 所有链接类型  
**优点:** 涵盖 GitHub 页面、仓库、原始内容、Gist

### Option C: 企业版 (私有 + 公开)

```
github.com,githubusercontent.com,huggingface.co,my-company.com,internal-cdn.com
```

**用途:** 混合使用 GitHub 公开技能 + 企业内部技能  
**注意:** 子域名自动支持，无需逐个列举

## 故障排除

### 问题：技能安装失败，错误提示"not in whitelist"

**解决方案：** 检查 URL 的域名

```python
URL: https://cdn.jsdelivr.net/gh/Fu-Jie/...

Whitelist: github.com

❌ 失败原因：
  - cdn.jsdelivr.net 不是 github 的子域名
  - 需要单独在白名单中添加 jsdelivr.net

✓ 修复方案：
  TRUSTED_DOMAINS = "github.com,jsdelivr.net,huggingface.co"
```

### 问题：GitHub Raw 链接被拒绝

```
URL: https://raw.githubusercontent.com/user/repo/...
White: github.com

問题：raw.githubusercontent.com 属于 githubusercontent.com，不属于 github.com

✓ 解决方案：
  TRUSTED_DOMAINS = "github.com,githubusercontent.com"
```

### 问题：不确定 URL 的域名是什么

**调试方法：**

```bash
# 在 bash 中提取域名
$ python3 -c "
from urllib.parse import urlparse
url = 'https://raw.githubusercontent.com/Fu-Jie/test.py'
hostname = urlparse(url).hostname
print(f'Domain: {hostname}')
"

# 输出: Domain: raw.githubusercontent.com
```

## 最佳实践

✅ **推荐做法：**

- 只添加必要的主域名
- 利用子域名自动匹配（无需逐个列举）
- 定期审查白名单内容
- 确保至少配置一个信任域名

❌ **避免做法：**

- `github.com,api.github.com,gist.github.com,raw.github.com` （冗余）
- 设置空的 `TRUSTED_DOMAINS` （会导致拒绝所有下载）

## 测试您的配置

运行提供的测试脚本：

```bash
python3 docs/test_domain_validation.py
```

输出示例：

```
✓ PASS | GitHub exact domain
  Result: ✓ Exact match: github.com == github.com

✓ PASS | GitHub API subdomain
  Result: ✓ Subdomain match: api.github.com.endswith('.github.com')
```

---

**版本:** 0.2.2  
**相关文档:** [Domain Whitelist Guide](DOMAIN_WHITELIST.md)
