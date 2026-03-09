# 🔄 快速参考：部署更新机制 (Quick Reference)

## 最简短的答案

✅ **再次部署会自动更新。**

## 工作原理 (30 秒理解)

```
每次运行部署脚本：
1. 优先尝试 UPDATE（如果插件已存在）→ 更新成功
2. 失败时自动 CREATE（第一次部署时）→ 创建成功

结果：
✅ 不管第几次部署，脚本都能正确处理
✅ 无需手动判断创建还是更新
✅ 立即生效，无需重启
```

## 三个场景

| 场景 | 发生什么 | 结果 |
|------|---------|------|
| **第1次部署** | UPDATE 失败 → CREATE 成功 | ✅ 插件被创建 |
| **修改代码后再次部署** | UPDATE 直接成功 | ✅ 插件立即更新 |
| **未修改，重复部署** | UPDATE 成功 (无任何变化) | ✅ 无效果 (安全) |

## 开发流程

```bash
# 1. 第一次部署
python deploy_async_context_compression.py
# 结果: ✅ Created

# 2. 修改代码
vim ../plugins/filters/async-context-compression/async_context_compression.py
# 编辑...

# 3. 再次部署 (自动更新)
python deploy_async_context_compression.py
# 结果: ✅ Updated

# 4. 继续修改，重复部署
# ... 可以无限重复 ...
```

## 关键点

✅ **自动化** — 不用管是更新还是创建  
✅ **快速** — 每次部署 5 秒  
✅ **安全** — 用户配置不会被覆盖  
✅ **即时** — 无需重启 OpenWebUI  
✅ **版本管理** — 自动从代码提取版本号  

## 版本号怎么管理？

修改代码中的版本号：

```python
# async_context_compression.py

"""
version: 1.3.0 → 1.3.1 (修复 Bug)
version: 1.3.0 → 1.4.0 (新功能)
version: 1.3.0 → 2.0.0 (重大更新)
"""
```

然后部署，脚本会自动读取新版本号并更新。

## 常见问题速答

**Q: 用户的配置会被覆盖吗？**  
A: ❌ 不会，Valves 配置保持不变

**Q: 需要重启 OpenWebUI 吗？**  
A: ❌ 不需要，立即生效

**Q: 更新失败了会怎样？**  
A: ✅ 安全，保持原有插件不变

**Q: 可以无限制地重复部署吗？**  
A: ✅ 可以，完全幂等

## 一行总结

> 首次部署创建插件，之后每次部署自动更新，5 秒即时反馈，无需重启。

---

📖 详细文档：`scripts/UPDATE_MECHANISM.md`
