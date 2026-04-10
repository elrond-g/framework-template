import { useState, useEffect, useRef } from "react";
import { getMessages, sendMessage, updateConversation, retryMessage } from "../api/chat";
import MessageBubble from "./MessageBubble";
import MessageInput from "./MessageInput";
import TextInput from "./TextInput";
import "./ChatWindow.css";

function ChatWindow({ conversationId, onTitleUpdated }) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);

  const loadMessages = async () => {
    setError(null);
    const res = await getMessages(conversationId);
    if (res.code === 0) {
      setMessages(res.data || []);
    } else {
      setError(res.message);
    }
  };

  useEffect(() => {
    setMessages([]);
    setError(null);
    loadMessages();
  }, [conversationId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (text, formData) => {
    const userMsg = { id: Date.now().toString(), role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    setError(null);

    // 首次发送消息时，使用八字表单信息更新会话标题
    if (formData && messages.length === 0) {
      const { year, month, day, hour, minute, gender, directions } = formData;
      const dirText = directions.join("、");
      const title = `${year}年${month}月${day}日 ${hour}:${minute} ${gender} ${dirText}`;
      const titleRes = await updateConversation(conversationId, title);
      if (titleRes.code === 0 && onTitleUpdated) {
        onTitleUpdated();
      }
    }

    const res = await sendMessage(conversationId, text);
    setLoading(false);

    if (res.code === 0 && res.data) {
      setMessages((prev) => [...prev, res.data]);
    } else {
      const errorMsg = {
        id: `error-${Date.now()}`,
        role: "error",
        content: res.message || "发送失败，请重试",
      };
      setMessages((prev) => [...prev, errorMsg]);
    }
  };

  // 普通追问：只发送文本消息，不传 formData
  const handleTextSend = async (text) => {
    await handleSend(text, null);
  };

  // 重试最后一轮对话
  const handleRetry = async () => {
    // 移除最后一条 assistant/error 消息
    setMessages((prev) => {
      const copy = [...prev];
      for (let i = copy.length - 1; i >= 0; i--) {
        if (copy[i].role === "assistant" || copy[i].role === "error") {
          copy.splice(i, 1);
          break;
        }
      }
      return copy;
    });
    setLoading(true);
    setError(null);

    const res = await retryMessage(conversationId);
    setLoading(false);

    if (res.code === 0 && res.data) {
      setMessages((prev) => [...prev, res.data]);
    } else {
      const errorMsg = {
        id: `error-${Date.now()}`,
        role: "error",
        content: res.message || "重试失败，请稍后再试",
      };
      setMessages((prev) => [...prev, errorMsg]);
    }
  };

  // 会话无消息时显示八字表单，有消息后显示普通输入框
  const isNewConversation = messages.length === 0;

  // 找到最后一条 assistant/error 消息的 id，用于显示重试按钮
  let lastRetryableId = null;
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].role === "assistant" || messages[i].role === "error") {
      lastRetryableId = messages[i].id;
      break;
    }
  }

  return (
    <div className="chat-window">
      <div className="messages">
        {error && <div className="chat-error-tip">{error}</div>}
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            role={msg.role}
            content={msg.content}
            showRetry={!loading && msg.id === lastRetryableId}
            onRetry={handleRetry}
          />
        ))}
        {loading && (
          <div className="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      {isNewConversation ? (
        <MessageInput onSend={handleSend} disabled={loading} />
      ) : (
        <TextInput onSend={handleTextSend} disabled={loading} />
      )}
    </div>
  );
}

export default ChatWindow;
