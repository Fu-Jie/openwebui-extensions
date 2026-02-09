import os
import sys
import json
import asyncio
from typing import List, Dict

# 1. 尝试导入 OpenWebUI 环境
try:
    from open_webui.models.models import Models, ModelForm, ModelMeta, ModelParams
    from open_webui.internal.db import get_session
except ImportError:
    print("❌ 错误: 无法导入 OpenWebUI 模块。请确保在 OpenWebUI 环境（如 conda ai）中运行此脚本。")
    sys.exit(1)

# 2. 导入 Copilot SDK
try:
    from copilot import CopilotClient
except ImportError:
    print("❌ 错误: 无法导入 copilot SDK。请运行: pip install github-copilot-sdk==0.1.23")
    sys.exit(1)

async def fetch_real_models() -> List[Dict]:
    gh_token = os.environ.get("GH_TOKEN")
    if not gh_token:
        print("❌ 错误: 未设置 GH_TOKEN 环境变量。")
        return []

    client = CopilotClient()
    try:
        await client.start()
        raw_models = await client.list_models()
        processed = []
        for m in raw_models:
            m_id = getattr(m, "id", str(m))
            # 提取倍率
            billing = getattr(m, "billing", {})
            if not isinstance(billing, dict): billing = vars(billing)
            multiplier = billing.get("multiplier", 1)
            
            # 提取能力
            cap = getattr(m, "capabilities", None)
            vision = False
            reasoning = False
            if cap:
                supports = getattr(cap, "supports", {})
                if not isinstance(supports, dict): supports = vars(supports)
                vision = supports.get("vision", False)
                reasoning = supports.get("reasoning_effort", False)

            processed.append({
                "id": m_id,
                "name": f"GitHub Copilot ({m_id})",
                "vision": vision,
                "reasoning": reasoning,
                "multiplier": multiplier
            })
        return processed
    except Exception as e:
        print(f"❌ 获取模型失败: {e}")
        return []
    finally:
        await client.stop()

async def sync_to_db():
    models = await fetch_real_models()
    if not models: return

    print(f"🔄 发现 {len(models)} 个 Copilot 模型，正在同步到工作区...")
    
    # 默认管理员 ID
    admin_user_id = "00000000-0000-0000-0000-000000000000" 

    for m in models:
        # 对应插件中的 ID 格式
        full_id = f"copilot-{m['id']}"
        
        existing = Models.get_model_by_id(full_id)
        if existing:
            print(f"⚠️ 跳过: {full_id} (已存在)")
            continue

        form_data = ModelForm(
            id=full_id,
            base_model_id=None,
            name=m['name'],
            meta=ModelMeta(
                description=f"GitHub Copilot 官方模型。倍率: {m['multiplier']}x。支持推理: {m['reasoning']}。",
                capabilities={
                    "vision": m['vision'],
                    "reasoning": m['reasoning']
                }
            ),
            params=ModelParams()
        )

        try:
            if Models.insert_new_model(form_data, admin_user_id):
                print(f"✅ 成功同步: {m['name']}")
        except Exception as e:
            print(f"❌ 同步 {m['id']} 失败: {e}")

if __name__ == "__main__":
    asyncio.run(sync_to_db())