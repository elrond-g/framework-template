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

export function createConversation(title = "New Conversation") {
  return request(`${BASE}/conversations`, {
    method: "POST",
    body: JSON.stringify({ title }),
  });
}

export function listConversations() {
  return request(`${BASE}/conversations`);
}

export function getMessages(conversationId) {
  return request(`${BASE}/conversations/${conversationId}/messages`);
}

export function sendMessage(conversationId, message) {
  return request(`${BASE}/conversations/${conversationId}/chat`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
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
