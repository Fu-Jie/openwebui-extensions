import asyncio
import importlib.util
import os
import sys
import types
import unittest


PLUGIN_PATH = os.path.join(os.path.dirname(__file__), "async_context_compression.py")
MODULE_NAME = "async_context_compression_under_test"


def _ensure_module(name: str) -> types.ModuleType:
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        sys.modules[name] = module
    return module


def _install_openwebui_stubs() -> None:
    _ensure_module("open_webui")
    _ensure_module("open_webui.utils")
    chat_module = _ensure_module("open_webui.utils.chat")
    _ensure_module("open_webui.models")
    users_module = _ensure_module("open_webui.models.users")
    models_module = _ensure_module("open_webui.models.models")
    chats_module = _ensure_module("open_webui.models.chats")
    main_module = _ensure_module("open_webui.main")
    _ensure_module("fastapi")
    fastapi_requests = _ensure_module("fastapi.requests")

    async def generate_chat_completion(*args, **kwargs):
        return {}

    class DummyUsers:
        pass

    class DummyModels:
        @staticmethod
        def get_model_by_id(model_id):
            return None

    class DummyChats:
        @staticmethod
        def get_chat_by_id(chat_id):
            return None

    class DummyRequest:
        pass

    chat_module.generate_chat_completion = generate_chat_completion
    users_module.Users = DummyUsers
    models_module.Models = DummyModels
    chats_module.Chats = DummyChats
    main_module.app = object()
    fastapi_requests.Request = DummyRequest


