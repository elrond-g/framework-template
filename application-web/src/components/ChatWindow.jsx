import { useState, useEffect, useRef, useCallback } from "react";
import { getMessages, updateConversation, sendMessageStream, retryMessageStream } from "../api/chat";
import MessageBubble from "./MessageBubble";
import MessageInput from "./MessageInput";
import TextInput from "./TextInput";
import "./ChatWindow.css";

function ChatWindow({ conversationId, onTitleUpdated }) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);
  // 用 ref 跟踪流式拼接，避免闭包陈旧问题
  const streamRef = useRef({ thinking: "", content: "" });

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

  // 更新正在流式生成的 assistant 消息
  const updateStreamingMsg = useCallback(() => {
    setMessages((prev) => {
      const copy = [...prev];
      const last = copy[copy.length - 1];
      if (last && last._streaming) {
        copy[copy.length - 1] = {
          ...last,
          thinking: streamRef.current.thinking,
          content: streamRef.current.content,
        };
      }
      return copy;
    });
  }, []);

  const handleSend = async (text, formData) => {
    const userMsg = { id: Date.now().toString(), role: "user", content: text };

    // 插入 user 消息 + 空的 streaming assistant 消息
    const streamingMsg = {
      id: `streaming-${Date.now()}`,
      role: "assistant",
      content: "",
      thinking: "",
      _streaming: true,
    };
    setMessages((prev) => [...prev, userMsg, streamingMsg]);
    setLoading(true);
    setError(null);
    streamRef.current = { thinking: "", content: "" };

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

    await sendMessageStream(conversationId, text, {
      onThinking: (chunk) => {
        streamRef.current.thinking += chunk;
        updateStreamingMsg();
      },
      onContent: (chunk) => {
        streamRef.current.content += chunk;
        updateStreamingMsg();
      },
      onDone: (data) => {
        setMessages((prev) => {
          const copy = [...prev];
          const last = copy[copy.length - 1];
          if (last && last._streaming) {
            copy[copy.length - 1] = {
              id: data.id,
              role: "assistant",
              content: streamRef.current.content,
              thinking: data.thinking || streamRef.current.thinking,
              created_at: data.created_at,
            };
          }
          return copy;
        });
        setLoading(false);
      },
      onError: (msg) => {
        setMessages((prev) => {
          const copy = [...prev];
          // 如果最后一条是 streaming 占位，替换为 error
          const last = copy[copy.length - 1];
          if (last && last._streaming) {
            copy[copy.length - 1] = {
              id: `error-${Date.now()}`,
              role: "error",
              content: msg || "发送失败，请重试",
            };
          } else {
            copy.push({
              id: `error-${Date.now()}`,
              role: "error",
              content: msg || "发送失败，请重试",
            });
          }
          return copy;
        });
        setLoading(false);
      },
    });
  };

  // 普通追问：只发送文本消息，不传 formData
  const handleTextSend = async (text) => {
    await handleSend(text, null);
  };

  // 重试最后一轮对话
  const handleRetry = async () => {
    // 移除最后一条 assistant/error 消息，插入 streaming 占位
    const streamingMsg = {
      id: `streaming-${Date.now()}`,
      role: "assistant",
      content: "",
      thinking: "",
      _streaming: true,
    };
    setMessages((prev) => {
      const copy = [...prev];
      for (let i = copy.length - 1; i >= 0; i--) {
        if (copy[i].role === "assistant" || copy[i].role === "error") {
          copy.splice(i, 1);
          break;
        }
      }
      return [...copy, streamingMsg];
    });
    setLoading(true);
    setError(null);
    streamRef.current = { thinking: "", content: "" };

    await retryMessageStream(conversationId, {
      onThinking: (chunk) => {
        streamRef.current.thinking += chunk;
        updateStreamingMsg();
      },
      onContent: (chunk) => {
        streamRef.current.content += chunk;
        updateStreamingMsg();
      },
      onDone: (data) => {
        setMessages((prev) => {
          const copy = [...prev];
          const last = copy[copy.length - 1];
          if (last && last._streaming) {
            copy[copy.length - 1] = {
              id: data.id,
              role: "assistant",
              content: streamRef.current.content,
              thinking: data.thinking || streamRef.current.thinking,
              created_at: data.created_at,
            };
          }
          return copy;
        });
        setLoading(false);
      },
      onError: (msg) => {
        setMessages((prev) => {
          const copy = [...prev];
          const last = copy[copy.length - 1];
          if (last && last._streaming) {
            copy[copy.length - 1] = {
              id: `error-${Date.now()}`,
              role: "error",
              content: msg || "重试失败，请稍后再试",
            };
          } else {
            copy.push({
              id: `error-${Date.now()}`,
              role: "error",
              content: msg || "重试失败，请稍后再试",
            });
          }
          return copy;
        });
        setLoading(false);
      },
    });
  };

  // 会话无消息时显示八字表单，有消息后显示普通输入框
  const isNewConversation = messages.length === 0;

  // 找到最后一条 assistant/error 消息的 id，用于显示重试按钮
  let lastRetryableId = null;
  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i];
    if ((msg.role === "assistant" || msg.role === "error") && !msg._streaming) {
      lastRetryableId = msg.id;
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
            thinking={msg.thinking}
            showRetry={!loading && msg.id === lastRetryableId}
            onRetry={handleRetry}
          />
        ))}
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
