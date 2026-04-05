import { useState, useEffect, useRef } from "react";
import { getMessages, sendMessage } from "../api/chat";
import MessageBubble from "./MessageBubble";
import MessageInput from "./MessageInput";
import "./ChatWindow.css";

function ChatWindow({ conversationId }) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  const loadMessages = async () => {
    const res = await getMessages(conversationId);
    if (res.code === 0) setMessages(res.data || []);
  };

  useEffect(() => {
    setMessages([]);
    loadMessages();
  }, [conversationId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (text) => {
    const userMsg = { id: Date.now().toString(), role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    const res = await sendMessage(conversationId, text);
    setLoading(false);

    if (res.code === 0 && res.data) {
      setMessages((prev) => [...prev, res.data]);
    }
  };

  return (
    <div className="chat-window">
      <div className="messages">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} role={msg.role} content={msg.content} />
        ))}
        {loading && (
          <div className="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <MessageInput onSend={handleSend} disabled={loading} />
    </div>
  );
}

export default ChatWindow;
