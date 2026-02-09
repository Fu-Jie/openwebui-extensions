import asyncio
import os
import json
import time
from typing import Any
from datetime import datetime
from copilot import CopilotClient

# 自定义 JSON 编码器，处理 datetime 等对象
class SDKEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)

async def run_debug_test(client, model_id, effort, prompt):
    print(f"\n" + "🔍" * 15)
    print(f"DEBUGGING: {model_id} | {effort.upper()}")
    print("🔍" * 15)
    
    session_config = {
        "model": model_id,
        "reasoning_effort": effort
    }
    
    queue = asyncio.Queue()
    done = asyncio.Event()
    SENTINEL = object()

    def handler(event):
        try:
            etype = getattr(event, "type", "unknown")
            if hasattr(etype, "value"): etype = etype.value
            
            raw_data = {}
            # 优先尝试 SDK 自带的 to_dict
            if hasattr(event, "to_dict"):
                raw_data = event.to_dict()
            elif hasattr(event, "data"):
                data_obj = event.data
                if isinstance(data_obj, dict):
                    raw_data = data_obj
                elif hasattr(data_obj, "to_dict"):
                    raw_data = data_obj.to_dict()
                else:
                    raw_data = {k: v for k, v in vars(data_obj).items() if not k.startswith('_')}
            else:
                raw_data = {k: v for k, v in vars(event).items() if not k.startswith('_')}
            
            queue.put_nowait((etype, raw_data))
            
            if etype in ["session.idle", "session.error"]:
                done.set()
                queue.put_nowait(SENTINEL)
        except Exception as e:
            print(f"Handler Error: {e}")

    try:
        session = await client.create_session(config=session_config)
        unsubscribe = session.on(handler)
        
        print(f"Sending prompt...")
        asyncio.create_task(session.send({"prompt": prompt, "mode": "immediate"}))
        
        event_count = 0
        while True:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=180)
                if item is SENTINEL: break
                
                etype, data = item
                event_count += 1
                
                # 打印所有事件，不进行过滤，这样我们可以看到完整的生命周期
                print(f"\n[#{event_count} EVENT: {etype}]")
                print(json.dumps(data, indent=2, ensure_ascii=False, cls=SDKEncoder))
                
            except asyncio.TimeoutError:
                print("\n⚠️ Timeout: No events for 180s")
                break

        unsubscribe()
        await session.destroy()
        
    except Exception as e:
        print(f"❌ Session Failed: {e}")

async def main():
    gh_token = os.environ.get("GH_TOKEN")
    if not gh_token:
        print("❌ Error: GH_TOKEN not set")
        return

    client = CopilotClient()
    await client.start()
    
    # 使用一个简单但需要思考的问题
    prompt = "123 * 456 等于多少？请给出思考过程。"
    target_model = "gpt-5-mini" 
    
    await run_debug_test(client, target_model, "high", prompt)
    
    await client.stop()

if __name__ == "__main__":
    asyncio.run(main())
