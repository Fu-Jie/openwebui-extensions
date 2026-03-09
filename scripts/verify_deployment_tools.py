#!/usr/bin/env python3
"""
Quick verification script to ensure all deployment tools are in place.

This script checks that all necessary files for async_context_compression
local deployment are present and functional.
"""

import sys
from pathlib import Path

def main():
    """Check all deployment tools are ready."""
    base_dir = Path(__file__).parent.parent
    
    print("\n" + "="*80)
    print("✨ 异步上下文压缩本地部署工具 — 验证状态")
    print("="*80 + "\n")
    
    files_to_check = {
        "🐍 Python 脚本": [
            "scripts/deploy_async_context_compression.py",
            "scripts/deploy_filter.py",
            "scripts/deploy_pipe.py",
        ],
        "📖 部署文档": [
            "scripts/README.md",
            "scripts/QUICK_START.md",
            "scripts/DEPLOYMENT_GUIDE.md",
            "scripts/DEPLOYMENT_SUMMARY.md",
            "plugins/filters/async-context-compression/DEPLOYMENT_REFERENCE.md",
        ],
        "🧪 测试文件": [
            "tests/scripts/test_deploy_filter.py",
        ],
    }
    
    all_exist = True
    
    for category, files in files_to_check.items():
        print(f"\n{category}:")
        print("-" * 80)
        
        for file_path in files:
            full_path = base_dir / file_path
            exists = full_path.exists()
            status = "✅" if exists else "❌"
            
            print(f"  {status} {file_path}")
            
            if exists and file_path.endswith(".py"):
                size = full_path.stat().st_size
                lines = len(full_path.read_text().split('\n'))
                print(f"     └─ [{size} bytes, ~{lines} lines]")
            
            if not exists:
                all_exist = False
    
    print("\n" + "="*80)
    
    if all_exist:
        print("✅ 所有部署工具文件已准备就绪！")
        print("="*80 + "\n")
        
        print("🚀 快速开始（3 种方式）：\n")
        
        print("  方式 1: 最简单 (推荐)")
        print("  ─────────────────────────────────────────────────────────")
        print("    cd scripts")
        print("    python deploy_async_context_compression.py")
        print()
        
        print("  方式 2: 通用工具")
        print("  ─────────────────────────────────────────────────────────")
        print("    cd scripts")
        print("    python deploy_filter.py")
        print()
        
        print("  方式 3: 部署其他 Filter")
        print("  ─────────────────────────────────────────────────────────")
        print("    cd scripts")
        print("    python deploy_filter.py --list")
        print("    python deploy_filter.py folder-memory")
        print()
        
        print("="*80 + "\n")
        print("📚 文档参考：\n")
        print("  • 快速开始:    scripts/QUICK_START.md")
        print("  • 完整指南:    scripts/DEPLOYMENT_GUIDE.md")
        print("  • 技术总结:    scripts/DEPLOYMENT_SUMMARY.md")
        print("  • 脚本说明:    scripts/README.md")
        print("  • 测试覆盖:    pytest tests/scripts/test_deploy_filter.py -v")
        print()
        
        print("="*80 + "\n")
        return 0
    else:
        print("❌ 某些文件缺失！")
        print("="*80 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
