# 域名白名单配置指南

## 概述

OpenWebUI Skills Manager 现在支持简化的 **主域名白名单** 来保护技能 URL 下载。您无需列举所有可能的域名变体，只需指定主域名，系统会自动接受任何子域名。

## 配置

### 参数：`TRUSTED_DOMAINS`

**默认值：**

```
github.com,huggingface.co
```

**说明：** 逗号分隔的主信任域名清单。

### 匹配规则

域名白名单**始终启用**以进行下载。URL 将根据以下逻辑与白名单进行验证：

#### ✅ 允许

- **完全匹配：** `github.com` → URL 域名为 `github.com`
- **子域名匹配：** `github.com` → URL 域名为 `api.github.com`、`gist.github.com`...

⚠️ **重要提示：** `raw.githubusercontent.com` 是 `githubusercontent.com` 的子域名，**不是** `github.com` 的子域名。

如果需要支持 GitHub 原始文件，应在白名单中添加 `githubusercontent.com`：

```
github.com,githubusercontent.com,huggingface.co
```

#### ❌ 阻止

- 域名不在清单中：`bitbucket.org`（如未配置）
- 协议不支持：`ftp://example.com`
- 本地文件：`file:///etc/passwd`

## 示例

### 场景 1：仅 GitHub 技能

**配置：**

```
TRUSTED_DOMAINS = "github.com"
```

**允许的 URL：**

- `https://github.com/...` ✓（完全匹配）
- `https://api.github.com/...` ✓（子域名）
- `https://gist.github.com/...` ✓（子域名）

**阻止的 URL：**

- `https://raw.githubusercontent.com/...` ✗（不是 github.com 的子域名）
- `https://bitbucket.org/...` ✗（不在白名单中）

### 场景 2：GitHub + GitHub 原始内容

为同时支持 GitHub 和 GitHub 原始内容站点，需添加两个主域名：

**配置：**

```
TRUSTED_DOMAINS = "github.com,githubusercontent.com,huggingface.co"
```

**允许的 URL：**

- `https://github.com/user/repo/...` ✓
- `https://raw.githubusercontent.com/user/repo/...` ✓
- `https://huggingface.co/...` ✓
- `https://hub.huggingface.co/...` ✓

## 测试

当尝试从 URL 安装时，如果域名不在白名单中，工具日志会显示：

```
INFO: URL domain 'example.com' is not in whitelist. Trusted domains: github.com, huggingface.co
```

## 最佳实践

1. **最小化配置：** 只添加您真正信任的域名

   ```
   TRUSTED_DOMAINS = "github.com,huggingface.co"
   ```

2. **添加注释说明：** 清晰标注每个域名的用途

   ```
   # GitHub 代码托管
   github.com
   # GitHub 原始内容交付
   githubusercontent.com
   # HuggingFace AI模型和数据集
   huggingface.co
   ```

3. **定期审查：** 每季度审计一次白名单，确保所有条目仍然必要

4. **利用子域名：** 当域名在白名单中时，无需列举所有子域名
   ✓ 正确方式：`github.com`（自动覆盖 github.com、api.github.com 等）
   ✗ 冗余方式：`github.com,api.github.com,gist.github.com`

## 技术细节

### 域名验证算法

```python
def is_domain_trusted(url_hostname, trusted_domains_list):
    url_hostname = url_hostname.lower()
    
    for trusted_domain in trusted_domains_list:
        trusted_domain = trusted_domain.lower()
        
        # 规则 1：完全匹配
        if url_hostname == trusted_domain:
            return True
        
        # 规则 2：子域名匹配（url_hostname 以 ".{trusted_domain}" 结尾）
        if url_hostname.endswith("." + trusted_domain):
            return True
    
    return False
```

### 安全防护层

该工具采用纵深防御策略：

1. **协议验证：** 仅允许 `http://` 和 `https://`
2. **IP 地址阻止：** 阻止私有 IP 范围（127.0.0.0/8、10.0.0.0/8 等）
3. **域名白名单：** 主机名必须与白名单条目匹配
4. **超时保护：** 下载超过 12 秒自动超时（可配置）

---

**版本：** 0.2.2  
**最后更新：** 2026-03-08
