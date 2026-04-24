"""Controller 层集成测试：FastAPI TestClient + 内存 DB + mock 掉 LLM。

默认情况下 LLMStep 在 LLM_API_KEY 为空时走 Mock 分支，所以聊天接口可直接测。
"""

import json

import pytest


class TestSystemController:
    def test_health(self, client):
        resp = client.get("/api/system/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["status"] == "ok"
        assert body["data"]["version"]


class TestChatConversationController:
    def test_create_list_update_delete(self, client):
        # create
        resp = client.post("/api/chat/conversations", json={"title": "A"})
        assert resp.status_code == 200
        conv = resp.json()["data"]
        assert conv["title"] == "A"
        conv_id = conv["id"]

        # list
        resp = client.get("/api/chat/conversations")
        titles = [c["title"] for c in resp.json()["data"]]
        assert "A" in titles

        # update title
        resp = client.patch(
            f"/api/chat/conversations/{conv_id}", json={"title": "B"}
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "B"

        # delete
        resp = client.delete(f"/api/chat/conversations/{conv_id}")
        assert resp.status_code == 200
        assert resp.json()["code"] == 0

        # delete again → 404
        resp = client.delete(f"/api/chat/conversations/{conv_id}")
        assert resp.status_code == 404

    def test_update_missing_returns_404(self, client):
        resp = client.patch(
            "/api/chat/conversations/not-exist", json={"title": "x"}
        )
        assert resp.status_code == 404
        assert resp.json()["code"] == 404

    def test_get_messages_missing_returns_404(self, client):
        resp = client.get("/api/chat/conversations/none/messages")
        assert resp.status_code == 404

    def test_create_with_system_prompt(self, client):
        resp = client.post(
            "/api/chat/conversations",
            json={"title": "T", "system_prompt": "你是助手"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["system_prompt"] == "你是助手"


def _parse_sse(body_text: str) -> list[dict]:
    """解析 SSE 响应字符串为 payload 列表。"""
    out: list[dict] = []
    for line in body_text.splitlines():
        line = line.strip()
        if not line.startswith("data: "):
            continue
        payload = json.loads(line[len("data: "):])
        out.append(payload)
    return out


class TestChatStreamingController:
    def test_chat_stream_mock_response(self, client):
        # 1. 创建会话
        resp = client.post("/api/chat/conversations", json={"title": "t"})
        conv_id = resp.json()["data"]["id"]

        # 2. 发起流式聊天（无 LLM_API_KEY → 走 mock 流式）
        with client.stream(
            "POST",
            f"/api/chat/conversations/{conv_id}/chat",
            json={"message": "你好"},
        ) as resp:
            assert resp.status_code == 200
            text = "".join(chunk for chunk in resp.iter_text())

        payloads = _parse_sse(text)
        types = [p["type"] for p in payloads]
        assert "content" in types
        assert types[-1] == "done"

        # 3. 历史消息被落库
        resp = client.get(f"/api/chat/conversations/{conv_id}/messages")
        msgs = resp.json()["data"]
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"
        assert "[Mock Response]" in msgs[1]["content"]

    def test_retry_stream_mock_response(self, client):
        # 准备一条完整对话
        resp = client.post("/api/chat/conversations", json={"title": "t"})
        conv_id = resp.json()["data"]["id"]
        with client.stream(
            "POST",
            f"/api/chat/conversations/{conv_id}/chat",
            json={"message": "hi"},
        ) as r:
            list(r.iter_text())

        # retry 会删除上一次 assistant 并重新生成
        with client.stream(
            "POST", f"/api/chat/conversations/{conv_id}/retry"
        ) as r:
            assert r.status_code == 200
            text = "".join(r.iter_text())

        payloads = _parse_sse(text)
        assert payloads[-1]["type"] == "done"

        msgs = client.get(
            f"/api/chat/conversations/{conv_id}/messages"
        ).json()["data"]
        assert len([m for m in msgs if m["role"] == "assistant"]) == 1
