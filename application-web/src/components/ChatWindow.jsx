import { useState, useEffect, useRef, useCallback } from "react";
import { getMessages, updateConversation, sendMessageStream, retryMessageStream } from "../api/chat";
import MessageBubble from "./MessageBubble";
import MessageInput from "./MessageInput";
import TextInput from "./TextInput";
import "./ChatWindow.css";

function ChatWindow({ conversationId, onTitleUpdated, initialMessage, onInitialMessageConsumed }) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);
  // 用 ref 跟踪流式拼接，避免闭包陈旧问题
  const streamRef = useRef({ thinking: "", content: "" });
  // 用 ref 读取最新的 initialMessage，避免加入 useEffect 依赖触发重复加载
  const initialMessageRef = useRef(initialMessage);
  useEffect(() => {
    initialMessageRef.current = initialMessage;
  }, [initialMessage]);
  // 记录上一次已初始化的 conversationId，StrictMode 下 effect 双跑时用于幂等短路，
  // 防止第二次 setMessages([]) 清空刚刚插入的 streaming 消息
  const initializedConvIdRef = useRef(null);

  const loadMessages = async () => {
    setError(null);
    const res = await getMessages(conversationId);
    if (res.code === 0) {
      setMessages(res.data || []);
      return res.data || [];
    }
    setError(res.message);
    return [];
  };

  useEffect(() => {
    if (initializedConvIdRef.current === conversationId) return;
    initializedConvIdRef.current = conversationId;
    setMessages([]);
    setError(null);
    (async () => {
      const loaded = await loadMessages();
      const pending = initialMessageRef.current;
      // 仅当新会话且外层挂有首条消息时，自动发起首轮对话
      if (pending && loaded.length === 0) {
        onInitialMessageConsumed?.();
        handleSend(pending.text, pending.formData);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
              input_tokens: data.input_tokens,
              output_tokens: data.output_tokens,
              thinking_duration_ms: data.thinking_duration_ms,
              total_duration_ms: data.total_duration_ms,
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
              input_tokens: data.input_tokens,
              output_tokens: data.output_tokens,
              thinking_duration_ms: data.thinking_duration_ms,
              total_duration_ms: data.total_duration_ms,
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
        {messages.map((msg) => {
          // 流式占位消息且尚无内容时，显示加载动画代替空气泡
          if (msg._streaming && !msg.content && !msg.thinking) {
            return (
              <div key={msg.id} className="message-bubble assistant loading-bubble">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                  <span className="typing-label">正在思考</span>
                </div>
              </div>
            );
          }
          return (
            <MessageBubble
              key={msg.id}
              role={msg.role}
              content={msg.content}
              thinking={msg.thinking}
              showRetry={!loading && msg.id === lastRetryableId}
              onRetry={handleRetry}
              inputTokens={msg.input_tokens}
              outputTokens={msg.output_tokens}
              thinkingDurationMs={msg.thinking_duration_ms}
              totalDurationMs={msg.total_duration_ms}
            />
          );
        })}
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
