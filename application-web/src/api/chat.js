const BASE = "/api/chat";

async function request(url, options = {}) {
  try {
    const res = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });

    if (!res.ok) {
      // 尝试解析服务端错误响应
      try {
        const body = await res.json();
        return {
          code: body.code || res.status,
          message: body.message || `请求失败 (${res.status})`,
          data: null,
        };
      } catch {
        return { code: res.status, message: `请求失败 (${res.status})`, data: null };
      }
    }

    return await res.json();
  } catch (err) {
    // 网络错误、DNS 解析失败、连接拒绝等
    return { code: -1, message: "网络连接失败，请检查网络后重试", data: null };
  }
}

export function createConversation(title = "New Conversation", systemPrompt = null) {
  const body = { title };
  if (systemPrompt && systemPrompt.trim()) {
    body.system_prompt = systemPrompt.trim();
  }
  return request(`${BASE}/conversations`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function listConversations() {
  return request(`${BASE}/conversations`);
}

export function getMessages(conversationId) {
  return request(`${BASE}/conversations/${conversationId}/messages`);
}

export function deleteConversation(conversationId) {
  return request(`${BASE}/conversations/${conversationId}`, {
    method: "DELETE",
  });
}

export function updateConversation(conversationId, title) {
  return request(`${BASE}/conversations/${conversationId}`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  });
}

/**
 * 流式发送消息。
 * @param {string} conversationId
 * @param {string} message
 * @param {object} callbacks - { onThinking, onContent, onDone, onError }
 */
export async function sendMessageStream(conversationId, message, callbacks) {
  return _streamRequest(
    `${BASE}/conversations/${conversationId}/chat`,
    { method: "POST", body: JSON.stringify({ message }) },
    callbacks,
  );
}

/**
 * 流式重试。
 * @param {string} conversationId
 * @param {object} callbacks - { onThinking, onContent, onDone, onError }
 */
export async function retryMessageStream(conversationId, callbacks) {
  return _streamRequest(
    `${BASE}/conversations/${conversationId}/retry`,
    { method: "POST" },
    callbacks,
  );
}

/**
 * 内部：通过 SSE 流式读取后端响应。
 */
async function _streamRequest(url, fetchOptions, { onThinking, onContent, onDone, onError }) {
  try {
    const res = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...fetchOptions,
    });

    if (!res.ok) {
      let msg = `请求失败 (${res.status})`;
      try {
        const body = await res.json();
        msg = body.message || msg;
      } catch { /* ignore */ }
      onError?.(msg);
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // 按双换行分割 SSE 事件
      const parts = buffer.split("\n\n");
      buffer = parts.pop(); // 最后一段可能不完整，保留在 buffer

      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith("data: ")) continue;

        const jsonStr = line.slice(6);
        let data;
        try {
          data = JSON.parse(jsonStr);
        } catch {
          continue;
        }

        switch (data.type) {
          case "thinking":
            onThinking?.(data.content);
            break;
          case "content":
            onContent?.(data.content);
            break;
          case "done":
            onDone?.(data);
            break;
          case "error":
            onError?.(data.message);
            break;
        }
      }
    }

    // 处理 buffer 中可能残留的最后一个事件
    if (buffer.trim()) {
      const line = buffer.trim();
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          switch (data.type) {
            case "thinking": onThinking?.(data.content); break;
            case "content": onContent?.(data.content); break;
            case "done": onDone?.(data); break;
            case "error": onError?.(data.message); break;
          }
        } catch { /* ignore */ }
      }
    }
  } catch (err) {
    onError?.("网络连接失败，请检查网络后重试");
  }
}

// 保留非流式版本供兼容使用
export function sendMessage(conversationId, message) {
  return request(`${BASE}/conversations/${conversationId}/chat`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export function retryMessage(conversationId) {
  return request(`${BASE}/conversations/${conversationId}/retry`, {
    method: "POST",
  });
}