_install_openwebui_stubs()
spec = importlib.util.spec_from_file_location(MODULE_NAME, PLUGIN_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[MODULE_NAME] = module
assert spec.loader is not None
spec.loader.exec_module(module)
module.Filter._init_database = lambda self: None


class TestAsyncContextCompression(unittest.TestCase):
    def setUp(self):
        self.filter = module.Filter()

    def test_inlet_logs_tool_trimming_outcome_when_no_oversized_outputs(self):
        self.filter.valves.show_debug_log = True
        self.filter.valves.enable_tool_output_trimming = True

        logged_messages = []

        async def fake_log(message, log_type="info", event_call=None):
            logged_messages.append(message)

        async def fake_user_context(__user__, __event_call__):
            return {"user_language": "en-US"}

        async def fake_event_call(_payload):
            return True

        self.filter._log = fake_log
        self.filter._get_user_context = fake_user_context
        self.filter._get_chat_context = lambda body, metadata=None: {
            "chat_id": "",
            "message_id": "",
        }
        self.filter._get_latest_summary = lambda chat_id: None

        body = {
            "params": {"function_calling": "native"},
            "messages": [
                {
                    "role": "assistant",
                    "tool_calls": [{"id": "call_1", "type": "function"}],
                    "content": "",
                },
                {"role": "tool", "content": "short result"},
                {"role": "assistant", "content": "Final answer"},
            ],
        }

        asyncio.run(self.filter.inlet(body, __event_call__=fake_event_call))

        self.assertTrue(
            any("Tool trimming check:" in message for message in logged_messages)
        )
        self.assertTrue(
            any(
                "no oversized native tool outputs were found" in message
                for message in logged_messages
            )
        )

    def test_inlet_logs_tool_trimming_skip_reason_when_disabled(self):
        self.filter.valves.show_debug_log = True
        self.filter.valves.enable_tool_output_trimming = False

        logged_messages = []

        async def fake_log(message, log_type="info", event_call=None):
            logged_messages.append(message)

        async def fake_user_context(__user__, __event_call__):
            return {"user_language": "en-US"}

        async def fake_event_call(_payload):
            return True

        self.filter._log = fake_log
        self.filter._get_user_context = fake_user_context
        self.filter._get_chat_context = lambda body, metadata=None: {
            "chat_id": "",
            "message_id": "",
        }
        self.filter._get_latest_summary = lambda chat_id: None

        body = {"messages": [], "params": {"function_calling": "native"}}

        asyncio.run(self.filter.inlet(body, __event_call__=fake_event_call))

        self.assertTrue(
            any("Tool trimming skipped: tool trimming disabled" in message for message in logged_messages)
        )

    def test_normalize_native_tool_call_ids_keeps_links_aligned(self):
        long_tool_call_id = "call_abcdefghijklmnopqrstuvwxyz_1234567890abcd"
        messages = [
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": long_tool_call_id,
                        "type": "function",
                        "function": {"name": "search", "arguments": "{}"},
                    }
                ],
                "content": "",
            },
            {
                "role": "tool",
                "tool_call_id": long_tool_call_id,
                "content": "tool result",
            },
        ]

        normalized_count = self.filter._normalize_native_tool_call_ids(messages)

        normalized_id = messages[0]["tool_calls"][0]["id"]
        self.assertEqual(normalized_count, 1)
        self.assertLessEqual(len(normalized_id), 40)
        self.assertNotEqual(normalized_id, long_tool_call_id)
        self.assertEqual(messages[1]["tool_call_id"], normalized_id)

    def test_trim_native_tool_outputs_restores_real_behavior(self):
        messages = [
            {
                "role": "assistant",
                "tool_calls": [{"id": "call_1", "type": "function"}],
                "content": "",
            },
            {"role": "tool", "content": "x" * 1600},
            {"role": "assistant", "content": "Final answer"},
        ]

        trimmed_count = self.filter._trim_native_tool_outputs(messages, "en-US")

        self.assertEqual(trimmed_count, 1)
        self.assertEqual(messages[1]["content"], "... [Content collapsed] ...")
        self.assertTrue(messages[1]["metadata"]["is_trimmed"])
        self.assertTrue(messages[2]["metadata"]["tool_outputs_trimmed"])
        self.assertIn("Final answer", messages[2]["content"])
        self.assertIn("Tool outputs trimmed", messages[2]["content"])

    def test_trim_native_tool_outputs_supports_embedded_tool_call_cards(self):
        messages = [
            {
                "role": "assistant",
                "content": (
                    '<details type="tool_calls" done="true" id="call-1" '
                    'name="execute_code" arguments="&quot;{}&quot;" '
                    f'result="&quot;{"x" * 1600}&quot;">\n'
                    "<summary>Tool Executed</summary>\n"
                    "</details>\n"
                    "Final answer"
                ),
            }
        ]

        trimmed_count = self.filter._trim_native_tool_outputs(messages, "en-US")

        self.assertEqual(trimmed_count, 1)
        self.assertIn(
            'result="&quot;... [Content collapsed] ...&quot;"',
            messages[0]["content"],
        )
        self.assertNotIn("x" * 200, messages[0]["content"])
        self.assertTrue(messages[0]["metadata"]["tool_outputs_trimmed"])

    def test_function_calling_mode_reads_params_fallback(self):
        self.assertEqual(
            self.filter._get_function_calling_mode(
                {"params": {"function_calling": "native"}}
            ),
            "native",
        )

    def test_function_calling_mode_infers_native_from_message_shape(self):
        self.assertEqual(
            self.filter._get_function_calling_mode(
                {
                    "messages": [
                        {
                            "role": "assistant",
                            "tool_calls": [{"id": "call_1", "type": "function"}],
                            "content": "",
                        },
                        {"role": "tool", "content": "tool result"},
                    ]
                }
            ),
            "native",
        )

    def test_trim_native_tool_outputs_handles_pending_tool_chain(self):
        messages = [
            {
                "role": "assistant",
                "tool_calls": [{"id": "call_1", "type": "function"}],
                "content": "",
            },
            {"role": "tool", "content": "x" * 1600},
        ]

        trimmed_count = self.filter._trim_native_tool_outputs(messages, "en-US")

        self.assertEqual(trimmed_count, 1)
        self.assertEqual(messages[1]["content"], "... [Content collapsed] ...")
        self.assertTrue(messages[1]["metadata"]["is_trimmed"])

    def test_target_progress_uses_original_history_coordinates(self):
        self.filter.valves.keep_last = 2
        summary_message = self.filter._build_summary_message(
            "older summary", "en-US", 6
        )
        messages = [
            {"role": "system", "content": "System prompt"},
            summary_message,
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
            {"role": "user", "content": "Question 2"},
            {"role": "assistant", "content": "Answer 2"},
        ]

        self.assertEqual(self.filter._get_original_history_count(messages), 10)
        self.assertEqual(self.filter._calculate_target_compressed_count(messages), 8)

    def test_load_full_chat_messages_rebuilds_active_history_branch(self):
        class FakeChats:
            @staticmethod
            def get_chat_by_id(chat_id):
                return types.SimpleNamespace(
                    chat={
                        "history": {
                            "currentId": "m3",
                            "messages": {
                                "m1": {
                                    "id": "m1",
                                    "role": "user",
                                    "content": "Question",
                                },
                                "m2": {
                                    "id": "m2",
                                    "role": "assistant",
                                    "content": "Tool call",
                                    "tool_calls": [{"id": "call_1"}],
                                    "parentId": "m1",
                                },
                                "m3": {
                                    "id": "m3",
                                    "role": "tool",
                                    "content": "Tool result",
                                    "tool_call_id": "call_1",
                                    "parentId": "m2",
                                },
                            },
                        }
                    }
                )

        original_chats = module.Chats
        module.Chats = FakeChats
        try:
            messages = self.filter._load_full_chat_messages("chat-1")
        finally:
            module.Chats = original_chats

        self.assertEqual([message["id"] for message in messages], ["m1", "m2", "m3"])
        self.assertEqual(messages[2]["role"], "tool")

    def test_outlet_unfolds_compact_tool_details_view(self):
        compact_messages = [
            {"role": "user", "content": "U1"},
            {
                "role": "assistant",
                "content": (
                    '<details type="tool_calls" done="true" id="call-1" '
                    'name="search_notes" arguments="&quot;{}&quot;" '
                    f'result="&quot;{"x" * 3000}&quot;">\n'
                    "<summary>Tool Executed</summary>\n"
                    "</details>\n"
                    "Answer 1"
                ),
            },
            {"role": "user", "content": "U2"},
            {
                "role": "assistant",
                "content": (
                    '<details type="tool_calls" done="true" id="call-2" '
                    'name="merge_notes" arguments="&quot;{}&quot;" '
                    f'result="&quot;{"y" * 4000}&quot;">\n'
                    "<summary>Tool Executed</summary>\n"
                    "</details>\n"
                    "Answer 2"
                ),
            },
        ]

        async def fake_user_context(__user__, __event_call__):
            return {"user_language": "en-US"}

        async def noop_log(*args, **kwargs):
            return None

        create_task_called = False

        def fake_create_task(coro):
            nonlocal create_task_called
            create_task_called = True
            coro.close()
            return None

        self.filter._get_user_context = fake_user_context
        self.filter._get_chat_context = lambda body, metadata=None: {
            "chat_id": "chat-1",
            "message_id": "msg-1",
        }
        self.filter._should_skip_compression = lambda body, model: False
        self.filter._log = noop_log

        # Set a low threshold so the task is guaranteed to trigger
        self.filter.valves.compression_threshold_tokens = 100

        original_create_task = asyncio.create_task
        asyncio.create_task = fake_create_task
        try:
            asyncio.run(
                self.filter.outlet(
                    {"model": "test-model", "messages": compact_messages},
                    __event_call__=None,
                )
            )
        finally:
            asyncio.create_task = original_create_task

        self.assertTrue(create_task_called)

    def test_summary_save_progress_matches_truncated_input(self):
        self.filter.valves.keep_first = 1
        self.filter.valves.keep_last = 1
        self.filter.valves.summary_model = "fake-summary-model"
        self.filter.valves.summary_model_max_context = 0

        captured = {}
        events = []

        async def mock_emitter(event):
            events.append(event)

        async def mock_summary_llm(
            previous_summary,
            new_conversation_text,
            body,
            user_data,
            __event_call__,
        ):
            return "new summary"

        def mock_save_summary(chat_id, summary, compressed_count):
            captured["chat_id"] = chat_id
            captured["summary"] = summary
            captured["compressed_count"] = compressed_count

        async def noop_log(*args, **kwargs):
            return None

        self.filter._log = noop_log
        self.filter._call_summary_llm = mock_summary_llm
        self.filter._save_summary = mock_save_summary
        self.filter._get_model_thresholds = lambda model_id: {
            "max_context_tokens": 3500
        }
        self.filter._calculate_messages_tokens = lambda messages: len(messages) * 1000
        self.filter._count_tokens = lambda text: 1000

        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
            {"role": "user", "content": "Question 2"},
            {"role": "assistant", "content": "Answer 2"},
            {"role": "user", "content": "Question 3"},
        ]

        asyncio.run(
            self.filter._generate_summary_async(
                messages=messages,
                chat_id="chat-1",
                body={"model": "fake-summary-model"},
                user_data={"id": "user-1"},
                target_compressed_count=5,
                lang="en-US",
                __event_emitter__=mock_emitter,
                __event_call__=None,
            )
        )

        self.assertEqual(captured["chat_id"], "chat-1")
        self.assertEqual(captured["summary"], "new summary")
        self.assertEqual(captured["compressed_count"], 2)
        self.assertTrue(any(event["type"] == "status" for event in events))


if __name__ == "__main__":
    unittest.main()
