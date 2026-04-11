import { useState, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import html2canvas from "html2canvas";

function MessageBubble({
  role, content, thinking, showRetry, onRetry,
  inputTokens, outputTokens, thinkingDurationMs, totalDurationMs,
}) {
  const [thinkingExpanded, setThinkingExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  const [saving, setSaving] = useState(false);
  const bubbleRef = useRef(null);

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

  const hasStats = role === "assistant" && (inputTokens != null || outputTokens != null || totalDurationMs != null);

  const handleSaveImage = async () => {
    if (!bubbleRef.current || saving) return;
    setSaving(true);
    try {
      // 截图时临时隐藏操作栏和统计栏，只保留消息内容
      const actions = bubbleRef.current.querySelector(".message-actions");
      const stats = bubbleRef.current.querySelector(".message-stats");
      if (actions) actions.style.display = "none";
      if (stats) stats.style.display = "none";

      const canvas = await html2canvas(bubbleRef.current, {
        backgroundColor: "#0f0f14",
        scale: 2,
      });

      // 恢复显示
      if (actions) actions.style.display = "";
      if (stats) stats.style.display = "";

      const link = document.createElement("a");
      link.download = `message-${Date.now()}.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
    } catch {
      // 静默失败
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className={`message-bubble ${role}`} ref={bubbleRef}>
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
        {role === "assistant" && content && (
          <button className="save-img-btn" onClick={handleSaveImage} disabled={saving} title="保存为图片">
            {saving ? (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" strokeDasharray="31.4" strokeDashoffset="10">
                  <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite" />
                </circle>
              </svg>
            ) : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <circle cx="8.5" cy="8.5" r="1.5"></circle>
                <polyline points="21 15 16 10 5 21"></polyline>
              </svg>
            )}
            <span>{saving ? "保存中..." : "保存图片"}</span>
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
      {hasStats && (
        <div className="message-stats">
          {inputTokens != null && <span>输入 {inputTokens}</span>}
          {outputTokens != null && <span>输出 {outputTokens}</span>}
          {thinkingDurationMs != null && thinkingDurationMs > 0 && (
            <span>思考 {(thinkingDurationMs / 1000).toFixed(1)}s</span>
          )}
          {totalDurationMs != null && (
            <span>耗时 {(totalDurationMs / 1000).toFixed(1)}s</span>
          )}
        </div>
      )}
    </div>
  );
}

export default MessageBubble;
