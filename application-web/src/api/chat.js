const BASE = "/api/chat";

async function request(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  return res.json();
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
