import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function MessageBubble({ role, content, thinking, showRetry, onRetry }) {
  const [thinkingExpanded, setThinkingExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content || "");
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // 降级：使用旧版 API
      const textarea = document.createElement("textarea");
      textarea.value = content || "";
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className={`message-bubble ${role}`}>
      {/* 思考内容折叠区域 */}
      {role === "assistant" && thinking && (
        <div className="thinking-section">
          <button
            className="thinking-toggle"
            onClick={() => setThinkingExpanded(!thinkingExpanded)}
          >
            <svg
              className={`thinking-arrow ${thinkingExpanded ? "expanded" : ""}`}
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polyline points="9 18 15 12 9 6"></polyline>
            </svg>
            <span>思考过程</span>
          </button>
          {thinkingExpanded && (
            <div className="thinking-content">{thinking}</div>
          )}
        </div>
      )}
      <div className="message-content">
        {role === "assistant" ? (
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content || ""}</ReactMarkdown>
        ) : (
          content
        )}
      </div>
      <div className="message-actions">
        {role === "assistant" && content && (
          <button className="copy-btn" onClick={handleCopy} title="复制内容">
            {copied ? (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            ) : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
            )}
            <span>{copied ? "已复制" : "复制"}</span>
          </button>
        )}
        {showRetry && (role === "assistant" || role === "error") && (
          <button className="retry-btn" onClick={onRetry}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="23 4 23 10 17 10"></polyline>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
            </svg>
            <span>重试</span>
          </button>
        )}
      </div>
    </div>
  );
}

export default MessageBubble;
